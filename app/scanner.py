import asyncio
import random
from datetime import datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def mock_security_scan(target_url: str) -> dict:
    print(f"Starting mock scan for {target_url} at {datetime.utcnow().isoformat()}")
    await asyncio.sleep(10)  # Simulate initial processing delay
    
        # Simulate scan results with random vulnerabilities
    vulnerabilities = []
    if "testphp" in target_url:
        vulnerabilities.append("SQL Injection possible")
        vulnerabilities.append("XSS reflected")
    elif "example" in target_url:
        vulnerabilities.append("TLS 1.0 enabled (Weak Cipher)")

    result = {
        "scan_time": datetime.utcnow().isoformat(),
        "status_code": random.choice([200, 403, 500]),
        "vulnerabilities_found": vulnerabilities,
        "risk_score": len(vulnerabilities) * 25
    }

    print(f"[Scanner] Completed scan on {target_url}. Risk score: {result['risk_score']}")
    return result
