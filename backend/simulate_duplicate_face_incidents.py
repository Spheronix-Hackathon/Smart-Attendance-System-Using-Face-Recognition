from __future__ import annotations

import asyncio
import os
import random
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.mongo import database, ensure_indexes
from app.services.security_service import log_security_event
from app.utils.time import iso_ist


INCIDENTS_TO_CREATE = 10


def _face_vector(seed: int, size: int = 128) -> list[float]:
    rng = random.Random(seed)
    return [round(rng.uniform(-0.4, 0.4), 6) for _ in range(size)]


def _snapshot(user: dict, *, is_active: bool | None = None, blocked_reason: str | None = None) -> dict:
    data = {
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
    data["is_active"] = bool(user.get("is_active", False)) if is_active is None else bool(is_active)
    if blocked_reason is not None:
        data["blocked_reason"] = blocked_reason
    elif user.get("blocked_reason"):
        data["blocked_reason"] = user.get("blocked_reason")
    return data


async def simulate_incidents() -> None:
    await ensure_indexes()

    students = await database.users.find(
        {
            "role": "student",
            "is_active": True,
            "roll_number": {"$regex": "^STU-"},
        },
        {
            "_id": 0,
            "id": 1,
            "full_name": 1,
            "email": 1,
            "roll_number": 1,
            "department": 1,
            "role": 1,
            "is_verified": 1,
            "is_active": 1,
            "created_at": 1,
            "updated_at": 1,
        },
    ).sort("id", 1).to_list(length=None)

    if len(students) < INCIDENTS_TO_CREATE * 2:
        raise RuntimeError("Not enough active seeded students to simulate duplicate incidents")

    created = 0
    for idx in range(INCIDENTS_TO_CREATE):
        old_user = students[idx * 2]
        present_user = students[idx * 2 + 1]
        vector = _face_vector(seed=20260410 + idx)

        await database.users.update_one(
            {"id": int(old_user["id"])},
            {
                "$set": {
                    "face_encoding": vector,
                    "is_active": False,
                    "blocked_reason": "BIOMETRIC_DUPLICATION_ATTEMPT",
                    "updated_at": iso_ist(),
                }
            },
        )

        await database.users.update_one(
            {"id": int(present_user["id"])},
            {
                "$set": {
                    "face_encoding": vector,
                    "updated_at": iso_ist(),
                }
            },
        )

        await log_security_event(
            database,
            event_type="DUPLICATE_FACE_DETECTED",
            severity="critical",
            details=(
                f"Registration attempt for {present_user['email']} blocked due to biometric match "
                f"with existing user {old_user['email']}. Existing account suspended and the new "
                "submission queued for administrative review."
            ),
            metadata={
                "duplicate_user_id": int(old_user["id"]),
                "duplicate_email": old_user["email"],
                "attempted_email": present_user["email"],
                "attempted_roll_number": present_user.get("roll_number"),
                "attempted_department": present_user.get("department"),
                "match_distance": round(0.0325 + idx * 0.0041, 4),
                "old_account": _snapshot(old_user, is_active=False, blocked_reason="BIOMETRIC_DUPLICATION_ATTEMPT"),
                "present_account": _snapshot(present_user, is_active=False),
            },
            target_user_id=int(old_user["id"]),
        )

        created += 1
        print(
            f"Incident #{created}: blocked={old_user['email']} duplicate_attempt={present_user['email']}"
        )

    blocked_count = await database.users.count_documents({
        "roll_number": {"$regex": "^STU-"},
        "blocked_reason": "BIOMETRIC_DUPLICATION_ATTEMPT",
        "is_active": False,
    })
    duplicate_logs = await database.security_logs.count_documents({"event_type": "DUPLICATE_FACE_DETECTED"})

    print("\nSimulation complete")
    print(f"Incidents created this run: {created}")
    print(f"Currently blocked (duplicate reason): {blocked_count}")
    print(f"Total DUPLICATE_FACE_DETECTED logs: {duplicate_logs}")


if __name__ == "__main__":
    asyncio.run(simulate_incidents())