"""
Criteria Assessment Service

This service evaluates patient responses against predefined criteria
to make assessments and recommendations based on chat conversations.
"""
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.repositories.ai_chat_repository import AIChatRepository
from app.models.ai_chat import AIChatSession
from app.models.chat_configuration import ChatStrategy
from app.core.ai_chat_config import get_ai_chat_settings
from app.services.base import BaseService


class CriteriaAssessmentService(BaseService):
    """Service for assessing patients against predefined criteria."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.db = db
        self.ai_chat_repo = AIChatRepository(db)
        self.settings = get_ai_chat_settings()
    
    async def assess_session(self, session_id: str) -> Dict[str, Any]:
        """Perform assessment based on extracted data and criteria."""
        session = self.ai_chat_repo.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        strategy = self.ai_chat_repo.get_strategy_by_id(session.strategy_id)
        if not strategy or not strategy.assessment_criteria:
            return {"status": "no_criteria", "message": "No assessment criteria defined"}
        
        # Perform assessment based on criteria
        assessment_results = {}
        
        for criteria_group in strategy.assessment_criteria:
            group_name = criteria_group.get("name", "default")
            criteria_list = criteria_group.get("criteria", [])
            
            group_results = self._assess_criteria_group(
                session.extracted_data or {},
                criteria_list
            )
            
            assessment_results[group_name] = group_results
        
        # Calculate overall assessment
        overall_assessment = self._calculate_overall_assessment(assessment_results)
        
        # Update session with assessment results
        session_update = {
            "assessment_results": {
                **session.assessment_results,
                **assessment_results,
                "overall": overall_assessment,
                "assessed_at": datetime.utcnow().isoformat()
            }
        }
        
        self.ai_chat_repo.update_session(session_id, session_update)
        
        return assessment_results
    
    def _assess_criteria_group(
        self, 
        extracted_data: Dict[str, Any], 
        criteria_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess a group of criteria."""
        results = {
            "criteria_met": [],
            "criteria_not_met": [],
            "criteria_unknown": [],
            "score": 0,
            "max_score": len(criteria_list),
            "percentage": 0
        }
        
        for criterion in criteria_list:
            criterion_id = criterion.get("id", "")
            criterion_name = criterion.get("name", criterion_id)
            
            met_status = self._evaluate_criterion(extracted_data, criterion)
            
            if met_status == "met":
                results["criteria_met"].append({
                    "id": criterion_id,
                    "name": criterion_name,
                    "value": self._get_criterion_value(extracted_data, criterion)
                })
                results["score"] += 1
            elif met_status == "not_met":
                results["criteria_not_met"].append({
                    "id": criterion_id,
                    "name": criterion_name,
                    "reason": self._get_not_met_reason(extracted_data, criterion)
                })
            else:
                results["criteria_unknown"].append({
                    "id": criterion_id,
                    "name": criterion_name,
                    "reason": "Insufficient data"
                })
        
        # Calculate percentage
        if results["max_score"] > 0:
            results["percentage"] = (results["score"] / results["max_score"]) * 100
        
        return results
    
    def _evaluate_criterion(self, extracted_data: Dict[str, Any], criterion: Dict[str, Any]) -> str:
        """Evaluate a single criterion. Returns 'met', 'not_met', or 'unknown'."""
        criterion_type = criterion.get("type", "")
        field = criterion.get("field", "")
        
        # Check if required field exists
        if field not in extracted_data:
            return "unknown"
        
        value = extracted_data[field]
        
        if criterion_type == "age_range":
            return self._evaluate_age_range(value, criterion)
        elif criterion_type == "yes_no":
            return self._evaluate_yes_no(value, criterion)
        elif criterion_type == "contains":
            return self._evaluate_contains(value, criterion)
        elif criterion_type == "family_history":
            return self._evaluate_family_history(value, criterion)
        elif criterion_type == "threshold":
            return self._evaluate_threshold(value, criterion)
        elif criterion_type == "existence":
            return "met" if value else "not_met"
        else:
            return "unknown"
    
    def _evaluate_age_range(self, age_value: Any, criterion: Dict[str, Any]) -> str:
        """Evaluate age range criterion."""
        try:
            age = int(age_value)
            min_age = criterion.get("min_age")
            max_age = criterion.get("max_age")
            
            if min_age is not None and age < min_age:
                return "not_met"
            if max_age is not None and age > max_age:
                return "not_met"
            
            return "met"
        except (ValueError, TypeError):
            return "unknown"
    
    def _evaluate_yes_no(self, response_value: Any, criterion: Dict[str, Any]) -> str:
        """Evaluate yes/no criterion."""
        expected = criterion.get("expected", "yes")
        
        if isinstance(response_value, str):
            response_lower = response_value.lower()
            if response_lower in ["yes", "true", "1"]:
                actual = "yes"
            elif response_lower in ["no", "false", "0"]:
                actual = "no"
            else:
                return "unknown"
        elif isinstance(response_value, bool):
            actual = "yes" if response_value else "no"
        else:
            return "unknown"
        
        return "met" if actual == expected else "not_met"
    
    def _evaluate_contains(self, value: Any, criterion: Dict[str, Any]) -> str:
        """Evaluate contains criterion."""
        required_items = criterion.get("required_items", [])
        
        if isinstance(value, list):
            value_list = value
        elif isinstance(value, str):
            value_list = [value]
        else:
            return "unknown"
        
        value_lower = [str(item).lower() for item in value_list]
        
        for required_item in required_items:
            if required_item.lower() not in value_lower:
                return "not_met"
        
        return "met"
    
    def _evaluate_family_history(self, family_data: Any, criterion: Dict[str, Any]) -> str:
        """Evaluate family history criterion."""
        if not isinstance(family_data, dict):
            return "unknown"
        
        required_conditions = criterion.get("required_conditions", [])
        required_relations = criterion.get("required_relations", [])
        
        mentioned_conditions = family_data.get("mentioned_conditions", [])
        mentioned_relations = family_data.get("mentioned_relations", [])
        
        # Check if required conditions are mentioned
        for condition in required_conditions:
            if condition.lower() not in [c.lower() for c in mentioned_conditions]:
                return "not_met"
        
        # Check if required relations are mentioned
        for relation in required_relations:
            if relation.lower() not in [r.lower() for r in mentioned_relations]:
                return "not_met"
        
        return "met"
    
    def _evaluate_threshold(self, value: Any, criterion: Dict[str, Any]) -> str:
        """Evaluate threshold criterion."""
        try:
            numeric_value = float(value)
            threshold = criterion.get("threshold")
            operator = criterion.get("operator", ">=")
            
            if operator == ">=":
                return "met" if numeric_value >= threshold else "not_met"
            elif operator == "<=":
                return "met" if numeric_value <= threshold else "not_met"
            elif operator == ">":
                return "met" if numeric_value > threshold else "not_met"
            elif operator == "<":
                return "met" if numeric_value < threshold else "not_met"
            elif operator == "==":
                return "met" if numeric_value == threshold else "not_met"
            else:
                return "unknown"
        except (ValueError, TypeError):
            return "unknown"
    
    def _get_criterion_value(self, extracted_data: Dict[str, Any], criterion: Dict[str, Any]) -> Any:
        """Get the actual value that met the criterion."""
        field = criterion.get("field", "")
        return extracted_data.get(field)
    
    def _get_not_met_reason(self, extracted_data: Dict[str, Any], criterion: Dict[str, Any]) -> str:
        """Get reason why criterion was not met."""
        field = criterion.get("field", "")
        value = extracted_data.get(field)
        criterion_type = criterion.get("type", "")
        
        if criterion_type == "age_range":
            min_age = criterion.get("min_age")
            max_age = criterion.get("max_age")
            if min_age and value < min_age:
                return f"Age {value} is below minimum {min_age}"
            if max_age and value > max_age:
                return f"Age {value} is above maximum {max_age}"
        elif criterion_type == "yes_no":
            expected = criterion.get("expected", "yes")
            return f"Expected '{expected}' but got '{value}'"
        
        return f"Value '{value}' does not meet criterion requirements"
    
    def _calculate_overall_assessment(self, assessment_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall assessment across all criteria groups."""
        total_score = 0
        total_max_score = 0
        all_met_criteria = []
        all_not_met_criteria = []
        all_unknown_criteria = []
        
        for group_name, group_results in assessment_results.items():
            if isinstance(group_results, dict):
                total_score += group_results.get("score", 0)
                total_max_score += group_results.get("max_score", 0)
                all_met_criteria.extend(group_results.get("criteria_met", []))
                all_not_met_criteria.extend(group_results.get("criteria_not_met", []))
                all_unknown_criteria.extend(group_results.get("criteria_unknown", []))
        
        overall_percentage = (total_score / total_max_score * 100) if total_max_score > 0 else 0
        
        # Determine recommendation level
        recommendation = self._get_recommendation_level(overall_percentage, assessment_results)
        
        return {
            "total_score": total_score,
            "total_max_score": total_max_score,
            "percentage": overall_percentage,
            "total_criteria_met": len(all_met_criteria),
            "total_criteria_not_met": len(all_not_met_criteria),
            "total_criteria_unknown": len(all_unknown_criteria),
            "recommendation": recommendation,
            "summary": self._generate_assessment_summary(
                overall_percentage, 
                len(all_met_criteria), 
                len(all_not_met_criteria)
            )
        }
    
    def _get_recommendation_level(
        self, 
        percentage: float, 
        assessment_results: Dict[str, Any]
    ) -> str:
        """Determine recommendation level based on assessment results."""
        if percentage >= 80:
            return "high_priority"
        elif percentage >= 60:
            return "moderate_priority"
        elif percentage >= 40:
            return "low_priority"
        else:
            return "not_indicated"
    
    def _generate_assessment_summary(
        self, 
        percentage: float, 
        criteria_met: int, 
        criteria_not_met: int
    ) -> str:
        """Generate a summary of the assessment."""
        if percentage >= 80:
            return f"Strong indication: {criteria_met} criteria met, {criteria_not_met} not met"
        elif percentage >= 60:
            return f"Moderate indication: {criteria_met} criteria met, {criteria_not_met} not met"
        elif percentage >= 40:
            return f"Weak indication: {criteria_met} criteria met, {criteria_not_met} not met"
        else:
            return f"Not indicated: {criteria_met} criteria met, {criteria_not_met} not met"
    
    def get_assessment_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get assessment history for a session."""
        session = self.ai_chat_repo.get_session_by_id(session_id)
        if not session or not session.assessment_results:
            return []
        
        # Extract assessment timestamps
        assessments = []
        if "assessed_at" in session.assessment_results:
            assessments.append({
                "assessed_at": session.assessment_results["assessed_at"],
                "results": session.assessment_results
            })
        
        return assessments
    
    def generate_recommendations(self, session_id: str) -> List[Dict[str, Any]]:
        """Generate recommendations based on assessment results."""
        session = self.ai_chat_repo.get_session_by_id(session_id)
        if not session or not session.assessment_results:
            return []
        
        overall = session.assessment_results.get("overall", {})
        recommendation_level = overall.get("recommendation", "not_indicated")
        
        recommendations = []
        
        if recommendation_level == "high_priority":
            recommendations.append({
                "type": "urgent_referral",
                "title": "Genetic Counseling Recommended",
                "description": "Based on your responses, genetic counseling is strongly recommended.",
                "priority": "high",
                "next_steps": [
                    "Schedule appointment with genetic counselor",
                    "Gather family medical history documents",
                    "Consider genetic testing options"
                ]
            })
        elif recommendation_level == "moderate_priority":
            recommendations.append({
                "type": "referral",
                "title": "Consider Genetic Counseling",
                "description": "Your responses suggest genetic counseling may be beneficial.",
                "priority": "medium",
                "next_steps": [
                    "Discuss with your primary care provider",
                    "Consider scheduling genetic counseling",
                    "Monitor family history updates"
                ]
            })
        elif recommendation_level == "low_priority":
            recommendations.append({
                "type": "monitoring",
                "title": "Continue Monitoring",
                "description": "Continue regular health monitoring and stay informed.",
                "priority": "low",
                "next_steps": [
                    "Maintain regular check-ups",
                    "Update family history as needed",
                    "Stay informed about genetic health"
                ]
            })
        else:
            recommendations.append({
                "type": "routine_care",
                "title": "Continue Routine Care",
                "description": "Continue with routine healthcare and screening.",
                "priority": "low",
                "next_steps": [
                    "Follow routine screening guidelines",
                    "Maintain healthy lifestyle",
                    "Contact healthcare provider with concerns"
                ]
            })
        
        return recommendations
