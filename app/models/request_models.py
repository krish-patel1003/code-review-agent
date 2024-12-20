from pydantic import BaseModel, HttpUrl
from typing import Optional


class AnalyzePRRequest(BaseModel):
    repo_url: HttpUrl
    pr_number: int
    github_token: Optional[str] = None


