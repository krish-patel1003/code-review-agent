from typing import Optional
from celery import Celery
from app.config import get_settings
from app.services import GithubService 
from app.services import CodeReviewAgent
from redis import Redis
from redis import ConnectionError


def _require_setting(value: Optional[str], setting_name: str) -> str:
    if value and value.strip():
        return value
    raise RuntimeError(f"Missing required setting: {setting_name}")


def get_github_service(github_token: Optional[str] = None) -> GithubService:

    settings = get_settings()
    token = _require_setting(github_token or settings.GITHUB_TOKEN, "GITHUB_TOKEN")
    return GithubService(token)


def get_code_review_agent(api_key: Optional[str] = None) -> CodeReviewAgent:

    settings = get_settings()
    gemini_key = _require_setting(api_key or settings.GEMINI_API_KEY, "GEMINI_API_KEY")
    github_service = get_github_service()
    return CodeReviewAgent(
        github_service=github_service,
        api_key=gemini_key,
        chat_model=settings.GEMINI_CHAT_MODEL,
        embedding_model=settings.GEMINI_EMBEDDING_MODEL,
    )


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
    except ConnectionError as exc:
        raise RuntimeError("Redis connection error") from exc

    raise RuntimeError("Redis ping failed")
