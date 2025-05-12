from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
from app.api.auth import get_current_active_user, User

router = APIRouter(prefix="/api", tags=["invites"])

class PatientData(BaseModel):
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    provider_id: str

class InviteResponse(BaseModel):
    invite_id: str
    invite_url: str

@router.post("/generate_invite", response_model=InviteResponse)
async def generate_invite(
    patient_data: PatientData,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a unique patient invite URL
    """
    # Generate a unique invite ID
    invite_id = str(uuid.uuid4())
    
    # In a real implementation, you would save this to a database
    # along with the patient data and the user who created it
    
    # Generate an invite URL with the invite ID
    base_url = "http://localhost:4321"  # This should come from configuration
    invite_url = f"{base_url}/invite/{invite_id}"
    
    return InviteResponse(
        invite_id=invite_id,
        invite_url=invite_url
    )
