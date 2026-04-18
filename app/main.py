from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.models import ScanRequest, ScanResponse, ScanUpdate
from app.scanner import process_scan_background
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(title="Security Scan Scheduler", lifespan=lifespan)


@app.get("/")
async def root():
    return {"service": "Security Scan Scheduler", "status": "operational"}


@app.post("/scans", response_model=ScanResponse)
async def create_scan(
    scan_req: ScanRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    # Prepare the document for MongoDB
    scan_doc = {"target_url": scan_req.target_url, "status": "pending"}

    # Insert into collection
    result = await db["scans"].insert_one(scan_doc)
    scan_id = str(result.inserted_id)

    # SCHEDULE BACKGROUND TASK
    background_tasks.add_task(process_scan_background, scan_id, scan_req.target_url)

    # Return immediate response (pending)
    new_scan = await db["scans"].find_one({"_id": result.inserted_id})
    new_scan["_id"] = scan_id
    return new_scan


@app.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    # Validate ObjectId format early to prevent server errors
    if not ObjectId.is_valid(scan_id):
        raise HTTPException(status_code=400, detail="Invalid scan ID format")

    scan = await db["scans"].find_one({"_id": ObjectId(scan_id)})

    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan["_id"] = str(scan["_id"])
    return scan


@app.put("/scans/{scan_id}")
async def update_scan_result(
    scan_id: str, update: ScanUpdate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    if not ObjectId.is_valid(scan_id):
        raise HTTPException(status_code=400, detail="Invalid scan ID format")

    # Build update dictionary
    update_data = {}
    if update.status is not None:
        update_data["status"] = update.status
    if update.result is not None:
        update_data["result"] = update.result

    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    result = await db["scans"].update_one(
        {"_id": ObjectId(scan_id)}, {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Scan not found")

    return {"message": "Scan updated successfully"}
