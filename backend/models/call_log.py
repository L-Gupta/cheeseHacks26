from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.config.database import Base
from backend.models.consultation import Consultation

class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"))
    transcript = Column(String)  # Final full text transcript
    ai_summary = Column(String)  # Structured JSON summary
    urgency_level = Column(String) # low, medium, high
    call_status = Column(String) # started, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    consultation = relationship("Consultation")
