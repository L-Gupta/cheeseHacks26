from google.cloud import storage
from backend.config.settings import settings

class GCSService:
    def __init__(self):
        # Implicitly uses GOOGLE_APPLICATION_CREDENTIALS 
        self.client = storage.Client(project=settings.GOOGLE_PROJECT_ID)
        self.bucket_name = f"{settings.GOOGLE_PROJECT_ID}-consultation-pdfs"
        
        # Ensure bucket exists
        try:
             self.bucket = self.client.get_bucket(self.bucket_name)
        except Exception:
             print(f"Bucket {self.bucket_name} not found. Creating...")
             try:
                 self.bucket = self.client.create_bucket(self.bucket_name, location=settings.GCP_LOCATION)
             except Exception as e:
                 print(f"Failed to create bucket: {e}")
                 self.bucket = None

    def upload_pdf(self, file_content: bytes, destination_blob_name: str) -> str:
        """Uploads a file to the bucket and returns the standard gs:// URL."""
        if not self.bucket:
             print("GCS Bucket not initialized.")
             return f"gs://{self.bucket_name}/{destination_blob_name}"
             
        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_string(file_content, content_type="application/pdf")
            
            return f"gs://{self.bucket_name}/{destination_blob_name}"
        except Exception as e:
            print(f"Error uploading to GCS: {e}")
            return ""