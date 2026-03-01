# Upload & Parse Test

Minimal frontends to test **consultation upload**, **PDF parsing**, and **Mic → Gemini** (no call).

1. **Create patient** – name, phone, doctor ID → creates a patient and shows their ID.
2. **Upload PDF** – patient ID, follow-up date, PDF file → uploads to backend, parses text, stores in DB; response shows `summary_text`, `pdf_url`, `id`, `status`.

3. **Mic → Gemini** (`mic-test.html`) – use the mic (browser speech recognition) or type a message → sent to Gemini via `POST /test/chat` → see and optionally speak the reply. No Twilio, no call.

## How to start the backend

“Start the backend” means run the FastAPI server so the upload and patient APIs are available.

1. Open a terminal and go to the **cheese** folder (project root, where `.env` and `backend/` are):
   ```bash
   cd path/to/cheese
   ```
2. Create a virtual environment and install dependencies (first time only):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```
3. Run the server:
   ```bash
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Or: `cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000` (then the app looks for `.env` in `cheese/`, so run from `cheese` if you use the first form).

The API will be at **http://localhost:8000**. Health check: http://localhost:8000/

**Database:** Your `.env` has `DATABASE_URL=` (empty). The app is set up so that when it’s empty it uses a **SQLite** file (`cheese/cheese.db`) for local testing, so you don’t need PostgreSQL to run it. To use PostgreSQL later, set `DATABASE_URL` in `.env` to your connection string.

## Run the test frontend

- With the backend running on `http://localhost:8000`, from this folder:
  ```bash
  npm start
  ```
- Open **http://localhost:3001** in the browser.

You can change the API base URL in the page if your backend runs elsewhere.
