# Organization Appointments API

## Overview

The Organization Appointments API endpoint allows authorized users to retrieve a paginated list of all appointments for patients within their organization (account). This endpoint is useful for organization administrators and staff who need to view and manage appointments across their entire patient base.

## Endpoint

**GET** `/api/organization/appointments`

## Authentication

- Requires valid JWT token
- User must be associated with an organization (have a valid `account_id`)

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (1-based, minimum: 1) |
| `page_size` | integer | No | 20 | Number of appointments per page (1-100) |
| `status` | string | No | - | Filter by appointment status |
| `date_from` | string | No | - | Start date filter (YYYY-MM-DD format) |
| `date_to` | string | No | - | End date filter (YYYY-MM-DD format) |
| `clinician_id` | string | No | - | Filter by specific clinician ID |
| `patient_id` | string | No | - | Filter by specific patient ID |

### Valid Status Values
- `scheduled`
- `confirmed`
- `completed`
- `canceled`
- `rescheduled`
- `no-show`

## Response Format

```json
{
  "appointments": [
    {
      "id": "appointment-uuid",
      "clinician_id": "clinician-uuid",
      "clinician_name": "Dr. John Smith",
      "patient_id": "patient-uuid", 
      "patient_name": "Jane Doe",
      "patient_email": "jane.doe@email.com",
      "date": "2025-09-20",
      "time": "14:30:00",
      "appointment_type": "virtual",
      "status": "scheduled",
      "notes": "Follow-up consultation",
      "confirmation_code": "ABC123",
      "created_at": "2025-09-19T10:00:00Z",
      "updated_at": "2025-09-19T10:00:00Z"
    }
  ],
  "total_count": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "has_next": true,
  "has_previous": false
}
```

## Response Fields

### Appointment Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique appointment identifier |
| `clinician_id` | string | ID of the assigned clinician |
| `clinician_name` | string | Full name of the clinician |
| `patient_id` | string | ID of the patient |
| `patient_name` | string | Full name of the patient |
| `patient_email` | string | Patient's email address (nullable) |
| `date` | string | Appointment date (YYYY-MM-DD) |
| `time` | string | Appointment time (HH:MM:SS) |
| `appointment_type` | string | Type of appointment (virtual, in-person, home-visit) |
| `status` | string | Current appointment status |
| `notes` | string | Additional notes (nullable) |
| `confirmation_code` | string | Appointment confirmation code |
| `created_at` | string | ISO timestamp when appointment was created |
| `updated_at` | string | ISO timestamp when appointment was last updated |

### Pagination Metadata

| Field | Type | Description |
|-------|------|-------------|
| `total_count` | integer | Total number of appointments matching filters |
| `page` | integer | Current page number |
| `page_size` | integer | Number of appointments per page |
| `total_pages` | integer | Total number of pages |
| `has_next` | boolean | Whether there are more pages |
| `has_previous` | boolean | Whether there are previous pages |

## Example Requests

### Get all appointments (first page)
```bash
GET /api/organization/appointments
Authorization: Bearer <jwt_token>
```

### Get appointments with pagination
```bash
GET /api/organization/appointments?page=2&page_size=50
Authorization: Bearer <jwt_token>
```

### Filter by status and date range
```bash
GET /api/organization/appointments?status=scheduled&date_from=2025-09-20&date_to=2025-09-30
Authorization: Bearer <jwt_token>
```

### Filter by specific clinician
```bash
GET /api/organization/appointments?clinician_id=clinician-uuid&page=1&page_size=25
Authorization: Bearer <jwt_token>
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied. User must be associated with an organization."
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["query", "page"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge",
      "ctx": {"limit_value": 1}
    }
  ]
}
```

## Implementation Notes

1. **Data Access**: Only appointments for patients belonging to the user's organization are returned
2. **Performance**: The endpoint uses database joins and pagination to handle large datasets efficiently
3. **Ordering**: Appointments are returned in descending order by appointment date/time (most recent first)
4. **Eager Loading**: Patient data is preloaded to avoid N+1 query issues
5. **Security**: Access is restricted to users with valid organization membership

## Usage Examples

### Administrative Dashboard
Organization administrators can use this endpoint to:
- View all upcoming appointments
- Monitor appointment statuses
- Generate reports for specific date ranges
- Track clinician schedules

### Staff Management
Organization staff can use filters to:
- View appointments for specific clinicians
- Monitor patient appointment history
- Identify cancelled or no-show appointments
- Plan resource allocation

## Rate Limiting

This endpoint may be subject to rate limiting based on your organization's API limits. Contact support for specific rate limit information.
