from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, ReturnDocument

from ..config import settings


client = AsyncIOMotorClient(settings.mongodb_uri)
database: AsyncIOMotorDatabase = client[settings.mongodb_db]


async def get_database() -> AsyncIOMotorDatabase:
    return database


async def _sync_counter_to_collection_max(collection_name: str) -> None:
    collection = getattr(database, collection_name)
    latest = await collection.find_one({"id": {"$exists": True, "$ne": None}}, sort=[("id", -1)])
    if not latest:
        return

    current = await database.counters.find_one({"_id": collection_name})
    latest_id = int(latest["id"])
    if current is None or int(current.get("seq", 0)) < latest_id:
        await database.counters.update_one(
            {"_id": collection_name},
            {"$set": {"seq": latest_id}},
            upsert=True,
        )


async def _backfill_missing_ids(collection_name: str) -> None:
    collection = getattr(database, collection_name)
    cursor = collection.find({"$or": [{"id": {"$exists": False}}, {"id": None}]})
    async for document in cursor:
        next_id = await next_sequence(collection_name)
        await collection.update_one({"_id": document["_id"]}, {"$set": {"id": next_id}})


async def ensure_indexes() -> None:
    for collection_name in ("users", "attendance", "security_logs"):
        await _sync_counter_to_collection_max(collection_name)
        await _backfill_missing_ids(collection_name)

    await database.users.create_index([("id", ASCENDING)], unique=True)
    await database.users.create_index([("email", ASCENDING)], unique=True)
    await database.users.create_index([("roll_number", ASCENDING)], unique=True)
    await database.users.create_index([("role", ASCENDING), ("department", ASCENDING)])
    await database.users.create_index([("is_active", ASCENDING), ("is_verified", ASCENDING)])
    await database.attendance.create_index([("id", ASCENDING)], unique=True)
    await database.attendance.create_index([("user_id", ASCENDING), ("date", ASCENDING)], unique=True)
    await database.security_logs.create_index([("id", ASCENDING)], unique=True)
    await database.security_logs.create_index([("created_at", ASCENDING)])
    await database.absent_notification_claims.create_index([("id", ASCENDING)], unique=True)
    await database.absent_notification_claims.create_index(
        [("date", ASCENDING), ("department", ASCENDING)],
        unique=True,
    )


async def next_sequence(name: str) -> int:
    result = await database.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(result["seq"])
