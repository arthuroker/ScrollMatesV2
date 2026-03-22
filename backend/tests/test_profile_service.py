from pathlib import Path

from backend.app.errors import ApiError
from backend.app.profile_service import ProfilePipelineService
from backend.tests.conftest import FakeGeminiClient
from backend.tests.helpers import sample_embeddings, sample_personality


def test_profile_pipeline_success(repository, tmp_path):
    video_path = tmp_path / "recording.mp4"
    video_path.write_bytes(b"video-bytes")

    repository.create_summary_job  # keep linters honest

    import asyncio

    asyncio.run(
        repository.create_summary_job(
            job_id="job-1",
            user_id="user-1",
            source_filename="recording.mp4",
            mime_type="video/mp4",
            duration_seconds=12.0,
        )
    )

    service = ProfilePipelineService(
        repository=repository,
        gemini_client=FakeGeminiClient(
            personality=sample_personality(),
            embeddings=sample_embeddings(),
        ),
    )

    asyncio.run(
        service.process_job(
            job_id="job-1",
            user_id="user-1",
            video_path=str(video_path),
            content_type="video/mp4",
            filename="recording.mp4",
            client_duration_seconds=12.0,
        )
    )

    job = repository.jobs["job-1"]
    assert job.status == "completed"
    assert repository.job_stage_history["job-1"] == [
        "upload",
        "gemini_analysis",
        "embedding",
        "done",
    ]
    assert len(repository.profile_rows) == 1
    profile_id = repository.profile_rows[0].id
    assert len(repository.profile_composites_by_id[profile_id]) == 5376
    assert not Path(video_path).exists()


def test_profile_pipeline_marks_job_failed_on_embedding_error(repository, tmp_path):
    video_path = tmp_path / "recording.mp4"
    video_path.write_bytes(b"video-bytes")

    import asyncio

    asyncio.run(
        repository.create_summary_job(
            job_id="job-2",
            user_id="user-1",
            source_filename="recording.mp4",
            mime_type="video/mp4",
            duration_seconds=12.0,
        )
    )

    service = ProfilePipelineService(
        repository=repository,
        gemini_client=FakeGeminiClient(
            personality=sample_personality(),
            embeddings=sample_embeddings(),
            embedding_error=ApiError(502, "embedding_request_failed", "embedding failed"),
        ),
    )

    asyncio.run(
        service.process_job(
            job_id="job-2",
            user_id="user-1",
            video_path=str(video_path),
            content_type="video/mp4",
            filename="recording.mp4",
            client_duration_seconds=12.0,
        )
    )

    job = repository.jobs["job-2"]
    assert job.status == "failed"
    assert job.error_code == "embedding_request_failed"
    assert not Path(video_path).exists()
