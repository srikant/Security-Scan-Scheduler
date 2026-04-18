import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

client = None
db = None


async def connect_to_mongo():
    global client, db
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client.scan_scheduler
    print(f"Connected to MongoDB at {mongo_url}")


async def close_mongo_connection():
    global client
    if client:
        client.close()


def get_database() -> AsyncIOMotorDatabase:
    return db
