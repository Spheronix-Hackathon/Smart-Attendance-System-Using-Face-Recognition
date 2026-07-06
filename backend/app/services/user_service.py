from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from ..config import settings
from ..models import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER, VALID_ROLES
from ..schemas import AdminAccountCreate, AdminUserUpdateRequest, TeacherCreate, UserCreate, UserProfileUpdate
from ..utils.security import create_access_token, hash_password, otp_hash, otp_salt, verify_password
from ..utils.time import iso_ist, now_ist


def _normalize_role(role: str | None, is_admin: bool = False) -> str:
    if is_admin:
        return ROLE_ADMIN
    value = (role or ROLE_STUDENT).strip().lower()
    return value if value in VALID_ROLES else ROLE_STUDENT


def serialize_user(user: dict):
    if not user:
        return user
    user = dict(user)
    user.pop("_id", None)
    return user


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> dict | None:
    return await db.users.find_one({"email": email.lower().strip()})


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: int) -> dict | None:
    return await db.users.find_one({"id": int(user_id)})


async def require_admin_password(admin_user: dict, password: str) -> None:
    if not verify_password(password, admin_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Admin password confirmation failed")


async def create_student_user(db: AsyncIOMotorDatabase, payload: UserCreate, face_encoding: list[float], otp: str) -> dict:
    user_seq = await db.counters.find_one_and_update(
        {"_id": "users"}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    doc = {
        "id": int(user_seq["seq"]),
        "full_name": payload.full_name,
        "email": payload.email.lower().strip(),
        "roll_number": payload.roll_number.strip(),
        "hashed_password": hash_password(payload.password),
        "profile_picture": None,
        "is_active": True,
        "is_verified": False,
        "is_admin": False,
        "role": ROLE_STUDENT,
        "department": payload.department.strip() if payload.department else None,
        "otp_hash": otp_hash(otp, otp_salt()),
        "otp_expires_at": (now_ist() + timedelta(minutes=10)).isoformat(),
        "face_encoding": face_encoding,
        "face_image": payload.face_image,
        "created_at": iso_ist(),
        "updated_at": iso_ist(),
    }
    await db.users.insert_one(doc)
    return doc


async def create_teacher_user(db: AsyncIOMotorDatabase, payload: TeacherCreate) -> dict:
    user_seq = await db.counters.find_one_and_update(
        {"_id": "users"}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    doc = {
        "id": int(user_seq["seq"]),
        "full_name": payload.full_name,
        "email": payload.email.lower().strip(),
        "roll_number": payload.employee_id.strip(),
        "hashed_password": hash_password(payload.password),
        "profile_picture": None,
        "is_active": True,
        "is_verified": True,
        "is_admin": False,
        "role": ROLE_TEACHER,
        "department": payload.department.strip(),
        "face_encoding": [],
        "face_image": None,
        "created_at": iso_ist(),
        "updated_at": iso_ist(),
    }
    await db.users.insert_one(doc)
    return doc


async def create_admin_user(db: AsyncIOMotorDatabase, payload: AdminAccountCreate) -> dict:
    user_seq = await db.counters.find_one_and_update(
        {"_id": "users"}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    doc = {
        "id": int(user_seq["seq"]),
        "full_name": payload.full_name,
        "email": payload.email.lower().strip(),
        "roll_number": payload.identifier.strip(),
        "hashed_password": hash_password(payload.password),
        "profile_picture": None,
        "is_active": True,
        "is_verified": True,
        "is_admin": True,
        "role": ROLE_ADMIN,
        "department": payload.department.strip() if payload.department else "Administration",
        "face_encoding": [],
        "face_image": None,
        "created_at": iso_ist(),
        "updated_at": iso_ist(),
    }
    await db.users.insert_one(doc)
    return doc


async def create_access_token_for_user(user: dict) -> str:
    return create_access_token({"sub": user["email"]}, timedelta(minutes=settings.access_token_expire_minutes))


async def verify_student_login(user: dict, password: str) -> None:
    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")


async def update_password(db: AsyncIOMotorDatabase, user: dict, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"hashed_password": hash_password(new_password), "updated_at": iso_ist()}},
    )


async def admin_update_user(db: AsyncIOMotorDatabase, target: dict, payload: AdminUserUpdateRequest) -> dict:
    updates: dict = {}
    if payload.full_name is not None:
        updates["full_name"] = payload.full_name
    if payload.email is not None:
        updates["email"] = payload.email.lower().strip()
    if payload.roll_number is not None:
        updates["roll_number"] = payload.roll_number.strip()
    if payload.role is not None:
        updates["role"] = _normalize_role(payload.role)
        updates["is_admin"] = updates["role"] == ROLE_ADMIN
    if payload.department is not None:
        updates["department"] = payload.department.strip()
    if not updates:
        raise HTTPException(status_code=400, detail="No changes provided")
    updates["updated_at"] = iso_ist()
    await db.users.update_one({"id": target["id"]}, {"$set": updates})
    return updates


async def set_active_status(db: AsyncIOMotorDatabase, user_id: int, is_active: bool) -> None:
    updates = {"is_active": is_active, "updated_at": iso_ist()}
    if is_active:
        updates["blocked_reason"] = None
    await db.users.update_one({"id": int(user_id)}, {"$set": updates})


async def reset_password(db: AsyncIOMotorDatabase, user: dict, temp_password: str = "SASUFR") -> None:
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"hashed_password": hash_password(temp_password), "updated_at": iso_ist()}},
    )


async def delete_user(db: AsyncIOMotorDatabase, user_id: int) -> None:
    await db.users.delete_one({"id": int(user_id)})
    await db.attendance.delete_many({"user_id": int(user_id)})


async def mark_verified(db: AsyncIOMotorDatabase, user: dict) -> None:
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"is_verified": True, "otp_hash": None, "otp_expires_at": None, "updated_at": iso_ist()}},
    )


async def resend_otp(db: AsyncIOMotorDatabase, user: dict, otp: str) -> None:
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"otp_hash": otp_hash(otp, otp_salt()), "otp_expires_at": (now_ist() + timedelta(minutes=10)).isoformat(), "updated_at": iso_ist()}},
    )
async def update_user_profile(db: AsyncIOMotorDatabase, user_id: int, payload: UserProfileUpdate) -> dict:
    updates: dict = {}
    if payload.full_name is not None:
        updates["full_name"] = payload.full_name
    if payload.department is not None:
        updates["department"] = payload.department.strip()
    
    if payload.preferences is not None:
        # Load existing user and merge preferences to prevent data loss
        user = await db.users.find_one({"id": int(user_id)})
        current_prefs = user.get("preferences", {})
        # Deep merge/Update with new preferences
        current_prefs.update(payload.preferences)
        updates["preferences"] = current_prefs

    if not updates:
        raise HTTPException(status_code=400, detail="No changes provided")
    
    updates["updated_at"] = iso_ist()
    await db.users.update_one({"id": int(user_id)}, {"$set": updates})
    return updates
