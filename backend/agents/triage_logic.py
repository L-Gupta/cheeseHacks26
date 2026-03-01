from vertexai.generative_models import GenerativeModel
import vertexai
from config.settings import settings
from agents.prompts import TRIAGE_PROMPT
from utils.helpers import extract_json_from_text, safe_urgency, parse_bool

# Ensure vertexai is initialized once globally or inside the init
vertexai.init(project=settings.GOOGLE_PROJECT_ID, location=settings.GCP_LOCATION)

class TriageAnalyzer:
    def __init__(self):
        self.model = GenerativeModel(model_name=settings.VERTEX_AI_MODEL)

    def analyze_call(self, transcript: str) -> dict:
        """
        Takes the full conversation transcript and returns a structured triage report.
        """
        if not transcript.strip():
            return {"summary": "Call dropped or no speech detected.", "urgency": "low", "requires_doctor": False}

        prompt = TRIAGE_PROMPT.format(transcript=transcript)
        
        try:
            response = self.model.generate_content(prompt)
            result = extract_json_from_text(response.text)

            if not isinstance(result, dict):
                result = {}
            summary = str(result.get("summary", "")).strip() or str(response.text).strip() or "No summary generated."
            urgency = safe_urgency(str(result.get("urgency", "medium")))
            requires_doctor = parse_bool(result.get("requires_doctor"), default=(urgency == "high"))
            if urgency == "high":
                requires_doctor = True

            return {"summary": summary, "urgency": urgency, "requires_doctor": requires_doctor}
        except Exception as e:
            print(f"Error in TriageAnalyzer: {e}")
            return {"summary": "Triage analysis failed.", "urgency": "high", "requires_doctor": True}
