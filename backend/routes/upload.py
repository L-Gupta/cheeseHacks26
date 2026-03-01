from datetime import datetime, timedelta, timezone
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.models.consultation import Consultation
from backend.models.patient import Patient
from backend.services.pdf_parser import extract_text_from_pdf
from backend.services.embedding_service import EmbeddingService
from backend.services.pinecone_service import PineconeService
from backend.services.gcs_service import GCSService
from backend.utils.helpers import chunk_text, normalize_phone_number

router = APIRouter(tags=["upload"])

@router.post("/upload-consultation")
async def upload_consultation(
    patient_name: str = Form(...),
    phone_number: str = Form(...),
    followup_days: int = Form(...),
    file: UploadFile = File(...),
    doctor_id: str = Form("default-doctor"),
    db: Session = Depends(get_db),
):
    """
    Receives a consultation PDF, stores consultation + vectors, and schedules follow-up date.
    """
    if not file:
        raise HTTPException(
            status_code=400,
            detail={"error": "MISSING_PDF", "message": "PDF file is required."},
        )
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_FILE_TYPE", "message": "Only PDF files are accepted."},
        )
    if followup_days < 0:
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_FOLLOWUP_DAYS", "message": "followup_days must be >= 0."},
        )

    ok_phone, normalized_phone = normalize_phone_number(phone_number)
    if not ok_phone:
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_PHONE_NUMBER", "message": "Phone number must be valid E.164."},
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=400,
            detail={"error": "EMPTY_FILE", "message": "Uploaded PDF is empty."},
        )

    try:
        gcs_service = GCSService()
        embedder = EmbeddingService()
        pinecone_db = PineconeService()
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"error": "SERVICE_INIT_FAILED", "message": f"Cloud service initialization failed: {str(e)}"},
        )

    destination_name = f"{uuid.uuid4()}_{file.filename}"
    pdf_url = gcs_service.upload_pdf(content, destination_name)
    if not pdf_url:
        raise HTTPException(
            status_code=502,
            detail={"error": "GCS_UPLOAD_FAILED", "message": "Failed to upload consultation PDF."},
        )

    summary_text = extract_text_from_pdf(content)
    if not summary_text:
        raise HTTPException(
            status_code=400,
            detail={"error": "PDF_TEXT_EXTRACTION_FAILED", "message": "Could not extract text from PDF."},
        )

    follow_up_date = datetime.now(timezone.utc) + timedelta(days=followup_days)
    patient = db.query(Patient).filter(Patient.phone_number == normalized_phone).first()
    if not patient:
        patient = Patient(name=patient_name.strip(), phone_number=normalized_phone, doctor_id=doctor_id)
        db.add(patient)
        db.flush()

    consultation = Consultation(
        patient_id=patient.id,
        doctor_id=doctor_id,
        pdf_url=pdf_url,
        summary_text=summary_text,
        follow_up_date=follow_up_date,
        status="pending",
    )
    db.add(consultation)
    db.flush()

    chunks = chunk_text(summary_text, chunk_size=800, overlap=100) or [summary_text]
    vectors_to_upsert = []
    for i, chunk in enumerate(chunks):
        vector = embedder.generate_embedding(chunk)
        if not vector:
            db.rollback()
            raise HTTPException(
                status_code=502,
                detail={"error": "EMBEDDING_FAILED", "message": "Failed to generate embedding from consultation text."},
            )
        vectors_to_upsert.append(
            {
                "id": f"{consultation.id}_chunk_{i}",
                "values": vector,
                "metadata": {
                    "consultation_id": str(consultation.id),
                    "patient_id": str(patient.id),
                    "patient_name": patient.name,
                    "doctor_id": doctor_id,
                    "diagnosis": "",
                    "follow_up_date": follow_up_date.isoformat(),
                    "summary_text": chunk,
                    "chunk_index": i,
                },
            }
        )

    if not pinecone_db.upsert_chunks(vectors_to_upsert):
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail={"error": "PINECONE_UPSERT_FAILED", "message": "Failed to store consultation vectors."},
        )

    db.commit()
    db.refresh(consultation)

    return {"success": True, "consultation_id": str(consultation.id)}

@router.post("/upload/consultation")
async def upload_consultation_legacy(
    patient_name: str = Form(...),
    phone_number: str = Form(...),
    followup_days: int = Form(...),
    file: UploadFile = File(...),
    doctor_id: str = Form("default-doctor"),
    db: Session = Depends(get_db),
):
    return await upload_consultation(
        patient_name=patient_name,
        phone_number=phone_number,
        followup_days=followup_days,
        file=file,
        doctor_id=doctor_id,
        db=db,
    )
