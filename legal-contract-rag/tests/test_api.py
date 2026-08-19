import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "environment" in data

def test_create_and_get_contract():
    # 1. Create contract
    create_res = client.post(
        "/api/v1/contracts/",
        json={"name": "Test NDA", "contract_type": "NDA", "governing_law": "NY"}
    )
    assert create_res.status_code == 201
    contract = create_res.json()
    contract_id = contract["id"]

    # 2. Get contract
    get_res = client.get(f"/api/v1/contracts/{contract_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Test NDA"

def test_async_document_upload_flow():
    # Create contract first
    c_res = client.post("/api/v1/contracts/", json={"name": "Upload Contract"})
    contract_id = c_res.json()["id"]

    # Async upload
    files = {"file": ("test_doc.txt", b"ARTICLE I\nThis is a test legal clause.", "text/plain")}
    data = {"contract_id": contract_id}
    up_res = client.post("/api/v1/documents/upload", data=data, files=files)

    assert up_res.status_code == 202
    res_json = up_res.json()
    assert res_json["status"] == "Queued"
    assert "jobId" in res_json
    assert "documentId" in res_json
