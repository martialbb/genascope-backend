"""
Models package.
"""
# Import all models here to ensure they're registered with SQLAlchemy
from app.models.user import UserRole, Account, User, PatientProfile, UserProfile
from app.models.chat_configuration import ChatStrategy, KnowledgeSource
from app.models.ai_chat import AIChatSession, ChatMessage, ExtractionRule, SessionAnalytics, DocumentChunk
from app.models.lab import TestType, OrderStatus, ResultStatus, LabIntegration, LabOrder, LabResult
from app.models.appointment import Appointment, Availability, RecurringAvailability

# Import these last to avoid circular imports
from app.models.patient import Patient, PatientStatus
from app.models.invite import PatientInvite
from app.models.risk_assessment import RiskAssessment
