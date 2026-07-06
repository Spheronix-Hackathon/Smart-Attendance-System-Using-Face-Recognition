from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: str | None = None


class UserBase(BaseModel):
    full_name: str | None = None
    email: EmailStr
    roll_number: str
    department: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=6)
    face_image: str


class TeacherCreate(BaseModel):
    admin_password: str
    full_name: str
    email: EmailStr
    employee_id: str
    department: str
    password: str = Field(min_length=6)


class AdminAccountCreate(BaseModel):
    admin_password: str
    account_type: Literal["teacher", "admin"] = "teacher"
    full_name: str
    email: EmailStr
    identifier: str = Field(min_length=1)
    department: str = Field(min_length=1)
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class OTPRequest(BaseModel):
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class FaceCaptureRequest(BaseModel):
    image: str
    latitude: float | None = None
    longitude: float | None = None


class ManualAttendanceRequest(BaseModel):
    status: str = "Present"
    latitude: float | None = None
    longitude: float | None = None


class AdminFaceUpdateRequest(BaseModel):
    image: str
    admin_password: str


class AdminUserUpdateRequest(BaseModel):
    admin_password: str
    full_name: str | None = None
    email: EmailStr | None = None
    roll_number: str | None = None
    role: str | None = None
    department: str | None = None


class AdminSetActiveRequest(BaseModel):
    admin_password: str
    is_active: bool


class AdminResetPasswordRequest(BaseModel):
    admin_password: str


class AdminDeleteRequest(BaseModel):
    admin_password: str


class MarkAttendanceRequest(BaseModel):
    image: str
    latitude: float | None = None
    longitude: float | None = None
    attendance_status: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str | None = None
    email: EmailStr
    roll_number: str
    profile_picture: str | None = None
    is_active: bool
    is_verified: bool
    is_admin: bool
    role: str
    department: str | None = None
    face_image: str | None = None
    preferences: dict = {}
    created_at: str | None = None
    updated_at: str | None = None


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date: str
    check_in: str
    check_out: str | None = None
    status: str
    marked_by_user_id: int | None = None
    method: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AttendanceStats(BaseModel):
    present_days: int
    late_days: int = 0
    attended_days: int = 0
    absences: int
    marked_days: int = 0
    pending_days: int = 0
    calculation_start_date: str | None = None
    calculation_through_date: str | None = None
    avg_check_in: str
    attendance_percentage: float = 0.0
    history: list[AttendanceOut] = []


class AdminStats(BaseModel):
    total_users: int
    total_students: int
    present_today: int
    absent_today: int
    attendance_percentage: float = 0.0
    system_status: str


class TeacherStats(BaseModel):
    total_students: int
    present: int
    late: int
    absent: int
    not_marked: int
    attendance_finalized: bool = False


class TeacherAttendanceRow(BaseModel):
    id: int
    roll_number: str | None = None
    full_name: str | None = None
    email: str
    status: str | None = None
    check_in: str | None = None
    department: str | None = None
    date: str | None = None
    method: str | None = None
    marked_by_user_id: int | None = None
    marked_by_name: str | None = None


class WeeklyReport(BaseModel):
    labels: list[str]
    counts: list[int]


class FacultyAttendanceReport(BaseModel):
    id: int
    full_name: str | None = None
    department: str | None = None
    attendance_percentage: float
    classes_attended: int
    total_classes: int
    status: str = "ACTIVE"


class MonitoringLocation(BaseModel):
    id: int
    name: str
    status: str
    lat: float
    lon: float


class MonthlyAttendanceSummary(BaseModel):
    id: int
    roll_number: str | None = None
    full_name: str | None = None
    department: str | None = None
    attendance_percentage: float
    classes_attended: int
    total_classes: int
    status: str


class PunctualityReport(BaseModel):
    on_time: int
    late: int
    absent: int


class UserStatusReport(BaseModel):
    active: int
    inactive: int


class MessageResponse(BaseModel):
    message: str


class AdminConfig(BaseModel):
    face_tolerance: float
    campus_lat: float
    campus_lon: float
    max_distance_km: float
    late_hour: int
    late_minute: int
    absent_notice_hour: int
    absent_notice_minute: int
    mfa_enabled: bool = False
    geofencing_enabled: bool = False
    lockout_enabled: bool = False


class AdminConfigUpdate(BaseModel):
    admin_password: str
    face_tolerance: float | None = None
    campus_lat: float | None = None
    campus_lon: float | None = None
    max_distance_km: float | None = None
    late_hour: int | None = None
    late_minute: int | None = None
    absent_notice_hour: int | None = None
    absent_notice_minute: int | None = None
    mfa_enabled: bool | None = None
    geofencing_enabled: bool | None = None
    lockout_enabled: bool | None = None


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    department: str | None = None
    preferences: dict | None = None
