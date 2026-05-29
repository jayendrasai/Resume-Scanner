import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    res = await client.post("/v1/auth/register", json={
        "email": "user@test.com",
        "password": "securepass"
    })
    assert res.status_code == 201
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dupe@test.com", "password": "pass123"}
    await client.post("/v1/auth/register", json=payload)
    res = await client.post("/v1/auth/register", json=payload)
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/v1/auth/register", json={
        "email": "login@test.com", "password": "mypassword"
    })
    res = await client.post("/v1/auth/login", json={
        "email": "login@test.com", "password": "mypassword"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/v1/auth/register", json={
        "email": "wrong@test.com", "password": "correct"
    })
    res = await client.post("/v1/auth/login", json={
        "email": "wrong@test.com", "password": "incorrect"
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client):
    reg = await client.post("/v1/auth/register", json={
        "email": "me@test.com", "password": "pass123"
    })
    token = reg.json()["access_token"]
    res = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["tier"] == "free"


@pytest.mark.asyncio
async def test_me_no_token(client):
    res = await client.get("/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_free_user_blocked_from_premium_route(client):
    """
    No premium route exists yet — this test is a contract test.
    Wire it to a real route on Day 7 when video endpoints are added.
    Validates require_premium raises 403 for free users.
    """
    from auth.dependencies import require_premium
    from fastapi import FastAPI
    from httpx import AsyncClient, ASGITransport

    test_app = FastAPI()

    @test_app.get("/v1/test-premium")
    async def premium_route(user=pytest.importorskip and __import__(
        'fastapi', fromlist=['Depends']
    ).Depends(require_premium)):
        return {"ok": True}

    # Register + get token
    reg = await client.post("/v1/auth/register", json={
        "email": "free@test.com", "password": "pass"
    })
    token = reg.json()["access_token"]

    # Hit a manually wired premium endpoint
    from main import app as main_app
    from auth.dependencies import require_premium as rp
    from fastapi import Depends

    @main_app.get("/v1/test-premium-gate")
    async def _gate(u=Depends(rp)):
        return {"ok": True}

    res = await client.get(
        "/v1/test-premium-gate",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403
    # assert res.json()["headers"]["X-Upgrade-Required"] == "true" or \
    #        "Premium" in res.json()["detail"]
    assert res.headers.get("X-Upgrade-Required") == "true"
    assert "Premium" in res.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token(client):
    reg = await client.post("/v1/auth/register", json={
        "email": "refresh@test.com", "password": "pass123"
    })
    token = reg.json()["access_token"]
    res = await client.post(
        "/v1/auth/refresh",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    new_token = res.json()["access_token"]
    assert new_token != token  # new token issued