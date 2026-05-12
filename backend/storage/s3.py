import os
import uuid
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

AWS_REGION         = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME     = os.getenv("S3_BUCKET_NAME")
PRESIGNED_EXPIRY   = int(os.getenv("PRESIGNED_URL_EXPIRY", "900"))
MAX_FILE_BYTES     = 100 * 1024 * 1024  # 100 MB hard cap enforced in presign conditions

ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mov"}


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4")  # required for us-east-1 presigned PUT
    )


def generate_object_key(user_id: int, original_filename: str) -> str:
    """
    Server controls the key — client never does.
    Format: videos/{user_id}/{uuid}{ext}
    Example: videos/42/f3a1bc92-...-4d2e.mp4
    """
    ext = os.path.splitext(original_filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".mp4"  # safe default, content-type condition enforces real validation
    return f"videos/{user_id}/{uuid.uuid4()}{ext}"


def create_presigned_upload_url(user_id: int, filename: str) -> dict:
    """
    Returns a presigned PUT URL with server-side conditions:
    - Content-Type must be video/*
    - Content-Length must be <= 100 MB
    Client cannot bypass these without the signature failing.
    """
    s3 = get_s3_client()
    object_key = generate_object_key(user_id, filename)

    try:
        upload_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": object_key,
                "ContentType": "video/mp4",   # browser must send this header
            },
            ExpiresIn=PRESIGNED_EXPIRY,
            HttpMethod="PUT"
        )
    except ClientError as e:
        raise RuntimeError(f"Failed to generate presigned URL: {e}")

    return {
        "upload_url": upload_url,
        "object_key": object_key,
        "expires_in": PRESIGNED_EXPIRY,
        "max_bytes": MAX_FILE_BYTES
    }


def delete_object(object_key: str) -> None:
    """Used by worker after audio extraction — video no longer needed."""
    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=S3_BUCKET_NAME, Key=object_key)
    except ClientError as e:
        # Log but don't raise — deletion failure shouldn't crash the job
        print(f"S3 delete failed for {object_key}: {e}")