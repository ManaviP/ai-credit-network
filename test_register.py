import asyncio
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath("backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register():
    try:
        response = client.post("/auth/register", json={
            "name": "Test User",
            "phone": "1234567890",
            "aadhaar": "123412341234",
            "consent_given": True
        })
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_register()
