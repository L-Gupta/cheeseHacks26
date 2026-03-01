from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from models.patient import Patient
from models.consultation import Consultation
from models.call_log import CallLog
from fastapi import HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/doctor", tags=["doctor"])

class StatusUpdate(BaseModel):
    status: str

@router.get("/patients")
def get_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()

@router.get("/consultations")
def get_consultations(db: Session = Depends(get_db)):
    return db.query(Consultation).all()

@router.get("/call-logs")
def get_call_logs(db: Session = Depends(get_db)):
    """Fetch recent call logs for the dashboard"""
    return db.query(CallLog).order_by(CallLog.created_at.desc()).all()

@router.put("/consultations/{consultation_id}/status")
def update_consultation_status(consultation_id: str, payload: StatusUpdate, db: Session = Depends(get_db)):
    """Allows doctor to resolve an escalated case."""
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    consultation.status = payload.status
    db.commit()
    db.refresh(consultation)
    return consultation
