from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import Settings, get_settings
from .errors import ApiError


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    claims: dict[str, Any]


def _decode_jwt(token: str, settings: Settings) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise ApiError(401, "invalid_token", "Invalid authentication token.") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    if credentials is None:
        raise ApiError(401, "missing_token", "Authentication is required.")

    claims = _decode_jwt(credentials.credentials, settings)
    user_id = claims.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise ApiError(401, "invalid_token", "Authentication token is missing a subject.")

    return AuthenticatedUser(user_id=user_id, claims=claims)


def require_admin(
    current_user: AuthenticatedUser = Depends(get_current_user),
    admin_secret: str | None = Header(default=None, alias="X-Admin-Secret"),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    if admin_secret != settings.admin_secret:
        raise ApiError(403, "admin_forbidden", "Admin access is required.")
    return current_user
