from celery.result import AsyncResult

def get_task_status(task_id: str) -> dict:
    task_result = AsyncResult(task_id)
    return {"task_id": task_id, "status": task_result.status}

def get_task_result(task_id: str) -> dict:
    task_result = AsyncResult(task_id)
    if task_result.status == "SUCCESS":
        return task_result.result
    else:
        return {"status": task_result.status, "error": str(task_result.result) if task_result.status == "FAILURE" else None}
