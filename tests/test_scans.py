import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.database import get_database
from app.scanner import mock_security_scan
from motor.motor_asyncio import AsyncIOMotorClient  

# TEST FIXTURES - Setup and Teardown
@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
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