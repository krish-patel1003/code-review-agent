from fastapi import APIRouter, HTTPException, Depends
from app.models.request_models import AnalyzePRRequest
from app.db.crud import save_analysis, get_analysis_by_id
from uuid import uuid4
from app.services import GithubService
from app.config import get_github_service
from app.services import CodeReviewAgent

router = APIRouter()

@router.post("/analyze-pr")
async def analyze_pr(payload: AnalyzePRRequest, github_service: GithubService = Depends(get_github_service)):

    try:
        pr_details = github_service.get_pr_details(
            str(payload.repo_url),
            payload.pr_number
        )

        print({
            "status": "success",
            "data": {
                "title": pr_details.title,
                "description": pr_details.description,
                "state": pr_details.state,
                "diff": pr_details.diff,
                "files": [
                    {
                        "filename": file.filename,
                        "status": file.status,
                        "additions": file.additions,
                        "deletions": file.deletions,
                        "changes": file.changes,
                        "content": file.content
                    }
                    for file in pr_details.files
                ],
                "total_files": len(pr_details.files)
            }
        })

        agent = CodeReviewAgent(repo_url=str(payload.repo_url), github_service=github_service)
        repo_context = agent.setup_repo_context()
        print(repo_context)
    
    except Exception as e:
        raise Exception(f"Error occured in post request fetching pr details url: {payload.repo_url}, pr_num: {payload.pr_number}")

    task_id = str(uuid4())

    # PR analysis 
    # analyze_pr()

    analysis_result = {
        "files": [
            {
                "name": "main.py",
                "issues": [
                    {
                        "type": "style",
                        "line": 15,
                        "description": "Line too long",
                        "suggestion": "Break line into multiple lines"
                    },
                    {
                        "type": "bug",
                        "line": 23,
                        "description": "Potential null pointer",
                        "suggestion": "Add null check"
                    }
                ]
            }
        ],
        "summary": {
            "total_files": 1,
            "total_issues": 2,
            "critical_issues": 1
        }
    }

    # Ṣave analysis to db
    # await save_analysis(task_id, str(payload.repo_url), analysis_result)

    return {'task_id': task_id}

@router.get("/result/{task_id}")
async def get_results(task_id: str):
    result = await get_analysis_by_id(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result