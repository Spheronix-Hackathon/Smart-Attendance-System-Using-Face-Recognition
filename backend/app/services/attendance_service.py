from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from ..config import settings
from ..models import ROLE_STUDENT
from ..schemas import AttendanceOut, AttendanceStats, MonthlyAttendanceSummary, TeacherAttendanceRow, TeacherStats
from ..utils.geo import is_within_radius
from ..utils.time import date_key, iso_ist, now_ist, time_key
from .email_service import get_last_mail_error, send_absent_notice
from .face_service import extract_encoding, extract_multiple_encodings, find_best_match, find_matches


def serialize_attendance(doc: dict):
    if not doc:
        return doc
    doc = dict(doc)
    doc.pop("_id", None)
    return doc


async def _next_id(db: AsyncIOMotorDatabase, name: str) -> int:
    result = await db.counters.find_one_and_update(
        {"_id": name}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    return int(result["seq"])


async def _get_today_attendance(db: AsyncIOMotorDatabase, user_id: int) -> dict | None:
    return await db.attendance.find_one({"user_id": int(user_id), "date": date_key()})


def _parse_date_value(value: str | None) -> datetime.date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None


def _attendance_day_completed(today_record_exists: bool) -> bool:
    _ = today_record_exists
    now = now_ist()
    return (now.hour, now.minute) >= (settings.absent_notice_hour, settings.absent_notice_minute)


def _finalized_through_date(today_record_exists: bool) -> datetime.date:
    today = now_ist().date()
    if _attendance_day_completed(today_record_exists):
        return today
    return today - timedelta(days=1)


def _absent_mail_failure_message() -> str:
    mail_error = get_last_mail_error()
    if mail_error == "quota_exceeded":
        return "Gmail daily sending limit exceeded. This is a rolling 24-hour quota, so the sender account must wait until the limit resets."
    if mail_error == "mail_not_configured":
        return "Mail is not configured correctly on the server. Check MAIL_USERNAME, MAIL_PASSWORD, and MAIL_FROM."
    if mail_error == "mail_disabled":
        return "Mail sending is disabled in the backend configuration. Set MAIL_ENABLED=true to deliver absent emails."
    return "Unable to deliver absent notification email right now. Please check Gmail app-password, SMTP settings, and the student's spam folder."


def _iter_dates(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def _month_window_dates(month: str | None = None) -> tuple[datetime.date, datetime.date]:
    month_value = month or now_ist().strftime("%Y-%m")
    try:
        month_start = datetime.strptime(month_value, "%Y-%m").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM.") from exc

    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)

    return month_start, next_month


async def _resolve_user_names(db: AsyncIOMotorDatabase, user_ids: set[int]) -> dict[int, str]:
    if not user_ids:
        return {}

    users = await db.users.find({"id": {"$in": list(user_ids)}}).to_list(length=None)
    names: dict[int, str] = {}
    for user in users:
        user_id = int(user["id"])
        names[user_id] = user.get("full_name") or user.get("email") or f"User #{user_id}"
    return names


async def get_attendance_report_rows(
    db: AsyncIOMotorDatabase,
    from_date: str,
    to_date: str,
    department: str | None = None,
) -> list[dict]:
    from ..models import ROLE_STUDENT

    try:
        start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date range. Use YYYY-MM-DD.") from exc

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date cannot be after end date.")

    student_query: dict = {"role": ROLE_STUDENT, "is_active": True}
    normalized_department = (department or "").strip()
    if normalized_department and normalized_department not in {"ALL", "ALL_DEPARTMENTS"}:
        student_query["department"] = normalized_department

    students = await db.users.find(student_query).sort([("department", 1), ("roll_number", 1)]).to_list(length=None)
    if not students:
        return []

    attendance_docs = await db.attendance.find({"date": {"$gte": from_date, "$lte": to_date}}).to_list(length=None)
    attendance_map = {
        (int(doc["user_id"]), str(doc["date"])): doc
        for doc in attendance_docs
        if doc.get("user_id") is not None and doc.get("date")
    }
    today = now_ist().date()
    today_key = today.isoformat()
    today_record_exists = any(str(doc.get("date")) == today_key for doc in attendance_docs)
    finalized_through_date = min(end_date, _finalized_through_date(today_record_exists))
    marker_ids = {
        int(doc["marked_by_user_id"])
        for doc in attendance_docs
        if doc.get("marked_by_user_id") is not None
    }
    marker_names = await _resolve_user_names(db, marker_ids)

    rows: list[dict] = []
    current_day = start_date
    while current_day <= end_date:
        day_key = current_day.isoformat()
        for student in students:
            student_start_date = _parse_date_value(student.get("created_at")) or start_date
            record = attendance_map.get((int(student["id"]), day_key))
            
            student_finalized_date = finalized_through_date
            if current_day == today and record:
                student_finalized_date = max(finalized_through_date, current_day)
                
            if current_day > student_finalized_date:
                status = "Pending"
                check_in = "--:--"
                method = "System"
                marker_id = None
                marker_name = None
            elif current_day < student_start_date:
                status = "Pre-Enrollment"
                check_in = "--:--"
                method = "System"
                marker_id = None
                marker_name = None
            else:
                marker_id = record.get("marked_by_user_id") if record else None
                status = record.get("status") if record else "Absent"
                check_in = record.get("check_in") if record else "--:--"
                method = record.get("method") if record else "System"
                marker_name = marker_names.get(int(marker_id)) if marker_id is not None else None
            rows.append({
                "id": student["id"],
                "roll_number": student.get("roll_number"),
                "full_name": student.get("full_name"),
                "email": student["email"],
                "department": student.get("department"),
                "date": day_key,
                "status": status,
                "check_in": check_in,
                "method": method,
                "marked_by_user_id": marker_id,
                "marked_by_name": marker_name,
            })
        current_day += timedelta(days=1)

    return rows


async def get_monthly_attendance_summary_rows(
    db: AsyncIOMotorDatabase,
    month: str | None = None,
    department: str | None = None,
) -> list[MonthlyAttendanceSummary]:
    month_start, next_month = _month_window_dates(month)
    month_end = next_month - timedelta(days=1)

    student_query: dict = {"role": ROLE_STUDENT}
    normalized_department = (department or "").strip()
    if normalized_department and normalized_department not in {"ALL", "ALL_DEPARTMENTS"}:
        student_query["department"] = normalized_department

    students = await db.users.find(student_query).sort("full_name", 1).to_list(length=None)
    if not students:
        return []

    attendance_docs = await db.attendance.find({"date": {"$gte": month_start.isoformat(), "$lt": next_month.isoformat()}}).to_list(length=None)
    today = now_ist().date()
    today_key = today.isoformat()
    today_record_exists = any(str(doc.get("date")) == today_key for doc in attendance_docs)
    finalized_through_date = min(month_end, _finalized_through_date(today_record_exists))

    attendance_map: dict[tuple[int, str], dict] = {}
    for doc in attendance_docs:
        user_id = doc.get("user_id")
        day_value = doc.get("date")
        if user_id is None or not day_value:
            continue
        attendance_map[(int(user_id), str(day_value))] = doc

    rows: list[MonthlyAttendanceSummary] = []
    for student in students:
        student_id = int(student["id"])
        baseline_date = _parse_date_value(student.get("created_at")) or month_start
        effective_start = max(month_start, baseline_date)
        
        student_finalized_date = finalized_through_date
        if attendance_map.get((student_id, today_key)):
            student_finalized_date = max(finalized_through_date, min(today, month_end))
            
        effective_end = min(month_end, student_finalized_date)

        present_days = 0
        late_days = 0
        absent_days = 0

        if effective_end >= effective_start:
            for current_day in _iter_dates(effective_start, effective_end):
                record = attendance_map.get((student_id, current_day.isoformat()))
                status = str(record.get("status") if record else "Absent").strip().lower()
                if status == "present":
                    present_days += 1
                elif status == "late":
                    late_days += 1
                else:
                    absent_days += 1

        attended_days = present_days + late_days
        total_classes = present_days + late_days + absent_days
        attendance_percentage = round((attended_days / total_classes * 100) if total_classes else 0.0, 1)

        if total_classes == 0:
            status = "PENDING"
        elif attendance_percentage >= 90:
            status = "CONSISTENT"
        elif attendance_percentage >= 75:
            status = "MONITORED"
        else:
            status = "AT_RISK"

        rows.append(
            MonthlyAttendanceSummary(
                id=student_id,
                roll_number=student.get("roll_number"),
                full_name=student.get("full_name"),
                department=student.get("department"),
                attendance_percentage=attendance_percentage,
                classes_attended=attended_days,
                total_classes=total_classes,
                status=status,
            )
        )

    rows.sort(key=lambda row: (-row.attendance_percentage, row.full_name or "", row.id))
    return rows


async def _get_geo_policy(db: AsyncIOMotorDatabase) -> dict:
    policy = {
        "campus_lat": settings.campus_lat,
        "campus_lon": settings.campus_lon,
        "max_distance_km": settings.max_distance_km,
        "geofencing_enabled": settings.geofencing_enabled,
    }

    doc = await db.config.find_one({"_id": "global"})
    if doc:
        for key in policy:
            if doc.get(key) is not None:
                policy[key] = doc[key]

    return policy


async def get_student_attendance_stats(db: AsyncIOMotorDatabase, user_id: int) -> AttendanceStats:
    user = await db.users.find_one({"id": int(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    history: list[dict] = []
    cursor = db.attendance.find({"user_id": int(user_id)}).sort("date", -1)
    async for record in cursor:
        history.append(serialize_attendance(record))

    today = now_ist().date()
    start_date = _parse_date_value(user.get("created_at")) or today
    today_record_exists = any(str(record.get("date")) == today.isoformat() for record in history)
    through_date = _finalized_through_date(today_record_exists)

    if through_date < start_date:
        completed_days: list[datetime.date] = []
    else:
        completed_days = [start_date + timedelta(days=offset) for offset in range((through_date - start_date).days + 1)]

    history_map = {str(record.get("date")): record for record in history if record.get("date")}

    for record in history:
        date_str = str(record.get("date"))
        if not date_str:
            continue
        try:
            record_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if record_date > through_date and record_date not in completed_days:
                completed_days.append(record_date)
        except ValueError:
            pass

    present_days = 0
    late_days = 0
    absences = 0
    for current_day in completed_days:
        record = history_map.get(current_day.isoformat())
        status = str(record.get("status") if record else "Absent").strip().lower()
        if status == "present":
            present_days += 1
        elif status == "late":
            late_days += 1
        else:
            absences += 1

    attended_days = present_days + late_days
    marked_days = len(completed_days)
    extra_days = sum(1 for d in completed_days if d > through_date)
    pending_days = max(0, (today - through_date).days - extra_days)

    total_minutes = 0
    count = 0
    for record in history:
        if record.get("status") not in {"Present", "Late"}:
            continue
        try:
            hour, minute, _ = map(int, record["check_in"].split(":"))
        except Exception:
            continue
        total_minutes += hour * 60 + minute
        count += 1

    avg_check_in = "--:--"
    if count:
        avg_minutes = total_minutes // count
        avg_check_in = f"{avg_minutes // 60:02d}:{avg_minutes % 60:02d}"

    attendance_percentage = round((attended_days / marked_days * 100), 1) if marked_days > 0 else 0.0

    return AttendanceStats(
        present_days=present_days,
        late_days=late_days,
        attended_days=attended_days,
        absences=absences,
        marked_days=marked_days,
        pending_days=pending_days,
        calculation_start_date=start_date.isoformat(),
        calculation_through_date=through_date.isoformat(),
        avg_check_in=avg_check_in,
        attendance_percentage=attendance_percentage,
        history=[AttendanceOut.model_validate(item) for item in history],
    )


async def get_student_attendance_history(db: AsyncIOMotorDatabase, user_id: int) -> list[dict]:
    records = []
    cursor = db.attendance.find({"user_id": int(user_id)}).sort("date", -1)
    async for record in cursor:
        records.append(serialize_attendance(record))
    return records


def _attendance_status_from_time(moment=None) -> str:
    moment = moment or now_ist()
    if (moment.hour, moment.minute) > (settings.late_hour, settings.late_minute):
        return "Late"
    return "Present"


async def _insert_or_update_attendance(db: AsyncIOMotorDatabase, *, user: dict, marked_by_user_id: int, status: str, method: str, latitude: float | None, longitude: float | None) -> tuple[dict, bool]:
    today = date_key()
    now = now_ist()
    existing = await _get_today_attendance(db, user["id"])
    if existing:
        return serialize_attendance(existing), False

    record = {
        "user_id": user["id"],
        "date": today,
        "check_in": time_key(now),
        "status": status,
        "marked_by_user_id": marked_by_user_id,
        "method": method,
        "latitude": latitude,
        "longitude": longitude,
        "created_at": iso_ist(),
        "updated_at": iso_ist(),
    }
    record["id"] = await _next_id(db, "attendance")
    await db.attendance.insert_one(record)
    return record, True


async def mark_attendance_by_face(db: AsyncIOMotorDatabase, *, teacher: dict, image: str, latitude: float | None, longitude: float | None) -> dict:
    if not teacher.get("is_active"):
        raise HTTPException(status_code=403, detail="Account is deactivated")

    geo_policy = await _get_geo_policy(db)
    distance = None
    if geo_policy.get("geofencing_enabled"):
        if latitude is None or longitude is None:
            raise HTTPException(status_code=400, detail="Location access is required while campus geofencing is enabled.")

        allowed, distance = is_within_radius(
            latitude,
            longitude,
            float(geo_policy["campus_lat"]),
            float(geo_policy["campus_lon"]),
            float(geo_policy["max_distance_km"]),
        )
        if not allowed:
            raise HTTPException(status_code=400, detail=f"Attendance can only be marked within {float(geo_policy['max_distance_km']):g} km of campus")

    teacher_department = teacher.get("department")
    if not teacher_department:
        raise HTTPException(status_code=400, detail="Teacher department is not configured")

    # Extract all faces from the image
    candidates = await extract_multiple_encodings(image)
    if not candidates:
        raise HTTPException(status_code=400, detail="No faces detected in the image")

    # Fetch all active verified students in the teacher's department
    students = []
    cursor = db.users.find({"role": ROLE_STUDENT, "department": teacher_department, "is_active": True, "is_verified": True})
    async for user in cursor:
        students.append(user)

    # Match all detected faces against department students
    matches = await find_matches(candidates, students)
    if not matches:
        raise HTTPException(status_code=404, detail="No matching student faces found in your department")

    results = []
    status = _attendance_status_from_time()
    
    for match in matches:
        student = match["user"]
        saved, was_created = await _insert_or_update_attendance(
            db, 
            user=student, 
            marked_by_user_id=teacher["id"], 
            status=status, 
            method="face", 
            latitude=latitude, 
            longitude=longitude
        )
        results.append({
            "student_id": student["id"],
            "student_email": student["email"],
            "student_name": student.get("full_name"),
            "check_in": saved["check_in"],
            "status": saved["status"] if was_created else "Already Recorded"
        })

    return {
        "message": f"Attendance marked successfully for {len(results)} students",
        "marked_count": len(results),
        "students": results,
        "distance_km": distance,
    }


async def mark_attendance_manual(db: AsyncIOMotorDatabase, *, teacher: dict, student_id: int, status: str, latitude: float | None, longitude: float | None) -> dict:
    student = await db.users.find_one({"id": int(student_id), "role": ROLE_STUDENT, "department": teacher.get("department")})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found in your department")

    geo_policy = await _get_geo_policy(db)
    distance = None
    if geo_policy.get("geofencing_enabled"):
        if latitude is None or longitude is None:
            raise HTTPException(status_code=400, detail="Location access is required while campus geofencing is enabled.")

        allowed, distance = is_within_radius(
            latitude,
            longitude,
            float(geo_policy["campus_lat"]),
            float(geo_policy["campus_lon"]),
            float(geo_policy["max_distance_km"]),
        )
        if not allowed:
            raise HTTPException(status_code=400, detail=f"Attendance can only be marked within {float(geo_policy['max_distance_km']):g} km of campus")

    saved, was_created = await _insert_or_update_attendance(db, user=student, marked_by_user_id=teacher["id"], status=status.title(), method="manual", latitude=latitude, longitude=longitude)
    
    if not was_created:
        raise HTTPException(status_code=400, detail="Attendance already marked for this student today.")

    return {
        "message": "Attendance marked successfully",
        "student_id": student["id"],
        "student_email": student["email"],
        "student_name": student.get("full_name"),
        "check_in": saved["check_in"],
        "status": saved["status"],
        "distance_km": distance,
    }


async def get_teacher_department_students(db: AsyncIOMotorDatabase, department: str, unmarked_only: bool = False) -> list[dict]:
    students = []
    cursor = db.users.find({"role": ROLE_STUDENT, "department": department, "is_active": True}).sort("roll_number", 1)
    async for user in cursor:
        if unmarked_only:
            record = await _get_today_attendance(db, user["id"])
            if record:
                continue
        students.append(user)
    return students


async def get_teacher_today_rows(db: AsyncIOMotorDatabase, department: str) -> list[TeacherAttendanceRow]:
    students = await get_teacher_department_students(db, department)
    rows = []
    day_finalized = _attendance_day_completed(False)
    marker_cache: dict[int, str] = {}

    async def resolve_marker_name(marker_id: int | None) -> str | None:
        if marker_id is None:
            return None
        if marker_id in marker_cache:
            return marker_cache[marker_id]

        marker = await db.users.find_one({"id": int(marker_id)})
        marker_name = None
        if marker:
            marker_name = marker.get("full_name") or marker.get("email") or f"User #{marker_id}"
        marker_cache[marker_id] = marker_name
        return marker_name

    for student in students:
        record = await db.attendance.find_one({"user_id": student["id"], "date": date_key()})
        marked_by_user_id = record.get("marked_by_user_id") if record else None
        if record:
            status = record.get("status") or "Pending"
            check_in = record.get("check_in")
            method = record.get("method")
        else:
            status = "Absent" if day_finalized else "Pending"
            check_in = None
            method = None
        rows.append(
            TeacherAttendanceRow(
                id=student["id"],
                roll_number=student.get("roll_number"),
                full_name=student.get("full_name"),
                email=student["email"],
                department=student.get("department"),
                date=date_key(),
                status=status,
                check_in=check_in,
                method=method,
                marked_by_user_id=marked_by_user_id,
                marked_by_name=await resolve_marker_name(marked_by_user_id),
            )
        )
    return rows


async def get_teacher_stats(db: AsyncIOMotorDatabase, department: str) -> TeacherStats:
    students = await get_teacher_department_students(db, department)
    today_records = await db.attendance.find({"date": date_key()}).to_list(length=None)
    by_user = {record["user_id"]: record for record in today_records}
    day_finalized = _attendance_day_completed(bool(today_records))

    present = late = absent = not_marked = 0
    for student in students:
        record = by_user.get(student["id"])
        if not record:
            if day_finalized:
                absent += 1
            else:
                not_marked += 1
        elif record.get("status") == "Present":
            present += 1
        elif record.get("status") == "Late":
            late += 1
        elif record.get("status") == "Absent":
            absent += 1
        else:
            if day_finalized:
                absent += 1
            else:
                not_marked += 1

    return TeacherStats(total_students=len(students), present=present, late=late, absent=absent, not_marked=not_marked, attendance_finalized=day_finalized)


async def send_absent_notifications(db: AsyncIOMotorDatabase, department: str) -> dict:
    today = date_key()
    if not _attendance_day_completed(False):
        return {
            "status": "not_finalized",
            "count": 0,
            "message": (
                "Attendance is not finalized yet. Absent notifications will be available after "
                f"{settings.absent_notice_hour:02d}:{settings.absent_notice_minute:02d}."
            ),
        }

    students = await get_teacher_department_students(db, department)
    attendance_today = await db.attendance.find({"date": today}).to_list(length=None)
    attended_ids = {item["user_id"] for item in attendance_today}
    absent_students = [student for student in students if student["id"] not in attended_ids]

    if not absent_students:
        return {
            "status": "no_absent",
            "count": 0,
            "message": "No absent students found in your department today.",
        }

    claim_filter = {"date": today, "department": department}
    claim_doc = {
        "id": await _next_id(db, "absent_notification_claims"),
        "date": today,
        "department": department,
        "status": "processing",
        "count": 0,
        "sent_student_ids": [],
        "created_at": iso_ist(),
        "updated_at": iso_ist(),
    }

    claim_record = claim_doc
    pending_students = absent_students
    try:
        await db.absent_notification_claims.insert_one(claim_doc)
    except DuplicateKeyError:
        existing = await db.absent_notification_claims.find_one(claim_filter)
        if existing and existing.get("status") == "sent":
            return {
                "status": "already_sent",
                "count": int(existing.get("count") or 0),
                "message": "Absent notifications were already sent today for your department.",
            }
        if existing and existing.get("status") == "processing":
            return {
                "status": "in_progress",
                "count": int(existing.get("count") or 0),
                "message": "Absent notifications are already being processed for your department.",
            }
        if existing and existing.get("status") == "failed":
            resumed = await db.absent_notification_claims.find_one_and_update(
                {**claim_filter, "status": "failed"},
                {"$set": {"status": "processing", "updated_at": iso_ist()}},
                return_document=ReturnDocument.AFTER,
            )
            if not resumed:
                return {
                    "status": "in_progress",
                    "count": int(existing.get("count") or 0),
                    "message": "Absent notifications are already being processed for your department.",
                }
            claim_record = resumed
            sent_ids = set(resumed.get("sent_student_ids") or [])
            pending_students = [student for student in absent_students if student["id"] not in sent_ids]
            if not pending_students:
                await db.absent_notification_claims.update_one(
                    claim_filter,
                    {"$set": {"status": "sent", "updated_at": iso_ist(), "count": int(resumed.get("count") or 0)}},
                )
                try:
                    await db.security_logs.insert_one(
                        {
                            "id": await _next_id(db, "security_logs"),
                            "event_type": "ABSENT_EMAIL_SENT",
                            "severity": "info",
                            "details": f"Absent notifications sent for {department}",
                            "metadata": {"date": today, "department": department, "count": int(resumed.get("count") or 0)},
                            "created_at": iso_ist(),
                        }
                    )
                except Exception:
                    pass
                return {
                    "status": "sent",
                    "count": int(resumed.get("count") or 0),
                    "message": f"Successfully dispatched alerts to {int(resumed.get('count') or 0)} students.",
                }
        else:
            return {
                "status": "in_progress",
                "count": int(existing.get("count") or 0) if existing else 0,
                "message": "Absent notifications are already being processed for your department.",
            }

    sent_count = 0
    try:
        for student in pending_students:
            delivered = await send_absent_notice(student["email"], student.get("full_name") or student["email"], today)
            if not delivered:
                raise RuntimeError(_absent_mail_failure_message())
            sent_count += 1
            await db.absent_notification_claims.update_one(
                claim_filter,
                {
                    "$set": {"updated_at": iso_ist(), "count": sent_count},
                    "$addToSet": {"sent_student_ids": student["id"]},
                },
            )
    except Exception as exc:
        failure_message = str(exc) or _absent_mail_failure_message()
        await db.absent_notification_claims.update_one(
            claim_filter,
            {"$set": {"status": "failed", "updated_at": iso_ist(), "count": sent_count}},
        )
        return {
            "status": "failed",
            "count": sent_count,
            "message": failure_message,
        }

    await db.absent_notification_claims.update_one(
        claim_filter,
        {"$set": {"status": "sent", "updated_at": iso_ist(), "count": sent_count}},
    )
    try:
        await db.security_logs.insert_one(
            {
                "id": await _next_id(db, "security_logs"),
                "event_type": "ABSENT_EMAIL_SENT",
                "severity": "info",
                "details": f"Absent notifications sent for {department}",
                "metadata": {"date": today, "department": department, "count": sent_count},
                "created_at": iso_ist(),
            }
        )
    except Exception:
        pass

    return {
        "status": "sent",
        "count": sent_count,
        "message": f"Successfully dispatched alerts to {sent_count} students.",
    }


async def get_all_attendance_report_data(db: AsyncIOMotorDatabase, date_str: str | None = None) -> list[dict]:
    """
    Fetches system-wide attendance report data for a specific date.
    """
    from ..models import ROLE_STUDENT
    
    if not date_str:
        date_str = date_key()

    report_date = _parse_date_value(date_str)
    if not report_date:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")
    
    # Get all active students
    students = await db.users.find({"role": ROLE_STUDENT, "is_active": True}).to_list(length=None)
    
    # Get attendance for that day
    attendance = await db.attendance.find({"date": date_str}).to_list(length=None)
    attendance_map = {item["user_id"]: item for item in attendance}
    today = now_ist().date()
    day_finalized = report_date < today or (report_date == today and _attendance_day_completed(bool(attendance)))
    
    report_data = []
    for student in students:
        record = attendance_map.get(student["id"])
        if record:
            status = record.get("status")
            check_in = record.get("check_in")
            method = record.get("method")
        elif day_finalized:
            status = "Absent"
            check_in = "--:--"
            method = "System"
        else:
            status = "Pending"
            check_in = "--:--"
            method = "System"
        report_data.append({
            "roll_number": student.get("roll_number", "---"),
            "full_name": student.get("full_name"),
            "email": student["email"],
            "department": student.get("department", "Unknown"),
            "status": status,
            "check_in": check_in,
            "method": method,
            "date": date_str
        })
    return report_data


async def get_admin_stats(db: AsyncIOMotorDatabase) -> dict:
    total_users = await db.users.count_documents({})
    total_students = await db.users.count_documents({"role": ROLE_STUDENT})
    today = date_key()
    today_records = await db.attendance.find({"date": today}).to_list(length=None)
    present_today = sum(1 for record in today_records if str(record.get("status")) in {"Present", "Late"})
    explicit_absent_today = sum(1 for record in today_records if str(record.get("status")) == "Absent")
    day_finalized = _attendance_day_completed(bool(today_records))
    absent_today = max(0, total_students - present_today) if day_finalized else explicit_absent_today
    attendance_percentage = round((present_today / total_students * 100), 1) if total_students else 0.0
    return {
        "total_users": total_users, 
        "total_students": total_students,
        "present_today": present_today, 
        "absent_today": absent_today,
        "attendance_percentage": attendance_percentage,
        "system_status": "Online"
    }


async def get_recent_attendance_logs(db: AsyncIOMotorDatabase, limit: int = 10) -> list[dict]:
    cursor = db.attendance.find({}).sort("created_at", -1).limit(limit)
    logs = []
    async for record in cursor:
        user = await db.users.find_one({"id": record["user_id"]})
        logs.append({
            "user_name": user.get("full_name") if user else "Unknown User",
            "department": user.get("department") if user else "N/A",
            "timestamp": record["check_in"],
            "status": record["status"]
        })
    return logs
