import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Load variables from .env file
load_dotenv()

# Get Cloud DB URL
database_url = os.getenv("DATABASE_CLOUD_URL")

print("Loaded DATABASE_CLOUD_URL:", database_url)

if not database_url:
    raise ValueError("DATABASE_CLOUD_URL is not set in .env")

try:
    engine = create_engine(database_url)

    with engine.connect() as conn:
        print("Cloud SQL connected ✅")

except SQLAlchemyError as e:
    print("Database connection failed ❌")
    print(e)