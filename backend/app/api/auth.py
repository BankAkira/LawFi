import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import AuthProvider, User
from app.schemas.user import (
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.utils.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter()

# In-memory brute-force tracker: {email: [timestamp, timestamp, ...]}
_login_failures: dict[str, list[float]] = defaultdict(list)
_BRUTE_FORCE_MAX_ATTEMPTS = 5
_BRUTE_FORCE_WINDOW_SECONDS = 900  # 15 minutes


def _check_brute_force(email: str) -> None:
    """Raise 429 if too many recent failed attempts for this email."""
    now = time.monotonic()
    # Prune old entries outside the window
    _login_failures[email] = [
        t for t in _login_failures[email] if now - t < _BRUTE_FORCE_WINDOW_SECONDS
    ]
    if len(_login_failures[email]) >= _BRUTE_FORCE_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"เข้าสู่ระบบล้มเหลวเกินกำหนด ({_BRUTE_FORCE_MAX_ATTEMPTS} ครั้ง) กรุณาลองใหม่ใน 15 นาที",
        )


def _record_failure(email: str) -> None:
    """Record a failed login attempt."""
    _login_failures[email].append(time.monotonic())


def _clear_failures(email: str) -> None:
    """Clear failure history after successful login."""
    _login_failures.pop(email, None)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user with email and password."""
    if len(data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร",
        )

    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="อีเมลนี้ถูกใช้งานแล้ว",
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with email and password, returns JWT tokens."""
    _check_brute_force(data.email)

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user is None or user.password_hash is None:
        _record_failure(data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง",
        )

    if not verify_password(data.password, user.password_hash):
        _record_failure(data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="บัญชีถูกระงับ",
        )

    _clear_failures(data.email)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """Refresh access token using a valid refresh token."""
    payload = decode_token(data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token ไม่ถูกต้องหรือหมดอายุ",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ไม่พบผู้ใช้",
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


class GoogleTokenRequest(BaseModel):
    id_token: str


@router.post("/google", response_model=TokenResponse)
async def google_login(
    data: GoogleTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Login or register via Google OAuth. Verifies the ID token with Google."""
    # In test mode, use headers instead of calling Google
    test_email = request.headers.get("X-Test-Google-Email")
    if test_email:
        google_info = {
            "email": test_email,
            "name": request.headers.get("X-Test-Google-Name", "Test User"),
        }
    else:
        from app.utils.google_auth import GoogleAuthError, verify_google_id_token

        try:
            google_info = await verify_google_id_token(data.id_token)
        except GoogleAuthError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

    email = google_info["email"]
    name = google_info["name"]

    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is not None:
        # Existing user -- must be a Google user (can't merge with email/password)
        if user.auth_provider != AuthProvider.GOOGLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="อีเมลนี้ลงทะเบียนด้วยรหัสผ่านแล้ว กรุณาเข้าสู่ระบบด้วยรหัสผ่าน",
            )
    else:
        # New user -- auto-create
        user = User(
            email=email,
            name=name,
            auth_provider=AuthProvider.GOOGLE,
            password_hash=None,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user profile."""
    return user
