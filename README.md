# 🩺 AI Patient Follow-Up Agent

An AI-powered healthcare assistant that automatically performs post-consultation follow-ups with patients via phone calls. The system schedules follow-ups after a doctor visit, calls patients using an AI voice agent, collects health updates, and escalates concerns to doctors when necessary.

---

## 🚀 Problem

After consultations, doctors prescribe treatment but often lose track of patient progress. Patients must book another appointment for simple follow-ups, leading to:

* Delayed care
* Overloaded clinics
* Poor treatment adherence
* Missed complications

This project automates follow-up care using an AI agent that contacts patients at scheduled intervals.

---

## 💡 Solution

Doctors upload consultation notes and define a follow-up interval.
An AI agent automatically calls the patient, conducts a structured health check, and summarizes outcomes.

### Workflow

1. Doctor uploads consultation summary
2. Doctor selects follow-up interval (e.g., 7 days)
3. System schedules follow-up
4. AI calls patient automatically
5. AI collects symptoms + responses
6. AI classifies patient condition
7. If needed → doctor notified for escalation

---

## 🧱 System Architecture

```
Doctor Dashboard
        │
        ▼
   FastAPI Backend
        │
 ┌──────┼───────────────┐
 │      │               │
 ▼      ▼               ▼
Database Scheduler   AI Agent
(PostgreSQL)         (LLM)
        │               │
        ▼               ▼
     Twilio  ⇄  Deepgram Voice
            (Call + Speech)
```

---

## 🧰 Tech Stack

### Backend

* **FastAPI** — API server & webhooks
* **Python 3.11+**
* **SQLAlchemy** — ORM
* **Pydantic** — validation
* **Background Scheduler (APScheduler / Celery)** — follow-up jobs

### AI & Voice

* **LLM:** Gemini (free tier) or Claude (free tier)
* **Speech-to-Text:** Deepgram STT
* **Text-to-Speech:** Deepgram TTS
* **Conversation Orchestration:** Custom AI agent logic

### Telephony

* **Twilio Programmable Voice**

  * Outbound calls
  * Webhook streaming
  * Call lifecycle events

### Database

* **PostgreSQL**
* Optional: **Redis** (priority scheduling)

### Frontend (Doctor Dashboard)

* **Next.js**
* **React**
* **Tailwind CSS**

### Hosting

* Backend: Railway / Render / Fly.io
* Database: Supabase / Neon
* Frontend: Vercel

---

## 📂 Project Structure

```
backend/
│
├── main.py
├── config/
│   ├── settings.py
│   └── database.py
│
├── models/
│   ├── patient.py
│   ├── consultation.py
│   └── call_log.py
│
├── routes/
│   ├── doctor_routes.py
│   ├── patient_routes.py
│   └── twilio_webhook.py
│
├── services/
│   ├── scheduler.py
│   ├── call_service.py
│   ├── ai_agent.py
│   ├── stt_service.py
│   ├── tts_service.py
│   └── escalation_service.py
│
├── agents/
│   ├── followup_agent.py
│   ├── prompts.py
│   └── triage_logic.py
│
└── utils/
    ├── logger.py
    └── helpers.py
```

---

## 🗄️ Database Schema

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
summary
follow_up_date
status (pending/completed/escalated)
created_at
```

### Call Logs

```
id
consultation_id
transcript
ai_summary
urgency_level
call_status
created_at
```

---

## 🤖 AI Agent Design

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

## ⏱ Scheduling Strategy

Follow-ups are triggered using:

### MVP

Query database periodically:

```sql
SELECT * FROM consultations
WHERE follow_up_date <= NOW()
AND status = 'pending';
```

### Optional Advanced

Redis Sorted Set:

* score = follow-up timestamp
* auto-pop due patients

---

## 📞 Call Flow

1. Scheduler detects due follow-up
2. Backend triggers Twilio outbound call
3. Twilio connects to webhook
4. Audio streamed to Deepgram
5. AI processes conversation
6. Responses stored
7. Escalation triggered if necessary

---

## 🔐 Safety Considerations

* AI never provides medical diagnosis
* Always advises contacting doctor for emergencies
* Secure storage of patient data
* HTTPS required
* Minimal PHI storage for demo purposes

---

## 🧪 Local Setup

### 1. Clone Repo

```
git clone <repo-url>
cd ai-followup-agent
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
DEEPGRAM_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
LLM_API_KEY=
```

### 5. Run Server

```
uvicorn main:app --reload
```

---

## 🎯 MVP Features

* Doctor uploads consultation
* Automated follow-up scheduling
* AI phone calls
* Conversation transcription
* AI-generated summaries
* Doctor escalation alerts

---

## ⭐ Future Improvements

* Multilingual patient calls
* Emotion detection
* EHR integration
* RAG-based personalized conversations
* SMS fallback when calls fail
* Nurse dashboard
* HIPAA-compliant deployment

---

## 🏆 Hackathon Value Proposition

* Reduces unnecessary appointments
* Improves patient outcomes
* Saves doctor time
* Enables scalable healthcare follow-ups

---

## 📜 License

MIT License

---

## 👥 Contributors

Hackathon Team — AI Patient Follow-Up Agent
