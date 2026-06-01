# import os
# import json
# from datetime import datetime, timezone, timedelta
# from fastapi import APIRouter, Depends, HTTPException, Request, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select

# from database import get_db
# from auth.dependencies import get_current_user
# from auth.models import User
# from payments.razorpay_client import verify_webhook_signature, create_order
# from payments.schemas import CreateOrderResponse, PassStatusResponse
# from logger import log

# router = APIRouter(tags=["payments"])

# PREMIUM_DURATION_DAYS = int(os.getenv("PREMIUM_DURATION_DAYS", "30"))
# PASS_PRICE_INR_PAISE = int(os.getenv("PASS_PRICE_INR_PAISE", "200"))

def mask_email(email: str) -> str:
    """turns 'sai@test.com' into 's**@test.com'"""
    parts = email.split('@')
    if len(parts) != 2:
        return '***'
    return f"{parts[0][0]}**@{parts[1]}"

# # ── 1. Create Order (Authenticated) ──────────────────────────────────────────
# @router.post("/billing/create-order", response_model=CreateOrderResponse)
# async def create_pass_order(
#     user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Generates an Order ID for the frontend to open Razorpay Checkout."""
    
#     # Optional: Prevent buying if they already have plenty of time left
#     if user.tier == "premium" and user.premium_expires_at:
#         if user.premium_expires_at > datetime.now(timezone.utc) + timedelta(days=7):
#             log.error(f"User {mask_email(user.email)} already has an active pass with more than 7 days remaining.")
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="You already have an active pass with more than 7 days remaining."
#             )

#     try:
#         # Create order in Razorpay
#         order = create_order(
#             amount_paise=PASS_PRICE_INR_PAISE,
#             receipt_id=f"receipt_user_{user.id}"
#         )
#     except Exception as e:
#         log.error(f"Could not create order: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail=f"Could not create order: {str(e)}"
#         )

#     # Store order_id so the webhook knows who paid
#     user.razorpay_order_id = order["id"]
#     db.add(user)
#     await db.commit()
#     log.info(f"Order created for user {mask_email(user.email)}: {order['id']}")

#     return CreateOrderResponse(
#         order_id=order["id"],
#         amount_inr=order["amount"]
#     )

# # ── 2. Pass Status (Authenticated) ───────────────────────────────────────────
# @router.get("/billing/status", response_model=PassStatusResponse)
# async def pass_status(user: User = Depends(get_current_user)):

#     """Frontend polls this to check if tier upgraded."""
#     log.info(f"Pass status for user {mask_email(user.email)}: tier={user.tier}, expires_at={user.premium_expires_at}")
#     return PassStatusResponse(
#         tier=user.tier,
#         premium_expires_at=(
#             user.premium_expires_at.isoformat() if user.premium_expires_at else None
#         )
#     )

# # ── 3. Webhook (Unauthenticated, from Razorpay) ──────────────────────────────
# @router.post("/webhooks/razorpay", status_code=200)
# async def razorpay_webhook(
#     request: Request,
#     db: AsyncSession = Depends(get_db)
# ):
#     body = await request.body()
#     signature = request.headers.get("X-Razorpay-Signature", "")
#     # print("body: ",body)
#     # print("signature: ",signature)
#     if not verify_webhook_signature(body, signature):
#         log.error("Invalid webhook signature")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid webhook signature"
#         )

#     try:
#         event = json.loads(body)
#     except json.JSONDecodeError:
#         log.error("Invalid JSON")
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

#     event_type = event.get("event")
#     log.info(f"Webhook event type: {event_type}")
#     # We only care about successful payments
#     if event_type != "order.paid":
#         log.info(f"Webhook event type: {event_type}")
#         return {"status": "ignored"}

#     payload = event.get("payload", {})
#     order = payload.get("order", {}).get("entity", {})
#     order_id = order.get("id")

#     if not order_id:
#         log.error("No order id found")
#         return {"status": "ignored"}

#     # Find the user who initiated this order
#     result = await db.execute(select(User).where(User.razorpay_order_id == order_id))
#     user = result.scalar_one_or_none()

#     if not user:
#         log.error("No user found for order_id: {order_id}")
#         return {"status": "user_not_found"}

#     # Grant 30 days from NOW (or stack it if they bought early)
#     now = datetime.now(timezone.utc)
#     base_date = max(user.premium_expires_at or now, now)
    
#     user.tier = "premium"
#     user.premium_expires_at = base_date + timedelta(days=PREMIUM_DURATION_DAYS)
    
#     # Clear the order ID so it can't be somehow re-used (though webhook idempotency handles this too)
#     user.razorpay_order_id = None 

#     log.info(f"30-Day Pass activated for user {mask_email(user.email)} Expires: {user.premium_expires_at}")

#     db.add(user)
#     await db.commit()

#     return {"status": "ok"}



import os
import json
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from database import get_db
from auth.dependencies import get_current_user
from auth.models import User
from payments.razorpay_client import (
    verify_webhook_signature,
    create_order,
)
from payments.schemas import (
    CreateOrderResponse,
    PassStatusResponse,
)
from payments.idempotency import (
    IdempotencyStatus,
    check_idempotency_key,
    set_idempotency_processing,
    set_idempotency_completed,
    clear_idempotency_key,
    acquire_webhook_lock,
    release_webhook_lock,
    is_webhook_already_processed,
    mark_webhook_processed,
)
from logger import log


router = APIRouter(tags=["payments"])

PREMIUM_DURATION_DAYS = int(os.getenv("PREMIUM_DURATION_DAYS", "30"))
PASS_PRICE_INR_PAISE = int(os.getenv("PASS_PRICE_INR_PAISE", "200"))



# ── /billing/create-order ──────────────────────────────────────────────────

@router.post("/billing/create-order", response_model=CreateOrderResponse)
async def create_order_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: Optional[str] = Header(None)
):
    """
    Idempotency flow:
    1. No key provided → proceed normally (no idempotency guarantee)
    2. Key exists + COMPLETED → return cached response immediately
    3. Key exists + PROCESSING → 409 (concurrent duplicate)
    4. Key doesn't exist → set PROCESSING, execute, set COMPLETED
    """

    # ── Step 1: Check idempotency key ─────────────────────────────────
    if x_idempotency_key:
        cached_status, cached_response = await check_idempotency_key(
            x_idempotency_key
        )

        if cached_status == IdempotencyStatus.COMPLETED and cached_response:
            log.info("idempotency_cache_hit",
                     key=x_idempotency_key, user_id=user.id)
            return CreateOrderResponse(**cached_response)

        if cached_status == IdempotencyStatus.PROCESSING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A request with this idempotency key is already being processed. "
                       "Please wait and retry."
            )

        # First attempt — atomically claim the key
        owned = await set_idempotency_processing(x_idempotency_key)
        if not owned:
            # Lost the race between check and set — another worker claimed it
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Concurrent request detected. Please retry in a moment."
            )

    # ── Step 2: Execute business logic ────────────────────────────────
    try:
        order = create_order(
            amount_paise=PASS_PRICE_INR_PAISE,
            receipt_id=f"receipt_user_{user.id}"
        )
    except Exception as e:
        # Clear key on failure — client can retry with same key
        if x_idempotency_key:
            await clear_idempotency_key(x_idempotency_key)
        log.error("razorpay_order_creation_failed",
                  error=str(e), user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not create payment order. Please try again."
        )

    # ── Step 3: Persist order_id on user ──────────────────────────────
    user.razorpay_order_id = order["id"]
    db.add(user)
    await db.commit()

    response = CreateOrderResponse(
        order_id=order["id"],
        amount_inr_paise=order.get("amount", 49900),
        currency=order.get("currency", "INR"),
        key_id=os.getenv("RAZORPAY_KEY_ID", ""),
    )

    # ── Step 4: Mark completed — cache response ────────────────────────
    if x_idempotency_key:
        await set_idempotency_completed(
            x_idempotency_key,
            response.model_dump()
        )
        log.info("idempotency_key_completed",
                 key=x_idempotency_key, user_id=user.id)

    return response


# ── /billing/status ────────────────────────────────────────────────────────

@router.get("/billing/status", response_model=PassStatusResponse)
async def subscription_status(user: User = Depends(get_current_user)):
    return PassStatusResponse(
        tier=user.tier,
        premium_expires_at=(
            user.premium_expires_at.isoformat()
            if user.premium_expires_at else None
        ),
        razorpay_order_id=user.razorpay_order_id,
    )


# ── /webhooks/razorpay ─────────────────────────────────────────────────────

@router.post("/webhooks/razorpay", status_code=200)
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # ── Step 1: Read raw body ──────────────────────────────────────────
    body = await request.body()

    # ── Step 2: Verify signature ───────────────────────────────────────
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not verify_webhook_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )

    # ── Step 3: Extract event ID from Razorpay header ─────────────────
    event_id = request.headers.get("X-Razorpay-Event-Id", "")

    # ── Step 4: Check permanent processed record ───────────────────────
    if event_id and await is_webhook_already_processed(event_id):
        log.info("webhook_already_processed", event_id=event_id)
        return {"status": "already_processed"}

    # ── Step 5: Acquire execution lock ────────────────────────────────
    # ── Step 5: Acquire execution lock ────────────────────────────────
    if event_id:
        lock_acquired = await acquire_webhook_lock(event_id)
        if not lock_acquired:
            log.info("webhook_lock_contention", event_id=event_id)
            # FORCE RAZORPAY TO RETRY LATER
            # If the current lock-holder succeeds, the retry will hit Step 4 and return 200 safely.
            # If the current lock-holder crashes, the retry will acquire the lock and succeed.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Processing by another worker, please retry"
            )

    # ── Step 6: Parse event ────────────────────────────────────────────
    try:
        event = json.loads(body)
        log.info("webhook_event_parsed", payload=event)
    except json.JSONDecodeError:
        if event_id:
            await release_webhook_lock(event_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    event_type   = event.get("event")
    log.info("webhook_event_type", event_type=event_type)
    payload      = event.get("payload", {})
    order_entity = payload.get("order", {}).get("entity", {})
    order_id     = order_entity.get("id")

    log.info("webhook_received", event_type=event_type,
             order_id=order_id, event_id=event_id)
    if not order_id:
        if event_id:
            await release_webhook_lock(event_id)
        return {"status": "ignored"}

    # ── Step 7: Handle order.paid ──────────────────────────────────────
    if event_type == "order.paid":
        # Find user by order_id — nullified after first process
        result = await db.execute(
            select(User).where(User.razorpay_order_id == order_id)
        )
        log.info("webhook_order_paid",
                 order_id=order_id, event_id=event_id, result=result)
        user = result.scalar_one_or_none()

        if not user:
            # Order already processed (order_id was nullified) OR unknown
            log.info("webhook_order_not_found",
                     order_id=order_id, event_id=event_id)
            if event_id:
                await release_webhook_lock(event_id)
            return {"status": "order_not_found"}

        # Grant premium — extend if already premium
        base = max(
            user.premium_expires_at or datetime.now(timezone.utc),
            datetime.now(timezone.utc)
        )
        user.premium_expires_at = base + timedelta(days=PREMIUM_DURATION_DAYS)
        user.tier = "premium"
        user.razorpay_order_id = None   # nullify — state-driven idempotency

        db.add(user)
        await db.commit()

        log.info("webhook_premium_granted",
                 user_id=user.id,
                 email=mask_email(user.email),
                 expires_at=user.premium_expires_at.isoformat())

    else:
        log.info("webhook_unhandled_event", event_type=event_type)
        if event_id:
            await release_webhook_lock(event_id)
        return {"status": "unhandled"}

    # ── Step 8: Mark processed + release lock ─────────────────────────
    if event_id:
        await mark_webhook_processed(event_id)
        await release_webhook_lock(event_id)

    return {"status": "ok"}