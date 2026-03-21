import mimetypes
import os
import subprocess
import time
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google import genai
from pydantic import ValidationError
from dotenv import load_dotenv

from .models import TraitSummary


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

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
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
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


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


app = FastAPI(title="ScrollMates API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApiError)
async def api_error_handler(_, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def remove_file(path: str | None) -> None:
    if path:
        Path(path).unlink(missing_ok=True)


def detect_mime_type(upload: UploadFile) -> str:
    content_type = (upload.content_type or "").lower()
    if content_type in SUPPORTED_VIDEO_MIME_TYPES:
        return content_type

    guessed, _ = mimetypes.guess_type(upload.filename or "")
    if guessed in SUPPORTED_VIDEO_MIME_TYPES:
        return guessed

    raise ApiError(415, "unsupported_media_type", "Upload a supported video file.")


async def persist_upload(upload: UploadFile) -> tuple[str, str]:
    mime_type = detect_mime_type(upload)
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

    return temp_path, mime_type


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


def summarize_video(video_path: str, mime_type: str) -> TraitSummary:
    client = build_client()
    uploaded_file = None

    try:
        uploaded_file = client.files.upload(file=video_path)
        uploaded_file = wait_for_active_file(client, uploaded_file)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[uploaded_file, PROMPT],
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


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/api/summarize", response_model=TraitSummary)
async def summarize(
    video: UploadFile = File(...),
    duration_seconds: float | None = Form(default=None),
):
    video_path = None

    try:
        video_path, mime_type = await persist_upload(video)
        resolved_duration_seconds = resolve_duration_seconds(video_path, duration_seconds)
        if resolved_duration_seconds > MAX_VIDEO_SECONDS:
            raise ApiError(
                413,
                "video_too_long",
                "Video exceeds the 45 minute limit for summarization.",
            )

        summary = summarize_video(video_path, mime_type)
        return summary
    finally:
        remove_file(video_path)
