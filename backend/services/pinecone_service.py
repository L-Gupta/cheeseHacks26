from pinecone import Pinecone, ServerlessSpec
from backend.config.settings import settings

class PineconeService:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = "followup-consultations"
        
        # Ensure index exists ideally, but doing it in __init__ is bad practice for production.
        # Assuming the operator creates it, or we handle it here:
        existing_indexes = [index_info["name"] for index_info in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
             self.pc.create_index(
                 name=self.index_name,
                 dimension=768, # Dimension for text-embedding-004
                 metric="cosine",
                 spec=ServerlessSpec(
                     cloud="aws",
                     region="us-east-1"
                 ) 
             )
        self.index = self.pc.Index(self.index_name)

    def upsert_consultation(self, consultation_id: str, vector: list[float], metadata: dict):
        """Upserts a single consultation embedding to Pinecone."""
        try:
            self.index.upsert(
                vectors=[
                    {
                        "id": str(consultation_id),
                        "values": vector,
                        "metadata": metadata
                    }
                ]
            )
        except Exception as e:
             print(f"Error upserting to Pinecone: {e}")

    def upsert_chunks(self, vectors: list[dict]):
        """Upserts a batch of chunk vectors to Pinecone."""
        if not self.index or not vectors:
            return False
            
        try:
            self.index.upsert(vectors=vectors)
            return True
        except Exception as e:
            print(f"Error upserting chunks to Pinecone: {e}")
            return False

    def query_context(self, consultation_id: str) -> dict:
        """Fetches the metadata back from Pinecone based on ID if we just want context."""
        try:
             result = self.index.fetch(ids=[str(consultation_id)])
             if result and "vectors" in result and str(consultation_id) in result["vectors"]:
                 return result["vectors"][str(consultation_id)]["metadata"]
             return {}
        except Exception as e:
             print(f"Pinecone Fetch Error: {e}")
             return {}
