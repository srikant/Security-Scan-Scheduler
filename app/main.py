from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager

from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.models import ScanRequest, ScanResponse

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(title="Security Scan Scheduler", lifespan=lifespan)    

@app.get("/")
async def root():
    return {"service": "Security Scan Scheduler", "status": "operational"}

@app.post("/scans", response_model=ScanResponse)
async def create_scan(scan_req: ScanRequest, background_tasks: BackgroundTasks, db: AsyncIOMotorDatabase = Depends(get_database)):
    scan_doc = {
        "target_url": scan_req.target_url,
        "status": "pending"
    }
    result = await db["scans"].insert_one(scan_doc)
    new_scan = await db["scans"].find_one({"_id": result.inserted_id})
    new_scan["id"] = str(new_scan["_id"])

    #background_tasks.add_task(run_scan, scan_id)

    return new_scan