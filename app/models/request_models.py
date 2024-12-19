from pydantic import BaseModel, HttpUrl


class AnalyzePRRequest(BaseModel):
    repo_url: HttpUrl
    pr_number: int


