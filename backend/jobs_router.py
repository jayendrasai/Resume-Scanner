from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from celery.result import AsyncResult

from auth.dependencies import require_premium
from auth.models import User
from tasks.celery_app import celery, analyze_video

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobCreateRequest(BaseModel):
    object_key: str

    @field_validator("object_key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        if not v.startswith("videos/"):
            raise ValueError("Invalid object key")
        if ".." in v or "//" in v:
            raise ValueError("Invalid object key")
        return v


class JobCreateResponse(BaseModel):
    task_id: str
    status: str


class JobStatusResponse(BaseModel):
    task_id: str
    status: str          # PENDING | STARTED | SUCCESS | FAILURE
    result: dict | None  # None until SUCCESS


@router.post("/create", response_model=JobCreateResponse, status_code=202)
async def create_job(
    payload: JobCreateRequest,
    user: User = Depends(require_premium)
):
    """
    Ownership check: object_key must belong to this user.
    Enqueues Celery task and returns task_id immediately — never blocks.
    """
    expected_prefix = f"videos/{user.id}/"
    if not payload.object_key.startswith(expected_prefix):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Object key does not belong to your account"
        )

    task = analyze_video.delay(
        object_key=payload.object_key,
        user_id=user.id
    )

    return JobCreateResponse(task_id=task.id, status="queued")


@router.get("/{task_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    task_id: str,
    user: User = Depends(require_premium)
):
    """
    Polls Celery AsyncResult.
    Frontend polls this every 3s until status = SUCCESS or FAILURE.
    """
    result = AsyncResult(task_id, app=celery)

    # Map Celery states to clean API states
    state_map = {
        "PENDING": "pending",
        "STARTED": "processing",
        "SUCCESS": "completed",
        "FAILURE": "failed",
        "RETRY":   "retrying",
        "REVOKED": "cancelled",
    }

    api_status = state_map.get(result.state, "unknown")

    response_result = None
    if result.state == "SUCCESS":
        response_result = result.result
    elif result.state == "FAILURE":
        response_result = {"error": str(result.result)}

    return JobStatusResponse(
        task_id=task_id,
        status=api_status,
        result=response_result
    )