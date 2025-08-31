"""
Entity Extraction Service

This service handles extraction of structured information from user messages
during AI chat conversations for patient assessment and data collection.
"""
import re
import json
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.repositories.ai_chat_repository import AIChatRepository
from app.models.ai_chat import AIChatSession, ExtractionRule
from app.models.chat_configuration import ChatStrategy
from app.core.ai_chat_config import get_ai_chat_settings, ai_chat_settings
from app.services.base import BaseService
from app.services.mock_ai_service import MockAIService


class EntityExtractionService(BaseService):
    """Service for extracting entities and structured data from chat messages."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.db = db
        self.ai_chat_repo = AIChatRepository(db)
        self.settings = get_ai_chat_settings()
        
        if ai_chat_settings.should_use_mock_mode:
            self.mock_service = MockAIService()
            self.use_mock_mode = True
        else:
            self.use_mock_mode = False
            # Initialize real extraction services
            try:
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
            except (ImportError, OSError):
                # Fallback to mock mode if spaCy is not available
                self.mock_service = MockAIService()
                self.use_mock_mode = True
    
    async def extract_entities(
        self, 
        message: str, 
        session: AIChatSession,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract entities from a user message based on session strategy."""
        try:
            if self.use_mock_mode:
                return await self.mock_service.extract_entities_mock(message, context or {})
            
            # Get extraction rules for the strategy
            strategy = self.ai_chat_repo.get_strategy_by_id(session.strategy_id)
            if not strategy or not strategy.extraction_rules:
                return {}
            
            extracted_data = {}
            
            # Apply each extraction rule
            for rule_config in strategy.extraction_rules:
                rule_result = self._apply_extraction_rule(message, rule_config, context or {})
                if rule_result:
                    extracted_data.update(rule_result)
            
            # Apply general extraction patterns
            general_extractions = self._extract_general_entities(message)
            extracted_data.update(general_extractions)
            
            return extracted_data
            
        except Exception as e:
            print(f"Error in entity extraction: {str(e)}")
            return {}
    
    def _apply_extraction_rule(
        self, 
        message: str, 
        rule_config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a specific extraction rule to the message."""
        extracted = {}
        
        rule_type = rule_config.get("type", "")
        field_name = rule_config.get("field", "")
        
        if rule_type == "age":
            age = self._extract_age(message)
            if age:
                extracted[field_name] = age
        
        elif rule_type == "yes_no":
            response = self._extract_yes_no(message)
            if response:
                extracted[field_name] = response
        
        elif rule_type == "family_history":
            family_history = self._extract_family_history(message)
            if family_history:
                extracted[field_name] = family_history
        
        elif rule_type == "medical_condition":
            conditions = self._extract_medical_conditions(message)
            if conditions:
                extracted[field_name] = conditions
        
        elif rule_type == "date":
            extracted_date = self._extract_date(message)
            if extracted_date:
                extracted[field_name] = extracted_date
        
        elif rule_type == "keyword":
            keywords = rule_config.get("keywords", [])
            if self._contains_keywords(message, keywords):
                extracted[field_name] = True
        
        elif rule_type == "pattern":
            pattern = rule_config.get("pattern", "")
            value = self._extract_by_pattern(message, pattern)
            if value:
                extracted[field_name] = value
        
        return extracted
    
    def _extract_general_entities(self, message: str) -> Dict[str, Any]:
        """Extract common entities that are useful across different strategies."""
        extracted = {}
        
        # Extract age
        age = self._extract_age(message)
        if age:
            extracted["age"] = age
        
        # Extract yes/no responses
        yes_no = self._extract_yes_no(message)
        if yes_no:
            extracted["last_response"] = yes_no
        
        # Extract family relationships
        family_relations = self._extract_family_relationships(message)
        if family_relations:
            extracted["mentioned_family"] = family_relations
        
        # Extract medical terms
        medical_terms = self._extract_medical_terms(message)
        if medical_terms:
            extracted["medical_terms"] = medical_terms
        
        return extracted
    
    def _extract_age(self, message: str) -> Optional[int]:
        """Extract age from message."""
        patterns = [
            r'\b(\d{1,3})\s*(?:years?\s*old|yrs?\s*old|year old|yr old)\b',
            r'\bi\s*am\s*(\d{1,3})\b',
            r'\bage\s*(\d{1,3})\b',
            r'\b(\d{1,3})\s*(?:years?|yrs?)\s*(?:of\s*age)?\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                age = int(match.group(1))
                if 0 <= age <= 120:  # Reasonable age range
                    return age
        
        return None
    
    def _extract_yes_no(self, message: str) -> Optional[str]:
        """Extract yes/no response from message."""
        message_lower = message.lower().strip()
        
        # Direct yes/no
        if re.match(r'^(yes|yeah|yep|yup|sure|absolutely|definitely)\.?$', message_lower):
            return "yes"
        if re.match(r'^(no|nope|nah|not really|absolutely not)\.?$', message_lower):
            return "no"
        
        # In context
        yes_patterns = [
            r'\b(yes|yeah|yep|yup|sure|absolutely|definitely)\b',
            r'\bi\s*(do|have|am|did|will)\b',
            r'\bthat\'s\s*(right|correct|true)\b'
        ]
        
        no_patterns = [
            r'\b(no|nope|nah|not really|absolutely not)\b',
            r'\bi\s*(don\'t|haven\'t|am not|didn\'t|won\'t)\b',
            r'\bnever\b',
            r'\bnot\s*(at\s*all|really)\b'
        ]
        
        # Count yes vs no indicators
        yes_count = sum(1 for pattern in yes_patterns if re.search(pattern, message_lower))
        no_count = sum(1 for pattern in no_patterns if re.search(pattern, message_lower))
        
        if yes_count > no_count and yes_count > 0:
            return "yes"
        elif no_count > yes_count and no_count > 0:
            return "no"
        
        return None
    
    def _extract_family_history(self, message: str) -> Dict[str, Any]:
        """Extract family history information."""
        family_history = {}
        message_lower = message.lower()
        
        # Family relationships
        relationships = {
            'mother': ['mother', 'mom', 'maternal'],
            'father': ['father', 'dad', 'paternal'],
            'sister': ['sister'],
            'brother': ['brother'],
            'grandmother': ['grandmother', 'grandma', 'granny'],
            'grandfather': ['grandfather', 'grandpa'],
            'aunt': ['aunt'],
            'uncle': ['uncle'],
            'cousin': ['cousin']
        }
        
        mentioned_relations = []
        for relation, keywords in relationships.items():
            if any(keyword in message_lower for keyword in keywords):
                mentioned_relations.append(relation)
        
        if mentioned_relations:
            family_history['mentioned_relations'] = mentioned_relations
        
        # Medical conditions in family context
        medical_conditions = ['cancer', 'breast cancer', 'ovarian cancer', 'diabetes', 'heart disease']
        mentioned_conditions = []
        
        for condition in medical_conditions:
            if condition in message_lower:
                mentioned_conditions.append(condition)
        
        if mentioned_conditions:
            family_history['mentioned_conditions'] = mentioned_conditions
        
        return family_history
    
    def _extract_family_relationships(self, message: str) -> List[str]:
        """Extract mentioned family relationships."""
        relationships = [
            'mother', 'mom', 'father', 'dad', 'sister', 'brother',
            'grandmother', 'grandma', 'grandfather', 'grandpa',
            'aunt', 'uncle', 'cousin', 'daughter', 'son'
        ]
        
        message_lower = message.lower()
        found_relations = []
        
        for relation in relationships:
            if relation in message_lower:
                found_relations.append(relation)
        
        return found_relations
    
    def _extract_medical_conditions(self, message: str) -> List[str]:
        """Extract medical conditions mentioned in the message."""
        conditions = [
            'cancer', 'breast cancer', 'ovarian cancer', 'lung cancer',
            'diabetes', 'heart disease', 'high blood pressure', 'hypertension',
            'depression', 'anxiety', 'asthma', 'arthritis'
        ]
        
        message_lower = message.lower()
        found_conditions = []
        
        for condition in conditions:
            if condition in message_lower:
                found_conditions.append(condition)
        
        return found_conditions
    
    def _extract_medical_terms(self, message: str) -> List[str]:
        """Extract general medical terms."""
        medical_terms = [
            'surgery', 'operation', 'medication', 'treatment', 'therapy',
            'diagnosis', 'doctor', 'hospital', 'clinic', 'test', 'screening',
            'genetic', 'hereditary', 'family history', 'symptoms'
        ]
        
        message_lower = message.lower()
        found_terms = []
        
        for term in medical_terms:
            if term in message_lower:
                found_terms.append(term)
        
        return found_terms
    
    def _extract_date(self, message: str) -> Optional[str]:
        """Extract date from message."""
        # Date patterns
        date_patterns = [
            r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b',  # MM/DD/YYYY or MM-DD-YYYY
            r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',    # YYYY/MM/DD or YYYY-MM-DD
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})\b'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(0)
        
        return None
    
    def _contains_keywords(self, message: str, keywords: List[str]) -> bool:
        """Check if message contains any of the specified keywords."""
        message_lower = message.lower()
        return any(keyword.lower() in message_lower for keyword in keywords)
    
    def _extract_by_pattern(self, message: str, pattern: str) -> Optional[str]:
        """Extract value using a regex pattern."""
        try:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        except re.error:
            print(f"Invalid regex pattern: {pattern}")
        
        return None
    
    def get_extraction_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of all extracted data for a session."""
        session = self.ai_chat_repo.get_session_by_id(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session_id,
            "extracted_data": session.extracted_data or {},
            "extraction_count": len(session.extracted_data or {}),
            "last_updated": session.updated_at.isoformat() if session.updated_at else None
        }
