#!/usr/bin/env python3
"""
Test script for AI chat responses with NCCN RAG system.
This script tests the real OpenAI integration with the RAG system.
"""
import asyncio
import sys
import os
sys.path.append('/app')

from app.db.database import get_db
from app.repositories.ai_chat_repository import AIChatRepository
from app.services.ai_chat_engine import ChatEngineService
from app.models.ai_chat import SessionType
from app.models.chat_configuration import ChatStrategy, KnowledgeSource
import uuid
import json


async def create_test_strategy(repo: AIChatRepository) -> ChatStrategy:
    """Create a test NCCN strategy for testing."""
    try:
        # Create a knowledge source with NCCN content
        knowledge_source_data = {
            "id": str(uuid.uuid4()),
            "name": "NCCN Breast Cancer Guidelines",
            "source_type": "file",
            "content": """NCCN Guidelines for Genetic Testing in Breast Cancer:

Criteria for BRCA1/2 genetic testing include:
1. Personal history of breast cancer diagnosed at age 45 or younger
2. Personal history of triple-negative breast cancer
3. Personal history of ovarian cancer
4. Family history of 2 or more breast cancers in close relatives
5. Family history of ovarian cancer in close relatives
6. Male breast cancer in family
7. Ashkenazi Jewish heritage with breast or ovarian cancer history

High-risk features that warrant genetic counseling:
- Early onset breast cancer (≤45 years)
- Triple-negative breast cancer at any age
- Bilateral breast cancer
- Breast and ovarian cancer in same individual
- Male breast cancer
- Family history patterns suggestive of hereditary cancer

Genetic testing should be offered to individuals who meet NCCN criteria.
Genetic counseling is recommended before and after testing.""",
            "metadata": {"source": "NCCN Guidelines v3.2024"},
            "created_at": "2024-09-14T00:00:00"
        }
        
        # Create strategy data
        strategy_data = {
            "id": "nccn-breast-cancer-test",
            "name": "NCCN Breast Cancer Genetic Testing Assessment",
            "description": "AI-powered assessment for NCCN breast cancer genetic testing criteria",
            "prompt_template": "Assess genetic testing eligibility based on NCCN guidelines",
            "is_active": True,
            "created_at": "2024-09-14T00:00:00"
        }
        
        # For testing, create a simple strategy object
        strategy = ChatStrategy(**strategy_data)
        knowledge_source = KnowledgeSource(**knowledge_source_data)
        strategy.knowledge_sources = [knowledge_source]
        
        print(f"✓ Created test strategy: {strategy.name}")
        return strategy
        
    except Exception as e:
        print(f"Error creating strategy: {e}")
        raise


async def test_ai_responses():
    """Test real AI responses with the NCCN RAG system."""
    print("🧪 Testing AI Chat Responses with OpenAI Integration")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Initialize the chat engine
        chat_engine = ChatEngineService(db)
        repo = AIChatRepository(db)
        
        # Create test strategy (mock it since we don't have the DB table yet)
        strategy = await create_test_strategy(repo)
        
        # Mock the repository method to return our test strategy
        original_get_strategy = repo.get_strategy_by_id
        def mock_get_strategy(strategy_id):
            if strategy_id == "nccn-breast-cancer-test":
                return strategy
            return None
        repo.get_strategy_by_id = mock_get_strategy
        
        print(f"📋 Using strategy: {strategy.name}")
        print(f"📚 Knowledge sources: {len(strategy.knowledge_sources)}")
        print()
        
        # Test 1: Generate welcome message
        print("🤖 Test 1: Welcome Message Generation")
        print("-" * 40)
        welcome_msg = chat_engine._generate_welcome_message(strategy)
        print(f"Welcome: {welcome_msg}")
        print()
        
        # Test 2: Generate AI response for family history question
        print("🤖 Test 2: AI Response to Family History")
        print("-" * 40)
        
        # Create a mock session for testing
        session_data = {
            "id": str(uuid.uuid4()),
            "strategy_id": "nccn-breast-cancer-test",
            "patient_id": "test-patient-123",
            "session_type": SessionType.screening,
            "status": "active",
            "chat_context": {},
            "extracted_data": {},
            "assessment_results": {},
            "messages": []
        }
        
        # Mock session object
        class MockSession:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
        
        mock_session = MockSession(session_data)
        
        # Test user message about family history
        user_message = "My mother had breast cancer at age 42, and my aunt also had breast cancer at 38."
        
        print(f"User: {user_message}")
        print()
        print("Generating AI response...")
        
        # Generate AI response
        ai_response = await chat_engine._generate_ai_response(
            mock_session, 
            user_message, 
            context=""
        )
        
        print(f"🤖 AI Response:")
        print(f"Content: {ai_response['content']}")
        print(f"Confidence: {ai_response['confidence']}")
        print(f"Response Type: {ai_response['metadata']['response_type']}")
        print(f"Model Used: {ai_response['metadata'].get('model_used', 'N/A')}")
        print(f"Response Time: {ai_response['metadata']['response_time_ms']}ms")
        print(f"RAG Enhanced: {ai_response['metadata'].get('rag_enhanced', False)}")
        
        if ai_response.get('assessment'):
            print(f"\\n📊 NCCN Assessment:")
            assessment = ai_response['assessment']
            print(f"Meets Criteria: {assessment.get('meets_nccn_criteria', 'N/A')}")
            print(f"Criteria Met: {assessment.get('criteria_met', [])}")
            print(f"Recommendation: {assessment.get('recommendation', 'N/A')}")
        
        print()
        
        # Test 3: Another scenario - personal history
        print("🤖 Test 3: AI Response to Personal History")
        print("-" * 40)
        
        user_message2 = "I was diagnosed with breast cancer at age 38. It was triple-negative."
        print(f"User: {user_message2}")
        print()
        
        ai_response2 = await chat_engine._generate_ai_response(
            mock_session, 
            user_message2, 
            context=""
        )
        
        print(f"🤖 AI Response:")
        print(f"Content: {ai_response2['content']}")
        print(f"Confidence: {ai_response2['confidence']}")
        
        if ai_response2.get('assessment'):
            print(f"\\n📊 NCCN Assessment:")
            assessment = ai_response2['assessment']
            print(f"Meets Criteria: {assessment.get('meets_nccn_criteria', 'N/A')}")
            print(f"Criteria Met: {assessment.get('criteria_met', [])}")
        
        print()
        print("✅ AI Response Testing Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_ai_responses())
