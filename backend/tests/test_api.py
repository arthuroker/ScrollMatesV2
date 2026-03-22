from io import BytesIO

from backend.tests.helpers import TEST_ADMIN_SECRET, create_token, make_week_start, sample_personality


def auth_headers(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id)}"}


def test_upload_requires_auth(client):
    response = client.post(
        "/api/upload",
        files={"video": ("scroll.mp4", BytesIO(b"video-bytes"), "video/mp4")},
        data={"duration_seconds": "12"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "missing_token"


def test_upload_creates_job_for_authenticated_user(client, repository):
    response = client.post(
        "/api/upload",
        files={"video": ("scroll.mp4", BytesIO(b"video-bytes"), "video/mp4")},
        data={"duration_seconds": "12"},
        headers=auth_headers("user-1"),
    )

    assert response.status_code == 202
    job_id = response.json()["job_id"]

    job = repository.jobs[job_id]
    assert job.user_id == "user-1"
    assert job.status == "completed"
    assert repository.job_stage_history[job_id] == [
        "upload",
        "gemini_analysis",
        "embedding",
        "done",
    ]


def test_jobs_are_user_scoped(client, repository):
    response = client.post(
        "/api/upload",
        files={"video": ("scroll.mp4", BytesIO(b"video-bytes"), "video/mp4")},
        data={"duration_seconds": "12"},
        headers=auth_headers("user-1"),
    )
    job_id = response.json()["job_id"]

    other_user_response = client.get(
        f"/api/jobs/{job_id}",
        headers=auth_headers("user-2"),
    )

    assert other_user_response.status_code == 404
    assert other_user_response.json()["error"]["code"] == "summary_job_not_found"


def test_profile_returns_latest_profile_without_embeddings(client, repository):
    client.post(
        "/api/upload",
        files={"video": ("scroll.mp4", BytesIO(b"video-bytes"), "video/mp4")},
        data={"duration_seconds": "12"},
        headers=auth_headers("user-1"),
    )

    response = client.get("/api/profile", headers=auth_headers("user-1"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["personality_json"] == sample_personality().model_dump(mode="json")
    assert "emb_relational_orientation" not in payload


def test_matches_returns_latest_completed_run(client, repository):
    client.post(
        "/api/upload",
        files={"video": ("scroll.mp4", BytesIO(b"video-bytes"), "video/mp4")},
        data={"duration_seconds": "12"},
        headers=auth_headers("user-1"),
    )
    client.post(
        "/api/upload",
        files={"video": ("scroll.mp4", BytesIO(b"video-bytes"), "video/mp4")},
        data={"duration_seconds": "12"},
        headers=auth_headers("user-2"),
    )

    trigger = client.post(
        "/api/admin/trigger-match-run",
        headers={
            **auth_headers("admin-user"),
            "X-Admin-Secret": TEST_ADMIN_SECRET,
        },
    )
    assert trigger.status_code == 200

    run_id = trigger.json()["match_run_id"]
    client.app.state.services.match_service.top_k = 1
    import asyncio
    asyncio.run(client.app.state.services.match_service.process_next_pending_run())

    response = client.get("/api/matches", headers=auth_headers("user-1"))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["rank"] == 1
    assert payload[0]["week_start"] == str(make_week_start())
    assert payload[0]["matched_user_id"] == "user-2"


def test_admin_trigger_requires_secret(client):
    response = client.post(
        "/api/admin/trigger-match-run",
        headers=auth_headers("admin-user"),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_forbidden"


def test_admin_trigger_is_idempotent(client):
    first = client.post(
        "/api/admin/trigger-match-run",
        headers={**auth_headers("admin-user"), "X-Admin-Secret": TEST_ADMIN_SECRET},
    )
    second = client.post(
        "/api/admin/trigger-match-run",
        headers={**auth_headers("admin-user"), "X-Admin-Secret": TEST_ADMIN_SECRET},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["already_existed"] is False
    assert second.json()["already_existed"] is True
