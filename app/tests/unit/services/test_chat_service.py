"""
Unit tests for the Chat service
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from datetime import datetime, timedelta

from app.services.chat import ChatService
from app.models import ChatSession, ChatQuestion, ChatAnswer, RiskAssessment
from app.models.user import User, UserRole


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return MagicMock()


@pytest.fixture
def chat_service(mock_db):
    """Create a ChatService instance with mock repositories"""
    service = ChatService(mock_db)
    service.session_repository = MagicMock()
    service.question_repository = MagicMock()
    service.answer_repository = MagicMock()
    service.risk_repository = MagicMock()
    return service


def test_get_or_create_session_existing(chat_service):
    """Test getting an existing session"""
    # Arrange
    patient_id = "test-patient-id"
    mock_session = ChatSession(
        id="test-session-id",
        patient_id=patient_id,
        status="active",
        session_type="assessment"
    )
    chat_service.session_repository.get_active_session_by_patient.return_value = mock_session
    
    # Act
    result = chat_service.get_or_create_session(patient_id)
    
    # Assert
    assert result == mock_session
    chat_service.session_repository.get_active_session_by_patient.assert_called_once_with(patient_id)
    chat_service.session_repository.create_session.assert_not_called()


def test_get_or_create_session_new(chat_service):
    """Test creating a new session when none exists"""
    # Arrange
    patient_id = "test-patient-id"
    mock_session = ChatSession(
        id="test-session-id",
        patient_id=patient_id,
        status="active",
        session_type="assessment"
    )
    chat_service.session_repository.get_active_session_by_patient.return_value = None
    chat_service.session_repository.create_session.return_value = mock_session
    
    # Act
    result = chat_service.get_or_create_session(patient_id)
    
    # Assert
    assert result == mock_session
    chat_service.session_repository.get_active_session_by_patient.assert_called_once_with(patient_id)
    chat_service.session_repository.create_session.assert_called_once()
    create_args = chat_service.session_repository.create_session.call_args[0][0]
    assert create_args["patient_id"] == patient_id
    assert create_args["status"] == "active"
    assert create_args["session_type"] == "assessment"


def test_get_next_question_first_question(chat_service):
    """Test getting the first question when no current question"""
    # Arrange
    session_id = "test-session-id"
    mock_session = ChatSession(id=session_id, status="active")
    mock_question = ChatQuestion(id="q1", sequence=1, text="First question")
    
    chat_service.session_repository.get_by_id.return_value = mock_session
    chat_service.answer_repository.get_answers_by_session.return_value = []
    chat_service.question_repository.get_all_questions.return_value = [mock_question]
    
    # Act
    result = chat_service.get_next_question(session_id)
    
    # Assert
    assert result == mock_question
    chat_service.session_repository.get_by_id.assert_called_once_with(session_id)
    chat_service.answer_repository.get_answers_by_session.assert_called_once_with(session_id)
    chat_service.question_repository.get_all_questions.assert_called_once()


def test_get_next_question_inactive_session(chat_service):
    """Test exception raised when session is not active"""
    # Arrange
    session_id = "test-session-id"
    mock_session = ChatSession(id=session_id, status="completed")
    chat_service.session_repository.get_by_id.return_value = mock_session
    
    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        chat_service.get_next_question(session_id)
    
    assert excinfo.value.status_code == 404
    assert "Active session not found" in str(excinfo.value.detail)


def test_save_answer(chat_service):
    """Test saving an answer to a question"""
    # Arrange
    session_id = "test-session-id"
    question_id = "test-question-id"
    answer_text = "Test answer"
    
    mock_session = ChatSession(id=session_id, status="active")
    mock_question = ChatQuestion(id=question_id, sequence=1, text="Test question")
    mock_answer = ChatAnswer(
        id="test-answer-id",
        session_id=session_id,
        question_id=question_id,
        answer_text=answer_text
    )
    
    chat_service.session_repository.get_by_id.return_value = mock_session
    chat_service.question_repository.get_by_id.return_value = mock_question
    chat_service.answer_repository.create_answer.return_value = mock_answer
    
    # Act
    result = chat_service.save_answer(session_id, question_id, answer_text)
    
    # Assert
    assert result == mock_answer
    chat_service.session_repository.get_by_id.assert_called_once_with(session_id)
    chat_service.question_repository.get_by_id.assert_called_once_with(question_id)
    chat_service.answer_repository.create_answer.assert_called_once()
    create_args = chat_service.answer_repository.create_answer.call_args[0][0]
    assert create_args["session_id"] == session_id
    assert create_args["question_id"] == question_id
    assert create_args["answer_text"] == answer_text


def test_save_answer_inactive_session(chat_service):
    """Test exception raised when saving answer to inactive session"""
    # Arrange
    session_id = "test-session-id"
    question_id = "test-question-id"
    answer_text = "Test answer"
    
    mock_session = ChatSession(id=session_id, status="completed")
    chat_service.session_repository.get_by_id.return_value = mock_session
    
    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        chat_service.save_answer(session_id, question_id, answer_text)
    
    assert excinfo.value.status_code == 404
    assert "Active session not found" in str(excinfo.value.detail)


def test_get_chat_history(chat_service):
    """Test getting chat history for a session"""
    # Arrange
    session_id = "test-session-id"
    mock_session = ChatSession(id=session_id)
    
    mock_answer1 = ChatAnswer(
        id="a1",
        session_id=session_id,
        question_id="q1",
        answer_text="Answer 1",
        created_at=datetime.utcnow()
    )
    
    mock_answer2 = ChatAnswer(
        id="a2",
        session_id=session_id,
        question_id="q2",
        answer_text="Answer 2",
        created_at=datetime.utcnow()
    )
    
    mock_question1 = ChatQuestion(id="q1", sequence=1, text="Question 1")
    mock_question2 = ChatQuestion(id="q2", sequence=2, text="Question 2")
    
    chat_service.session_repository.get_by_id.return_value = mock_session
    chat_service.answer_repository.get_answers_by_session.return_value = [mock_answer1, mock_answer2]
    
    def mock_get_by_id(question_id):
        if question_id == "q1":
            return mock_question1
        elif question_id == "q2":
            return mock_question2
        return None
    
    chat_service.question_repository.get_by_id.side_effect = mock_get_by_id
    
    # Act
    result = chat_service.get_chat_history(session_id)
    
    # Assert
    assert len(result) == 2
    assert result[0]["question_id"] == "q1"
    assert result[0]["question_text"] == "Question 1"
    assert result[0]["answer_text"] == "Answer 1"
    assert result[1]["question_id"] == "q2"
    assert result[1]["question_text"] == "Question 2"
    assert result[1]["answer_text"] == "Answer 2"


def test_calculate_risk_assessment(chat_service):
    """Test calculating risk assessment based on chat answers"""
    # Arrange
    session_id = "test-session-id"
    patient_id = "test-patient-id"
    mock_session = ChatSession(id=session_id, patient_id=patient_id)
    
    # Mock questions
    q_family = ChatQuestion(id="q1", text="Do you have a family history of breast cancer?")
    q_age = ChatQuestion(id="q2", text="How old are you?")
    q_genetic = ChatQuestion(id="q3", text="Have you had genetic testing for BRCA1 or BRCA2?")
    
    # Mock answers
    a_family = ChatAnswer(id="a1", question_id="q1", answer_text="Yes")
    a_age = ChatAnswer(id="a2", question_id="q2", answer_text="56")
    a_genetic = ChatAnswer(id="a3", question_id="q3", answer_text="No")
    
    chat_service.session_repository.get_by_id.return_value = mock_session
    chat_service.answer_repository.get_answers_by_session.return_value = [a_family, a_age, a_genetic]
    
    def mock_get_question_by_id(question_id):
        if question_id == "q1":
            return q_family
        elif question_id == "q2":
            return q_age
        elif question_id == "q3":
            return q_genetic
        return None
    
    chat_service.question_repository.get_by_id.side_effect = mock_get_question_by_id
    
    mock_assessment = RiskAssessment(
        id="test-assessment-id",
        patient_id=patient_id,
        session_id=session_id,
        is_eligible=True,
        nccn_eligible=True,
        tyrer_cuzick_score=8.0,
        tyrer_cuzick_threshold=7.5,
        risk_factors=["FAMILY_HISTORY", "AGE"],
        recommendations=["Annual mammogram recommended", "Consider genetic testing"]
    )
    
    chat_service.risk_repository.create_assessment.return_value = mock_assessment
    
    # Act
    result = chat_service.calculate_risk_assessment(session_id)
    
    # Assert
    assert result == mock_assessment
    chat_service.session_repository.get_by_id.assert_called_once_with(session_id)
    chat_service.answer_repository.get_answers_by_session.assert_called_once_with(session_id)
    
    # Verify risk assessment creation with correct parameters
    chat_service.risk_repository.create_assessment.assert_called_once()
    assessment_data = chat_service.risk_repository.create_assessment.call_args[0][0]
    assert assessment_data["patient_id"] == patient_id
    assert assessment_data["session_id"] == session_id
    assert "risk_factors" in assessment_data
    assert "recommendations" in assessment_data
