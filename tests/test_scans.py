import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.scanner import mock_security_scan
from motor.motor_asyncio import AsyncIOMotorClient


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    await connect_to_mongo()
    yield
    await close_mongo_connection()


@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# TEST 1: Can we submit a scan request?
@pytest.mark.asyncio
async def test_create_scan(client):
    payload = {"target_url": "https://hackthissite.org"}

    response = await client.post("/scans", json=payload)

    # Assertions (The SPEC)
    assert response.status_code == 200
    data = response.json()
    assert data["target_url"] == "https://hackthissite.org"
    assert data["status"] == "pending"
    assert "_id" in data
    assert len(data["_id"]) == 24  # MongoDB ObjectId length


# TEST 2: Can we retrieve a scan by ID?
@pytest.mark.asyncio
async def test_get_scan_by_id(client):
    # 1. First, create a scan so we have an ID to fetch
    payload = {"target_url": "https://testsite.com"}
    create_res = await client.post("/scans", json=payload)
    scan_id = create_res.json()["_id"]

    # 2. Now fetch it
    response = await client.get(f"/scans/{scan_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["target_url"] == "https://testsite.com"
    assert data["_id"] == scan_id


# TEST 3: Test not found scan
@pytest.mark.asyncio
async def test_get_scan_not_found(client):
    fake_id = "507f1f77bcf86cd799439011"  # Valid format, but not in DB
    response = await client.get(f"/scans/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Scan not found"


# TEST 4: Update scan result (internal use by scanner)
@pytest.mark.asyncio
async def test_update_scan_result(client):
    # 1. Create a scan to update
    payload = {"target_url": "https://vulnerable-site.local"}
    create_res = await client.post("/scans", json=payload)
    scan_id = create_res.json()["_id"]

    # 2. Simulate scan result data (what background task would generate)
    update_payload = {
        "status": "completed",
        "result": {
            "scan_time": "2024-01-01T00:00:00",
            "risk_score": 75,
            "vulnerabilities_found": ["XSS", "Open Port 22"],
        },
    }

    # 3. PUT to update
    response = await client.put(f"/scans/{scan_id}", json=update_payload)
    assert response.status_code == 200

    # 4. Verify update with GET
    get_res = await client.get(f"/scans/{scan_id}")
    data = get_res.json()
    assert data["status"] == "completed"
    assert data["result"]["risk_score"] == 75


# TEST 5: End-to-End test for full scan lifecycle
@pytest.mark.slow
@pytest.mark.asyncio
async def test_full_scan_lifecycle_e2e(client):
    """
    E2E Test: Submit a scan, poll for completion, verify result.
    """
    # 1. Submit scan
    payload = {"target_url": "https://testphp.vulnweb.com"}
    post_res = await client.post("/scans", json=payload)
    assert post_res.status_code == 200
    scan_id = post_res.json()["_id"]

    # 2. Poll for completion (max 15 seconds)
    max_polls = 15
    status = "pending"

    for _ in range(max_polls):
        await asyncio.sleep(1)  # Wait 1 second between polls
        get_res = await client.get(f"/scans/{scan_id}")
        assert get_res.status_code == 200
        data = get_res.json()
        status = data["status"]
        if status != "pending":
            break

    # 3. Assert final state
    assert status == "completed"
    assert "result" in data
    assert "vulnerabilities_found" in data["result"]
    # Since URL contains testphp, we expect at least one vuln
    assert len(data["result"]["vulnerabilities_found"]) > 0


# TEST 6: Test mock scanner function directly
@pytest.mark.asyncio
async def test_mock_scanner():
    result = await mock_security_scan("https://testphp.example.com")
    assert "scan_time" in result
    assert "status_code" in result
    assert "vulnerabilities_found" in result
    assert "risk_score" in result
    assert isinstance(result["vulnerabilities_found"], list)
