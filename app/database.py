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
        print("MongoDB connection closed")

def get_database() -> AsyncIOMotorDatabase:
    global db
    if db is None:
        raise Exception("Database connection not established. Call connect_to_mongo() first.")
    return db        