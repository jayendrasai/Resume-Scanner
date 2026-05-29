import pytest
import json
import hmac
import hashlib
import os
from unittest.mock import patch
from sqlalchemy import update, select
from auth.models import User
from tests.conftest import TestSessionLocal

# ── Environment Setup ──────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def setup_razorpay_env(monkeypatch):
    """Forcefully locks test env vars for every test in this file, overriding .env"""
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_key")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "rzp_test_secret")

# ── Helpers ────────────────────────────────────────────────────────────────
async def make_premium_user(client, email="pay@test.com") -> tuple[str, int]:
    reg = await client.post("/auth/register", json={
        "email": email, "password": "pass1234"
    })
    token = reg.json()["access_token"]
    
    async with TestSessionLocal() as db:
        await db.execute(
            update(User).where(User.email == email).values(tier="premium")
        )
        await db.commit()
        
    refresh = await client.post(
        "/auth/refresh", headers={"Authorization": f"Bearer {token}"}
    )
    token = refresh.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()["id"]

async def make_free_user(client, email="free_pay@test.com") -> tuple[str, int]:
    reg = await client.post("/auth/register", json={
        "email": email, "password": "pass1234"
    })
    token = reg.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()["id"]

def make_webhook_payload(event_type: str, order_id: str) -> tuple[bytes, str]:
    """Returns (body_bytes, valid_signature) for Orders"""
    payload = {
        "event": event_type,
        "payload": {
            "order": {
                "entity": {"id": order_id}
            }
        }
    }
    body = json.dumps(payload).encode("utf-8")
    secret = os.environ["RAZORPAY_WEBHOOK_SECRET"]
    sig = hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    return body, sig

# ── Signature verification ─────────────────────────────────────────────────
def test_valid_signature():
    from payments.razorpay_client import verify_webhook_signature
    body = b'{"event": "test"}'
    # Pulling from the monkeypatched environment
    secret = os.environ["RAZORPAY_WEBHOOK_SECRET"]
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(body, sig) is True

def test_invalid_signature():
    from payments.razorpay_client import verify_webhook_signature
    body = b'{"event": "test"}'
    assert verify_webhook_signature(body, "bad_signature") is False

def test_tampered_body_fails():
    from payments.razorpay_client import verify_webhook_signature
    body = b'{"event": "test"}'
    secret = os.environ["RAZORPAY_WEBHOOK_SECRET"]
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    tampered = b'{"event": "tampered"}'
    assert verify_webhook_signature(tampered, sig) is False

# ── Create order endpoint ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_create_order_free_user(client):
    token, _ = await make_free_user(client, "create_order@test.com")
    
    mock_order = {
        "id": "order_test123",
        "amount": 200,
        "currency": "INR",
    }
    
    with patch("payments.router.create_order", return_value=mock_order):
        res = await client.post(
            "/billing/create-order",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        assert res.json()["order_id"] == "order_test123"
        assert res.json()["amount_inr"] == 200

# ── Webhook events ─────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_webhook_invalid_signature(client):
    res = await client.post(
        "/webhooks/razorpay",
        content=b'{"event": "order.paid"}',
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "badsig"
        }
    )
    assert res.status_code == 400

@pytest.mark.asyncio
async def test_webhook_order_paid(client):
    _, user_id = await make_free_user(client, "webhook_paid@test.com")

    # Pre-set order_id on user
    async with TestSessionLocal() as db:
        await db.execute(
            update(User)
            .where(User.email == "webhook_paid@test.com")
            .values(razorpay_order_id="order_paid_test")
        )
        await db.commit()

    body, sig = make_webhook_payload("order.paid", "order_paid_test")
    
    res = await client.post(
        "/webhooks/razorpay",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig
        }
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    async with TestSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == "webhook_paid@test.com")
        )
        user = result.scalar_one()
        assert user.tier == "premium"
        assert user.premium_expires_at is not None
        assert user.razorpay_order_id is None  # Should be cleared

@pytest.mark.asyncio
async def test_webhook_unknown_order_id(client):
    body, sig = make_webhook_payload("order.paid", "order_does_not_exist")
    
    res = await client.post(
        "/webhooks/razorpay",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig
        }
    )
    # 200 not 400 — we don't want Razorpay to retry forever
    assert res.status_code == 200
    assert res.json()["status"] == "user_not_found"

# ── Billing status ─────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_billing_status(client):
    token, _ = await make_free_user(client, "status_check@test.com")
    
    res = await client.get(
        "/billing/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["tier"] == "free"
    assert res.json()["premium_expires_at"] is None