from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from config.settings import settings
from config.database import engine, Base
from routes import followups, twilio_webhook, patient_routes, upload
from services import scheduler

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend for AI Patient Follow-up Agent hosted on Google Cloud Run"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect Routes
app.include_router(followups.router)
app.include_router(patient_routes.router)
app.include_router(twilio_webhook.router)
app.include_router(scheduler.router)
app.include_router(upload.router)

FAVICON_PATH = Path(__file__).resolve().parents[1] / "frontend" / "src" / "app" / "favicon.ico"


@app.get("/")
def read_root():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    if FAVICON_PATH.exists():
        return FileResponse(FAVICON_PATH)
    return Response(status_code=204)

if __name__ == "__main__":
    import uvicorn
    # Cloud Run expects the app to bind to 0.0.0.0:8080 usually via PORT env var
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=settings.DEBUG)
