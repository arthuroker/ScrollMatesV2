from io import BytesIO

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "model" in payload


def test_rejects_unsupported_upload_type():
    response = client.post(
        "/api/summarize",
        files={"video": ("notes.txt", BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"
