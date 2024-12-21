from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from app.tasks import full_review_workflow_task
from app.config import get_code_review_agent, get_github_service


router = APIRouter()

@router.post("/analyze-pr")
def analyze_pr(repo_url: str, pr_number: int):
    try:
        task = full_review_workflow_task.apply_async(
            args=[repo_url, pr_number]
        )
        return {"task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting review workflow: {e}")

@router.get("/status/{task_id}")
def get_status(task_id: str):
    task_result = AsyncResult(task_id)
    return {"task_id": task_id, "status": task_result.status}

@router.get("/results/{task_id}")
def get_results(task_id: str):
    task_result = AsyncResult(task_id)
    if task_result.status == "SUCCESS":
        return {"task_id": task_id, "result": task_result.result}
    elif task_result.status == "PENDING":
        raise HTTPException(status_code=202, detail="Task is still in progress")
    elif task_result.status == "FAILURE":
        raise HTTPException(status_code=500, detail=str(task_result.result))
    else:
        raise HTTPException(status_code=500, detail="Unexpected task status")
