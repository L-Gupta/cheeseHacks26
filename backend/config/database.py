from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

from config.settings import settings

database_url = settings.DATABASE_URL
if database_url.startswith("sqlite:///./"):
    # Resolve relative sqlite paths against the repository root.
    relative_db_path = database_url.replace("sqlite:///./", "", 1)
    root_dir = Path(__file__).resolve().parents[2]
    database_url = f"sqlite:///{(root_dir / relative_db_path).resolve().as_posix()}"

engine_kwargs = {}
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(database_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
