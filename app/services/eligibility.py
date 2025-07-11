"""
Eligibility service module for cancer screening eligibility analysis.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
from datetime import datetime

from app.models.user import UserRole
from app.services.base import BaseService


class EligibilityService(BaseService):
    """
    Service for eligibility analysis operations
    """
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_mock_eligibility(self, patient_id: str) -> Dict[str, Any]:
        """
        Mock eligibility analysis for demonstration
        In a real implementation, this would:
        1. Get patient's risk factors from their profile
        2. Apply NCCN guidelines
        3. Calculate risk scores (Tyrer-Cuzick, etc.)
        4. Return recommendations
        """
        
        # Mock response for demonstration
        return {
            "is_eligible": True,
            "nccn_eligible": True,
            "tyrer_cuzick_score": 0.25,  # 25% lifetime risk
            "tyrer_cuzick_threshold": 0.20,  # 20% threshold
            "risk_factors": [
                "family_history",  # Fixed: use lowercase enum values
                "age"             # Fixed: use lowercase enum values
            ],
            "recommendations": [
                "Annual mammography starting at age 40",
                "Consider breast MRI screening",
                "Genetic counseling consultation recommended"
            ],
            "analysis_date": datetime.utcnow().isoformat(),
            "patient_id": patient_id
        }
    
    def get_detailed_analysis(self, patient_id: str) -> Dict[str, Any]:
        """
        Get detailed eligibility analysis including risk breakdown
        """
        
        # Mock detailed analysis
        return {
            "patient_id": patient_id,
            "is_eligible": True,
            "nccn_eligible": True,
            "overall_risk_level": "High",
            "lifetime_risk_percentage": 25.0,
            "risk_factors": [
                {
                    "factor": "family_history",  # Fixed: use lowercase enum value
                    "present": True,
                    "details": "First-degree relative with breast cancer",
                    "risk_contribution": 8.5
                },
                {
                    "factor": "age",  # Fixed: use lowercase enum value
                    "present": True,
                    "details": "Age 45-50",
                    "risk_contribution": 5.2
                }
            ],
            "recommendations": [
                {
                    "type": "screening",
                    "description": "Annual mammography",
                    "priority": "high",
                    "start_age": 40
                },
                {
                    "type": "imaging",
                    "description": "Consider breast MRI",
                    "priority": "medium",
                    "frequency": "annual"
                },
                {
                    "type": "consultation",
                    "description": "Genetic counseling",
                    "priority": "high",
                    "urgency": "within_3_months"
                }
            ],
            "next_assessment_date": datetime.utcnow().isoformat(),
            "analysis_date": datetime.utcnow().isoformat()
        }
