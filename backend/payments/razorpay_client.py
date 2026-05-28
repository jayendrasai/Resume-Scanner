import os
import hmac
import hashlib
import razorpay

# RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
# RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
# RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

def get_razorpay_client() -> razorpay.Client:
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    return razorpay.Client(auth=(key_id, key_secret))

def verify_webhook_signature(body: bytes, signature: str) -> bool:
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    if not webhook_secret:
        return False
    try:
        expected = hmac.new(
            webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False

def create_order(amount_paise: int, receipt_id: str) -> dict:
    """Creates a one-time payment order."""
    client = get_razorpay_client()
    return client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt_id,
    })