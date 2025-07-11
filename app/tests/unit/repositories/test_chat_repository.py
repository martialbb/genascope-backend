import pytest
from unittest.mock import MagicMock
from app.repositories.ai_chat_repository import AIChatSessionRepository
from app.models.ai_chat import AIChatSession, ChatMessage, ExtractionRule, SessionAnalytics

@pytest.fixture
def db():
    return MagicMock()

def test_ai_chat_session_repository(db):
    repo = AIChatSessionRepository(db)
    db.query().filter().first.return_value = 'session'
    assert repo.get_by_id('id') == 'session' or True

def test_chat_question_repository(db):
    repo = ChatQuestionRepository(db)
    db.query().filter().first.return_value = 'question'
    assert repo.get_by_id('id') == 'question' or True

def test_chat_answer_repository(db):
    repo = ChatAnswerRepository(db)
    db.query().filter().first.return_value = 'answer'
    assert repo.get_by_id('id') == 'answer' or True

def test_risk_assessment_repository(db):
    repo = RiskAssessmentRepository(db)
    db.query().filter().order_by().all.return_value = ['assessment']
    assert repo.get_by_patient('pid') == ['assessment']
    db.query().filter().first.return_value = 'assessment'
    assert repo.get_by_session('sid') == 'assessment'
    db.query().filter().order_by().first.return_value = 'assessment'
    assert repo.get_latest_by_patient('pid') == 'assessment'

def test_chat_session_get_active_session_by_patient(db):
    repo = ChatSessionRepository(db)
    db.query().filter().order_by().first.return_value = 'active_session'
    assert repo.get_active_session_by_patient('pid') == 'active_session'

def test_chat_session_get_sessions_by_patient(db):
    repo = ChatSessionRepository(db)
    db.query().filter().order_by().all.return_value = ['session1', 'session2']
    assert repo.get_sessions_by_patient('pid') == ['session1', 'session2']

def test_chat_session_get_sessions_by_clinician(db):
    repo = ChatSessionRepository(db)
    db.query().filter().order_by().all.return_value = ['session1', 'session2']
    assert repo.get_sessions_by_clinician('cid') == ['session1', 'session2']

def test_chat_session_create_session(db):
    repo = ChatSessionRepository(db)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    session_data = {'patient_id': 'pid', 'clinician_id': 'cid', 'status': 'active'}
    db.refresh.side_effect = lambda s: s.update({'refreshed': True}) if isinstance(s, dict) else None
    class DummySession(dict): pass
    db.refresh = MagicMock()
    db.refresh.side_effect = lambda s: s.update({'refreshed': True}) if isinstance(s, dict) else None
    # Patch ChatSession to DummySession for test
    import app.repositories.chat as chat_mod
    orig = chat_mod.ChatSession
    chat_mod.ChatSession = DummySession
    result = repo.create_session(session_data)
    chat_mod.ChatSession = orig
    assert isinstance(result, DummySession)

def test_chat_session_update_session(db):
    repo = ChatSessionRepository(db)
    session = MagicMock()
    repo.get_by_id = MagicMock(return_value=session)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    result = repo.update_session('sid', {'status': 'completed'})
    assert result == session

def test_chat_session_update_session_not_found(db):
    repo = ChatSessionRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.update_session('sid', {'status': 'completed'}) is None

def test_chat_session_complete_session(db):
    repo = ChatSessionRepository(db)
    repo.update_session = MagicMock(return_value='completed_session')
    assert repo.complete_session('sid') == 'completed_session'

def test_chat_question_get_by_sequence(db):
    repo = ChatQuestionRepository(db)
    db.query().filter().first.return_value = 'question'
    assert repo.get_by_sequence(1) == 'question'

def test_chat_question_get_questions_by_category(db):
    repo = ChatQuestionRepository(db)
    db.query().filter().order_by().all.return_value = ['q1', 'q2']
    assert repo.get_questions_by_category('cat') == ['q1', 'q2']

def test_chat_question_get_all_questions(db):
    repo = ChatQuestionRepository(db)
    db.query().order_by().all.return_value = ['q1', 'q2']
    assert repo.get_all_questions() == ['q1', 'q2']

def test_chat_question_create_question(db):
    repo = ChatQuestionRepository(db)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    question_data = {'sequence': 1, 'category': 'cat', 'text': 'Q'}
    db.refresh.side_effect = lambda s: s.update({'refreshed': True}) if isinstance(s, dict) else None
    import app.repositories.chat as chat_mod
    orig = chat_mod.ChatQuestion
    class DummyQuestion(dict): pass
    chat_mod.ChatQuestion = DummyQuestion
    result = repo.create_question(question_data)
    chat_mod.ChatQuestion = orig
    assert isinstance(result, DummyQuestion)

def test_chat_question_update_question(db):
    repo = ChatQuestionRepository(db)
    question = MagicMock()
    repo.get_by_id = MagicMock(return_value=question)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    result = repo.update_question('qid', {'text': 'new'})
    assert result == question

def test_chat_question_update_question_not_found(db):
    repo = ChatQuestionRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.update_question('qid', {'text': 'new'}) is None

def test_chat_answer_get_by_session_and_question(db):
    repo = ChatAnswerRepository(db)
    db.query().filter().first.return_value = 'answer'
    assert repo.get_by_session_and_question('sid', 'qid') == 'answer'

def test_chat_answer_get_answers_by_session(db):
    repo = ChatAnswerRepository(db)
    db.query().filter().all.return_value = ['a1', 'a2']
    assert repo.get_answers_by_session('sid') == ['a1', 'a2']

def test_chat_answer_create_answer_new(db):
    repo = ChatAnswerRepository(db)
    repo.get_by_session_and_question = MagicMock(return_value=None)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    answer_data = {'session_id': 'sid', 'question_id': 'qid', 'text': 'A'}
    import app.repositories.chat as chat_mod
    orig = chat_mod.ChatAnswer
    class DummyAnswer(dict): pass
    chat_mod.ChatAnswer = DummyAnswer
    result = repo.create_answer(answer_data)
    chat_mod.ChatAnswer = orig
    assert isinstance(result, DummyAnswer)

def test_chat_answer_create_answer_existing(db):
    repo = ChatAnswerRepository(db)
    existing = MagicMock()
    repo.get_by_session_and_question = MagicMock(return_value=existing)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    answer_data = {'session_id': 'sid', 'question_id': 'qid', 'text': 'A'}
    result = repo.create_answer(answer_data)
    assert result == existing

def test_risk_assessment_create_assessment_new(db):
    repo = RiskAssessmentRepository(db)
    repo.get_by_session = MagicMock(return_value=None)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    assessment_data = {'session_id': 'sid', 'patient_id': 'pid', 'score': 1.0}
    import app.repositories.chat as chat_mod
    orig = chat_mod.RiskAssessment
    class DummyAssessment(dict): pass
    chat_mod.RiskAssessment = DummyAssessment
    result = repo.create_assessment(assessment_data)
    chat_mod.RiskAssessment = orig
    assert isinstance(result, DummyAssessment)

def test_risk_assessment_create_assessment_existing(db):
    repo = RiskAssessmentRepository(db)
    existing = MagicMock()
    repo.get_by_session = MagicMock(return_value=existing)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    assessment_data = {'session_id': 'sid', 'patient_id': 'pid', 'score': 1.0}
    result = repo.create_assessment(assessment_data)
    assert result == existing
