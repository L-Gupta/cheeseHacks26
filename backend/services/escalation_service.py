import logging

logger = logging.getLogger("escalation")

def notify_doctor(consultation_id: int, summary: str, urgency: str):
    """
    Called when the AI triage logic detects a concerning condition affecting the patient.
    In a real app, this would use Twilio SMS, SendGrid for Email, or Firebase push notifications
    to alert the doctor immediately.
    """
    logger.warning(
        f"ESCALATION ALERT | Consultation ID {consultation_id} | URGENCY: {urgency.upper()}"
    )
    logger.warning(f"Patient Condition Summary: {summary}")
    
    # Mock sending SMS to doctor
    # client.messages.create(to='+1DoctorNumber', from_='+1OurNumber', body=f'Escalation: {summary}')
    
    return True
