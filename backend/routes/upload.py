import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from backend.config.database import get_db
from backend.models.consultation import Consultation
from backend.services.pdf_parser import extract_text_from_pdf

# Lazy-load services that pull in vertexai/protobuf (not Python 3.14–safe at import time)
router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/consultation")
async def upload_consultation(
    patient_id: str = Form(...),
    doctor_id: str = Form("dr_default_123"),
    follow_up_date: datetime = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    1. Receives PDF file.
    2. Uploads to Cloud Storage (if available).
    3. Extracts text using pdfplumber.
    4. Stores raw summary in DB.
    5. Generates Vertex Embedding & upserts to Pinecone (if available).
    """
    content = await file.read()
    destination_name = f"{uuid.uuid4()}_{file.filename}"
    pdf_url = ""

    try:
        from backend.services.gcs_service import GCSService
        gcs_service = GCSService()
        pdf_url = gcs_service.upload_pdf(content, destination_name) or pdf_url
    except Exception as e:
        print(f"GCS skipped: {e}")
        pdf_url = f"local://{destination_name}"

    summary_text = extract_text_from_pdf(content)
    if not summary_text:
        raise HTTPException(400, "Could not extract text from PDF.")

    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(400, "Invalid patient_id format (must be a UUID).")

    db_consultation = Consultation(
        patient_id=patient_uuid,
        pdf_url=pdf_url,
        summary_text=summary_text,
        follow_up_date=follow_up_date,
    )
    db.add(db_consultation)
    db.commit()
    db.refresh(db_consultation)

    try:
        from backend.services.embedding_service import EmbeddingService
        from backend.services.pinecone_service import PineconeService
        embedder = EmbeddingService()
        pinecone_db = PineconeService()
        vector = embedder.generate_embedding(summary_text)
        if vector:
            metadata = {
                "consultation_id": str(db_consultation.id),
                "patient_id": str(patient_id),
                "doctor_id": str(doctor_id),
                "summary_text": summary_text,
            }
            pinecone_db.upsert_consultation(str(db_consultation.id), vector, metadata)
    except Exception as e:
        print(f"Embedding/Pinecone skipped: {e}")

    return db_consultation
