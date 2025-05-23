"""
Chat service module for business logic related to chat sessions, questions, answers, and risk assessments.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid

from app.repositories.chat import (
    ChatSessionRepository, ChatQuestionRepository, 
    ChatAnswerRepository, RiskAssessmentRepository
)
from app.models import ChatSession, ChatQuestion, ChatAnswer, RiskAssessment
from app.services.base import BaseService


class ChatService(BaseService):
    """
    Service for chat-related operations
    """
    def __init__(self, db: Session):
        self.db = db
        self.session_repository = ChatSessionRepository(db)
        self.question_repository = ChatQuestionRepository(db)
        self.answer_repository = ChatAnswerRepository(db)
        self.risk_repository = RiskAssessmentRepository(db)
    
    def get_or_create_session(self, patient_id: str, session_data: Optional[Dict[str, Any]] = None) -> ChatSession:
        """
        Get an active session for a patient or create a new one
        """
        active_session = self.session_repository.get_active_session_by_patient(patient_id)
        
        if active_session:
            return active_session
        
        if not session_data:
            session_data = {}
        
        session_data.update({
            "patient_id": patient_id,
            "status": "active",
            "session_type": session_data.get("session_type", "assessment")
        })
        
        return self.session_repository.create_session(session_data)
    
    def get_next_question(self, session_id: str, current_question_id: Optional[str] = None) -> Optional[ChatQuestion]:
        """
        Get the next question based on current question and previous answers
        """
        session = self.session_repository.get_by_id(session_id)
        if not session or session.status != "active":
            raise HTTPException(status_code=404, detail="Active session not found")
        
        # Get all answered questions for this session
        answered = self.answer_repository.get_answers_by_session(session_id)
        answered_ids = [a.question_id for a in answered]
        
        # If no current question, get the first unanswered question
        if not current_question_id:
            all_questions = self.question_repository.get_all_questions()
            for question in all_questions:
                if question.id not in answered_ids:
                    return question
            return None
        
        # Get the current question
        current_question = self.question_repository.get_by_id(current_question_id)
        if not current_question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Get the current answer
        current_answer = self.answer_repository.get_by_session_and_question(session_id, current_question_id)
        
        # Check if there's custom logic for the next question
        if current_question.next_question_logic and current_answer:
            # Example logic: {"answer_value": {"Yes": 5, "No": 7}}
            logic = current_question.next_question_logic
            answer_value = current_answer.answer_text
            
            if "answer_value" in logic and answer_value in logic["answer_value"]:
                next_seq = logic["answer_value"][answer_value]
                return self.question_repository.get_by_sequence(next_seq)
        
        # Default: get next question by sequence
        next_question = self.question_repository.get_by_sequence(current_question.sequence + 1)
        
        # If the next question is already answered, recursively find the next unanswered one
        if next_question and next_question.id in answered_ids:
            return self.get_next_question(session_id, next_question.id)
        
        return next_question
    
    def save_answer(self, session_id: str, question_id: str, answer_text: str, answer_value: Any = None) -> ChatAnswer:
        """
        Save an answer to a question
        """
        session = self.session_repository.get_by_id(session_id)
        if not session or session.status != "active":
            raise HTTPException(status_code=404, detail="Active session not found")
        
        question = self.question_repository.get_by_id(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        answer_data = {
            "session_id": session_id,
            "question_id": question_id,
            "answer_text": answer_text,
            "answer_value": answer_value
        }
        
        return self.answer_repository.create_answer(answer_data)
    
    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get the full conversation history for a session
        """
        session = self.session_repository.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        answers = self.answer_repository.get_answers_by_session(session_id)
        
        history = []
        for answer in answers:
            question = self.question_repository.get_by_id(answer.question_id)
            if question:
                history.append({
                    "question_id": question.id,
                    "question_text": question.text,
                    "answer_text": answer.answer_text,
                    "answer_value": answer.answer_value,
                    "timestamp": answer.created_at.isoformat()
                })
        
        # Sort by question sequence
        return sorted(history, key=lambda x: self.question_repository.get_by_id(x["question_id"]).sequence)
    
    def complete_session(self, session_id: str) -> ChatSession:
        """
        Mark a session as completed
        """
        session = self.session_repository.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return self.session_repository.complete_session(session_id)
    
    def calculate_risk_assessment(self, session_id: str) -> RiskAssessment:
        """
        Calculate risk assessment based on chat answers
        """
        session = self.session_repository.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get all answers for the session
        answers = self.answer_repository.get_answers_by_session(session_id)
        
        # In a real implementation, this would run through a risk assessment algorithm
        # For now, we'll use some simple mock logic
        
        # Convert answers to a dictionary for easier processing
        answer_dict = {}
        for answer in answers:
            question = self.question_repository.get_by_id(answer.question_id)
            if question:
                answer_dict[question.text] = answer.answer_text
        
        # Check for key risk factors
        is_eligible = False
        nccn_eligible = False
        tyrer_cuzick_score = 3.0  # Default low score
        tyrer_cuzick_threshold = 7.5
        risk_factors = []
        
        # Family history
        if answer_dict.get("Do you have a family history of breast cancer?") == "Yes":
            risk_factors.append("FAMILY_HISTORY")
            tyrer_cuzick_score += 3.0
        
        # Age
        age_answer = answer_dict.get("How old are you?", "0")
        try:
            age = int(age_answer)
            if age >= 55:
                risk_factors.append("AGE")
                tyrer_cuzick_score += 2.0
            elif age >= 45:
                tyrer_cuzick_score += 1.0
        except (ValueError, TypeError):
            pass
        
        # BRCA testing
        if answer_dict.get("Have you had genetic testing for BRCA1 or BRCA2?") == "Yes":
            risk_factors.append("GENETIC_TESTING")
            tyrer_cuzick_score += 2.0
        
        # Set eligibility based on score
        if tyrer_cuzick_score >= tyrer_cuzick_threshold:
            is_eligible = True
            nccn_eligible = True
        
        # Generate recommendations
        recommendations = []
        if is_eligible:
            recommendations.append("Annual mammogram recommended")
            recommendations.append("Consider genetic testing")
            if "FAMILY_HISTORY" in risk_factors:
                recommendations.append("Discuss family history with specialist")
        else:
            recommendations.append("Regular screenings as per standard guidelines")
        
        # Create risk assessment record
        assessment_data = {
            "patient_id": session.patient_id,
            "session_id": session_id,
            "is_eligible": is_eligible,
            "nccn_eligible": nccn_eligible,
            "tyrer_cuzick_score": tyrer_cuzick_score,
            "tyrer_cuzick_threshold": tyrer_cuzick_threshold,
            "risk_factors": risk_factors,
            "recommendations": recommendations
        }
        
        return self.risk_repository.create_assessment(assessment_data)
    
    def get_or_calculate_risk_assessment(self, session_id: str) -> RiskAssessment:
        """
        Get an existing risk assessment or calculate a new one
        """
        # Check if assessment already exists
        assessment = self.risk_repository.get_by_session(session_id)
        if assessment:
            return assessment
        
        # Calculate new assessment
        return self.calculate_risk_assessment(session_id)
    
    def seed_initial_questions(self) -> List[ChatQuestion]:
        """
        Seed the database with initial chat questions
        """
        questions = [
            {
                "sequence": 1,
                "text": "Do you have a family history of breast cancer?",
                "description": "First-degree relatives (mother, sister) with breast cancer",
                "answer_type": "boolean",
                "options": ["Yes", "No"],
                "required": True,
                "category": "risk_assessment"
            },
            {
                "sequence": 2,
                "text": "How old are you?",
                "description": "Your current age",
                "answer_type": "number",
                "required": True,
                "category": "risk_assessment"
            },
            {
                "sequence": 3,
                "text": "Have you had genetic testing for BRCA1 or BRCA2?",
                "description": "Previous genetic testing for breast cancer genes",
                "answer_type": "boolean",
                "options": ["Yes", "No"],
                "required": True,
                "category": "risk_assessment"
            },
            {
                "sequence": 4,
                "text": "Have you had a mammogram in the last year?",
                "description": "Recent mammogram screening",
                "answer_type": "boolean",
                "options": ["Yes", "No"],
                "required": True, 
                "category": "risk_assessment"
            },
            {
                "sequence": 5,
                "text": "Have you ever been diagnosed with breast cancer?",
                "description": "Previous breast cancer diagnosis",
                "answer_type": "boolean",
                "options": ["Yes", "No"],
                "required": True,
                "category": "risk_assessment"
            }
        ]
        
        created_questions = []
        for q in questions:
            # Check if question already exists by sequence
            existing = self.question_repository.get_by_sequence(q["sequence"])
            if not existing:
                created_questions.append(self.question_repository.create_question(q))
        
        return created_questions
