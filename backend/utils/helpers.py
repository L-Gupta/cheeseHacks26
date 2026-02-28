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
