"""Authentication dependencies: Supabase JWT verification (ES256 via JWKS)."""

import uuid

import jwt
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.engine import get_db
from src.db.models import User

security = HTTPBearer()

# Cache the JWKS client (fetches keys lazily and caches them)
_jwks_client = PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")


def _decode_token(token: str) -> dict:
    """Decode a Supabase JWT, supporting both ES256 (new) and HS256 (legacy)."""
    try:
        # Try JWKS (ES256) first
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except Exception:
        # Fallback to legacy HS256 secret
        if settings.supabase_jwt_secret:
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        raise


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> uuid.UUID:
    """Decode Supabase JWT and return the user UUID."""
    token = credentials.credentials
    try:
        payload = _decode_token(token)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing sub")
        return uuid.UUID(sub)
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}")


async def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Fetch the User row, creating it if it doesn't exist yet (first login sync)."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        user = User(id=user_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def get_optional_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> uuid.UUID | None:
    """Optionally extract user ID from JWT. Returns None for anonymous requests."""
    if not credentials:
        return None
    try:
        payload = _decode_token(credentials.credentials)
        sub = payload.get("sub")
        return uuid.UUID(sub) if sub else None
    except (jwt.PyJWTError, ValueError):
        return None
