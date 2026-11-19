import calendar
from typing import Dict, Tuple

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user, require_roles
from app.db import get_db
from app.models import DayShifts, ScheduleData, ScheduleResponse, UserOut

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])


def get_month_dates(year: int, month: int):
    days = calendar.monthrange(year, month)[1]
    return [f"{year}-{month:02d}-{d:02d}" for d in range(1, days + 1)]

def parse_year_month(year_month: str) -> Tuple[int, int]:
    try:
        parts = year_month.split("-")
        if len(parts) != 2:
            raise ValueError("Invalid format")
        year = int(parts[0])
        month = int(parts[1])
        if not (2000 <= year <= 2100 and 1 <= month <= 12):
            raise ValueError("Out of range")
        return year, month
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Neplatný formát měsíce. Očekáváno YYYY-MM (např. 2026-11).",
        )


def normalize_month_shifts(
    year: int, month: int, raw_shifts: Dict[str, dict]
) -> Dict[str, DayShifts]:
    dates = get_month_dates(year, month)
    normalized: Dict[str, DayShifts] = {}
    for d in dates:
        entry = raw_shifts.get(d, {})
        if isinstance(entry, DayShifts):
            normalized[d] = entry
        else:
            normalized[d] = DayShifts(
                day=list(dict.fromkeys(entry.get("day", []))),
                night=list(dict.fromkeys(entry.get("night", []))),
                vacation=list(dict.fromkeys(entry.get("vacation", []))),
            )
    return normalized


def build_schedule_response(year_month: str) -> ScheduleResponse:
    year, month = parse_year_month(year_month)
    snap = get_db().collection("schedules").document(year_month).get()
    if snap.exists:
        data = snap.to_dict() or {}
        schedule_status = data.get("status", "draft")
        shifts_map = normalize_month_shifts(year, month, data.get("shifts", {}))
    else:
        schedule_status = "draft"
        shifts_map = normalize_month_shifts(year, month, {})
    return ScheduleResponse(
        schedule_id=year_month,
        year=year,
        month=month,
        status=schedule_status,
        shifts=shifts_map,
    )


@router.get("/{year_month}", response_model=ScheduleResponse)
def get_schedule(
    year_month: str,
    current_user: UserOut = Depends(get_current_user),
) -> ScheduleResponse:
    """Načte měsíční rozpis směn (pokud neexistuje, vrátí prázdný draft)."""
    return build_schedule_response(year_month)


@router.put("/{year_month}", response_model=ScheduleResponse)
def save_schedule(
    year_month: str,
    payload: ScheduleData,
    current_user: UserOut = Depends(require_roles("head_nurse", "admin")),
) -> ScheduleResponse:
    """Uloží kompletní měsíční rozpis směn (Vrchní sestra / Admin)."""
    year, month = parse_year_month(year_month)
    normalized = normalize_month_shifts(
        year, month, {k: v.model_dump() for k, v in payload.shifts.items()}
    )
    get_db().collection("schedules").document(year_month).set(
        {
            "year": year,
            "month": month,
            "status": payload.status,
            "shifts": {k: v.model_dump() for k, v in normalized.items()},
        }
    )
    return build_schedule_response(year_month)
