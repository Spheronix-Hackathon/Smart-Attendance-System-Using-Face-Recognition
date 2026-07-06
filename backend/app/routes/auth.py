from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database.mongo import get_database
from ..dependencies import get_current_user
from ..models import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER
from ..schemas import ChangePasswordRequest, LoginRequest, OTPRequest, OTPVerifyRequest, Token, UserCreate, UserOut, UserProfileUpdate
from ..services.attendance_service import serialize_attendance
from ..services.email_service import get_last_mail_error, send_password_changed, send_registration_success, send_otp_email
from ..services.face_service import extract_encoding, find_best_match
from ..services.security_service import log_security_event
from ..services.user_service import (
    create_access_token_for_user,
    create_student_user,
    get_user_by_email,
    mark_verified,
    resend_otp,
    serialize_user,
    verify_student_login,
    update_password,
    update_user_profile,
)
from ..utils.security import generate_otp, otp_hash, otp_salt, verify_otp as verify_otp_hash
from ..utils.time import iso_ist, now_ist


router = APIRouter(tags=["auth"])


def _security_account_snapshot(user: dict, *, is_active: bool | None = None, blocked_reason: str | None = None) -> dict:
    snapshot = {
        "id": user.get("id"),
        "full_name": user.get("full_name"),
        "email": user.get("email"),
        "roll_number": user.get("roll_number"),
        "department": user.get("department"),
        "role": user.get("role"),
        "is_verified": bool(user.get("is_verified", False)),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }
    if is_active is not None:
        snapshot["is_active"] = bool(is_active)
    elif "is_active" in user:
        snapshot["is_active"] = bool(user.get("is_active", False))
    if blocked_reason is not None:
        snapshot["blocked_reason"] = blocked_reason
    elif user.get("blocked_reason"):
        snapshot["blocked_reason"] = user.get("blocked_reason")
    return snapshot


@router.post("/register")
async def register(
    payload: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    email = payload.email.lower().strip()
    if not email.endswith("@gmail.com"):
        raise HTTPException(status_code=400, detail="Only @gmail.com addresses are permitted for registration.")
        
    roll_number = payload.roll_number.strip()

    if await get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already registered")

    if await db.users.find_one({"roll_number": roll_number}):
        raise HTTPException(status_code=400, detail="Roll number already registered")

    if not payload.department or not payload.department.strip():
        raise HTTPException(status_code=400, detail="Department is required")

    face_encoding = await extract_encoding(payload.face_image)
    existing_faces = []
    cursor = db.users.find({"face_encoding": {"$exists": True, "$ne": []}, "is_active": True})
    async for user in cursor:
        existing_faces.append(user)

    duplicate = await find_best_match(face_encoding, existing_faces)
    if duplicate:
        target = duplicate["user"]
        target_snapshot = _security_account_snapshot(target, is_active=False, blocked_reason="BIOMETRIC_DUPLICATION_ATTEMPT")
        attempted_snapshot = {
            "full_name": payload.full_name,
            "email": email,
            "roll_number": roll_number,
            "department": payload.department.strip(),
            "role": ROLE_STUDENT,
            "is_active": False,
            "is_verified": False,
        }
        # Double-Block Action: deactivating existing account and rejecting new one
        await db.users.update_one(
            {"id": target["id"]}, 
            {"$set": {"is_active": False, "blocked_reason": "BIOMETRIC_DUPLICATION_ATTEMPT", "updated_at": iso_ist()}}
        )
        await log_security_event(
            db,
            event_type="DUPLICATE_FACE_DETECTED",
            severity="critical",
            details=f"Registration attempt for {email} blocked due to biometric match with existing user {target['email']}. Existing account suspended and the new submission queued for administrative review.",
            metadata={
                "duplicate_user_id": target["id"],
                "duplicate_email": target["email"],
                "attempted_email": email,
                "match_distance": round(float(duplicate.get("distance", 0.0)), 4),
                "old_account": target_snapshot,
                "present_account": attempted_snapshot,
            },
            target_user_id=target["id"],
            ip_address=(request.client.host if request and request.client else None),
            user_agent=(request.headers.get("user-agent") if request else None),
        )
        raise HTTPException(status_code=400, detail="Biometric duplication detected. The existing account has been suspended for security verification, and this registration terminal has been locked. Only a system administrator can authorize reactivation.")

    otp = generate_otp()
    await create_student_user(db, payload, face_encoding, otp)
    # Send directly and fail fast if SMTP delivery is unavailable.
    otp_sent = await send_otp_email(email, otp)
    if not otp_sent:
        mail_error = get_last_mail_error()
        if mail_error == "quota_exceeded":
            raise HTTPException(
                status_code=503,
                detail="Gmail daily sending limit exceeded. This is a rolling 24-hour quota, so the sender account must wait until the limit resets.",
            )
        raise HTTPException(
            status_code=503,
            detail="Unable to deliver verification email right now. Please try again in a few minutes.",
        )
    await log_security_event(
        db,
        event_type="STUDENT_REGISTERED_PENDING_OTP",
        severity="info",
        details=f"Registration created for {email}",
        metadata={"email": email, "roll_number": roll_number},
        ip_address=(request.client.host if request and request.client else None),
        user_agent=(request.headers.get("user-agent") if request else None),
    )
    return {"message": "Registration successful. Please enter the verification code sent to your email address to complete the process."}


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    user = await get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Your account has been deactivated. Please contact the system administrator for assistance.")

    await verify_student_login(user, payload.password)

    if not user.get("is_verified", False):
        raise HTTPException(status_code=400, detail="Account verification is required. Please verify your email address to proceed.")

    token = await create_access_token_for_user(user)
    await db.users.update_one({"id": user["id"]}, {"$set": {"last_login_at": iso_ist(), "updated_at": iso_ist()}})
    return Token(access_token=token)


@router.post("/verify-otp")
async def verify_otp(
    payload: OTPVerifyRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user = await get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="Account not found.")

    otp_hash_value = user.get("otp_hash")
    if not otp_hash_value:
        raise HTTPException(status_code=400, detail="Verification code is invalid or has already been used.")

    expires_at = user.get("otp_expires_at")
    if expires_at:
        try:
            expires_dt = datetime.fromisoformat(expires_at)
        except Exception:
            expires_dt = None
        if expires_dt and now_ist() > expires_dt:
            raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new code.")

    if not verify_otp_hash(payload.otp, otp_salt(), otp_hash_value):
        raise HTTPException(status_code=400, detail="The verification code entered is incorrect.")

    await mark_verified(db, user)
    background_tasks.add_task(send_registration_success, user["email"])
    await log_security_event(
        db,
        event_type="EMAIL_VERIFIED",
        severity="info",
        details=f"Email verified for {user['email']}",
        user_id=user["id"],
        ip_address=(request.client.host if request and request.client else None),
        user_agent=(request.headers.get("user-agent") if request else None),
    )
    return {"message": "Verification successful"}


@router.post("/resend-otp")
async def resend_otp_endpoint(
    payload: OTPRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user = await get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("is_verified"):
        return {"message": "Account is already verified. Please login instead of requesting a new OTP.", "already_verified": True}

    otp = generate_otp()
    await resend_otp(db, user, otp)
    otp_sent = await send_otp_email(user["email"], otp)
    if not otp_sent:
        mail_error = get_last_mail_error()
        if mail_error == "quota_exceeded":
            raise HTTPException(
                status_code=503,
                detail="Gmail daily sending limit exceeded. This is a rolling 24-hour quota, so the sender account must wait until the limit resets.",
            )
        raise HTTPException(
            status_code=503,
            detail="Unable to deliver verification email right now. Please try again in a few minutes.",
        )
    return {"message": "Verification code has been resent to your email address."}


@router.get("/users/me", response_model=UserOut)
async def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/users/me/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    await update_password(db, current_user, payload.current_password, payload.new_password)
    background_tasks.add_task(send_password_changed, current_user["email"])
    await log_security_event(
        db,
        event_type="PASSWORD_CHANGED",
        severity="info",
        details=f"Password changed for {current_user['email']}",
        user_id=current_user["id"],
        ip_address=(request.client.host if request and request.client else None),
        user_agent=(request.headers.get("user-agent") if request else None),
    )
    return {"message": "Password updated successfully"}


@router.patch("/users/me")
async def update_current_user_profile(
    payload: UserProfileUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    await update_user_profile(db, current_user.get("id"), payload)
    return {"message": "Profile updated successfully"}
