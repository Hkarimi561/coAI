from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models import User
from app.redis_client import rate_limit
from app.schemas import LoginIn, UserOut
from app.security import clear_auth_cookie, create_token, get_current_user, hash_password, set_auth_cookie, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# Pre-computed bcrypt hash so unknown e-mails cost the same as wrong passwords (no user enumeration by timing).
_DUMMY_HASH = hash_password("not-a-real-password")


@router.post("/login", response_model=UserOut)
async def login(body: LoginIn, request: Request, response: Response, session: AsyncSession = Depends(get_session)) -> User:
    ip = request.client.host if request.client else "unknown"
    email = body.email.strip().lower()
    await rate_limit(f"login:{ip}:{email}", get_settings().login_rate_limit_per_5min, 300)
    user = (await session.execute(select(User).where(func.lower(User.email) == email))).scalar_one_or_none()
    ok = verify_password(body.password, user.password_hash if user else _DUMMY_HASH)
    if not user or not ok or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    set_auth_cookie(response, create_token(user))
    return user


@router.post("/logout", status_code=204)
async def logout(response: Response) -> None:
    clear_auth_cookie(response)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> User:
    return user
