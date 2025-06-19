from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create engine with URL from settings
engine = create_engine(settings.DATABASE_URI)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for ORM models
Base = declarative_base()

# Import all models to register them with Base
from app.models.accounts import Account
from app.models.user import User, PatientProfile
from app.models.patient import Patient
from app.models.chat import ChatSession, ChatQuestion, ChatAnswer, RiskAssessment
from app.models.invite import PatientInvite
from app.models.appointment import Appointment, Availability, RecurringAvailability
from app.models.lab import LabOrder, LabResult, LabIntegration
from app.models.chat_configuration import (
    ChatStrategy, KnowledgeSource, StrategyKnowledgeSource,
    TargetingRule, OutcomeAction, StrategyExecution, StrategyAnalytics
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
