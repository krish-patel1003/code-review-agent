from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database URL
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

# Create the engine
engine = create_engine(DATABASE_URL, echo=True)

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