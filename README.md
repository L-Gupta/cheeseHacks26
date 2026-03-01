# AI Patient Follow-Up Agent

An AI-powered healthcare assistant that automatically performs post-consultation follow-ups with patients via phone calls. The system schedules follow-ups after a doctor visit, calls patients using an AI voice agent, collects health updates, and escalates concerns to doctors when necessary.

---

## Problem

After consultations, doctors prescribe treatment but often lose track of patient progress. Patients must book another appointment for simple follow-ups, leading to:

* Delayed care
* Overloaded clinics
* Poor treatment adherence
* Missed complications

This project automates follow-up care using an AI agent that contacts patients at scheduled intervals.

---

## Solution

Doctors upload consultation notes and define a follow-up interval.
An AI agent automatically calls the patient, conducts a structured health check, and summarizes outcomes.

### Workflow

1. Doctor uploads consultation summary
2. Doctor selects follow-up interval (e.g., 7 days)
3. System schedules follow-up
4. AI calls patient automatically
5. AI collects symptoms + responses
6. AI classifies patient condition
7. If needed -> doctor notified for escalation

---

## System Architecture

```
Doctor Dashboard
        |
        v
   FastAPI Backend
        |
 +------+-----------------------+
 |      |                       |
 v      v                       v
Database Cloud Scheduler        AI Agent (Gemini)
(PostgreSQL) (/trigger-followups) + RAG (Pinecone)
        |                       |
        v                       v
     Twilio <-> Google STT / Google TTS
          (Bidirectional Media Stream)
```

---

## Tech Stack

### Backend

* **FastAPI** - API server & webhooks
* **Python 3.11+**
* **SQLAlchemy + pg8000** - ORM + PostgreSQL driver
* **Pydantic + pydantic-settings** - validation & config
* **Google Cloud Scheduler trigger endpoint** - follow-up jobs

### AI & Voice

* **LLM:** Gemini via **Vertex AI** (`gemini-2.5-flash`)
* **Speech-to-Text:** **Google Cloud Speech-to-Text**
* **Text-to-Speech:** **Google Cloud Text-to-Speech**
* **Vector Search (RAG):** **Pinecone**
* **Document Storage:** **Google Cloud Storage**
* **PDF Parsing:** **pdfplumber**
* **Conversation Orchestration:** Custom AI agent logic

### Telephony

* **Twilio Programmable Voice**

  * Outbound calls
  * Webhook streaming
  * Call lifecycle events
* **Twilio SMS** for doctor escalation alerts

### Database

* **PostgreSQL**

### Frontend (Doctor Dashboard)

* **Next.js 16**
* **React 19**
* **TypeScript**
* **Tailwind CSS v4**
* **Framer Motion**

### Hosting

* Backend: **Google Cloud Run**
* Cloud services: **Vertex AI, Cloud Speech, Cloud TTS, Cloud Storage**
* Database: **PostgreSQL** (managed or self-hosted)
* Frontend: **Next.js app**

---

## Project Structure

```
backend/
|
|-- main.py
|-- config/
|   |-- settings.py
|   `-- database.py
|
|-- models/
|   |-- patient.py
|   |-- consultation.py
|   `-- call_log.py
|
|-- routes/
|   |-- followups.py
|   |-- patient_routes.py
|   |-- twilio_webhook.py
|   `-- upload.py
|
|-- services/
|   |-- scheduler.py
|   |-- call_service.py
|   |-- gemini_service.py
|   |-- speech_to_text.py
|   |-- text_to_speech.py
|   |-- embedding_service.py
|   |-- pinecone_service.py
|   |-- gcs_service.py
|   |-- pdf_parser.py
|   |-- session_state.py
|   `-- escalation_service.py
|
|-- agents/
|   |-- prompts.py
|   `-- triage_logic.py
|
`-- utils/
    `-- helpers.py

frontend/
|-- src/
|-- package.json
`-- next.config.ts
```

---

## Database Schema

### Patients

```
id
name
phone_number
doctor_id
created_at
```

### Consultations

```
id
patient_id
doctor_id
pdf_url
summary_text
follow_up_date
status (pending/calling/completed/escalated)
created_at
```

### Call Logs

```
id
conversation_id
consultation_id
transcript
ai_summary
urgency_level
call_duration
call_status
dashboard_alert
created_at
```

---

## AI Agent Design

The AI agent performs structured medical follow-ups.

### Responsibilities

* Verify patient identity
* Ask symptom-based questions
* Check medication adherence
* Detect worsening conditions
* Generate structured summary

### Output Format (JSON)

```json
{
  "summary": "Patient reports reduced pain but mild nausea.",
  "urgency": "medium",
  "requires_doctor": true
}
```

---

## Scheduling Strategy

Follow-ups are triggered using:

### MVP

Google Cloud Scheduler calls the backend trigger endpoint periodically:

* `GET /trigger-followups`
* `POST /cron/trigger-followups`

The backend then queries due consultations:

```sql
SELECT * FROM consultations
WHERE follow_up_date <= NOW()
AND status = 'pending';
```

### Optional Advanced

Migrate scheduler trigger to a queue-based workflow (e.g., Cloud Tasks) for higher scale and retries.

---

## Call Flow

1. Scheduler detects due follow-up
2. Backend triggers Twilio outbound call
3. Twilio connects to webhook
4. Audio streamed to backend WebSocket
5. Google STT transcribes patient speech
6. Gemini generates responses
7. Google TTS synthesizes AI replies
8. Responses + triage stored
9. Escalation triggered if necessary

---

## Safety Considerations

* AI never provides medical diagnosis
* Always advises contacting doctor for emergencies
* Secure storage of patient data
* HTTPS required
* Minimal PHI storage for demo purposes

---

## Local Setup

### 1. Clone Repo

```
git clone <repo-url>
cd cheeseHacks26
```

### 2. Create Environment

```
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

### 4. Environment Variables

Create `.env`:

```
DATABASE_URL=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
DOCTOR_ALERT_PHONE_NUMBER=
HOST_DOMAIN=
GOOGLE_PROJECT_ID=
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=
VERTEX_AI_MODEL=gemini-2.5-flash
PINECONE_API_KEY=
PINECONE_ENV=
```

### 5. Run Server

```
uvicorn backend.main:app --reload
```

---

## MVP Features

* Doctor uploads consultation
* Automated follow-up scheduling
* AI phone calls
* Conversation transcription
* AI-generated summaries
* Doctor escalation alerts

---

## Demo Runtime Notes (Cloud Run)

For hackathon demo stability with Twilio media streams, deploy with a single instance:

* min instances = 1
* max instances = 1

This avoids cross-instance session loss for live call state.

---

## Future Improvements

* Multilingual patient calls
* Emotion detection
* EHR integration
* RAG-based personalized conversations
* SMS fallback when calls fail
* Nurse dashboard
* HIPAA-compliant deployment

---

## Hackathon Value Proposition

* Reduces unnecessary appointments
* Improves patient outcomes
* Saves doctor time
* Enables scalable healthcare follow-ups

---

## License

MIT License

---

## Contributors

Hackathon Team - AI Patient Follow-Up Agent
