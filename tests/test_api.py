import pytest
from fastapi.testclient import TestClient
from satquery.backend.api.main import app
from satquery.backend.database.database import Base, engine

# Create the tables in the test database (which defaults to sqlite from settings)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}

def test_get_bodies():
    response = client.get("/api/bodies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(b["id"] == "earth" for b in data)

def test_simulation_start():
    response = client.post("/api/simulation/start")
    assert response.status_code == 200
    assert response.json()["status"] == "started"
    
def test_simulation_state():
    response = client.get("/api/simulation/state")
    assert response.status_code == 200
    assert "clock" in response.json()

def test_create_mission():
    payload = {
        "name": "Test API Mission",
        "target_body_id": "mars"
    }
    response = client.post("/api/mission", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    assert "mission_id" in data
