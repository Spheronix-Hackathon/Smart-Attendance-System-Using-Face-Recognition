from __future__ import annotations

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.mongo import database, ensure_indexes, next_sequence
from app.services.user_service import get_user_by_email
from app.utils.security import hash_password
from app.utils.time import iso_ist

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "hr@spheronixtechnology.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Spheronix@123$")
ADMIN_ROLL = os.getenv("ADMIN_ROLL", "admin")
ADMIN_NAME = os.getenv("ADMIN_NAME", "System Admin")


async def create_admin() -> None:
    await ensure_indexes()
    existing = await get_user_by_email(database, ADMIN_EMAIL)
    if existing:
        await database.users.update_one(
            {"id": existing["id"]},
            {
                "$set": {
                    "full_name": ADMIN_NAME,
                    "roll_number": ADMIN_ROLL,
                    "hashed_password": hash_password(ADMIN_PASSWORD),
                    "is_admin": True,
                    "role": "admin",
                    "is_active": True,
                    "is_verified": True,
                    "updated_at": iso_ist(),
                }
            },
        )
        print(f"Admin account updated: {ADMIN_EMAIL}")
        return

    existing_roll = await database.users.find_one({"roll_number": ADMIN_ROLL})
    if existing_roll:
        await database.users.update_one(
            {"id": existing_roll["id"]},
            {
                "$set": {
                    "full_name": ADMIN_NAME,
                    "email": ADMIN_EMAIL,
                    "hashed_password": hash_password(ADMIN_PASSWORD),
                    "is_admin": True,
                    "role": "admin",
                    "is_active": True,
                    "is_verified": True,
                    "updated_at": iso_ist(),
                }
            },
        )
        print(f"Promoted existing roll to admin: {ADMIN_EMAIL}")
        return

    user_id = await next_sequence("users")
    await database.users.insert_one(
        {
            "id": user_id,
            "full_name": ADMIN_NAME,
            "email": ADMIN_EMAIL,
            "roll_number": ADMIN_ROLL,
            "hashed_password": hash_password(ADMIN_PASSWORD),
            "profile_picture": None,
            "is_active": True,
            "is_verified": True,
            "is_admin": True,
            "role": "admin",
            "department": None,
            "face_encoding": [],
            "face_image": None,
            "created_at": iso_ist(),
            "updated_at": iso_ist(),
        }
    )
    print("Admin account created successfully!")
    print(f"Email: {ADMIN_EMAIL}")
    print(f"Password: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(create_admin())
