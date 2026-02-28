from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.config.database import Base
from backend.models.patient import Patient

class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    summary = Column(String)
    follow_up_date = Column(DateTime(timezone=True))
    status = Column(String, default="pending") # pending, completed, escalated
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient")
