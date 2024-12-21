from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from app.tasks import full_review_workflow_task
from app.config import get_cache_client
from app.db import get_analysis_by_id
from datetime import timedelta
from app.models import AnalyzePRRequest


router = APIRouter()

@router.post("/analyze-pr")
def analyze_pr(payload: AnalyzePRRequest):
    try:
        task = full_review_workflow_task.apply_async(
            args=[str(payload.repo_url), payload.pr_number]
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

    cache_client = get_cache_client()

    cached_result = cache_client.get(task_id)
    if cached_result:
        return {"task_id": task_id, "result": eval(cached_result)}

    # If not found in cache, fetch from database
    print("task_id in get_results:\t", task_id)
    analysis_result = get_analysis_by_id(task_id)
    if analysis_result:
        cache_client.setex(task_id, timedelta(minutes=5), str(analysis_result.result))
        return {"task_id": task_id, "result": analysis_result.result}
    else:
        raise HTTPException(status_code=404, detail="Task result not found")