"""
Risk Assessment Repository

Handles database operations for risk assessments.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.risk_assessment import RiskAssessment


class RiskAssessmentRepository:
    """Repository for risk assessment database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, risk_assessment: RiskAssessment) -> RiskAssessment:
        """Create a new risk assessment.

        Args:
            risk_assessment: RiskAssessment instance to create

        Returns:
            Created RiskAssessment instance
        """
        self.db.add(risk_assessment)
        self.db.commit()
        self.db.refresh(risk_assessment)
        return risk_assessment

    def get_by_id(self, assessment_id: str) -> Optional[RiskAssessment]:
        """Get risk assessment by ID.

        Args:
            assessment_id: Assessment ID

        Returns:
            RiskAssessment instance or None
        """
        return self.db.query(RiskAssessment).filter(
            RiskAssessment.id == assessment_id
        ).first()

    def get_by_patient(
        self,
        patient_id: str,
        assessment_type: Optional[str] = None,
        limit: int = 10
    ) -> List[RiskAssessment]:
        """Get risk assessments for a patient.

        Args:
            patient_id: Patient ID
            assessment_type: Optional filter by assessment type
            limit: Maximum number of results

        Returns:
            List of RiskAssessment instances
        """
        query = self.db.query(RiskAssessment).filter(
            RiskAssessment.patient_id == patient_id
        )

        if assessment_type:
            query = query.filter(RiskAssessment.assessment_type == assessment_type)

        return query.order_by(RiskAssessment.created_at.desc()).limit(limit).all()

    def get_latest_by_patient(
        self,
        patient_id: str,
        assessment_type: str
    ) -> Optional[RiskAssessment]:
        """Get the most recent assessment for a patient.

        Args:
            patient_id: Patient ID
            assessment_type: Type of assessment

        Returns:
            Most recent RiskAssessment or None
        """
        return self.db.query(RiskAssessment).filter(
            RiskAssessment.patient_id == patient_id,
            RiskAssessment.assessment_type == assessment_type
        ).order_by(RiskAssessment.created_at.desc()).first()

    def get_high_risk_patients(
        self,
        assessment_type: Optional[str] = None,
        limit: int = 100
    ) -> List[RiskAssessment]:
        """Get high-risk patient assessments.

        Args:
            assessment_type: Optional filter by assessment type
            limit: Maximum number of results

        Returns:
            List of high-risk RiskAssessment instances
        """
        query = self.db.query(RiskAssessment).filter(
            RiskAssessment.risk_category == "high"
        )

        if assessment_type:
            query = query.filter(RiskAssessment.assessment_type == assessment_type)

        return query.order_by(RiskAssessment.created_at.desc()).limit(limit).all()

    def update(self, assessment_id: str, update_data: Dict[str, Any]) -> Optional[RiskAssessment]:
        """Update a risk assessment.

        Args:
            assessment_id: Assessment ID
            update_data: Dictionary of fields to update

        Returns:
            Updated RiskAssessment or None
        """
        assessment = self.get_by_id(assessment_id)
        if not assessment:
            return None

        for key, value in update_data.items():
            if hasattr(assessment, key):
                setattr(assessment, key, value)

        assessment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def delete(self, assessment_id: str) -> bool:
        """Delete a risk assessment.

        Args:
            assessment_id: Assessment ID

        Returns:
            True if deleted, False if not found
        """
        assessment = self.get_by_id(assessment_id)
        if not assessment:
            return False

        self.db.delete(assessment)
        self.db.commit()
        return True
