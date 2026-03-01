from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Uuid, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
from models.consultation import Consultation
import uuid

class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    conversation_id = Column(String, index=True)
    consultation_id = Column(Uuid, ForeignKey("consultations.id"))
    transcript = Column(String)  
    ai_summary = Column(String)  
    urgency_level = Column(String) # low, medium, high
    call_duration = Column(Integer) # duration in seconds
    call_status = Column(String) # started, completed, failed
    dashboard_alert = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    consultation = relationship("Consultation")
