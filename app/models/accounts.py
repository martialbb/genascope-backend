from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.database import Base

class Account(Base):
    """Account model representing an organization in the system"""
    __tablename__ = "accounts"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

    # Relationships
    users = relationship("User", back_populates="account", cascade="all, delete-orphan")
