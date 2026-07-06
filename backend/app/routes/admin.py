import csv
import io
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database.mongo import get_database
from ..dependencies import get_current_user
from ..models import ROLE_ADMIN
from ..schemas import AdminAccountCreate, AdminDeleteRequest, AdminResetPasswordRequest, AdminSetActiveRequest, AdminStats, AdminUserUpdateRequest, TeacherCreate, UserOut, WeeklyReport, PunctualityReport, UserStatusReport, AdminConfig, AdminConfigUpdate, FacultyAttendanceReport, MonitoringLocation, MonthlyAttendanceSummary
from ..services.attendance_service import get_admin_stats, serialize_attendance, get_recent_attendance_logs, get_attendance_report_rows, get_monthly_attendance_summary_rows
from ..services.email_service import send_password_changed
from ..services.security_service import log_security_event, get_security_logs
from ..services.user_service import create_teacher_user, delete_user, get_user_by_id, require_admin_password, reset_password, serialize_user, set_active_status, admin_update_user
from ..services.user_service import create_admin_user, get_user_by_email
from ..services.report_service import generate_excel_report, generate_pdf_report
from ..utils.time import date_key, iso_ist, now_ist
from ..config import settings

router = APIRouter(tags=["admin"])




def _is_admin(user: dict) -> bool:
    return bool(user.get("is_admin")) or (user.get("role") or "").lower() == ROLE_ADMIN


def _month_window(month: str | None) -> tuple[str, str]:
    month_value = month or now_ist().strftime("%Y-%m")
    try:
        month_start = datetime.strptime(month_value, "%Y-%m")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM.") from exc

    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)

    return month_start.strftime("%Y-%m-01"), next_month.strftime("%Y-%m-01")


async def _require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Administrative access required.")
    return current_user


@router.get("/admin/attendance/export")
async def export_admin_attendance(
    format: str = Query("excel", pattern="^(excel|pdf)$"),
    date: str | None = Query(None, pattern="^\d{4}-\d{2}-\d{2}$"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(_require_admin)
):
    report_date = date or date_key()
    records = await get_attendance_report_rows(db, report_date, report_date, None)
    if not records:
        raise HTTPException(status_code=404, detail="No attendance records found for this date.")
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == "excel":
        file_obj = generate_excel_report(records)
        return StreamingResponse(
            file_obj,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=system_attendance_{report_date}_{timestamp}.xlsx"}
        )
    else:
        title = f"System Attendance Report - {report_date}"
        file_obj = generate_pdf_report(records, title)
        return StreamingResponse(
            file_obj,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=system_attendance_{report_date}_{timestamp}.pdf"}
        )


@router.get("/admin/reports/export")
async def export_admin_report(
    format: str = Query("excel", pattern="^(excel|pdf)$"),
    from_date: str = Query(..., pattern="^\d{4}-\d{2}-\d{2}$"),
    to_date: str = Query(..., pattern="^\d{4}-\d{2}-\d{2}$"),
    scope: str = Query("custom", pattern="^(daily|weekly|monthly|yearly|custom)$"),
    department: str | None = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(_require_admin),
):
    records = await get_attendance_report_rows(db, from_date, to_date, department)
    if not records:
        raise HTTPException(status_code=404, detail="No attendance records found for the selected range.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dept_slug = (department or "all_departments").strip().lower().replace(" ", "_") or "all_departments"
    scope_slug = scope.lower()
    range_slug = f"{from_date}_to_{to_date}"

    if format == "excel":
        file_obj = generate_excel_report(records)
        return StreamingResponse(
            file_obj,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=admin_report_{dept_slug}_{scope_slug}_{range_slug}_{timestamp}.xlsx"},
        )

    title = f"Admin Attendance Report - {department or 'All Departments'} - {from_date} to {to_date}"
    file_obj = generate_pdf_report(records, title)
    return StreamingResponse(
        file_obj,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=admin_report_{dept_slug}_{scope_slug}_{range_slug}_{timestamp}.pdf"},
    )


@router.get("/admin/config", response_model=AdminConfig)
async def get_admin_config(current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    config_data = {
        "face_tolerance": settings.face_tolerance,
        "campus_lat": settings.campus_lat,
        "campus_lon": settings.campus_lon,
        "max_distance_km": settings.max_distance_km,
        "late_hour": settings.late_hour,
        "late_minute": settings.late_minute,
        "absent_notice_hour": settings.absent_notice_hour,
        "absent_notice_minute": settings.absent_notice_minute,
        "mfa_enabled": settings.mfa_enabled,
        "geofencing_enabled": settings.geofencing_enabled,
        "lockout_enabled": settings.lockout_enabled
    }
    
    doc = await db.config.find_one({"_id": "global"})
    if doc:
        doc.pop("_id", None)
        config_data.update(doc)
        
    return AdminConfig(**config_data)


@router.patch("/admin/config")
async def update_admin_config(payload: AdminConfigUpdate, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    await require_admin_password(current_user, payload.admin_password)
    update_data = payload.model_dump(exclude={"admin_password"}, exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No changes provided")
    await db.config.update_one({"_id": "global"}, {"$set": update_data}, upsert=True)
    await log_security_event(
        db,
        event_type="ADMIN_CONFIG_UPDATE",
        severity="warning",
        details="System configuration modified by administrator",
        admin_user_id=current_user["id"],
        metadata=update_data
    )
    return {"message": "System configuration updated successfully."}

@router.get("/admin/stats", response_model=AdminStats)
async def admin_stats(current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    data = await get_admin_stats(db)
    return AdminStats(**data)

@router.get("/admin/users", response_model=list[UserOut])
async def admin_users(current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    users: list[dict] = []
    cursor = db.users.find({}).sort("id", 1)
    async for user in cursor:
        users.append(serialize_user(user))
    return users


@router.get("/admin/logs")
async def admin_logs(limit: int = 10, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    logs = await get_recent_attendance_logs(db, limit)
    return logs


@router.get("/admin/security-logs")
async def admin_security_logs(limit: int = 20, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    logs = await get_security_logs(db, limit)
    return logs


@router.post("/admin/teachers")
async def admin_create_teacher(payload: TeacherCreate, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    await require_admin_password(current_user, payload.admin_password)
    existing_email = await db.users.find_one({"email": payload.email.lower().strip()})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    existing_roll = await db.users.find_one({"roll_number": payload.employee_id.strip()})
    if existing_roll:
        raise HTTPException(status_code=400, detail="Employee ID already registered")
    teacher = await create_teacher_user(db, payload)
    await log_security_event(
        db,
        event_type="ADMIN_CREATE_TEACHER",
        severity="info",
        details=f"Teacher created: {teacher['email']}",
        admin_user_id=current_user["id"],
        target_user_id=teacher["id"],
        ip_address=None,
        user_agent=None,
    )
    return {"message": "Faculty account created successfully.", "user": serialize_user(teacher)}


@router.post("/admin/accounts")
async def admin_create_account(payload: AdminAccountCreate, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    await require_admin_password(current_user, payload.admin_password)
    email = payload.email.lower().strip()
    if await get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already registered")

    identifier = payload.identifier.strip()
    if await db.users.find_one({"roll_number": identifier}):
        raise HTTPException(status_code=400, detail="Identifier already registered")

    if payload.account_type == "admin":
        account = await create_admin_user(db, payload)
        event_type = "ADMIN_CREATE_ADMIN"
        details = f"Admin created: {account['email']}"
        message = "Administrator account created successfully."
    else:
        teacher_payload = TeacherCreate(
            admin_password=payload.admin_password,
            full_name=payload.full_name,
            email=payload.email,
            employee_id=identifier,
            department=payload.department,
            password=payload.password,
        )
        account = await create_teacher_user(db, teacher_payload)
        event_type = "ADMIN_CREATE_TEACHER"
        details = f"Faculty created: {account['email']}"
        message = "Faculty account created successfully."

    await log_security_event(
        db,
        event_type=event_type,
        severity="info",
        details=details,
        admin_user_id=current_user["id"],
        target_user_id=account["id"],
        ip_address=None,
        user_agent=None,
    )
    return {"message": message, "user": serialize_user(account)}


@router.patch("/admin/users/{user_id}")
async def admin_edit_user(user_id: int, payload: AdminUserUpdateRequest, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    await require_admin_password(current_user, payload.admin_password)
    target = await get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Account not found.")
    await admin_update_user(db, target, payload)
    await log_security_event(
        db,
        event_type="ADMIN_USER_UPDATE",
        severity="info",
        details=f"User updated: {target['email']}",
        admin_user_id=current_user["id"],
        target_user_id=target["id"],
        ip_address=None,
        user_agent=None,
    )
    return {"message": "Account details updated successfully."}


@router.post("/admin/users/{user_id}/set-active")
async def admin_set_active(user_id: int, payload: AdminSetActiveRequest, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    await require_admin_password(current_user, payload.admin_password)
    target = await get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Account not found.")
    if target.get("is_admin") and not payload.is_active:
        raise HTTPException(status_code=400, detail="Cannot deactivate an admin account")
    await set_active_status(db, user_id, payload.is_active)
    await log_security_event(
        db,
        event_type="ADMIN_SET_ACTIVE",
        severity="info",
        details=f"User {user_id} active={payload.is_active}",
        admin_user_id=current_user["id"],
        target_user_id=user_id,
        ip_address=None,
        user_agent=None,
    )
    return {"message": "Account status updated", "is_active": payload.is_active}


@router.post("/admin/users/{user_id}/reset-password")
async def admin_reset_password(user_id: int, payload: AdminResetPasswordRequest, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    await require_admin_password(current_user, payload.admin_password)
    target = await get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Account not found.")
    await reset_password(db, target)
    await log_security_event(
        db,
        event_type="ADMIN_RESET_PASSWORD",
        severity="warning",
        details=f"Password reset for {target['email']}",
        admin_user_id=current_user["id"],
        target_user_id=target["id"],
        ip_address=None,
        user_agent=None,
    )
    return {"message": "Password reset successfully", "temporary_password": "SASUFR"}


@router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: int, payload: AdminDeleteRequest, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    await require_admin_password(current_user, payload.admin_password)
    target = await get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Account not found.")
    await delete_user(db, user_id)
    await log_security_event(
        db,
        event_type="ADMIN_DELETE_USER",
        severity="warning",
        details=f"Deleted user {target['email']}",
        admin_user_id=current_user["id"],
        target_user_id=target["id"],
        ip_address=None,
        user_agent=None,
    )
    return {"message": "Account deleted successfully."}


@router.get("/admin/reports/weekly")
async def admin_report_weekly(days: int = 6, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    labels: list[str] = []
    counts: list[int] = []
    for offset in range(days, -1, -1):
        day = (now_ist() - timedelta(days=offset)).date().isoformat()
        labels.append(day)
        counts.append(await db.attendance.count_documents({"date": day, "status": {"$in": ["Present", "Late"]}}))
    return WeeklyReport(labels=labels, counts=counts)


@router.get("/admin/reports/punctuality")
async def admin_report_punctuality(days: int = 7, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    since = (now_ist() - timedelta(days=days)).date().isoformat()
    on_time = await db.attendance.count_documents({"date": {"$gte": since}, "status": "Present"})
    late = await db.attendance.count_documents({"date": {"$gte": since}, "status": "Late"})
    absent = await db.attendance.count_documents({"date": {"$gte": since}, "status": "Absent"})
    return PunctualityReport(on_time=on_time, late=late, absent=absent)


@router.get("/admin/reports/users-status")
async def admin_report_users_status(current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    active = await db.users.count_documents({"is_active": True})
    inactive = await db.users.count_documents({"is_active": False})
    return UserStatusReport(active=active, inactive=inactive)


@router.get("/admin/reports/faculty", response_model=list[FacultyAttendanceReport])
async def admin_report_faculty(days: int = 30, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    since = (now_ist() - timedelta(days=days)).date().isoformat()
    teachers = await db.users.find({"role": "teacher"}).sort("full_name", 1).to_list(length=None)
    attendance_docs = await db.attendance.find({"date": {"$gte": since}}).to_list(length=None)

    total_days = len({doc.get("date") for doc in attendance_docs if doc.get("date")})
    day_map: dict[int, set[str]] = {}

    for doc in attendance_docs:
        marked_by_user_id = doc.get("marked_by_user_id")
        day_value = doc.get("date")
        if marked_by_user_id is None or not day_value:
            continue
        day_map.setdefault(int(marked_by_user_id), set()).add(str(day_value))

    result: list[dict] = []
    for teacher in teachers:
        covered_days = len(day_map.get(int(teacher["id"]), set()))
        percentage = round((covered_days / total_days * 100) if total_days else 0.0, 1)
        result.append({
            "id": teacher["id"],
            "full_name": teacher.get("full_name"),
            "department": teacher.get("department"),
            "attendance_percentage": percentage,
            "classes_attended": covered_days,
            "total_classes": total_days,
            "status": "ACTIVE" if teacher.get("is_active", True) else "INACTIVE",
        })

    result.sort(key=lambda item: (-item["attendance_percentage"], item["full_name"] or "", item["id"]))
    return [FacultyAttendanceReport(**row) for row in result[:10]]


@router.get("/admin/locations", response_model=list[MonitoringLocation])
async def admin_locations(current_user: dict = Depends(_require_admin)):
    return [
        MonitoringLocation(id=1, name="MAIN_CAMPUS", status="ACTIVE", lat=settings.campus_lat, lon=settings.campus_lon),
        MonitoringLocation(id=2, name="TECHNOLOGY_BLOCK", status="ACTIVE", lat=settings.campus_lat + 0.0008, lon=settings.campus_lon + 0.0008),
        MonitoringLocation(id=3, name="AUDITORIUM", status="IN_MAINTENANCE", lat=settings.campus_lat - 0.0006, lon=settings.campus_lon - 0.0006),
    ]


@router.get("/admin/reports/monthly-summary", response_model=list[MonthlyAttendanceSummary])
async def admin_report_monthly_summary(
    month: str | None = Query(None, pattern="^\d{4}-\d{2}$"),
    department: str | None = Query(None),
    current_user: dict = Depends(_require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await get_monthly_attendance_summary_rows(db, month, department)


@router.get("/admin/reports/attendance.csv")
async def admin_report_csv(days: int = 7, current_user: dict = Depends(_require_admin), db: AsyncIOMotorDatabase = Depends(get_database)):
    since = (now_ist() - timedelta(days=days)).date().isoformat()
    records = await db.attendance.find({"date": {"$gte": since}}).sort("date", -1).to_list(length=None)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "date", "check_in", "status", "method", "marked_by_user_id"])
    for record in records:
        writer.writerow([
            record.get("id"),
            record.get("user_id"),
            record.get("date"),
            record.get("check_in"),
            record.get("status"),
            record.get("method"),
            record.get("marked_by_user_id"),
        ])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=attendance.csv"})
