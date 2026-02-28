from vertexai.generative_models import GenerativeModel
import vertexai
from backend.config.settings import settings
from backend.agents.prompts import TRIAGE_PROMPT
from backend.utils.helpers import extract_json_from_text

# Ensure vertexai is initialized once globally or inside the init
vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_LOCATION)

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
            
            # Default fallback if parsing fails
            if "requires_doctor" not in result:
                return {"summary": response.text, "urgency": "medium", "requires_doctor": True}
                
            return result
        except Exception as e:
            print(f"Error in TriageAnalyzer: {e}")
            return {"summary": "Triage analysis failed.", "urgency": "high", "requires_doctor": True}
