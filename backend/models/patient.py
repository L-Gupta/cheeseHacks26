from sqlalchemy import Column, String, DateTime, Uuid
from sqlalchemy.sql import func
from backend.config.database import Base
import uuid

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    phone_number = Column(String, unique=True, index=True)
    doctor_id = Column(String)  # Treating as string ID for simplicity
    created_at = Column(DateTime(timezone=True), server_default=func.now())
