"""
Risk Assessment Model

Stores structured risk assessments for patients, including NCCN criteria
evaluations and genetic testing recommendations.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


class RiskAssessment(Base):
    """Risk assessment record for a patient.

    Stores formal risk assessments performed through AI chat sessions
    or manual clinical evaluations. Used for analytics, reporting, and
    tracking patient risk profiles over time.
    """
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=True)
    assessment_type = Column(String(100), nullable=False)  # e.g., "NCCN_breast_cancer"
    risk_score = Column(Numeric(5, 2), nullable=True)  # 0.00 to 100.00
    risk_category = Column(String(50), nullable=True)  # e.g., "high", "moderate", "low"
    details = Column(JSONB, nullable=True)  # Additional assessment details
    assessed_by = Column(String(36), ForeignKey("users.id"), nullable=True)  # User or system ID

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.current_timestamp())

    # Relationships
    patient = relationship("Patient", back_populates="risk_assessments")
    assessor = relationship("User", foreign_keys=[assessed_by])

    def __repr__(self):
        return f"<RiskAssessment(id={self.id}, type={self.assessment_type}, risk={self.risk_category})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert risk assessment to dictionary."""
        return {
            "id": str(self.id),
            "patient_id": str(self.patient_id) if self.patient_id else None,
            "assessment_type": self.assessment_type,
            "risk_score": float(self.risk_score) if self.risk_score else None,
            "risk_category": self.risk_category,
            "details": self.details,
            "assessed_by": str(self.assessed_by) if self.assessed_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_nccn_assessment(
        cls,
        patient_id: str,
        assessment_data: Dict[str, Any],
        session_id: Optional[str] = None,
        assessed_by: Optional[str] = None
    ) -> "RiskAssessment":
        """Create RiskAssessment from NCCN criteria assessment.

        Args:
            patient_id: ID of the patient being assessed
            assessment_data: NCCN assessment results dictionary
            session_id: Optional chat session ID that generated this assessment
            assessed_by: Optional user ID (defaults to system)

        Returns:
            RiskAssessment instance
        """
        meets_criteria = assessment_data.get("meets_nccn_criteria", False)

        # Determine risk category
        if meets_criteria:
            risk_category = "high"
            risk_score = Decimal("80.0")  # High risk if criteria met
        else:
            risk_category = "low"
            risk_score = Decimal("20.0")  # Low risk if criteria not met

        # Build details JSON
        details = {
            "meets_nccn_criteria": meets_criteria,
            "criteria_met": assessment_data.get("criteria_met", []),
            "recommendation": assessment_data.get("recommendation", ""),
            "confidence": assessment_data.get("confidence"),
            "extracted_data": assessment_data.get("extracted_data", {}),
            "session_id": session_id,
            "assessment_date": datetime.utcnow().isoformat()
        }

        return cls(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            assessment_type="NCCN_breast_cancer",
            risk_score=risk_score,
            risk_category=risk_category,
            details=details,
            assessed_by=assessed_by,  # None for AI-generated assessments
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
