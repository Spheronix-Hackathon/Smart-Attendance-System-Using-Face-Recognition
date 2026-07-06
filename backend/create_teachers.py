from __future__ import annotations

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.mongo import database, ensure_indexes, next_sequence
from app.services.user_service import get_user_by_email
from app.utils.security import hash_password
from app.utils.time import iso_ist

TEACHERS = [
    {
        "full_name": "M Kiran Kumar",
        "email": "Kiranmangala2002@gmail.com",
        "employee_id": "SPX-COO-001",
        "department": "COO",
        "password": "Bunny@2005",
    },
]


async def upsert_teacher(teacher: dict) -> None:
    existing_email = await get_user_by_email(database, teacher["email"])
    existing_roll = await database.users.find_one({"roll_number": teacher["employee_id"]})

    if existing_email and existing_roll and existing_email["id"] != existing_roll["id"]:
        print(f"Skipped {teacher['email']}: email and employee-id conflict")
        return

    target = existing_email or existing_roll
    if target:
        await database.users.update_one(
            {"id": target["id"]},
            {
                "$set": {
                    "full_name": teacher["full_name"],
                    "email": teacher["email"],
                    "roll_number": teacher["employee_id"],
                    "hashed_password": hash_password(teacher["password"]),
                    "department": teacher["department"],
                    "role": "teacher",
                    "is_admin": False,
                    "is_active": True,
                    "is_verified": True,
                    "updated_at": iso_ist(),
                }
            },
        )
        print(f"Updated teacher account: {teacher['email']}")
        return

    user_id = await next_sequence("users")
    await database.users.insert_one(
        {
            "id": user_id,
            "full_name": teacher["full_name"],
            "email": teacher["email"],
            "roll_number": teacher["employee_id"],
            "hashed_password": hash_password(teacher["password"]),
            "profile_picture": None,
            "is_active": True,
            "is_verified": True,
            "is_admin": False,
            "role": "teacher",
            "department": teacher["department"],
            "face_encoding": [],
            "face_image": None,
            "created_at": iso_ist(),
            "updated_at": iso_ist(),
        }
    )
    print(f"Created teacher account: {teacher['email']}")


async def create_teachers() -> None:
    await ensure_indexes()
    for teacher in TEACHERS:
        await upsert_teacher(teacher)

    print("Teacher seed complete")
    for teacher in TEACHERS:
        print(f"- {teacher['full_name']} | {teacher['email']} | {teacher['department']} | {teacher['employee_id']}")


if __name__ == "__main__":
    asyncio.run(create_teachers())
