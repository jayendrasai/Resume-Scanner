import pytest
from unittest.mock import patch, MagicMock


# ── helpers ────────────────────────────────────────────────────────────────

async def get_premium_token(client) -> str:
    """Register a user and manually flip tier to premium for storage tests."""
    reg = await client.post("/auth/register", json={
        "email": "premium@test.com",
        "password": "pass1234"
    })
    token = reg.json()["access_token"]

    # Force tier to premium directly in test DB
    from sqlalchemy import update
    from auth.models import User
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as db:
        await db.execute(
            update(User)
            .where(User.email == "premium@test.com")
            .values(tier="premium")
        )
        await db.commit()

    # Refresh token so JWT carries updated tier
    refresh = await client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {token}"}
    )
    return refresh.json()["access_token"]


async def get_free_token(client) -> str:
    reg = await client.post("/auth/register", json={
        "email": "free@test.com",
        "password": "pass1234"
    })
    return reg.json()["access_token"]


# ── presign tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_presign_requires_premium(client):
    token = await get_free_token(client)
    res = await client.post(
        "/upload/presign",
        json={"filename": "interview.mp4"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_presign_unauthenticated(client):
    res = await client.post(
        "/upload/presign",
        json={"filename": "interview.mp4"}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_presign_invalid_extension(client):
    token = await get_premium_token(client)
    with patch("storage.s3.boto3.client"):
        res = await client.post(
            "/upload/presign",
            json={"filename": "malware.exe"},
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_presign_path_traversal_blocked(client):
    token = await get_premium_token(client)
    res = await client.post(
        "/upload/presign",
        json={"filename": "../../etc/passwd.mp4"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_presign_success(client):
    token = await get_premium_token(client)

    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = (
        "https://resume-scanner-videos-prod-758890598931-us-east-1-an"
        ".s3.amazonaws.com/videos/1/abc.mp4?X-Amz-Signature=fake"
    )

    with patch("storage.s3.boto3.client", return_value=mock_s3):
        res = await client.post(
            "/upload/presign",
            json={"filename": "interview.mp4"},
            headers={"Authorization": f"Bearer {token}"}
        )

    assert res.status_code == 200
    body = res.json()
    assert "upload_url" in body
    assert "object_key" in body
    assert body["object_key"].startswith("videos/")
    assert body["expires_in"] == 900
    assert body["max_bytes"] == 100 * 1024 * 1024


# ── confirm tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_confirm_wrong_user_key_blocked(client):
    """User 1 cannot submit user 2's object key."""
    token = await get_premium_token(client)

    # Register a second premium user
    await client.post("/auth/register", json={
        "email": "other@test.com", "password": "pass"
    })

    res = await client.post(
        "/upload/confirm",
        json={"object_key": "videos/999/somefile.mp4"},  # 999 != this user's id
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_confirm_invalid_key_format(client):
    token = await get_premium_token(client)
    res = await client.post(
        "/upload/confirm",
        json={"object_key": "../../etc/shadow"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_confirm_success(client):
    token = await get_premium_token(client)

    # Get this user's actual id from /auth/me
    me = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    user_id = me.json()["id"]

    # 1. Create a fake Celery task object
    mock_task = MagicMock()
    mock_task.id = "fake-task-uuid"

    # 2. Patch the Celery call so it doesn't try to connect to Redis
    with patch("storage.router.analyze_video.delay", return_value=mock_task):
        res = await client.post(
            "/upload/confirm",
            json={"object_key": f"videos/{user_id}/test.mp4"},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert res.status_code == 202
    assert res.json()["status"] == "queued"
    assert res.json()["task_id"] == "fake-task-uuid"  # Proves the mock worked