"""Basic API tests"""

import pytest
from fastapi.testclient import TestClient

from simiir_api.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_simulation():
    """Test creating a simulation"""
    
    config_xml = """<?xml version="1.0" encoding="UTF-8"?>
<simulation>
    <name>Test</name>
    <users>
        <user>user1</user>
    </users>
    <topics>
        <topic>303</topic>
    </topics>
    <output>
        <directory>./outputs</directory>
    </output>
</simulation>"""
    
    response = client.post(
        "/simulations/",
        json={
            "name": "Test Simulation",
            "description": "Test",
            "config_content": config_xml,
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Simulation"
    assert data["status"] == "pending"
    assert "id" in data


def test_list_simulations():
    """Test listing simulations"""
    response = client.get("/simulations/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

