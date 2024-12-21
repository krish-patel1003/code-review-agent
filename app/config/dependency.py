from typing import Optional
from celery import Celery
from app.config import get_settings
from app.services import GithubService 
from app.services import CodeReviewAgent
from redis import Redis
import sys
from redis import ConnectionError


def get_github_service(github_token: Optional[str] = None) -> GithubService:

    settings = get_settings()
    token = github_token or settings.GITHUB_TOKEN
    return GithubService(token)


def get_code_review_agent(api_key: Optional[str] = None) -> CodeReviewAgent:

    settings = get_settings()
    gemini_key = settings.GEMINI_API_KEY
    github_service = get_github_service()
    return CodeReviewAgent(github_service=github_service, api_key=gemini_key)


def get_celery_app() -> Celery:

    settings = get_settings()
    celery_app = Celery(
        "pr_analysis",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND
    )

    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True
    )

    return celery_app

def get_cache_client() -> Redis:

    settings = get_settings()
    redis_client_url = settings.REDIS_CLIENT_URL
    try:
        cache_client = Redis.from_url(redis_client_url)
        ping = cache_client.ping()
        if ping is True:
            return cache_client
    except ConnectionError:
        print("Redis Connection Error!")
        sys.exit(1)

    
    return cache_client

