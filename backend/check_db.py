import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def check():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    
    config = await db.config.find_one({"_id": "global"})
    print("CURRENT_DB_CONFIG:", config)
    
    logs = await db.security_logs.find().sort("created_at", -1).limit(5).to_list(None)
    print("LATEST_SECURITY_LOGS:", logs)

if __name__ == "__main__":
    asyncio.run(check())
