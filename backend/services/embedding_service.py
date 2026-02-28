from vertexai.language_models import TextEmbeddingModel
import vertexai
from backend.config.settings import settings

# Usually global init happens in main or once per service
# vertexai.init(project=settings.GOOGLE_PROJECT_ID, location=settings.GCP_LOCATION)

class EmbeddingService:
    def __init__(self):
        # We use a standard text embedding model (e.g., text-embedding-004)
        self.model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    def generate_embedding(self, text: str) -> list[float]:
        try:
            embeddings = self.model.get_embeddings([text])
            if embeddings:
                return embeddings[0].values
            return []
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
