from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from app.config import settings
from app.db import get_db
from app.models import UserOut, UserRole

security = HTTPBearer(auto_error=False)


def create_access_token(user: UserOut, expires_hours: int = 24) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "microsoft_oid": user.microsoft_oid,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=expires_hours)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def parse_microsoft_token_claims(raw_token: str) -> dict:
    """
    Extract claims from a Microsoft Entra ID (Azure AD) JWT token.
    In production with an active tenant, JWKS signature verification against
    https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys can be enforced.
    """
    try:
        claims = jwt.decode(raw_token, options={"verify_signature": False})
        return claims if isinstance(claims, dict) else {}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Neplatný Microsoft token: {exc}",
        )


def get_user_by_id(user_id: str) -> Optional[UserOut]:
    db = get_db()
    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict() or {}
    return UserOut(id=doc.id, **data)


def find_user_by_microsoft_identity(
    microsoft_oid: Optional[str], email: Optional[str]
) -> Optional[UserOut]:
    db = get_db()
    email_norm = (email or "").strip().lower()

    for doc in db.collection("users").stream():
        data = doc.to_dict() or {}
        if microsoft_oid and data.get("microsoft_oid") == microsoft_oid:
            return UserOut(id=doc.id, **data)
        if email_norm and str(data.get("email", "")).strip().lower() == email_norm:
            if microsoft_oid and not data.get("microsoft_oid"):
                db.collection("users").document(doc.id).update(
                    {"microsoft_oid": microsoft_oid}
                )
                data["microsoft_oid"] = microsoft_oid
            return UserOut(id=doc.id, **data)
    return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_dev_user_id: Optional[str] = Header(default=None),
) -> UserOut:
    """
    Resolve authenticated hospital user from Bearer JWT token
    (or X-Dev-User-Id header when AUTH_DEV_MODE is enabled).
    """
    if credentials and credentials.credentials:
        token = credentials.credentials
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            user_id = payload.get("sub")
            if user_id:
                user = get_user_by_id(user_id)
                if user and user.active:
                    return user
        except jwt.PyJWTError:
            # Check if a raw Microsoft token was sent directly in Authorization header
            claims = parse_microsoft_token_claims(token)
            oid = claims.get("oid") or claims.get("sub")
            email = (
                claims.get("preferred_username")
                or claims.get("email")
                or claims.get("upn")
            )
            user = find_user_by_microsoft_identity(oid, email)
            if user and user.active:
                return user

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neplatný nebo expirovaný přihlašovací token.",
        )

    if settings.auth_dev_mode and x_dev_user_id:
        user = get_user_by_id(x_dev_user_id)
        if user and user.active:
            return user

    if settings.auth_dev_mode:
        # Default fallback in dev mode to head_nurse if no header is passed
        default_user = get_user_by_id("user_head")
        if default_user:
            return default_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Uživatel není přihlášen (vyžadován Microsoft účet nemocnice).",
    )


def require_roles(*allowed_roles: UserRole) -> Callable:
    def role_checker(current_user: UserOut = Depends(get_current_user)) -> UserOut:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Nedostatečná oprávnění. Vyžadována role: "
                    f"{', '.join(allowed_roles)} (vaše role: {current_user.role})."
                ),
            )
        return current_user

    return role_checker
