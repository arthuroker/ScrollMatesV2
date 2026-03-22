from __future__ import annotations

import mimetypes
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile

from .errors import ApiError


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
