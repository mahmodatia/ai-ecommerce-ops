from fastapi import APIRouter, HTTPException

from app.core.config import get_settings

router = APIRouter()


@router.get("/{task_id}")
def job_status(task_id: str):
    settings = get_settings()

    if settings.tasks_mode != "celery":
        raise HTTPException(
            status_code=400,
            detail="Background jobs are disabled. Set TASKS_MODE=celery.",
        )

    from celery.result import AsyncResult
    from app.tasks.celery_app import celery

    result = AsyncResult(task_id, app=celery)

    response = {
        "task_id": task_id,
        "state": result.state,
        "ready": result.ready(),
    }

    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.result)

    return response
