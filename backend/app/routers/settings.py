from fastapi import APIRouter, Depends

from app.auth import get_current_user, require_roles
from app.db import get_db
from app.models import DepartmentConfig, UserOut
from app.seed import SEED_DEPARTMENT_CONFIG

router = APIRouter(prefix="/api/settings", tags=["Department Settings"])


def load_department_config() -> DepartmentConfig:
    db = get_db()
    doc = db.collection("settings").document("department_config").get()
    if not doc.exists:
        db.collection("settings").document("department_config").set(SEED_DEPARTMENT_CONFIG)
        return DepartmentConfig(**SEED_DEPARTMENT_CONFIG)
    return DepartmentConfig(**(doc.to_dict() or SEED_DEPARTMENT_CONFIG))


@router.get("", response_model=DepartmentConfig)
def get_settings(current_user: UserOut = Depends(get_current_user)) -> DepartmentConfig:
    """Vrátí globální nastavení oddělení (12h směny, minimální obsazenost D/N, pravidla)."""
    return load_department_config()


@router.put("", response_model=DepartmentConfig)
def update_settings(
    payload: DepartmentConfig,
    current_user: UserOut = Depends(require_roles("admin", "head_nurse")),
) -> DepartmentConfig:
    """Uloží globální nastavení oddělení (Admin / Vrchní sestra)."""
    db = get_db()
    data = payload.model_dump()
    db.collection("settings").document("department_config").set(data)
    return payload
