import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Example connection string for MySQL (change based on your local DB setup)
Connection = os.getenv("DATABASE_URL")
if not Connection:
    raise ValueError("CRITICAL: DATABASE_URL is not set in the environment variables.")

# Initialize the SQLAlchemy engine
engine = create_engine(Connection, echo=False)

# Create a thread-safe Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency provider for FastAPI routes to yield database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()