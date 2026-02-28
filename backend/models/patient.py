from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from backend.config.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone_number = Column(String, unique=True, index=True)
    doctor_id = Column(Integer)  # Simulated simpler relation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
