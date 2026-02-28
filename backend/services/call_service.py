import os
from twilio.rest import Client
from backend.config.settings import settings

def get_twilio_client():
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        print("Warning: Twilio credentials not fully set up")
        return None
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def initiate_outbound_call(phone_number: str, consultation_id: str):
    """
    Initates a call to the patient via Twilio.
    Tells Twilio to fetch TwiML from our /twilio/twiml endpoint which will
    set up the WebSocket Media Stream.
    """
    client = get_twilio_client()
    if not client:
        return False
        
    try:
        # The URL Twilio will fetch when the call connects
        # e.g., https://my-app.a.run.app/twilio/twiml?consultation_id=123
        twiml_url = f"https://{settings.HOST_DOMAIN}/twilio/twiml?consultation_id={consultation_id}"
        
        call = client.calls.create(
            to=phone_number,
            from_=settings.TWILIO_PHONE_NUMBER,
            url=twiml_url,
            record=False # We capture audio via stream, not Twilio recording
        )
        print(f"Initiated call for consultation {consultation_id}: SID {call.sid}")
        return True
    except Exception as e:
        print(f"Error initiating Twilio call: {e}")
        return False
