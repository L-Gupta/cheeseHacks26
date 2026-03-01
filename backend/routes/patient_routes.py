from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from pydantic import BaseModel

from config.database import get_db
from models.patient import Patient

router = APIRouter(prefix="/patients", tags=["patients"])

class PatientCreate(BaseModel):
    name: str
    phone_number: str
    doctor_id: str

@router.post("/")
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    db_patient = db.query(Patient).filter(Patient.phone_number == patient.phone_number).first()
    if db_patient:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    new_patient = Patient(
        name=patient.name,
        phone_number=patient.phone_number,
        doctor_id=patient.doctor_id
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

@router.get("/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    try:
        pid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    patient = db.query(Patient).filter(Patient.id == pid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
