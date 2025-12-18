"""Authentication and authorization helpers using JWT."""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt import InvalidTokenError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.logging_config import get_logger
from app.db.session import AsyncSessionLocal
from app.db.models import TeamMember

logger = get_logger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(user: TeamMember, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT for the given user."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_exp_minutes)
    )
    to_encode = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> TeamMember:
    """Validate JWT from Authorization header and fetch the user."""
    if credentials is None or not credentials.scheme.lower() == "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
    except InvalidTokenError as exc:
        logger.warning("Invalid JWT", extra={"extra_data": {"error": str(exc)}})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_id or not email or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async with AsyncSessionLocal() as session:
        user = await session.get(TeamMember, int(user_id))

    if not user or user.email != email or user.role != role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or role mismatch",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.user = user
    return user
