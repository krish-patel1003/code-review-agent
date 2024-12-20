from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from pydantic import validator, Field, PostgresDsn, RedisDsn
import os
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
        default=...,
        description="App secret key"
    )
    DEBUG: bool = Field(default=False, description="Debug mode flag")

    # Application
    PROJECT_NAME: str = Field(default="Code Review Agent", description="Project name")
    VERSION: str = Field(default="1.0.0", description="API version")
    API_PREFIX: str = Field(default="/api/v1", description="API prefix")

    # GitHub Configuration
    GITHUB_TOKEN: str = Field(
        default=...,  # This makes it required
        description="GitHub Personal Access Token"
    )

    # Database Configuration
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@db:5432/code_review",
        description="PostgreSQL database URL"
    )

    GEMINI_API_KEY: str = Field(
        default=...,
        description="Gemine api key"
    )

    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        if os.getenv("DATABASE_URL"):
            return os.getenv("DATABASE_URL")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

# @lru_cache()
def get_settings() -> Settings:
    """
    Create cached instance of settings.
    Use this function to get settings throughout the application.
    """
    return Settings()