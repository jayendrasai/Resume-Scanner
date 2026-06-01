import pytest
import json
import hmac
import hashlib
import os
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy import update
from auth.models import User
from tests.conftest import TestSessionLocal

os.environ.setdefault("RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")


async def make_free_user(client, email="idm@test.com") -> tuple[str, int]:
    reg = await client.post("/v1/auth/register", json={
        "email": email, "password": "pass1234"
    })
    token = reg.json()["access_token"]
    me = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    return token, me.json()["id"]


def make_signed_webhook(
    order_id: str,
    event_id: str = "evt_test_001"
) -> tuple[bytes, dict]:
    payload = {
        "event": "order.paid",
        "payload": {
            "order": {"entity": {"id": order_id, "amount": 200}},
            "payment": {"entity": {"id": "pay_test", "status": "captured"}}
        }
    }
    body = json.dumps(payload).encode()
    secret = os.environ["RAZORPAY_WEBHOOK_SECRET"]
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": sig,
        "X-Razorpay-Event-Id": event_id,
    }
    return body, headers


# ── Idempotency key — create-order ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_first_request_succeeds(client):
    token, _ = await make_free_user(client, "idm1@test.com")
    mock_order = {"id": "order_idm1", "amount": 200, "currency": "INR"}

    with patch("payments.router.create_order", return_value=mock_order), \
         patch("payments.idempotency.get_redis") as mock_redis_factory:

        mock_r = AsyncMock()
        mock_r.get.return_value = None       # key doesn't exist
        mock_r.set.return_value = True       # NX set succeeded
        mock_redis_factory.return_value = mock_r

        res = await client.post(
            "/v1/billing/create-order",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Idempotency-Key": "test-key-001"
            }
        )
    assert res.status_code == 200
    assert res.json()["order_id"] == "order_idm1"


@pytest.mark.asyncio
async def test_completed_key_returns_cached_response(client):
    token, _ = await make_free_user(client, "idm2@test.com")
    cached = {
        "order_id": "order_cached",
        "amount_inr_paise": 200,
        "currency": "INR",
        "key_id": "rzp_test"
    }

    with patch("payments.idempotency.get_redis") as mock_redis_factory:
        mock_r = AsyncMock()
        mock_r.get.return_value = json.dumps({
            "status": "COMPLETED",
            "response": cached
        })
        mock_redis_factory.return_value = mock_r

        res = await client.post(
            "/v1/billing/create-order",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Idempotency-Key": "test-key-002"
            }
        )
    assert res.status_code == 200
    # Cached response returned — Razorpay never called
    assert res.json()["order_id"] == "order_cached"


@pytest.mark.asyncio
async def test_processing_key_returns_409(client):
    token, _ = await make_free_user(client, "idm3@test.com")

    with patch("payments.idempotency.get_redis") as mock_redis_factory:
        mock_r = AsyncMock()
        mock_r.get.return_value = json.dumps({"status": "PROCESSING"})
        mock_redis_factory.return_value = mock_r

        res = await client.post(
            "/v1/billing/create-order",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Idempotency-Key": "test-key-003"
            }
        )
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_key_cleared_on_razorpay_failure(client):
    token, _ = await make_free_user(client, "idm4@test.com")

    with patch("payments.router.create_order",
               side_effect=Exception("Razorpay down")), \
         patch("payments.idempotency.get_redis") as mock_redis_factory:

        mock_r = AsyncMock()
        mock_r.get.return_value = None
        mock_r.set.return_value = True
        mock_redis_factory.return_value = mock_r

        res = await client.post(
            "/v1/billing/create-order",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Idempotency-Key": "test-key-004"
            }
        )
    assert res.status_code == 503
    # Verify delete was called — key cleared for retry
    mock_r.delete.assert_called_once()


# ── Webhook idempotency ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_first_delivery_succeeds(client):
    _, user_id = await make_free_user(client, "wh1@test.com")

    async with TestSessionLocal() as db:
        await db.execute(
            update(User)
            .where(User.email == "wh1@test.com")
            .values(razorpay_order_id="order_wh1")
        )
        await db.commit()

    body, headers = make_signed_webhook("order_wh1", "evt_001")

    with patch("payments.idempotency.get_redis") as mock_redis_factory:
        mock_r = AsyncMock()
        mock_r.exists.return_value = 0      # not processed yet
        mock_r.set.return_value = True      # lock acquired
        mock_redis_factory.return_value = mock_r

        res = await client.post(
            "/v1/webhooks/razorpay",
            content=body, headers=headers
        )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    async with TestSessionLocal() as db:
        from sqlalchemy import select
        r = await db.execute(
            select(User).where(User.email == "wh1@test.com")
        )
        user = r.scalar_one()
        assert user.tier == "premium"
        assert user.razorpay_order_id is None

    # Verify user is premium
    async with TestSessionLocal() as db:
        from sqlalchemy import select
        r = await db.execute(
            select(User).where(User.email == "wh1@test.com")
        )
        user = r.scalar_one()
        assert user.tier == "premium"
        assert user.razorpay_order_id is None  # nullified


@pytest.mark.asyncio
async def test_webhook_duplicate_delivery_blocked(client):
    """Same event_id fired twice — second must be blocked."""
    _, _ = await make_free_user(client, "wh2@test.com")
    body, headers = make_signed_webhook("order_wh2", "evt_002")

    with patch("payments.idempotency.get_redis") as mock_redis_factory:
        mock_r = AsyncMock()
        # Simulate: event already in webhook_done
        mock_r.exists.return_value = 1
        mock_redis_factory.return_value = mock_r

        res = await client.post(
            "/v1/webhooks/razorpay",
            content=body, headers=headers
        )
    assert res.status_code == 200
    assert res.json()["status"] == "already_processed"


@pytest.mark.asyncio
async def test_webhook_concurrent_lock_contention(client):
    """
    Two workers receive same event simultaneously.
    Second must return 409 — forces Razorpay to retry.
    NOT 200 — that would prevent retry if first worker crashes.
    """
    _, _ = await make_free_user(client, "wh3@test.com")
    body, headers = make_signed_webhook("order_wh3", "evt_003")

    with patch("payments.idempotency.get_redis") as mock_redis_factory:
        mock_r = AsyncMock()
        mock_r.exists.return_value = 0     # not in done set
        mock_r.set.return_value = None     # NX failed — lock taken
        mock_redis_factory.return_value = mock_r

        res = await client.post(
            "/v1/webhooks/razorpay",
            content=body, headers=headers
        )

    # 409 — not 200 — Razorpay will retry
    assert res.status_code == 409

@pytest.mark.asyncio
async def test_webhook_no_event_id_still_works(client):
    """
    Razorpay may not always send X-Razorpay-Event-Id in test mode.
    Webhook must still process using state-driven idempotency (null order_id).
    """
    _, _ = await make_free_user(client, "wh4@test.com")

    async with TestSessionLocal() as db:
        await db.execute(
            update(User)
            .where(User.email == "wh4@test.com")
            .values(razorpay_order_id="order_wh4")
        )
        await db.commit()

    payload = {
        "event": "order.paid",
        "payload": {
            "order": {"entity": {"id": "order_wh4"}},
            "payment": {"entity": {"id": "pay_wh4", "status": "captured"}}
        }
    }
    body = json.dumps(payload).encode()
    secret = os.environ["RAZORPAY_WEBHOOK_SECRET"]
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    # No X-Razorpay-Event-Id header
    res = await client.post(
        "/v1/webhooks/razorpay",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig
            # deliberately no X-Razorpay-Event-Id
        }
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"