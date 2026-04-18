import asyncio
import random
from datetime import datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId


async def mock_security_scan(target_url: str) -> dict:
    """
    Simulates a long-running security scan.
    In a real app, this would run nmap, ZAP, or call an AI model.
    """
    print(f"[Scanner] Starting scan on {target_url}...")

    # Simulate work (10 seconds)
    await asyncio.sleep(10)

    # Simulate findings
    vulnerabilities = []
    if "testphp" in target_url:
        vulnerabilities.append("SQL Injection possible")
        vulnerabilities.append("XSS reflected")
    elif "example" in target_url:
        vulnerabilities.append("TLS 1.0 enabled (Weak Cipher)")

    result = {
        "scan_time": datetime.utcnow().isoformat(),
        "status_code": random.choice([200, 200, 200, 403, 500]),  # Weighted
        "vulnerabilities_found": vulnerabilities,
        "risk_score": len(vulnerabilities) * 25,
    }

    print(f"[Scanner] Completed scan on {target_url}. Risk: {result['risk_score']}")
    return result


async def process_scan_background(scan_id: str, target_url: str):
    """
    This function runs in the background.
    It must create its own DB connection because it's outside the request lifecycle.
    """
    # Get MongoDB URL from environment (same as main app)
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client.scan_scheduler

    try:
        # 1. Perform the mock scan
        scan_result = await mock_security_scan(target_url)

        # 2. Update the document in MongoDB
        await db["scans"].update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": {"status": "completed", "result": scan_result}},
        )
        print(f"[Background] Scan {scan_id} updated successfully.")
    except Exception as e:
        print(f"[Background] Scan {scan_id} failed: {e}")
        await db["scans"].update_one(
            {"_id": ObjectId(scan_id)}, {"$set": {"status": "failed", "error": str(e)}}
        )
    finally:
        client.close()
