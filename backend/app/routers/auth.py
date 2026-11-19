from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import (
    create_access_token,
    find_user_by_microsoft_identity,
    get_current_user,
    get_user_by_id,
    parse_microsoft_token_claims,
)
from app.config import settings
from app.db import get_db
from app.models import (
    AuthTokenResponse,
    DevLoginRequest,
    MicrosoftAuthRequest,
    UserOut,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication (Microsoft Entra ID)"])


@router.post("/microsoft", response_model=AuthTokenResponse)
def login_with_microsoft(payload: MicrosoftAuthRequest) -> AuthTokenResponse:
    """
    Přihlášení přes nemocniční Microsoft účet (Microsoft Entra ID / Azure AD).
    Ověří MSAL id_token / access_token nebo identitu účtu a spáruje s kolekcí `users`.
    """
    oid = payload.microsoft_oid
    email = payload.email

    raw_token = payload.id_token or payload.access_token
    if raw_token:
        claims = parse_microsoft_token_claims(raw_token)
        oid = oid or claims.get("oid") or claims.get("sub")
        email = (
            email
            or claims.get("preferred_username")
            or claims.get("email")
            or claims.get("upn")
        )

    if not oid and not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chybí Microsoft token nebo identifikátor nemocničního účtu.",
        )

    user = find_user_by_microsoft_identity(oid, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Nemocniční Microsoft účet ({email or oid}) nebyl nalezen v databázi "
                f"oddělení. Kontaktujte administrátora pro přiřazení role."
            ),
        )
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tento uživatelský účet je deaktivován.",
        )

    token = create_access_token(user)
    return AuthTokenResponse(
        access_token=token,
        auth_provider="microsoft_entra_id",
        user=user,
    )


@router.post("/dev-login", response_model=AuthTokenResponse)
def dev_microsoft_login(payload: DevLoginRequest) -> AuthTokenResponse:
    """
    Simulované přihlášení nemocničním Microsoft účtem pro vývojové a testovací prostředí.
    """
    if not settings.auth_dev_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vývojové přihlášení je v produkčním režimu vypnuté.",
        )
    user = get_user_by_id(payload.user_id)
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uživatel nebyl nalezen nebo není aktivní.",
        )
    token = create_access_token(user)
    return AuthTokenResponse(
        access_token=token,
        auth_provider="microsoft_entra_id_dev",
        user=user,
    )


@router.get("/dev-accounts", response_model=List[UserOut])
def list_dev_accounts() -> List[UserOut]:
    """Vrátí seznam nemocničních účtů pro rychlé přepínání rolí v Betě."""
    db = get_db()
    users: List[UserOut] = []
    for doc in db.collection("users").stream():
        data = doc.to_dict() or {}
        if data.get("active", True):
            users.append(UserOut(id=doc.id, **data))
    role_order = {"admin": 0, "head_nurse": 1, "nurse": 2}
    users.sort(key=lambda u: (role_order.get(u.role, 9), u.name))
    return users


@router.get("/me", response_model=UserOut)
def get_me(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    """Vrátí profil aktuálně přihlášeného uživatele."""
    return current_user
