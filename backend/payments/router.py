import os
import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from auth.dependencies import get_current_user
from auth.models import User
from payments.razorpay_client import verify_webhook_signature, create_order
from payments.schemas import CreateOrderResponse, PassStatusResponse
from logger import log

router = APIRouter(tags=["payments"])

PREMIUM_DURATION_DAYS = int(os.getenv("PREMIUM_DURATION_DAYS", "30"))
PASS_PRICE_INR_PAISE = int(os.getenv("PASS_PRICE_INR_PAISE", "200"))

def mask_email(email: str) -> str:
    """turns 'sai@test.com' into 's**@test.com'"""
    parts = email.split('@')
    if len(parts) != 2:
        return '***'
    return f"{parts[0][0]}**@{parts[1]}"

# ── 1. Create Order (Authenticated) ──────────────────────────────────────────
@router.post("/billing/create-order", response_model=CreateOrderResponse)
async def create_pass_order(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates an Order ID for the frontend to open Razorpay Checkout."""
    
    # Optional: Prevent buying if they already have plenty of time left
    if user.tier == "premium" and user.premium_expires_at:
        if user.premium_expires_at > datetime.now(timezone.utc) + timedelta(days=7):
            log.error(f"User {mask_email(user.email)} already has an active pass with more than 7 days remaining.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have an active pass with more than 7 days remaining."
            )

    try:
        # Create order in Razorpay
        order = create_order(
            amount_paise=PASS_PRICE_INR_PAISE,
            receipt_id=f"receipt_user_{user.id}"
        )
    except Exception as e:
        log.error(f"Could not create order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not create order: {str(e)}"
        )

    # Store order_id so the webhook knows who paid
    user.razorpay_order_id = order["id"]
    db.add(user)
    await db.commit()
    log.info(f"Order created for user {mask_email(user.email)}: {order['id']}")

    return CreateOrderResponse(
        order_id=order["id"],
        amount_inr=order["amount"]
    )

# ── 2. Pass Status (Authenticated) ───────────────────────────────────────────
@router.get("/billing/status", response_model=PassStatusResponse)
async def pass_status(user: User = Depends(get_current_user)):

    """Frontend polls this to check if tier upgraded."""
    log.info(f"Pass status for user {mask_email(user.email)}: tier={user.tier}, expires_at={user.premium_expires_at}")
    return PassStatusResponse(
        tier=user.tier,
        premium_expires_at=(
            user.premium_expires_at.isoformat() if user.premium_expires_at else None
        )
    )

# ── 3. Webhook (Unauthenticated, from Razorpay) ──────────────────────────────
@router.post("/webhooks/razorpay", status_code=200)
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    # print("body: ",body)
    # print("signature: ",signature)
    if not verify_webhook_signature(body, signature):
        log.error("Invalid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        log.error("Invalid JSON")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    event_type = event.get("event")
    log.info(f"Webhook event type: {event_type}")
    # We only care about successful payments
    if event_type != "order.paid":
        log.info(f"Webhook event type: {event_type}")
        return {"status": "ignored"}

    payload = event.get("payload", {})
    order = payload.get("order", {}).get("entity", {})
    order_id = order.get("id")

    if not order_id:
        log.error("No order id found")
        return {"status": "ignored"}

    # Find the user who initiated this order
    result = await db.execute(select(User).where(User.razorpay_order_id == order_id))
    user = result.scalar_one_or_none()

    if not user:
        log.error("No user found for order_id: {order_id}")
        return {"status": "user_not_found"}

    # Grant 30 days from NOW (or stack it if they bought early)
    now = datetime.now(timezone.utc)
    base_date = max(user.premium_expires_at or now, now)
    
    user.tier = "premium"
    user.premium_expires_at = base_date + timedelta(days=PREMIUM_DURATION_DAYS)
    
    # Clear the order ID so it can't be somehow re-used (though webhook idempotency handles this too)
    user.razorpay_order_id = None 

    log.info(f"30-Day Pass activated for user {mask_email(user.email)} Expires: {user.premium_expires_at}")

    db.add(user)
    await db.commit()

    return {"status": "ok"}