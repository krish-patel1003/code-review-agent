from fastapi import Depends
from typing import Optional
from app.config import get_settings
from app.services import GithubService 

def get_github_service(github_token: Optional[str] = None) -> GithubService:

    settings = get_settings()
    token = github_token or settings.GITHUB_TOKEN
    return GithubService(token)