import json

with open("backend/service-account.json") as f:
    data = json.load(f)

print("Service account project_id:", data["project_id"])