from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database.mongo import get_database
from ..dependencies import get_current_user
from ..utils.time import date_key
from ..models import ROLE_TEACHER
from ..schemas import TeacherStats, TeacherAttendanceRow, MarkAttendanceRequest, ManualAttendanceRequest, UserOut
from ..services.attendance_service import (
    get_teacher_stats, 
    get_teacher_today_rows, 
    send_absent_notifications,
    get_teacher_department_students,
    mark_attendance_by_face,
    mark_attendance_manual,
    get_attendance_report_rows,
)
from ..services.report_service import generate_excel_report, generate_pdf_report


router = APIRouter(tags=["teacher"])


async def _require_teacher(current_user: dict = Depends(get_current_user)) -> dict:
    if (current_user.get("role") or "").lower() != ROLE_TEACHER:
        raise HTTPException(status_code=403, detail="Faculty access required.")
    return current_user


@router.get("/teacher/dashboard-stats", response_model=TeacherStats)
async def teacher_stats(current_user: dict = Depends(_require_teacher), db: AsyncIOMotorDatabase = Depends(get_database)):
    department = current_user.get("department")
    if not department:
        raise HTTPException(status_code=400, detail="Faculty department not configured.")
    return await get_teacher_stats(db, department)


@router.get("/teacher/department/stats", response_model=TeacherStats)
async def teacher_dept_stats(current_user: dict = Depends(_require_teacher), db: AsyncIOMotorDatabase = Depends(get_database)):
    department = current_user.get("department")
    if not department:
        raise HTTPException(status_code=400, detail="Faculty department not configured.")
    return await get_teacher_stats(db, department)


@router.get("/teacher/attendance/today", response_model=list[TeacherAttendanceRow])
async def teacher_today_attendance(current_user: dict = Depends(_require_teacher), db: AsyncIOMotorDatabase = Depends(get_database)):
    department = current_user.get("department")
    if not department:
        raise HTTPException(status_code=400, detail="Faculty department not configured.")
    return await get_teacher_today_rows(db, department)


@router.post("/teacher/notifications/absent")
async def teacher_notify_absent(current_user: dict = Depends(_require_teacher), db: AsyncIOMotorDatabase = Depends(get_database)):
    department = current_user.get("department")
    if not department:
        raise HTTPException(status_code=400, detail="Faculty department not configured.")

    result = await send_absent_notifications(db, department)
    if result.get("status") == "failed":
        raise HTTPException(status_code=503, detail=result.get("message") or "Failed to send absent notifications.")
    return {"message": result["message"]}


@router.get("/teacher/department/students", response_model=list[UserOut])
async def get_my_students(
    unmarked_only: bool = Query(False),
    current_user: dict = Depends(_require_teacher), 
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    department = current_user.get("department")
    if not department:
        raise HTTPException(status_code=400, detail="Faculty department not configured.")
    return await get_teacher_department_students(db, department, unmarked_only=unmarked_only)


@router.post("/teacher/mark-attendance")
async def mark_face_attendance(
    payload: MarkAttendanceRequest, 
    current_user: dict = Depends(_require_teacher), 
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await mark_attendance_by_face(
        db, 
        teacher=current_user, 
        image=payload.image, 
        latitude=payload.latitude, 
        longitude=payload.longitude
    )


@router.post("/teacher/mark-attendance/manual/{student_id}")
async def mark_manual_attendance(
    student_id: int,
    payload: ManualAttendanceRequest,
    current_user: dict = Depends(_require_teacher),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await mark_attendance_manual(
        db,
        teacher=current_user,
        student_id=student_id,
        status=payload.status,
        latitude=payload.latitude,
        longitude=payload.longitude
    )


@router.get("/teacher/attendance/export")
async def export_teacher_attendance(
    format: str = Query("excel", pattern="^(excel|pdf)$"),
    db: AsyncIOMotorDatabase = Depends(get_database), 
    current_user: dict = Depends(_require_teacher)
):
    department = current_user.get("department")
    if not department:
        raise HTTPException(status_code=400, detail="Faculty department not configured.")
    report_date = date_key()
    records = await get_attendance_report_rows(db, report_date, report_date, department)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dept_slug = department.lower().replace(" ", "_")
    
    if format == "excel":
        file_obj = generate_excel_report(records)
        return StreamingResponse(
            file_obj, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            headers={"Content-Disposition": f"attachment; filename=attendance_{dept_slug}_{timestamp}.xlsx"}
        )
    else:
        title = f"Attendance Report - {department} - {datetime.now().strftime('%Y-%m-%d')}"
        file_obj = generate_pdf_report(records, title)
        return StreamingResponse(
            file_obj, 
            media_type="application/pdf", 
            headers={"Content-Disposition": f"attachment; filename=attendance_{dept_slug}_{timestamp}.pdf"}
        )


@router.get("/teacher/reports/export")
async def export_teacher_report(
    format: str = Query("excel", pattern="^(excel|pdf)$"),
    from_date: str = Query(..., pattern="^\d{4}-\d{2}-\d{2}$"),
    to_date: str = Query(..., pattern="^\d{4}-\d{2}-\d{2}$"),
    scope: str = Query("custom", pattern="^(daily|weekly|monthly|yearly|custom)$"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(_require_teacher),
):
    department = current_user.get("department")
    if not department:
        raise HTTPException(status_code=400, detail="Faculty department not configured.")

    records = await get_attendance_report_rows(db, from_date, to_date, department)
    if not records:
        raise HTTPException(status_code=404, detail="No attendance records found for the selected range.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dept_slug = department.lower().replace(" ", "_")
    scope_slug = scope.lower()
    range_slug = f"{from_date}_to_{to_date}"

    if format == "excel":
        file_obj = generate_excel_report(records)
        return StreamingResponse(
            file_obj,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=teacher_report_{dept_slug}_{scope_slug}_{range_slug}_{timestamp}.xlsx"},
        )

    title = f"Teacher Attendance Report - {department} - {from_date} to {to_date}"
    file_obj = generate_pdf_report(records, title)
    return StreamingResponse(
        file_obj,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=teacher_report_{dept_slug}_{scope_slug}_{range_slug}_{timestamp}.pdf"},
    )
