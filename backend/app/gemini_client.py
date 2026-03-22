from __future__ import annotations

import time
from typing import Any

from google import genai
from pydantic import ValidationError

from .config import Settings
from .errors import ApiError
from .models import PersonalitySummary


FILE_ACTIVE_TIMEOUT_SECONDS = 300
FILE_ACTIVE_POLL_INTERVAL_SECONDS = 5
ANALYSIS_PROMPT = """
Analyze this scrolling session recording and infer the viewer's psychographic profile from the content they spend time on, pause on, and repeatedly engage with.

Return only JSON that matches the provided schema.

For each trait:
- write a concise natural-language description grounded in the observed content themes
- set weight as a float between 0 and 1
- keep the full set of weights approximately normalized so the total is close to 1.0

Do not include markdown, commentary, safety disclaimers, or extra keys.
""".strip()


def _extract_embedding_values(response: Any) -> list[float]:
    embeddings = getattr(response, "embeddings", None)
    if embeddings:
        candidate = embeddings[0]
        values = getattr(candidate, "values", None)
        if values is not None:
            return [float(value) for value in values]
        if isinstance(candidate, dict) and "values" in candidate:
            return [float(value) for value in candidate["values"]]

    embedding = getattr(response, "embedding", None)
    if embedding is not None:
        values = getattr(embedding, "values", None)
        if values is not None:
            return [float(value) for value in values]
        if isinstance(embedding, dict) and "values" in embedding:
            return [float(value) for value in embedding["values"]]

    raise ApiError(
        502,
        "invalid_embedding_output",
        "Gemini returned an unexpected embedding payload.",
    )


class GeminiClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def analyze_video(self, video_path: str, mime_type: str) -> PersonalitySummary:
        uploaded_file = None

        try:
            uploaded_file = self._client.files.upload(file=video_path)
            uploaded_file = self._wait_for_active_file(uploaded_file)
            response = self._client.models.generate_content(
                model=self._settings.gemini_model,
                contents=[
                    uploaded_file,
                    f"{ANALYSIS_PROMPT}\n\nUploaded video MIME type: {mime_type}",
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": PersonalitySummary.model_json_schema(),
                },
            )
            return PersonalitySummary.model_validate_json(response.text)
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
                    self._client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []

        for text in texts:
            try:
                response = self._client.models.embed_content(
                    model=self._settings.gemini_embedding_model,
                    contents=text,
                )
            except Exception as exc:
                raise ApiError(
                    502,
                    "embedding_request_failed",
                    f"Gemini embedding request failed: {exc}",
                ) from exc

            embeddings.append(_extract_embedding_values(response))

        return embeddings

    def _wait_for_active_file(self, uploaded_file: Any) -> Any:
        started_at = time.monotonic()
        current_file = uploaded_file

        while True:
            current_state = getattr(current_file, "state", None)
            current_state_name = getattr(current_state, "name", None)

            if current_state_name in (None, "ACTIVE"):
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
            current_file = self._client.files.get(name=current_file.name)
