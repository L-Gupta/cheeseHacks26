import logging
from backend.config.settings import settings
from backend.services.call_service import get_twilio_client

logger = logging.getLogger("escalation")

def notify_doctor(consultation_id: str, summary: str, urgency: str, doctor_phone_number: str | None = None):
    """
    Called when the AI triage logic detects a concerning condition affecting the patient.
    In a real app, this would use Twilio SMS, SendGrid for Email, or Firebase push notifications
    to alert the doctor immediately.
    """
    logger.warning(
        f"ESCALATION ALERT | Consultation ID {consultation_id} | URGENCY: {urgency.upper()}"
    )
    logger.warning(f"Patient Condition Summary: {summary}")
    
    to_phone = doctor_phone_number or settings.DOCTOR_ALERT_PHONE_NUMBER
    if not to_phone:
        logger.warning("No doctor alert phone number configured.")
        return False

    client = get_twilio_client()
    if not client or not settings.TWILIO_PHONE_NUMBER:
        logger.warning("Twilio client unavailable for escalation SMS.")
        return False

    try:
        body = (
            f"URGENT follow-up escalation.\n"
            f"Consultation: {consultation_id}\n"
            f"Urgency: {urgency}\n"
            f"Summary: {summary}"
        )
        client.messages.create(
            to=to_phone,
            from_=settings.TWILIO_PHONE_NUMBER,
            body=body,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send doctor escalation SMS: {e}")
        return False
