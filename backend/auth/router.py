from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from auth.models import User
from auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserOut
from auth.utils import hash_password, verify_password, create_access_token ,SECRET_KEY, ALGORITHM
from auth.dependencies import get_current_user , bearer_scheme, HTTPAuthorizationCredentials
from jose import jwt, JWTError



router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check duplicate email
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        tier="free"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.email, user.tier)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token(user.id, user.email, user.tier)
    return TokenResponse(access_token=token)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts a still-valid (or recently expired) token.
    Issues a fresh token with updated tier from DB.
    This matters when tier changes (free → premium) — old token
    has stale tier claim, refresh gives the frontend the correct one.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    try:
        # decode without verifying expiry so recently-expired tokens can refresh
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False}
        )
        user_id: int = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Always pull tier from DB — not from old token claim
    token = create_access_token(user.id, user.email, user.tier)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user

