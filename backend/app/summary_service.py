import mimetypes
import os
import subprocess
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable

from fastapi import UploadFile
from google import genai
from pydantic import ValidationError

from .errors import ApiError
from .job_repository import SummaryJobRepository
from .models import TraitSummary


MAX_VIDEO_BYTES = 2 * 1024 * 1024 * 1024
MAX_VIDEO_SECONDS = 45 * 60
CHUNK_SIZE = 1024 * 1024
SUPPORTED_VIDEO_MIME_TYPES = {
    "video/3gpp",
    "video/mp4",
    "video/mpeg",
    "video/mpg",
    "video/mpegs",
    "video/quicktime",
    "video/webm",
    "video/wmv",
    "video/x-flv",
}
FILE_ACTIVE_TIMEOUT_SECONDS = 300
FILE_ACTIVE_POLL_INTERVAL_SECONDS = 5
PROMPT = """
Analyze this scrolling session recording and infer the viewer's psychographic profile from the content they spend time on, pause on, and repeatedly engage with.

Return only JSON that matches the provided schema.

For each trait:
- write a concise natural-language description grounded in the observed content themes
- set weight as a float between 0 and 1
- keep the full set of weights approximately normalized so the total is close to 1.0

Do not include markdown, commentary, safety disclaimers, or extra keys.
""".strip()


def get_model_name() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def remove_file(path: str | None) -> None:
    if path:
        Path(path).unlink(missing_ok=True)


def detect_supported_mime_type(content_type: str | None, filename: str | None) -> str:
    normalized_content_type = (content_type or "").lower()
    if normalized_content_type in SUPPORTED_VIDEO_MIME_TYPES:
        return normalized_content_type

    guessed, _ = mimetypes.guess_type(filename or "")
    if guessed in SUPPORTED_VIDEO_MIME_TYPES:
        return guessed

    raise ApiError(415, "unsupported_media_type", "Upload a supported video file.")


async def persist_upload(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix or ".video"
    temp_file = NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = temp_file.name
    total_bytes = 0

    try:
        while chunk := await upload.read(CHUNK_SIZE):
            total_bytes += len(chunk)
            if total_bytes > MAX_VIDEO_BYTES:
                raise ApiError(
                    413,
                    "file_too_large",
                    "Video exceeds the 2 GB Gemini file limit.",
                )
            temp_file.write(chunk)
    except Exception:
        temp_file.close()
        remove_file(temp_path)
        raise
    finally:
        temp_file.close()
        await upload.close()

    return temp_path


def probe_duration_seconds(video_path: str) -> float | None:
    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError as exc:
        raise ApiError(
            400,
            "invalid_video",
            "Unable to inspect the uploaded video file.",
        ) from exc

    try:
        return float(completed.stdout.strip())
    except ValueError as exc:
        raise ApiError(
            400,
            "invalid_video",
            "Unable to determine the uploaded video duration.",
        ) from exc


def resolve_duration_seconds(
    video_path: str,
    client_duration_seconds: float | None,
) -> float:
    probed_duration_seconds = probe_duration_seconds(video_path)
    if probed_duration_seconds is not None:
        return probed_duration_seconds

    if client_duration_seconds is None:
        raise ApiError(
            400,
            "missing_duration",
            "Unable to determine the uploaded video duration.",
        )

    if client_duration_seconds <= 0:
        raise ApiError(
            400,
            "invalid_duration",
            "Uploaded video duration must be greater than zero.",
        )

    return client_duration_seconds


def build_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ApiError(
            500,
            "missing_api_key",
            "Set GEMINI_API_KEY before calling the summarization endpoint.",
        )
    return genai.Client(api_key=api_key)


def wait_for_active_file(client: genai.Client, uploaded_file):
    started_at = time.monotonic()
    current_file = uploaded_file

    while True:
        current_state = getattr(current_file, "state", None)
        current_state_name = getattr(current_state, "name", None)

        if current_state_name == "ACTIVE":
            return current_file

        if current_state_name == "FAILED":
            raise ApiError(
                502,
                "file_processing_failed",
                "Gemini failed to process the uploaded video file.",
            )

        if time.monotonic() - started_at >= FILE_ACTIVE_TIMEOUT_SECONDS:
            raise ApiError(
                504,
                "file_processing_timeout",
                "Gemini took too long to activate the uploaded video file.",
            )

        time.sleep(FILE_ACTIVE_POLL_INTERVAL_SECONDS)
        current_file = client.files.get(name=current_file.name)


def summarize_video(
    video_path: str,
    mime_type: str,
    *,
    on_uploaded: Callable[[], None] | None = None,
    on_generating: Callable[[], None] | None = None,
) -> TraitSummary:
    client = build_client()
    uploaded_file = None

    try:
        uploaded_file = client.files.upload(file=video_path)
        if on_uploaded is not None:
            on_uploaded()
        uploaded_file = wait_for_active_file(client, uploaded_file)
        if on_generating is not None:
            on_generating()
        response = client.models.generate_content(
            model=get_model_name(),
            contents=[
                uploaded_file,
                f"{PROMPT}\n\nUploaded video MIME type: {mime_type}",
            ],
            config={
                "response_mime_type": "application/json",
                "response_json_schema": TraitSummary.model_json_schema(),
            },
        )
        return TraitSummary.model_validate_json(response.text)
    except ValidationError as exc:
        raise ApiError(
            502,
            "invalid_model_output",
            "Gemini returned JSON that did not match the required schema.",
        ) from exc
    except ApiError:
        raise
    except Exception as exc:
        raise ApiError(
            502,
            "gemini_request_failed",
            f"Gemini request failed: {exc}",
        ) from exc
    finally:
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass


def process_summary_job(
    job_id: str,
    video_path: str,
    content_type: str | None,
    filename: str | None,
    client_duration_seconds: float | None,
    repository: SummaryJobRepository,
) -> None:
    try:
        repository.update_stage(job_id, "validating_video")
        mime_type = detect_supported_mime_type(content_type, filename)
        resolved_duration_seconds = resolve_duration_seconds(
            video_path,
            client_duration_seconds,
        )
        if resolved_duration_seconds > MAX_VIDEO_SECONDS:
            raise ApiError(
                413,
                "video_too_long",
                "Video exceeds the 45 minute limit for summarization.",
            )

        repository.update_stage(
            job_id,
            "uploading_to_gemini",
            mime_type=mime_type,
            duration_seconds=resolved_duration_seconds,
        )
        summary = summarize_video(
            video_path,
            mime_type,
            on_uploaded=lambda: repository.update_stage(job_id, "waiting_for_gemini"),
            on_generating=lambda: repository.update_stage(job_id, "generating_summary"),
        )
        repository.complete_job(job_id, summary)
    except ApiError as exc:
        repository.fail_job(job_id, exc.code, exc.message)
    except Exception as exc:
        repository.fail_job(
            job_id,
            "internal_error",
            f"Unexpected error while summarizing video: {exc}",
        )
    finally:
        remove_file(video_path)
