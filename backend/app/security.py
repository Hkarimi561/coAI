import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models import User

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], hashed.encode("utf-8"))
    except ValueError:
        return False


def create_token(user: User) -> str:
    s = get_settings()
    now = datetime.now(UTC)
    payload = {"sub": str(user.id), "iat": now, "exp": now + timedelta(hours=s.jwt_expire_hours)}
    return jwt.encode(payload, s.jwt_secret, algorithm=ALGORITHM)


def create_mcp_token(user_id: uuid.UUID | str) -> str:
    """Short-lived signed identity the backend sends to MCP servers that enforce per-user permissions."""
    now = datetime.now(UTC)
    return jwt.encode({"sub": str(user_id), "typ": "mcp", "iat": now, "exp": now + timedelta(seconds=120)}, get_settings().jwt_secret, algorithm=ALGORITHM)


def decode_mcp_token(token: str) -> uuid.UUID:
    payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
    if payload.get("typ") != "mcp":
        raise jwt.InvalidTokenError("not an MCP token")
    return uuid.UUID(payload["sub"])


def set_auth_cookie(response: Response, token: str) -> None:
    s = get_settings()
    response.set_cookie(
        s.cookie_name,
        token,
        max_age=s.jwt_expire_hours * 3600,
        httponly=True,
        secure=s.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(get_settings().cookie_name, path="/")


async def get_current_user(request: Request, session: AsyncSession = Depends(get_session)) -> User:
    s = get_settings()
    token = request.cookies.get(s.cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=[ALGORITHM])
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid session") from None
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user


def require_permission(key: str):  # noqa: ANN201
    """Dependency: the signed-in user must hold `key` through at least one of their roles."""

    async def dep(user: User = Depends(get_current_user)) -> User:
        if not user.has_permission(key):
            raise HTTPException(status_code=403, detail="You do not have permission to do this")
        return user

    return dep


def require_any_of(*keys: str):  # noqa: ANN201
    """Dependency: the user must hold at least one of `keys` (e.g. a role picker needed by both user and role admins)."""

    async def dep(user: User = Depends(get_current_user)) -> User:
        if not any(user.has_permission(k) for k in keys):
            raise HTTPException(status_code=403, detail="You do not have permission to do this")
        return user

    return dep


async def require_any_permission(user: User = Depends(get_current_user)) -> User:
    """Dependency for admin-area endpoints every staff member needs (dashboard counters)."""
    if not user.permissions:
        raise HTTPException(status_code=403, detail="You do not have permission to do this")
    return user
