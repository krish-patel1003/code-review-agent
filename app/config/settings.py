from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field, PostgresDsn
from enum import Enum

class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # Environment
    APP_ENV: EnvironmentType = Field(
        default=EnvironmentType.DEVELOPMENT,
        description="Environment the application is running in"
    )
    APP_SECRET_KEY: str = Field(
        default="",
        description="App secret key"
    )
    DEBUG: bool = Field(default=False, description="Debug mode flag")

    # Application
    PROJECT_NAME: str = Field(default="Code Review Agent", description="Project name")
    VERSION: str = Field(default="1.0.0", description="API version")
    API_PREFIX: str = Field(default="/api/v1", description="API prefix")

    # GitHub Configuration
    GITHUB_TOKEN: Optional[str] = Field(
        default=None,
        description="GitHub Personal Access Token"
    )

    # Database Configuration
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+psycopg2://postgres:postgres@db:5432/code_review",
        description="PostgreSQL database URL"
    )

    GEMINI_API_KEY: Optional[str] = Field(
        default=None,
        description="Gemine api key"
    )

    GEMINI_CHAT_MODEL: str = Field(
        default="gemini-3.1-pro-preview",
        description="Gemini chat model name"
    )

    GEMINI_EMBEDDING_MODEL: str = Field(
        default="models/gemini-embedding-001",
        description="Gemini embedding model name"
    )

    CELERY_BROKER_URL: str = Field(
        default="redis://redis:6379/0",
        description="Celery broker url"
    )

    CELERY_RESULT_BACKEND: str = Field(
        default="redis://redis:6379/0",
        description="CELERY RESULT BACKEND"
    ) 

    REDIS_CLIENT_URL: str = Field(
        default="redis://redis:6379/0",
        description="Redis client url"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True

def get_settings() -> Settings:
    """
    Create cached instance of settings.
    Use this function to get settings throughout the application.
    """
    return Settings()
