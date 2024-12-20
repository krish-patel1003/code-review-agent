from fastapi import Depends
from typing import Optional
from app.config import get_settings
from app.services import GithubService 
from app.services import CodeReviewAgent

def get_github_service(github_token: Optional[str] = None) -> GithubService:

    settings = get_settings()
    token = github_token or settings.GITHUB_TOKEN
    return GithubService(token)


def get_code_review_agent(api_key: Optional[str] = None) -> CodeReviewAgent:

    settings = get_settings()
    gemini_key = settings.GEMINI_API_KEY
    github_service = get_github_service()
    return CodeReviewAgent(github_service=github_service, api_key=gemini_key)
