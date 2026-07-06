from __future__ import annotations

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database.mongo import get_database
from ..dependencies import get_current_user
from ..schemas import AttendanceOut
from ..services.attendance_service import get_student_attendance_history, get_student_attendance_stats, serialize_attendance


router = APIRouter(tags=["attendance"])


@router.get("/attendance/me/stats")
async def attendance_me_stats(current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    stats = await get_student_attendance_stats(db, current_user["id"])
    total = stats.present_days + stats.absences
    percentage = round((stats.present_days / total * 100), 1) if total > 0 else 0.0
    return {
        "present_days": stats.present_days,
        "absences": stats.absences,
        "attendance_percentage": percentage,
        "avg_check_in": stats.avg_check_in
    }


@router.get("/attendance/me/history", response_model=list[AttendanceOut])
async def attendance_me_history(current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    records = await get_student_attendance_history(db, current_user["id"])
    return [serialize_attendance(record) for record in records]
