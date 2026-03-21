from io import BytesIO

import backend.app.main as main_module
from backend.app.summary_service import remove_file


def test_health_check(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "model" in payload


def test_summarize_returns_job_kickoff_and_persists_completed_result(
    client,
    monkeypatch,
    sample_summary,
):
    def fake_process_job(
        job_id,
        video_path,
        content_type,
        filename,
        client_duration_seconds,
        repository,
    ):
        repository.update_stage(
            job_id,
            "generating_summary",
            mime_type="video/mp4",
            duration_seconds=client_duration_seconds,
        )
        repository.complete_job(job_id, sample_summary)
        remove_file(video_path)

    monkeypatch.setattr(main_module, "process_summary_job", fake_process_job)

    response = client.post(
        "/api/summarize",
        files={"video": ("scroll.mp4", BytesIO(b"video-bytes"), "video/mp4")},
        data={"duration_seconds": "12"},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "processing"
    assert payload["stage"] == "persisting_upload"
    assert payload["job_id"]

    job_response = client.get(f"/api/summarize/{payload['job_id']}")

    assert job_response.status_code == 200
    job_payload = job_response.json()
    assert job_payload["status"] == "completed"
    assert job_payload["stage"] == "completed"
    assert job_payload["summary"] == sample_summary.model_dump(mode="json")
    assert job_payload["error"] is None


def test_summarize_persists_failed_job_for_unsupported_media(client):
    response = client.post(
        "/api/summarize",
        files={"video": ("notes.txt", BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["job_id"]

    job_response = client.get(f"/api/summarize/{payload['job_id']}")

    assert job_response.status_code == 200
    job_payload = job_response.json()
    assert job_payload["status"] == "failed"
    assert job_payload["stage"] == "failed"
    assert job_payload["summary"] is None
    assert job_payload["error"] == {
        "code": "unsupported_media_type",
        "message": "Upload a supported video file.",
    }


def test_get_summary_job_returns_queued_state(client, repository):
    repository.create_job(
        job_id="job-queued",
        source_filename="queued.mp4",
        duration_seconds=15.0,
    )

    response = client.get("/api/summarize/job-queued")

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert response.json()["stage"] == "queued"
    assert response.json()["summary"] is None


def test_get_summary_job_returns_processing_state(client, repository):
    repository.create_job(
        job_id="job-processing",
        source_filename="processing.mp4",
        duration_seconds=15.0,
    )
    repository.mark_started("job-processing", "persisting_upload")
    repository.update_stage("job-processing", "waiting_for_gemini")

    response = client.get("/api/summarize/job-processing")

    assert response.status_code == 200
    assert response.json()["status"] == "processing"
    assert response.json()["stage"] == "waiting_for_gemini"
    assert response.json()["summary"] is None


def test_get_summary_job_returns_failed_state(client, repository):
    repository.create_job(
        job_id="job-failed",
        source_filename="failed.mp4",
        duration_seconds=15.0,
    )
    repository.fail_job("job-failed", "invalid_duration", "Duration must be positive.")

    response = client.get("/api/summarize/job-failed")

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["stage"] == "failed"
    assert response.json()["error"] == {
        "code": "invalid_duration",
        "message": "Duration must be positive.",
    }


def test_get_summary_job_returns_404_for_unknown_job(client):
    response = client.get("/api/summarize/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "summary_job_not_found"
