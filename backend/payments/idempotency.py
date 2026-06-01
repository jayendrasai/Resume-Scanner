import json
import redis.asyncio as aioredis
import os
from enum import Enum
from typing import Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
IDEMPOTENCY_TTL = 3600       # 1 hour — client key window
WEBHOOK_LOCK_TTL = 30        # 30 seconds — webhook execution lock


class IdempotencyStatus(str, Enum):
    PROCESSING = "PROCESSING"
    COMPLETED  = "COMPLETED"


def get_redis() -> aioredis.Redis:
    return aioredis.from_url(REDIS_URL, decode_responses=True)


# ── Client-to-backend idempotency ──────────────────────────────────────────

async def check_idempotency_key(
    key: str
) -> tuple[IdempotencyStatus | None, dict | None]:
    """
    Returns (status, cached_response) or (None, None) if key doesn't exist.
    """
    r = get_redis()
    try:
        raw = await r.get(f"idempotency:{key}")
        if raw is None:
            return None, None
        data = json.loads(raw)
        return IdempotencyStatus(data["status"]), data.get("response")
    finally:
        await r.aclose()


async def set_idempotency_processing(key: str) -> bool:
    """
    Atomically sets PROCESSING state only if key doesn't exist.
    Returns True if this request owns the key (first attempt).
    Returns False if key already exists (concurrent duplicate).
    Uses SET NX (set if not exists) — atomic, no race condition.
    """
    r = get_redis()
    try:
        result = await r.set(
            f"idempotency:{key}",
            json.dumps({"status": IdempotencyStatus.PROCESSING}),
            ex=IDEMPOTENCY_TTL,
            nx=True       # only set if NOT exists — atomic
        )
        return result is True
    finally:
        await r.aclose()


async def set_idempotency_completed(key: str, response: dict) -> None:
    """
    Upgrades key from PROCESSING → COMPLETED with cached response.
    TTL resets to full window from now.
    """
    r = get_redis()
    try:
        await r.set(
            f"idempotency:{key}",
            json.dumps({
                "status": IdempotencyStatus.COMPLETED,
                "response": response
            }),
            ex=IDEMPOTENCY_TTL
        )
    finally:
        await r.aclose()


async def clear_idempotency_key(key: str) -> None:
    """
    Deletes key on failure — allows client to retry with same key.
    If we leave a PROCESSING key on failure, client is locked out for 1hr.
    """
    r = get_redis()
    try:
        await r.delete(f"idempotency:{key}")
    finally:
        await r.aclose()


# ── Webhook execution lock ─────────────────────────────────────────────────

async def acquire_webhook_lock(event_id: str) -> bool:
    """
    Acquires a short-lived Redis lock on the Razorpay event ID.
    Returns True if this worker owns the lock (safe to proceed).
    Returns False if another worker is already processing this event.

    Uses SET NX EX — atomic Redis primitive.
    TTL of 30s covers the worst-case DB write latency.
    Lock expires automatically even if the worker crashes.
    """
    r = get_redis()
    try:
        result = await r.set(
            f"webhook_lock:{event_id}",
            "locked",
            ex=WEBHOOK_LOCK_TTL,
            nx=True
        )
        return result is True
    finally:
        await r.aclose()


async def release_webhook_lock(event_id: str) -> None:
    """
    Explicitly releases lock after successful processing.
    Allows Razorpay to retry the same event if needed after a clean failure
    (as opposed to a crash, where TTL expiry handles release).
    """
    r = get_redis()
    try:
        await r.delete(f"webhook_lock:{event_id}")
    finally:
        await r.aclose()


async def is_webhook_already_processed(event_id: str) -> bool:
    """
    Permanent record of processed events — survives beyond lock TTL.
    Key pattern: webhook_done:{event_id}
    TTL: 48 hours — covers Razorpay's maximum retry window.
    """
    r = get_redis()
    try:
        exists = await r.exists(f"webhook_done:{event_id}")
        return bool(exists)
    finally:
        await r.aclose()


async def mark_webhook_processed(event_id: str) -> None:
    """Marks event as permanently processed — 48hr TTL."""
    r = get_redis()
    try:
        await r.set(
            f"webhook_done:{event_id}",
            "1",
            ex=172800   # 48 hours
        )
    finally:
        await r.aclose()