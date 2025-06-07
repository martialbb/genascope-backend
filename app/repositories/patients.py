"""
Repository module for patient operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from app.models.patient import Patient
from app.repositories.base import BaseRepository
from app.models.invite import PatientInvite
import uuid
from datetime import datetime


class PatientRepository(BaseRepository):
    """Repository for Patient operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, Patient)
    
    def get_by_email(self, email: str) -> Optional[Patient]:
        """Get a patient by email address"""
        return self.db.query(Patient).filter(Patient.email == email).first()
    
    def get_by_external_id(self, external_id: str, account_id: Optional[str] = None) -> Optional[Patient]:
        """Get a patient by external_id (clinic's internal ID)"""
        query = self.db.query(Patient).filter(Patient.external_id == external_id)
        
        if account_id:
            query = query.filter(Patient.account_id == account_id)
            
        return query.first()
    
    def get_by_clinician(self, clinician_id: str) -> List[Patient]:
        """Get all patients assigned to a clinician"""
        return self.db.query(Patient).filter(Patient.clinician_id == clinician_id).all()
    
    def get_by_account(self, account_id: str) -> List[Patient]:
        """Get all patients in an account"""
        return self.db.query(Patient).filter(Patient.account_id == account_id).all()
    
    def search_patients(
        self, 
        account_id: Optional[str] = None, 
        account_name: Optional[str] = None,
        clinician_id: Optional[str] = None, 
        query: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Patient]:
        """
        Search for patients with various filters
        
        Args:
            account_id: Optional account ID to filter by
            account_name: Optional account name to filter by (for superusers)
            clinician_id: Optional clinician ID to filter by
            query: Optional search term to match against name, email, or external_id
            status: Optional status filter
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            List[Patient]: List of matching patients
        """
        from app.models.accounts import Account
        
        # If filtering by account name, we need to join with accounts table
        if account_name:
            db_query = self.db.query(Patient).join(Account, Patient.account_id == Account.id)
            db_query = db_query.filter(Account.name.ilike(f"%{account_name}%"))
        else:
            db_query = self.db.query(Patient)
        
        if account_id:
            db_query = db_query.filter(Patient.account_id == account_id)
        
        if clinician_id:
            db_query = db_query.filter(Patient.clinician_id == clinician_id)
        
        if status:
            db_query = db_query.filter(Patient.status == status)
        
        if query:
            search = f"%{query}%"
            db_query = db_query.filter(
                or_(
                    Patient.first_name.ilike(search),
                    Patient.last_name.ilike(search),
                    Patient.email.ilike(search),
                    Patient.external_id.ilike(search)
                )
            )
        
        return db_query.order_by(desc(Patient.created_at)).offset(offset).limit(limit).all()
    
    def create_patient(self, patient_data: Dict[str, Any]) -> Patient:
        """Create a new patient"""
        if "id" not in patient_data:
            patient_data["id"] = str(uuid.uuid4())
        
        patient = Patient(**patient_data)
        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)
        return patient
    
    def bulk_create_patients(self, patients_data: List[Dict[str, Any]]) -> List[Patient]:
        """Create multiple patients at once"""
        patients = []
        
        for patient_data in patients_data:
            if "id" not in patient_data:
                patient_data["id"] = str(uuid.uuid4())
            
            patient = Patient(**patient_data)
            self.db.add(patient)
            patients.append(patient)
        
        self.db.commit()
        
        # Refresh all patients
        for patient in patients:
            self.db.refresh(patient)
        
        return patients
    
    def get_patients_with_pending_invites(self, account_id: Optional[str] = None) -> List[Patient]:
        """Get all patients with pending invites"""
        query = self.db.query(Patient).join(
            PatientInvite, 
            and_(
                PatientInvite.patient_id == Patient.id,
                PatientInvite.status == "pending"
            )
        )
        
        if account_id:
            query = query.filter(Patient.account_id == account_id)
            
        return query.all()
    
    def has_pending_invite(self, patient_id: str) -> bool:
        """Check if a patient has a pending invite"""
        count = self.db.query(func.count(PatientInvite.id)).filter(
            and_(
                PatientInvite.patient_id == patient_id,
                PatientInvite.status == "pending"
            )
        ).scalar()
        
        return count > 0
