from fastapi import APIRouter, HTTPException
from app.models.request_models import AnalyzePRRequest
from app.db.crud import save_analysis, get_analysis_by_id
from uuid import uuid4

router = APIRouter()

@router.post("/analyze-pr")
async def analyze_pr(payload: AnalyzePRRequest):

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
    await save_analysis(task_id, str(payload.repo_url), analysis_result)

    return {'task_id': task_id}

@router.get("/result/{task_id}")
async def get_results(task_id: str):
    result = await get_analysis_by_id(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result