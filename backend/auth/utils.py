import os
import uuid
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY  = os.getenv("JWT_SECRET", "change-this-in-production")
ALGORITHM   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: int, email: str, tier: str) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "tier": tier,
        "exp": expires,
        "iat": now,
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)