from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from ..utils.time import iso_ist


async def next_security_id(db: AsyncIOMotorDatabase) -> int:
    result = await db.counters.find_one_and_update(
        {"_id": "security_logs"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(result["seq"])


async def log_security_event(
    db: AsyncIOMotorDatabase,
    *,
    event_type: str,
    severity: str,
    details: str,
    metadata: dict | None = None,
    user_id: int | None = None,
    target_user_id: int | None = None,
    admin_user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict:
    doc = {
        "id": await next_security_id(db),
        "event_type": event_type,
        "severity": severity,
        "details": details,
        "metadata": metadata or {},
        "user_id": user_id,
        "target_user_id": target_user_id,
        "admin_user_id": admin_user_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "created_at": iso_ist(),
    }
    await db.security_logs.insert_one(doc)
    return doc


async def get_security_logs(db: AsyncIOMotorDatabase, limit: int = 20) -> list[dict]:
    cursor = db.security_logs.find({}).sort("created_at", -1).limit(limit)
    logs: list[dict] = []
    async for log in cursor:
        log["_id"] = str(log["_id"])
        logs.append(log)
    return logs
