import re
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from auth.dependencies import require_premium
from auth.models import User
from storage.s3 import create_presigned_upload_url, ALLOWED_EXTENSIONS

router = APIRouter(prefix="/upload", tags=["storage"])

SAFE_FILENAME_RE = re.compile(r'^[\w\-. ]+$')  # no path traversal chars


class PresignRequest(BaseModel):
    filename: str

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Filename cannot be empty")

        # Block path traversal attempts
        if "/" in v or "\\" in v or ".." in v:
            raise ValueError("Invalid filename")

        if not SAFE_FILENAME_RE.match(v):
            raise ValueError("Filename contains invalid characters")

        import os
        ext = os.path.splitext(v)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        return v


class PresignResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_in: int
    max_bytes: int


class JobCreateRequest(BaseModel):
    object_key: str

    @field_validator("object_key")
    @classmethod
    def validate_object_key(cls, v: str) -> str:
        # Must match the pattern our server generates — nothing else accepted
        if not v.startswith("videos/"):
            raise ValueError("Invalid object key")
        if ".." in v or "//" in v:
            raise ValueError("Invalid object key")
        return v


@router.post("/presign", response_model=PresignResponse)
async def get_presigned_url(
    payload: PresignRequest,
    user: User = Depends(require_premium)
):
    """
    Premium users only.
    Returns a presigned S3 PUT URL valid for 15 minutes.
    The browser PUTs directly to S3 — FastAPI server never touches video bytes.
    """
    try:
        result = create_presigned_upload_url(user.id, payload.filename)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    return PresignResponse(**result)


@router.post("/confirm", status_code=202)
async def confirm_upload(
    payload: JobCreateRequest,
    user: User = Depends(require_premium)
):
    """
    Called by frontend after S3 PUT succeeds.
    Day 4 will enqueue the Celery task here.
    For now: validates the key belongs to this user and returns task placeholder.
    """
    # Ownership check — key must belong to this user
    expected_prefix = f"videos/{user.id}/"
    if not payload.object_key.startswith(expected_prefix):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Object key does not belong to your account"
        )

    # Day 4 will replace this stub with: task = analyze_video.delay(object_key)
    return {
        "task_id": "pending-celery-day4",
        "object_key": payload.object_key,
        "status": "queued"
    }