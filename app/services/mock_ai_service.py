import random
import re
from typing import Dict, List, Optional, Any
from app.core.ai_chat_config import MOCK_RESPONSE_TEMPLATES, ai_chat_settings

class MockAIService:
    """Mock AI service for development and testing without OpenAI API."""
    
    def __init__(self):
        self.conversation_state = {}
        self.common_extractions = {
            "age": r"\b(\d{1,2})\s*(?:years?\s*old|yo|y\.o\.)\b",
            "family_history": r"\b(?:mother|father|sister|brother|aunt|uncle|grandmother|grandfather)\b.*\b(?:cancer|tumor|malignancy)\b",
            "symptoms": r"\b(?:pain|lump|discharge|changes|concerns?)\b",
            "medications": r"\b(?:taking|on|medication|drug|pill|treatment)\b",
            "medical_history": r"\b(?:history|diagnosed|had|previous)\b.*\b(?:cancer|surgery|condition|disease)\b"
        }
    
    async def generate_response(
        self, 
        session_id: str,
        user_message: str, 
        conversation_history: List[Dict],
        extracted_data: Dict,
        strategy_config: Dict
    ) -> Dict[str, Any]:
        """Generate a mock AI response based on conversation context."""
        
        specialty = strategy_config.get("specialty", "general").lower()
        templates = MOCK_RESPONSE_TEMPLATES.get(specialty, MOCK_RESPONSE_TEMPLATES["general"])
        
        # Track conversation state
        if session_id not in self.conversation_state:
            self.conversation_state[session_id] = {
                "turn_count": 0,
                "topics_covered": set(),
                "assessment_complete": False
            }
        
        state = self.conversation_state[session_id]
        state["turn_count"] += 1
        
        # Determine response type based on conversation progress
        if state["turn_count"] == 1:
            response_type = "welcome"
        elif state["turn_count"] < 8 and not state["assessment_complete"]:
            response_type = "follow_up"
        elif not state["assessment_complete"]:
            response_type = "assessment"
            state["assessment_complete"] = True
        else:
            response_type = "closing"
        
        # Generate contextual response
        response_content = self._generate_contextual_response(
            user_message, extracted_data, templates, response_type, specialty
        )
        
        return {
            "content": response_content,
            "metadata": {
                "mock_mode": True,
                "response_type": response_type,
                "turn_count": state["turn_count"],
                "confidence": 0.85  # Mock confidence score
            }
        }
    
    def _generate_contextual_response(
        self, 
        user_message: str, 
        extracted_data: Dict, 
        templates: Dict, 
        response_type: str,
        specialty: str
    ) -> str:
        """Generate contextual response based on user message and extracted data."""
        
        template = templates[response_type]
        
        if response_type == "welcome":
            return template
        
        elif response_type == "follow_up":
            # Extract key information from user message
            extracted_info = self._summarize_extracted_info(extracted_data, user_message)
            next_topic = self._determine_next_topic(extracted_data, specialty)
            
            return template.format(
                extracted_info=extracted_info,
                next_topic=next_topic
            )
        
        elif response_type == "assessment":
            summary = self._generate_assessment_summary(extracted_data, specialty)
            return template.format(summary=summary)
        
        else:  # closing
            return template
    
    def _summarize_extracted_info(self, extracted_data: Dict, user_message: str) -> str:
        """Summarize the information extracted from the user's message."""
        summaries = []
        
        if "age" in extracted_data:
            summaries.append(f"you're {extracted_data['age']} years old")
        
        if "family_history" in extracted_data:
            summaries.append("you have a family history of cancer")
        
        if "symptoms" in user_message.lower():
            summaries.append("you mentioned some symptoms")
        
        if not summaries:
            summaries.append("you shared that information")
        
        return ", ".join(summaries)
    
    def _determine_next_topic(self, extracted_data: Dict, specialty: str) -> str:
        """Determine the next topic to ask about based on specialty and current data."""
        
        if specialty == "oncology":
            if "family_history" not in extracted_data:
                return "your family history"
            elif "symptoms" not in extracted_data:
                return "any symptoms or concerns"
            elif "medical_history" not in extracted_data:
                return "your medical history"
            else:
                return "your lifestyle factors"
        
        elif specialty == "genetics":
            if "family_history" not in extracted_data:
                return "your family's cancer history"
            elif "ethnicity" not in extracted_data:
                return "your ethnic background"
            else:
                return "previous genetic testing"
        
        else:
            return "your health concerns"
    
    def _generate_assessment_summary(self, extracted_data: Dict, specialty: str) -> str:
        """Generate a summary of the assessment based on extracted data."""
        
        summary_parts = []
        
        if "age" in extracted_data:
            age = extracted_data["age"]
            if specialty == "oncology":
                if age >= 40:
                    summary_parts.append(f"At {age} years old, you're in the age group where regular screening is recommended")
                else:
                    summary_parts.append(f"At {age} years old, we'll consider your risk factors for screening recommendations")
        
        if "family_history" in extracted_data:
            summary_parts.append("Your family history of cancer is an important risk factor to consider")
        
        if not summary_parts:
            summary_parts.append("You've provided valuable information about your health")
        
        return ". ".join(summary_parts) + "."
    
    async def extract_entities_mock(self, text: str, context: Dict) -> Dict[str, Any]:
        """Mock entity extraction without requiring spaCy or advanced NLP."""
        
        extracted = {}
        text_lower = text.lower()
        
        # Extract age
        age_match = re.search(self.common_extractions["age"], text_lower)
        if age_match:
            try:
                extracted["age"] = int(age_match.group(1))
            except ValueError:
                pass
        
        # Extract family history
        if re.search(self.common_extractions["family_history"], text_lower):
            extracted["family_history"] = "positive"
        
        # Extract symptoms
        if re.search(self.common_extractions["symptoms"], text_lower):
            extracted["symptoms"] = "reported"
        
        # Extract medications
        if re.search(self.common_extractions["medications"], text_lower):
            extracted["medications"] = "mentioned"
        
        # Extract medical history
        if re.search(self.common_extractions["medical_history"], text_lower):
            extracted["medical_history"] = "positive"
        
        return extracted
    
    async def generate_embeddings_mock(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for RAG functionality."""
        # Return random embeddings for testing
        return [[random.random() for _ in range(1536)] for _ in texts]
