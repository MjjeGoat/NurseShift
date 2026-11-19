import os

os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:1"

import pytest
from fastapi.testclient import TestClient

from app.main import app

ADMIN = {"X-Dev-User-Id": "user_admin"}
HEAD = {"X-Dev-User-Id": "user_head"}
NURSE = {"X-Dev-User-Id": "user_1"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        c.post("/api/seed?force=true")
        yield c


def test_health_and_seed(client):
    data = client.get("/api/health").json()
    assert data["status"] == "ok"
    assert data["users_count"] == 12
    assert data["department_configured"] is True


def test_users_crud(client):
    assert len(client.get("/api/users", headers=NURSE).json()) == 12
    payload = {"name": "Test Sestra", "email": "test@nemocnice.cz", "id": "user_test"}
    assert client.post("/api/users", json=payload, headers=HEAD).status_code == 403
    assert client.post("/api/users", json=payload, headers=ADMIN).status_code == 201
    assert client.post("/api/users", json=payload, headers=ADMIN).status_code == 409
    r = client.put("/api/users/user_test", json={"workload": 0.5}, headers=ADMIN)
    assert r.json()["workload"] == 0.5
    assert client.delete("/api/users/user_test", headers=ADMIN).status_code == 200
    assert client.put("/api/users/user_test", json={"workload": 1.0}, headers=ADMIN).status_code == 404


def test_settings(client):
    cfg = client.get("/api/settings", headers=NURSE).json()
    assert cfg["shift_duration_hours"] == 12
    cfg["min_staff_day"] = 4
    assert client.put("/api/settings", json=cfg, headers=NURSE).status_code == 403
    assert client.put("/api/settings", json=cfg, headers=HEAD).json()["min_staff_day"] == 4


def test_schedule_save_and_load(client):
    body = {
        "year": 2026, "month": 12, "status": "draft",
        "shifts": {"2026-12-01": {"day": ["user_1"], "night": ["user_2"], "vacation": []}},
    }
    assert client.put("/api/schedules/2026-12", json=body, headers=NURSE).status_code == 403
    assert client.put("/api/schedules/2026-12", json=body, headers=HEAD).status_code == 200
    loaded = client.get("/api/schedules/2026-12", headers=NURSE).json()
    assert len(loaded["shifts"]) == 31
    assert loaded["shifts"]["2026-12-01"]["day"] == ["user_1"]


def test_invalid_month(client):
    assert client.get("/api/schedules/2026-13", headers=NURSE).status_code == 400
