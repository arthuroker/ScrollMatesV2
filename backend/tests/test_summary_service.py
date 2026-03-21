from pathlib import Path

import pytest

from backend.app.errors import ApiError
from backend.app.summary_service import process_summary_job


def test_process_summary_job_updates_stages_in_order(
    repository,
    sample_summary,
    tmp_path,
    monkeypatch,
):
    video_path = tmp_path / "recording.mp4"
    video_path.write_bytes(b"video-bytes")

    repository.create_job(
        job_id="job-success",
        source_filename="recording.mp4",
        duration_seconds=18.0,
    )
    repository.mark_started("job-success", "persisting_upload")

    monkeypatch.setattr(
        "backend.app.summary_service.detect_supported_mime_type",
        lambda content_type, filename: "video/mp4",
    )
    monkeypatch.setattr(
        "backend.app.summary_service.resolve_duration_seconds",
        lambda video_path, client_duration_seconds: 18.0,
    )

    def fake_summarize(video_path, mime_type, *, on_uploaded, on_generating):
        on_uploaded()
        on_generating()
        return sample_summary

    monkeypatch.setattr("backend.app.summary_service.summarize_video", fake_summarize)

    process_summary_job(
        "job-success",
        str(video_path),
        "video/mp4",
        "recording.mp4",
        18.0,
        repository,
    )

    job = repository.get_job("job-success")
    assert job is not None
    assert repository.stage_history["job-success"] == [
        "queued",
        "persisting_upload",
        "validating_video",
        "uploading_to_gemini",
        "waiting_for_gemini",
        "generating_summary",
        "completed",
    ]
    assert job.status == "completed"
    assert job.stage == "completed"
    assert job.summary_json == sample_summary
    assert not video_path.exists()


@pytest.mark.parametrize(
    ("job_id", "setup_failure", "expected_code", "expected_message"),
    [
        (
            "job-unsupported",
            lambda monkeypatch: monkeypatch.setattr(
                "backend.app.summary_service.detect_supported_mime_type",
                lambda content_type, filename: (_ for _ in ()).throw(
                    ApiError(
                        415,
                        "unsupported_media_type",
                        "Upload a supported video file.",
                    )
                ),
            ),
            "unsupported_media_type",
            "Upload a supported video file.",
        ),
        (
            "job-invalid-duration",
            lambda monkeypatch: (
                monkeypatch.setattr(
                    "backend.app.summary_service.detect_supported_mime_type",
                    lambda content_type, filename: "video/mp4",
                ),
                monkeypatch.setattr(
                    "backend.app.summary_service.resolve_duration_seconds",
                    lambda video_path, client_duration_seconds: (_ for _ in ()).throw(
                        ApiError(
                            400,
                            "invalid_duration",
                            "Uploaded video duration must be greater than zero.",
                        )
                    ),
                ),
            ),
            "invalid_duration",
            "Uploaded video duration must be greater than zero.",
        ),
        (
            "job-gemini-upload",
            lambda monkeypatch: (
                monkeypatch.setattr(
                    "backend.app.summary_service.detect_supported_mime_type",
                    lambda content_type, filename: "video/mp4",
                ),
                monkeypatch.setattr(
                    "backend.app.summary_service.resolve_duration_seconds",
                    lambda video_path, client_duration_seconds: 18.0,
                ),
                monkeypatch.setattr(
                    "backend.app.summary_service.summarize_video",
                    lambda video_path, mime_type, *, on_uploaded, on_generating: (_ for _ in ()).throw(
                        ApiError(
                            502,
                            "gemini_request_failed",
                            "Gemini upload failed.",
                        )
                    ),
                ),
            ),
            "gemini_request_failed",
            "Gemini upload failed.",
        ),
        (
            "job-timeout",
            lambda monkeypatch: (
                monkeypatch.setattr(
                    "backend.app.summary_service.detect_supported_mime_type",
                    lambda content_type, filename: "video/mp4",
                ),
                monkeypatch.setattr(
                    "backend.app.summary_service.resolve_duration_seconds",
                    lambda video_path, client_duration_seconds: 18.0,
                ),
                monkeypatch.setattr(
                    "backend.app.summary_service.summarize_video",
                    lambda video_path, mime_type, *, on_uploaded, on_generating: (_ for _ in ()).throw(
                        ApiError(
                            504,
                            "file_processing_timeout",
                            "Gemini took too long to activate the uploaded video file.",
                        )
                    ),
                ),
            ),
            "file_processing_timeout",
            "Gemini took too long to activate the uploaded video file.",
        ),
        (
            "job-invalid-output",
            lambda monkeypatch: (
                monkeypatch.setattr(
                    "backend.app.summary_service.detect_supported_mime_type",
                    lambda content_type, filename: "video/mp4",
                ),
                monkeypatch.setattr(
                    "backend.app.summary_service.resolve_duration_seconds",
                    lambda video_path, client_duration_seconds: 18.0,
                ),
                monkeypatch.setattr(
                    "backend.app.summary_service.summarize_video",
                    lambda video_path, mime_type, *, on_uploaded, on_generating: (_ for _ in ()).throw(
                        ApiError(
                            502,
                            "invalid_model_output",
                            "Gemini returned JSON that did not match the required schema.",
                        )
                    ),
                ),
            ),
            "invalid_model_output",
            "Gemini returned JSON that did not match the required schema.",
        ),
    ],
)
def test_process_summary_job_persists_failures(
    repository,
    tmp_path,
    monkeypatch,
    job_id,
    setup_failure,
    expected_code,
    expected_message,
):
    video_path = tmp_path / f"{job_id}.mp4"
    video_path.write_bytes(b"video-bytes")

    repository.create_job(
        job_id=job_id,
        source_filename=f"{job_id}.mp4",
        duration_seconds=12.0,
    )
    repository.mark_started(job_id, "persisting_upload")
    setup_failure(monkeypatch)

    process_summary_job(
        job_id,
        str(video_path),
        "video/mp4",
        f"{job_id}.mp4",
        12.0,
        repository,
    )

    job = repository.get_job(job_id)
    assert job is not None
    assert job.status == "failed"
    assert job.stage == "failed"
    assert job.summary_json is None
    assert job.error_code == expected_code
    assert job.error_message == expected_message
    assert not Path(video_path).exists()
