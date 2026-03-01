import json
import re

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
