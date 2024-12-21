from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from app.config import get_settings

settings = get_settings()

DATABASE_URL = settings.DATABASE_URL

# Create synchronous engine
engine = create_engine(str(DATABASE_URL), echo=True)

# Create synchronous sessionmaker
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base class for models
Base = declarative_base()

def init_db():
    with engine.begin() as conn:
        Base.metadata.create_all(bind=engine)
