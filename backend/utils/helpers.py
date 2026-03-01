import json
import re
from typing import Tuple

def extract_json_from_text(text: str) -> dict:
    """Extracts a JSON object from a plaintext string using regex."""
    try:
        # Match a basic JSON object shape
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        return {}
    except Exception:
        return {}

def normalize_phone_number(phone_number: str) -> Tuple[bool, str]:
    """
    US-focused E.164 normalization for demo.
    Accepts:
    - 10 digits: 5551234567 -> +15551234567
    - 11 digits with leading 1: 15551234567 -> +15551234567
    - E.164: +15551234567
    """
    raw = (phone_number or "").strip()
    if raw.startswith("+"):
        digits = re.sub(r"[^\d]", "", raw[1:])
        candidate = f"+{digits}"
    else:
        digits = re.sub(r"[^\d]", "", raw)
        if len(digits) == 10:
            candidate = f"+1{digits}"
        elif len(digits) == 11 and digits.startswith("1"):
            candidate = f"+{digits}"
        else:
            return False, ""

    if not re.fullmatch(r"\+1\d{10}", candidate):
        return False, ""
    return True, candidate

def safe_urgency(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"low", "medium", "high"}:
        return normalized
    return "medium"

def parse_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    return default

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Splits a long string into overlapping chunks for vector embeddings."""
    if not text:
        return []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[int(start):int(end)])
        start += chunk_size - overlap
    
    return chunks
