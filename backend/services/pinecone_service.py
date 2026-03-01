from pinecone import Pinecone, ServerlessSpec
from config.settings import settings

class PineconeService:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = "followup-consultations"
        
        # Ensure index exists ideally, but doing it in __init__ is bad practice for production.
        # Assuming the operator creates it, or we handle it here:
        listed = self.pc.list_indexes()
        try:
            existing_indexes = [index_info["name"] for index_info in listed]
        except Exception:
            try:
                existing_indexes = [index_info.name for index_info in listed.indexes]
            except Exception:
                existing_indexes = []
        
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
        """Fetches metadata from first chunk by consultation id."""
        try:
            chunk_id = f"{consultation_id}_chunk_0"
            result = self.index.fetch(ids=[chunk_id])
            if result and "vectors" in result and chunk_id in result["vectors"]:
                return result["vectors"][chunk_id].get("metadata", {})
            return {}
        except Exception as e:
            print(f"Pinecone Fetch Error: {e}")
            return {}

    def query_similar_chunks(self, query_vector: list[float], consultation_id: str | None = None, top_k: int = 3) -> list[dict]:
        """Returns top-k matching vector metadata for RAG context injection."""
        if not query_vector:
            return []
        try:
            pinecone_filter = {"consultation_id": str(consultation_id)} if consultation_id else None
            result = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=pinecone_filter,
            )
            matches = result.get("matches", []) if isinstance(result, dict) else getattr(result, "matches", [])
            normalized = []
            for m in matches:
                metadata = m.get("metadata", {}) if isinstance(m, dict) else getattr(m, "metadata", {}) or {}
                normalized.append(metadata)
            return normalized
        except Exception as e:
            print(f"Pinecone Query Error: {e}")
            return []
