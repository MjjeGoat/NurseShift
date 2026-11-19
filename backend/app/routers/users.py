from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user, require_roles
from app.db import get_db
from app.models import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("", response_model=List[UserOut])
def list_users(
    active_only: bool = False,
    current_user: UserOut = Depends(get_current_user),
) -> List[UserOut]:
    """Vrátí seznam všech uživatelů oddělení."""
    db = get_db()
    result: List[UserOut] = []
    for doc in db.collection("users").stream():
        data = doc.to_dict() or {}
        if active_only and not data.get("active", True):
            continue
        result.append(UserOut(id=doc.id, **data))
    role_order = {"admin": 0, "head_nurse": 1, "nurse": 2}
    result.sort(key=lambda u: (role_order.get(u.role, 9), u.name))
    return result


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: UserOut = Depends(require_roles("admin")),
) -> UserOut:
    """Vytvoří nového uživatele a spáruje jej s nemocničním Microsoft účtem (pouze Admin)."""
    db = get_db()
    user_id = payload.id or f"user_{uuid.uuid4().hex[:8]}"
    doc_ref = db.collection("users").document(user_id)
    if doc_ref.get().exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Uživatel s ID '{user_id}' již existuje.",
        )

    data = payload.model_dump(exclude={"id"})
    doc_ref.set(data)
    return UserOut(id=user_id, **data)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdate,
    current_user: UserOut = Depends(require_roles("admin")),
) -> UserOut:
    """Upraví údaje uživatele, roli nebo úvazek (pouze Admin)."""
    db = get_db()
    doc_ref = db.collection("users").document(user_id)
    snap = doc_ref.get()
    if not snap.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Uživatel '{user_id}' nebyl nalezen.",
        )

    existing = snap.to_dict() or {}
    updates = payload.model_dump(exclude_unset=True)
    existing.update(updates)
    doc_ref.set(existing)
    return UserOut(id=user_id, **existing)


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    current_user: UserOut = Depends(require_roles("admin")),
) -> dict:
    """Odstraní uživatele z databáze (pouze Admin)."""
    db = get_db()
    doc_ref = db.collection("users").document(user_id)
    if not doc_ref.get().exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Uživatel '{user_id}' nebyl nalezen.",
        )
    doc_ref.delete()
    return {"status": "deleted", "user_id": user_id}
