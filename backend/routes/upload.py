import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from backend.config.database import get_db
from backend.models.consultation import Consultation
from backend.services.pdf_parser import extract_text_from_pdf
from backend.services.embedding_service import EmbeddingService
from backend.services.pinecone_service import PineconeService

router = APIRouter(prefix="/upload", tags=["upload"])

# Initialize services (lazy load or dependency inject in real app)
embedder = EmbeddingService()
pinecone_db = PineconeService()

@router.post("/consultation")
async def upload_consultation(
    patient_id: str = Form(...),
    doctor_id: str = Form("dr_default_123"), 
    follow_up_date: datetime = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    1. Receives PDF file.
    2. Uploads to Cloud Storage (mocked local for now)
    3. Extracts text using pdfplumber.
    4. Stores raw summary in DB.
    5. Generates Vertex Embedding.
    6. Upserts to Pinecone.
    """
    
    # Read PDF bytes
    content = await file.read()
    
    # Optional Real GCS upload:
    # url = upload_to_gcs(content, file.filename)
    pdf_url = f"gs://patient-pdfs/{uuid.uuid4()}_{file.filename}"

    # Extract text
    summary_text = extract_text_from_pdf(content)
    if not summary_text:
        raise HTTPException(400, "Could not extract text from PDF.")

    # Save to Consultation Database
    db_consultation = Consultation(
        patient_id=patient_id,
        pdf_url=pdf_url,
        summary_text=summary_text,
        follow_up_date=follow_up_date
    )
    db.add(db_consultation)
    db.commit()
    db.refresh(db_consultation)
    
    # Generate Embedding & Upsert to Pinecone
    vector = embedder.generate_embedding(summary_text)
    if vector:
        metadata = {
            "consultation_id": str(db_consultation.id),
            "patient_id": str(patient_id),
            "doctor_id": str(doctor_id),
            "summary_text": summary_text # keeping the raw text in metadata is handy for RAG retrieval
        }
        pinecone_db.upsert_consultation(str(db_consultation.id), vector, metadata)
    
    return db_consultation
