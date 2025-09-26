import os
import jwt
from fastapi.testclient import TestClient
from app.api_server import app
from app.config import settings

def make_internal_token(sub: str = "test-user-id", email: str = "test@example.com"):
    payload = {"sub": sub, "email": email, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

def test_user_stats_structure():
    client = TestClient(app)
    token = make_internal_token()
    r = client.get("/v1/user/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    data = r.json()
    for key in ["total_calls", "monthly_calls", "quota", "active_keys", "last_activity"]:
        assert key in data
    assert isinstance(data["total_calls"], int)
    assert isinstance(data["monthly_calls"], int)
    assert isinstance(data["quota"], int)
    assert isinstance(data["active_keys"], int)
