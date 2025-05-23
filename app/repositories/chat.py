"""
Chat repository module for handling database operations for chat sessions, questions, answers, and risk assessments.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from app.models import ChatSession, ChatQuestion, ChatAnswer, RiskAssessment
from app.repositories.base import BaseRepository
import uuid
from datetime import datetime


class ChatSessionRepository(BaseRepository):
    """Repository for ChatSession operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, ChatSession)
    
    def get_active_session_by_patient(self, patient_id: str) -> Optional[ChatSession]:
        """Get the active chat session for a patient"""
        return self.db.query(ChatSession).filter(
            and_(
                ChatSession.patient_id == patient_id,
                ChatSession.status == "active"
            )
        ).order_by(desc(ChatSession.created_at)).first()
    
    def get_sessions_by_patient(self, patient_id: str) -> List[ChatSession]:
        """Get all chat sessions for a patient"""
        return self.db.query(ChatSession).filter(
            ChatSession.patient_id == patient_id
        ).order_by(desc(ChatSession.created_at)).all()
    
    def get_sessions_by_clinician(self, clinician_id: str) -> List[ChatSession]:
        """Get all chat sessions managed by a clinician"""
        return self.db.query(ChatSession).filter(
            ChatSession.clinician_id == clinician_id
        ).order_by(desc(ChatSession.created_at)).all()
    
    def create_session(self, session_data: Dict[str, Any]) -> ChatSession:
        """Create a new chat session"""
        if "id" not in session_data:
            session_data["id"] = str(uuid.uuid4())
        
        session = ChatSession(**session_data)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def update_session(self, session_id: str, update_data: Dict[str, Any]) -> Optional[ChatSession]:
        """Update a chat session"""
        session = self.get_by_id(session_id)
        if not session:
            return None
        
        for key, value in update_data.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def complete_session(self, session_id: str) -> Optional[ChatSession]:
        """Mark a chat session as completed"""
        return self.update_session(session_id, {
            "status": "completed",
            "completed_at": datetime.utcnow()
        })


class ChatQuestionRepository(BaseRepository):
    """Repository for ChatQuestion operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, ChatQuestion)
    
    def get_by_sequence(self, sequence: int) -> Optional[ChatQuestion]:
        """Get a question by its sequence number"""
        return self.db.query(ChatQuestion).filter(
            ChatQuestion.sequence == sequence
        ).first()
    
    def get_questions_by_category(self, category: str) -> List[ChatQuestion]:
        """Get all questions in a category"""
        return self.db.query(ChatQuestion).filter(
            ChatQuestion.category == category
        ).order_by(ChatQuestion.sequence).all()
    
    def get_all_questions(self) -> List[ChatQuestion]:
        """Get all questions ordered by sequence"""
        return self.db.query(ChatQuestion).order_by(ChatQuestion.sequence).all()
    
    def create_question(self, question_data: Dict[str, Any]) -> ChatQuestion:
        """Create a new chat question"""
        if "id" not in question_data:
            question_data["id"] = str(uuid.uuid4())
        
        question = ChatQuestion(**question_data)
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question
    
    def update_question(self, question_id: str, update_data: Dict[str, Any]) -> Optional[ChatQuestion]:
        """Update a chat question"""
        question = self.get_by_id(question_id)
        if not question:
            return None
        
        for key, value in update_data.items():
            if hasattr(question, key):
                setattr(question, key, value)
        
        question.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(question)
        return question


class ChatAnswerRepository(BaseRepository):
    """Repository for ChatAnswer operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, ChatAnswer)
    
    def get_by_session_and_question(self, session_id: str, question_id: str) -> Optional[ChatAnswer]:
        """Get an answer by session and question IDs"""
        return self.db.query(ChatAnswer).filter(
            and_(
                ChatAnswer.session_id == session_id,
                ChatAnswer.question_id == question_id
            )
        ).first()
    
    def get_answers_by_session(self, session_id: str) -> List[ChatAnswer]:
        """Get all answers for a chat session"""
        return self.db.query(ChatAnswer).filter(
            ChatAnswer.session_id == session_id
        ).all()
    
    def create_answer(self, answer_data: Dict[str, Any]) -> ChatAnswer:
        """Create a new chat answer"""
        if "id" not in answer_data:
            answer_data["id"] = str(uuid.uuid4())
        
        # Check if an answer already exists for this session and question
        existing = self.get_by_session_and_question(
            answer_data["session_id"], 
            answer_data["question_id"]
        )
        
        if existing:
            # Update the existing answer
            for key, value in answer_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create a new answer
        answer = ChatAnswer(**answer_data)
        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)
        return answer


class RiskAssessmentRepository(BaseRepository):
    """Repository for RiskAssessment operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, RiskAssessment)
    
    def get_by_patient(self, patient_id: str) -> List[RiskAssessment]:
        """Get all risk assessments for a patient"""
        return self.db.query(RiskAssessment).filter(
            RiskAssessment.patient_id == patient_id
        ).order_by(desc(RiskAssessment.created_at)).all()
    
    def get_by_session(self, session_id: str) -> Optional[RiskAssessment]:
        """Get the risk assessment for a chat session"""
        return self.db.query(RiskAssessment).filter(
            RiskAssessment.session_id == session_id
        ).first()
    
    def get_latest_by_patient(self, patient_id: str) -> Optional[RiskAssessment]:
        """Get the most recent risk assessment for a patient"""
        return self.db.query(RiskAssessment).filter(
            RiskAssessment.patient_id == patient_id
        ).order_by(desc(RiskAssessment.created_at)).first()
    
    def create_assessment(self, assessment_data: Dict[str, Any]) -> RiskAssessment:
        """Create a new risk assessment"""
        if "id" not in assessment_data:
            assessment_data["id"] = str(uuid.uuid4())
        
        # Check if an assessment already exists for this session
        existing = self.get_by_session(assessment_data["session_id"])
        
        if existing:
            # Update the existing assessment
            for key, value in assessment_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create a new assessment
        assessment = RiskAssessment(**assessment_data)
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment
