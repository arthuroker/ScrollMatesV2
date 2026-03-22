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


load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")

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
You are analyzing a screen recording of someone's short-form video feed (TikTok, Reels, etc.) to build a deep personality profile. The goal is to produce a description so accurate and specific that the user feels the app understands them better than they understand themselves. Be opinionated and direct — use sharp, specific labels rather than clinical or hedged language. Prefer "strongly politically incorrect humor" over "offensive humor", "parasocial and emotionally avoidant" over "difficulty with relationships."

Before extracting any trait, consider the full context of the session:
- Distinguish genuine interests from content where the subject is merely a vehicle. For every category of content, ask: is the subject matter the point, or is something else (absurdity, chaos, irony, social commentary) the point? A useful test: would a genuine enthusiast of this subject watch this specific video earnestly? If the appeal is clearly the chaos, absurdity, or humor — not the subject itself — classify it under humor/personality style, not as an interest in that subject. For example: videos of cars doing absurd or destructive things are not evidence of interest in cars or extreme sports — they reflect an appetite for absurdist humor. Videos mocking a subculture are not evidence of interest in that subculture.
- Ask not just what they watch, but why. What underlying need, value, or worldview does this content satisfy? Someone who watches chaotic absurdist memes and someone who watches dry deadpan humor may both "like comedy" — but they are very different people.
- Name tensions and contradictions if you see them. A person who watches both extremely online irony content and sincere heartfelt videos about family is more interesting and accurately described by naming that duality.

Write each description as a tight, opinionated label for the trait — not a full sentence about the person. Prefer noun phrases: "dark, politically incorrect humor fixated on chaos and cringe" over "This person has a dark sense of humor." No hedging.

Be specific. Mention real references, subcultures, aesthetics, or communities where relevant and where you are confident they reflect a genuine interest. Avoid vague words like "enjoys" or "is interested in" — instead describe the specific flavor of that interest and what it reveals about them as a person.

Return only JSON that matches the provided schema.

For each trait:
- write a tight noun-phrase label (1–2 phrases max) that characterizes the trait with specificity and confidence
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


def transcode_video(input_path: str) -> str | None:
    output_file = NamedTemporaryFile(delete=False, suffix=".mp4")
    output_path = output_file.name
    output_file.close()

    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-vf", "fps=6,scale=-2:360",
                "-an",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
                output_path,
            ],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        remove_file(output_path)
        return None
    except subprocess.CalledProcessError as exc:
        remove_file(output_path)
        raise ApiError(
            400,
            "transcode_failed",
            "Unable to transcode the uploaded video.",
        ) from exc

    original_mb = Path(input_path).stat().st_size / 1024 / 1024
    compressed_mb = Path(output_path).stat().st_size / 1024 / 1024
    print(f"[transcode] {original_mb:.1f} MB → {compressed_mb:.1f} MB ({output_path})")

    return output_path


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
    transcoded_path = None

    try:
        video_path, _ = await persist_upload(video)
        resolved_duration_seconds = resolve_duration_seconds(video_path, duration_seconds)
        if resolved_duration_seconds > MAX_VIDEO_SECONDS:
            raise ApiError(
                413,
                "video_too_long",
                "Video exceeds the 45 minute limit for summarization.",
            )

        transcoded_path = transcode_video(video_path)
        upload_path = transcoded_path if transcoded_path is not None else video_path

        summary = summarize_video(upload_path, "video/mp4")
        return summary
    finally:
        remove_file(transcoded_path)
        remove_file(video_path)
