from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

# Database URL
DATABASE_URL = get_settings().DATABASE_URL 

# Create the engine
engine = create_engine(str(DATABASE_URL), echo=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# Dependency to get the database session
def init_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()