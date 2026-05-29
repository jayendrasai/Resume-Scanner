import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import update
from auth.models import User
from tests.conftest import TestSessionLocal


async def get_premium_token(client, email="jobpremium@test.com") -> tuple[str, int]:
    reg = await client.post("/v1/auth/register", json={
        "email": email, "password": "pass1234"
    })
    token = reg.json()["access_token"]

    async with TestSessionLocal() as db:
        await db.execute(
            update(User)
            .where(User.email == email)
            .values(tier="premium")
        )
        await db.commit()

    refresh = await client.post(
        "/v1/auth/refresh",
        headers={"Authorization": f"Bearer {token}"}
    )
    token = refresh.json()["access_token"]

    me = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()["id"]


@pytest.mark.asyncio
async def test_create_job_success(client):
    token, user_id = await get_premium_token(client)

    mock_task = MagicMock()
    mock_task.id = "test-task-uuid-1234"

    with patch("jobs_router.analyze_video.delay", return_value=mock_task):
        res = await client.post(
            "/v1/jobs/create",
            json={"object_key": f"videos/{user_id}/test.mp4"},
            headers={"Authorization": f"Bearer {token}"}
        )

    assert res.status_code == 202
    assert res.json()["task_id"] == "test-task-uuid-1234"
    assert res.json()["status"] == "queued"


@pytest.mark.asyncio
async def test_create_job_wrong_owner(client):
    token, user_id = await get_premium_token(client, "owner@test.com")

    res = await client.post(
        "/v1/jobs/create",
        json={"object_key": "videos/999/test.mp4"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_create_job_free_user_blocked(client):
    reg = await client.post("/v1/auth/register", json={
        "email": "freejob@test.com", "password": "pass"
    })
    token = reg.json()["access_token"]

    res = await client.post(
        "/v1/jobs/create",
        json={"object_key": "videos/1/test.mp4"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_job_status_pending(client):
    token, _ = await get_premium_token(client, "statuspremium@test.com")

    mock_result = MagicMock()
    mock_result.state = "PENDING"
    mock_result.result = None

    with patch("jobs_router.AsyncResult", return_value=mock_result):
        res = await client.get(
            "/v1/jobs/fake-task-id/status",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert res.status_code == 200
    assert res.json()["status"] == "pending"
    assert res.json()["result"] is None


@pytest.mark.asyncio
async def test_job_status_success(client):
    token, _ = await get_premium_token(client, "successpremium@test.com")

    mock_result = MagicMock()
    mock_result.state = "SUCCESS"
    mock_result.result = {
        "transcript": "stub",
        "analysis": {"filler_words": {}, "pace_wpm": 0,
                     "clarity_score": 0, "tips": []}
    }

    with patch("jobs_router.AsyncResult", return_value=mock_result):
        res = await client.get(
            "/v1/jobs/fake-task-id/status",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert res.status_code == 200
    assert res.json()["status"] == "completed"
    assert "transcript" in res.json()["result"]


@pytest.mark.asyncio
async def test_job_status_failure(client):
    token, _ = await get_premium_token(client, "failpremium@test.com")

    mock_result = MagicMock()
    mock_result.state = "FAILURE"
    mock_result.result = Exception("Worker crashed")

    with patch("jobs_router.AsyncResult", return_value=mock_result):
        res = await client.get(
            "/v1/jobs/fake-task-id/status",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert res.status_code == 200
    assert res.json()["status"] == "failed"
    assert "error" in res.json()["result"]