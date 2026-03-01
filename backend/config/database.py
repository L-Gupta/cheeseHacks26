import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.config.settings import settings

# Use SQLite for local testing when DATABASE_URL is not set
database_url = settings.DATABASE_URL.strip()
if not database_url:
    # SQLite file next to the backend folder when running from project root
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    database_url = f"sqlite:///{os.path.join(_base, 'cheese.db')}"

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
