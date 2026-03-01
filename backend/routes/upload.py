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
from backend.services.gcs_service import GCSService
from backend.utils.helpers import chunk_text

router = APIRouter(prefix="/upload", tags=["upload"])

# Initialize services (lazy load or dependency inject in real app)
embedder = EmbeddingService()
pinecone_db = PineconeService()
gcs_service = GCSService()

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
    
    # Upload to Real GCS Bucket
    destination_name = f"{uuid.uuid4()}_{file.filename}"
    pdf_url = gcs_service.upload_pdf(content, destination_name)

    # Extract text
    summary_text = extract_text_from_pdf(content)
    if not summary_text:
        raise HTTPException(400, "Could not extract text from PDF.")

    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient_id format. Must be a UUID.")

    # Save to Consultation Database
    db_consultation = Consultation(
        patient_id=patient_uuid,
        doctor_id=doctor_id,
        pdf_url=pdf_url,
        summary_text=summary_text,
        follow_up_date=follow_up_date
    )
    db.add(db_consultation)
    db.commit()
    db.refresh(db_consultation)
    
    # Chunk text, generate Embeddings & Upsert to Pinecone
    chunks = chunk_text(summary_text, chunk_size=800, overlap=100)
    vectors_to_upsert = []
    
    for i, chunk in enumerate(chunks):
        vector = embedder.generate_embedding(chunk)
        if vector:
            metadata = {
                "consultation_id": str(db_consultation.id),
                "patient_id": str(patient_id),
                "doctor_id": str(doctor_id),
                "summary_text": chunk, # keeping the chunk's text in metadata is required for RAG retrieval
                "chunk_index": i
            }
            vectors_to_upsert.append({
                "id": f"{db_consultation.id}_chunk_{i}",
                "values": vector,
                "metadata": metadata
            })
            
    if vectors_to_upsert:
        pinecone_db.upsert_chunks(vectors_to_upsert)
    
    return db_consultation
