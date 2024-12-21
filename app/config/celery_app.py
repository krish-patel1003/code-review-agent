from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "pr_analysis",  # Name of your Celery application
    broker=settings.CELERY_BROKER_URL,  # Use broker URL from settings
    backend=settings.CELERY_RESULT_BACKEND  # Use result backend URL from settings
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
