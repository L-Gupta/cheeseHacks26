from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.models.patient import Patient
from backend.models.consultation import Consultation

router = APIRouter(prefix="/doctor", tags=["doctor"])

@router.get("/patients")
def get_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()

@router.get("/consultations")
def get_consultations(db: Session = Depends(get_db)):
    return db.query(Consultation).all()
