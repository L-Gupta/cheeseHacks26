from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
from models.patient import Patient
import uuid

class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(Uuid, ForeignKey("patients.id"))
    doctor_id = Column(String)
    pdf_url = Column(String)
    summary_text = Column(String)
    follow_up_date = Column(DateTime(timezone=True))
    status = Column(String, default="pending") # pending, calling, completed, escalated
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient")
