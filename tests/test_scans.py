import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.scanner import mock_security_scan
from motor.motor_asyncio import AsyncIOMotorClient  

# TEST FIXTURES - Setup and Teardown
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    await connect_to_mongo()
    yield
    await close_mongo_connection()

@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

# Test 1: Create Scan Endpoint
@pytest.mark.asyncio
async def test_create_scan(client):
    payload = {"target": "http://hackthissite.org"}
    response = await client.post("/scans", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["target_url"] == "http://hackthissite.org"
    assert data["status"] == "pending"
    assert "id" in data
    assert len(data["id"]) == 24

# Test 2: Retrieve Scan by ID
@pytest.mark.asyncio
async def test_get_scan_by_id(client):
    # Step1: First, create a scan
    payload = {"target": "http://hackthissite.org"}
    create_res = await client.post("/scans", json=payload)
    scan_id = create_res.json()["id"]

    # Step 2: Retrieve the scan by ID
    response = await client.get(f"/scans/{scan_id}")

    # Verify successful retrieval
    assert response.status_code == 200, "Should find existing scan"

    # Verify the retrieved data matches what was created
    data = response.json()
    assert data["target_url"] == "http://hackthissite.org", "URL should match"
    assert data["id"] == scan_id, "IDs should match"

# Test 3: Retrieve Non-Existent Scan
@pytest.mark.asyncio
async def test_get_scan_not_found(client):    
    fake_id = "60d5f4832f8fb814c8a1b234"  # Random ObjectId
    response = await client.get(f"/scans/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Scan not found"

# Test 4: Update Scan Results (Internal Endpoint)
@pytest.mark.asyncio
async def test_update_scan_results(client):
    # Step 1: Create a scan
    payload = {"target_url": "http://vulnerable-site.local"}
    create_res = await client.post("/scans", json=payload)
    scan_id = create_res.json()["id"]

    # Step 2: Update the scan results
    update_payload = {
        "status": "completed",
        "results": {
            "scan_time": "2024-06-01T12:00:00Z",
            "vulnerabilities_found": [ "XSS", "Open Port 22"],
            "risk_score": 75
        }
    }

    response = await client.put(f"/scans/{scan_id}", json=update_payload)

    # Verify successful update
    assert response.status_code == 200, "Update should succeed"
    
    get_res = await client.get(f"/scans/{scan_id}")
    data = get_res.json()
    assert data["status"] == "completed", "Status should be updated"
    assert data["results"]["risk_score"] == 75, "Risk score should match"