# Patient Invite System Documentation

## Overview

The Patient Invite System allows clinicians and physicians to generate unique invite links for patients. These links provide patients with secure access to the CancerGenix risk assessment chat interface.

## Backend Implementation

The invite system is implemented in the `/app/api/invites.py` file:

### Models

```python
class PatientData(BaseModel):
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    provider_id: str

class InviteResponse(BaseModel):
    invite_id: str
    invite_url: str
```

### API Endpoint

```python
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
```

## Frontend Implementation

### GenerateInviteForm Component

The `GenerateInviteForm.tsx` component provides a user interface for clinicians to create patient invites:

- Collects patient information (name, email, phone)
- Submits data to the backend API
- Displays the generated invite link for sharing
- Includes a copy-to-clipboard feature for easy sharing

### API Integration

```typescript
// Generate an invite
const response = await apiService.generateInvite({
  email,
  first_name: firstName,
  last_name: lastName,
  phone,
  provider_id: providerId
});

// Access the invite URL
const inviteUrl = response.invite_url;
```

### Invite Page

The `/invite.astro` page renders the invite form and handles any pre-filled patient data passed through query parameters.

## Invitation Workflow

1. **Provider Action**: A clinician or physician generates an invite for a patient from the dashboard or invite page
2. **Link Generation**: The backend generates a unique invite URL with a UUID
3. **Link Sharing**: The clinician shares the link with the patient via email or other means
4. **Patient Access**: When the patient accesses the link, they are taken to the assessment interface
5. **Authentication**: The invite UUID serves as a secure, one-time access token for the patient

## Security Considerations

- Invites should have an expiration time (to be implemented)
- Patient data associated with invites should be properly secured
- Rate limiting should be implemented to prevent abuse
- Invites should be single-use where appropriate

## Future Enhancements

- Email integration to automatically send invites to patients
- SMS integration for mobile-friendly invite delivery
- Invite expiration and revocation capabilities
- Analytics to track invite usage and conversion rates
- QR code generation for easier mobile access
