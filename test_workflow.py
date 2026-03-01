import time
import requests
import datetime

BASE_URL = "http://localhost:8000"

def test_workflow():
    print("1. Creating Patient...")
    patient_data = {
        "name": "Testing User",
        "phone_number": "+16082131997",
        "doctor_id": "dr_001"
    }
    r = requests.post(f"{BASE_URL}/patients/", json=patient_data)
    if r.status_code == 200:
        patient_id = r.json()["id"]
        print(f"✅ Created Patient successfully! ID: {patient_id}")
    elif r.status_code == 400 and "already registered" in r.text:
        # Fetch patient id if they exist (we might need a GET /patients)
        print("Patient exists, fetching patients...")
        patients = requests.get(f"{BASE_URL}/doctor/patients").json()
        patient_id = next(p["id"] for p in patients if p["phone_number"] == patient_data["phone_number"])
        print(f"✅ Found Existing Patient! ID: {patient_id}")
    else:
        print("❌ Failed to create patient:", r.text)
        return

    print("2. Uploading Consultation PDF...")
    with open("john_doe_cardiology_report.pdf", "rb") as f:
        files = {"file": ("john_doe_cardiology_report.pdf", f, "application/pdf")}
        data = {
            "patient_id": patient_id,
            "doctor_id": "dr_001",
            "follow_up_date": datetime.datetime.now().isoformat()
        }
        r = requests.post(f"{BASE_URL}/upload/consultation", files=files, data=data)
        if r.status_code == 200:
            print("✅ Uploaded Consultation and Embeddings completed successfully!")
        else:
            print("❌ Failed to upload consultation:", r.text)
            return

    print("3. Triggering Scheduler...")
    time.sleep(2) # Give the database a moment
    r = requests.post(f"{BASE_URL}/cron/trigger-followups")
    if r.status_code == 200:
        response = r.json()
        print(f"✅ Triggered Scheduler! Response: {response}")
    else:
        print("❌ Failed to trigger scheduler:", r.text)
        return

if __name__ == "__main__":
    test_workflow()
