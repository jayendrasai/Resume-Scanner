from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from auth.models import User
from auth.utils import SECRET_KEY, ALGORITHM

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id: int = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


async def require_premium(user: User = Depends(get_current_user)) -> User:
    """
    Correct order matters:
    1. Check expiry first — expired premium users still have tier='premium' in DB
    2. Then check tier — catches free users who never subscribed
    """
    now = datetime.now(timezone.utc)

    # Step 1: premium user whose subscription lapsed
    if user.tier == "premium" and user.premium_expires_at:
        if user.premium_expires_at.replace(tzinfo=timezone.utc) < now:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Premium subscription expired. Please renew to continue.",
                headers={"X-Upgrade-Required": "true"}
            )

    # Step 2: free user who never subscribed
    if user.tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required.",
            headers={"X-Upgrade-Required": "true"}
        )

    return user