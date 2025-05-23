def create_mock_appointment(
    id=None, 
    clinician_id="clinician-123", 
    patient_id="patient-123",
    date_obj=None,
    time_obj=None,
    date_str=None,
    time_str=None,
    appointment_type="virtual",
    status="scheduled",
    notes=None,
    confirmation_code=None,
    cancellation_reason=None,
    created_at=None,
    updated_at=None
):
    """
    Create a mock Appointment instance with specified attributes.
    
    Args:
        id: Appointment ID (defaults to a UUID string)
        clinician_id: ID of the clinician
        patient_id: ID of the patient
        date_obj: Appointment date as a date object
        time_obj: Appointment time as a time object
        date_str: Appointment date as a string (alternative to date_obj)
        time_str: Appointment time as a string (alternative to time_obj)
        appointment_type: Type of appointment (virtual, in-person, etc.)
        status: Appointment status (scheduled, completed, cancelled, etc.)
        notes: Additional notes for the appointment
        confirmation_code: Confirmation code for the appointment
        cancellation_reason: Reason for cancellation (if applicable)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    
    Returns:
        MagicMock: Configured to mimic an Appointment model
    """
    from datetime import datetime, date, time
    
    mock_appointment = MagicMock()
    mock_appointment.id = id or str(uuid.uuid4())
    mock_appointment.clinician_id = clinician_id
    mock_appointment.patient_id = patient_id
    
    # Handle date and time inputs
    if date_obj is not None:
        mock_appointment.date = date_obj
    elif date_str is not None:
        from datetime import datetime
        mock_appointment.date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        mock_appointment.date = date.today()
        
    if time_obj is not None:
        mock_appointment.time = time_obj
    elif time_str is not None:
        from datetime import datetime
        mock_appointment.time = datetime.strptime(time_str, "%H:%M").time()
    else:
        mock_appointment.time = time(9, 0)  # Default to 9:00 AM
    
    mock_appointment.appointment_type = appointment_type
    mock_appointment.status = status
    mock_appointment.notes = notes
    mock_appointment.confirmation_code = confirmation_code or f"CONF-{uuid.uuid4().hex[:6].upper()}"
    mock_appointment.cancellation_reason = cancellation_reason
    mock_appointment.created_at = created_at or datetime.now()
    mock_appointment.updated_at = updated_at or datetime.now()
    
    # Relationship mocks
    mock_appointment.clinician = MagicMock()
    mock_appointment.clinician.id = clinician_id
    mock_appointment.clinician.name = "Dr. Test Clinician"
    mock_appointment.clinician.role = "clinician"
    
    mock_appointment.patient = MagicMock()
    mock_appointment.patient.id = patient_id
    mock_appointment.patient.name = "Test Patient"
    mock_appointment.patient.role = "patient"
    
    # Configure additional computed properties
    mock_appointment.clinician_name = "Dr. Test Clinician"
    mock_appointment.patient_name = "Test Patient"
    
    # Configure the __repr__ method for debugging
    mock_appointment.__repr__ = lambda self: (
        f"<Appointment(id={self.id}, clinician={self.clinician_id}, "
        f"patient={self.patient_id}, date={self.date}, time={self.time})>"
    )
    
    return mock_appointment


def create_mock_clinician_availability(
    id=None,
    clinician_id="clinician-123",
    date_obj=None,
    date_str=None,
    available_slots=None,
    timezone="America/New_York",
    created_at=None,
    updated_at=None
):
    """
    Create a mock ClinicianAvailability instance with specified attributes.
    
    Args:
        id: Availability record ID (defaults to a UUID string)
        clinician_id: ID of the clinician
        date_obj: Availability date as a date object
        date_str: Availability date as a string (alternative to date_obj)
        available_slots: List of available time slots
        timezone: Timezone for the availability
        created_at: Creation timestamp
        updated_at: Last update timestamp
    
    Returns:
        MagicMock: Configured to mimic a ClinicianAvailability model
    """
    from datetime import datetime, date, time
    
    mock_availability = MagicMock()
    mock_availability.id = id or str(uuid.uuid4())
    mock_availability.clinician_id = clinician_id
    
    # Handle date input
    if date_obj is not None:
        mock_availability.date = date_obj
    elif date_str is not None:
        mock_availability.date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        mock_availability.date = date.today()
    
    # Default available slots if none provided
    if available_slots is None:
        available_slots = [
            {"time": "09:00", "available": True},
            {"time": "10:00", "available": True},
            {"time": "11:00", "available": True},
            {"time": "13:00", "available": True},
            {"time": "14:00", "available": True},
            {"time": "15:00", "available": True},
            {"time": "16:00", "available": True}
        ]
    
    mock_availability.available_slots = available_slots
    mock_availability.timezone = timezone
    mock_availability.created_at = created_at or datetime.now()
    mock_availability.updated_at = updated_at or datetime.now()
    
    # Relationship mock
    mock_availability.clinician = MagicMock()
    mock_availability.clinician.id = clinician_id
    mock_availability.clinician.name = "Dr. Test Clinician"
    mock_availability.clinician.role = "clinician"
    
    # Configure the __repr__ method for debugging
    mock_availability.__repr__ = lambda self: (
        f"<ClinicianAvailability(id={self.id}, clinician={self.clinician_id}, "
        f"date={self.date}, slots={len(self.available_slots)})>"
    )
    
    return mock_availability
