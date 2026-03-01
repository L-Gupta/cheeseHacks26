from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from backend.config.database import get_db
from backend.models.consultation import Consultation
from backend.services.call_service import initiate_outbound_call

router = APIRouter(tags=["cloud_scheduler"])

def _trigger_scheduled_followups(db: Session):
    """
    Called by Google Cloud Scheduler every X minutes.
    Finds pending consultations due for follow-up and initiates calls via Twilio.
    """
    now = datetime.utcnow()
    
    # 1. Find all due consultations
    due_consultations = db.query(Consultation).filter(
        Consultation.status == "pending",
        Consultation.follow_up_date <= now
    ).all()
    
    if not due_consultations:
        return {"message": "No follow-ups due."}
        
    results = []
    # 2. Trigger calls
    for consultation in due_consultations:
        try:
            # Lock the consultation before dialing to avoid duplicate calls from overlapping cron runs.
            consultation.status = "calling"
            db.commit()
            db.refresh(consultation)

            # We fetch the patient to get phone number
            patient = consultation.patient
            success = initiate_outbound_call(
                phone_number=patient.phone_number,
                consultation_id=consultation.id
            )
            if success:
                results.append({"id": str(consultation.id), "status": "calling"})
            else:
                consultation.status = "pending"
                db.commit()
                results.append({"id": str(consultation.id), "status": "call_failed"})
        except Exception as e:
            try:
                consultation.status = "pending"
                db.commit()
            except Exception:
                db.rollback()
            results.append({"id": str(consultation.id), "status": f"error: {str(e)}"})

    return {"processed": len(due_consultations), "results": results}

@router.get("/trigger-followups")
def trigger_scheduled_followups_get(db: Session = Depends(get_db)):
    return _trigger_scheduled_followups(db)

@router.post("/cron/trigger-followups")
def trigger_scheduled_followups_legacy(db: Session = Depends(get_db)):
    return _trigger_scheduled_followups(db)
