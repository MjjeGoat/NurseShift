from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

UserRole = Literal["admin", "head_nurse", "nurse"]
ScheduleStatus = Literal["open_for_preferences", "draft", "published"]


class UserBase(BaseModel):
    name: str = Field(..., min_length=2, description="Celé jméno včetně titulů")
    email: str = Field(..., description="Nemocniční Microsoft e-mail")
    microsoft_oid: Optional[str] = Field(
        default=None, description="Object ID účtu v Microsoft Entra ID (Azure AD)"
    )
    role: UserRole = "nurse"
    workload: float = Field(default=1.0, ge=0.1, le=1.5, description="Úvazek (např. 1.0, 0.5)")
    active: bool = True


class UserCreate(UserBase):
    id: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    microsoft_oid: Optional[str] = None
    role: Optional[UserRole] = None
    workload: Optional[float] = Field(default=None, ge=0.1, le=1.5)
    active: Optional[bool] = None


class UserOut(UserBase):
    id: str


class RulesConfig(BaseModel):
    prevent_night_to_day: bool = True
    max_consecutive_shifts: int = Field(default=3, ge=1, le=10)


class DepartmentConfig(BaseModel):
    shift_duration_hours: int = Field(default=12, ge=1, le=24)
    min_staff_day: int = Field(default=3, ge=0, le=50)
    min_staff_night: int = Field(default=2, ge=0, le=50)
    weekly_hours_full_workload: float = Field(default=37.5, ge=10.0, le=60.0)
    rules_config: RulesConfig = Field(default_factory=RulesConfig)


class DayShifts(BaseModel):
    day: List[str] = Field(default_factory=list)
    night: List[str] = Field(default_factory=list)
    vacation: List[str] = Field(default_factory=list)


class ScheduleData(BaseModel):
    year: int
    month: int = Field(..., ge=1, le=12)
    status: ScheduleStatus = "draft"
    shifts: Dict[str, DayShifts] = Field(default_factory=dict)


class MicrosoftAuthRequest(BaseModel):
    id_token: Optional[str] = None
    access_token: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    microsoft_oid: Optional[str] = None


class DevLoginRequest(BaseModel):
    user_id: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    auth_provider: str = "microsoft_entra_id"
    user: UserOut


class ScheduleResponse(BaseModel):
    schedule_id: str
    year: int
    month: int
    status: ScheduleStatus
    shifts: Dict[str, DayShifts]
