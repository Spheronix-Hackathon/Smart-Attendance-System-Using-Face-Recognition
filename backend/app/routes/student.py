from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database.mongo import get_database
from ..dependencies import get_current_user
from ..models import ROLE_STUDENT
from ..schemas import AttendanceStats
from ..services.attendance_service import get_student_attendance_stats


router = APIRouter(tags=["student"])


async def _require_student(current_user: dict = Depends(get_current_user)) -> dict:
    if (current_user.get("role") or "").lower() != ROLE_STUDENT:
        raise HTTPException(status_code=403, detail="Student access required.")
    return current_user


@router.get("/student/stats", response_model=AttendanceStats)
async def student_stats(current_user: dict = Depends(_require_student), db: AsyncIOMotorDatabase = Depends(get_database)):
    return await get_student_attendance_stats(db, current_user["id"])
