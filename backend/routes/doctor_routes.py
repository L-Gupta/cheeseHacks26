from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel

from backend.config.database import get_db
from backend.models.patient import Patient
from backend.models.consultation import Consultation

router = APIRouter(prefix="/doctor", tags=["doctor"])

class ConsultationCreate(BaseModel):
    patient_id: int
    summary: str
    follow_up_date: datetime

@router.post("/consultation")
def create_consultation(consultation: ConsultationCreate, db: Session = Depends(get_db)):
    db_consultation = Consultation(
        patient_id=consultation.patient_id,
        summary=consultation.summary,
        follow_up_date=consultation.follow_up_date
    )
    db.add(db_consultation)
    db.commit()
    db.refresh(db_consultation)
    return db_consultation

@router.get("/patients")
def get_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()
