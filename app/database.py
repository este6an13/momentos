from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

import os

STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local").lower()
DB_FILE = "photos.db" if STORAGE_BACKEND == "gcp" else "photos-local.db"
DATABASE_URL = f"sqlite:///./{DB_FILE}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
