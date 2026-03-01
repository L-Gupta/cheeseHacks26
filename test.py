from google.cloud import storage
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "cheesehacks26"
KEY_PATH = "backend/service-account.json"

# Load credentials manually
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)

print("Testing Cloud Storage...")

client = storage.Client(project=PROJECT_ID, credentials=credentials)
buckets = list(client.list_buckets())
print("Storage works ✅")

print("Testing Vertex AI...")

vertexai.init(
    project=PROJECT_ID,
    location="us-central1",
    credentials=credentials
)

model = GenerativeModel("gemini-2.5-flash")
response = model.generate_content("Say hello in 5 words.")

print("Vertex AI response:", response.text)
print("Vertex AI works ✅")