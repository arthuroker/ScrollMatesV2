from __future__ import annotations

import asyncio

from .errors import ApiError
from .gemini_client import GeminiClient
from .media import MAX_VIDEO_SECONDS, detect_supported_mime_type, remove_file, resolve_duration_seconds
from .models import CATEGORY_NAMES, PersonalitySummary
from .repository import PostgresRepository


PROFILE_VERSION = 1


def _build_weighted_composite(
    embeddings: dict[str, list[float]],
    weights: dict[str, float],
) -> list[float]:
    composite: list[float] = []
    for category_name in CATEGORY_NAMES:
        category_embedding = embeddings[category_name]
        category_weight = weights[category_name]
        composite.extend(value * category_weight for value in category_embedding)
    return composite


class ProfilePipelineService:
    def __init__(self, repository: PostgresRepository, gemini_client: GeminiClient):
        self.repository = repository
        self.gemini_client = gemini_client

    async def process_job(
        self,
        *,
        job_id: str,
        user_id: str,
        video_path: str,
        content_type: str | None,
        filename: str | None,
        client_duration_seconds: float | None,
    ) -> None:
        try:
            mime_type = await asyncio.to_thread(
                detect_supported_mime_type,
                content_type,
                filename,
            )
            duration_seconds = await asyncio.to_thread(
                resolve_duration_seconds,
                video_path,
                client_duration_seconds,
            )
            if duration_seconds > MAX_VIDEO_SECONDS:
                raise ApiError(
                    413,
                    "video_too_long",
                    "Video exceeds the 45 minute limit for summarization.",
                )

            await self.repository.mark_job_processing(
                job_id,
                "gemini_analysis",
                mime_type=mime_type,
                duration_seconds=duration_seconds,
            )
            personality = await asyncio.to_thread(
                self.gemini_client.analyze_video,
                video_path,
                mime_type,
            )

            await self.repository.mark_job_processing(
                job_id,
                "embedding",
                summary=personality,
            )
            embeddings = await asyncio.to_thread(
                self._embed_personality,
                personality,
            )
            weights = {
                category_name: getattr(personality, category_name).weight
                for category_name in CATEGORY_NAMES
            }
            composite_embedding = _build_weighted_composite(embeddings, weights)
            await self.repository.insert_user_profile(
                user_id=user_id,
                job_id=job_id,
                profile_version=PROFILE_VERSION,
                personality_json=personality,
                embeddings=embeddings,
                weights=weights,
                composite_embedding=composite_embedding,
            )
            await self.repository.complete_job(job_id)
        except ApiError as exc:
            await self.repository.fail_job(job_id, exc.code, exc.message)
        except Exception as exc:
            await self.repository.fail_job(
                job_id,
                "internal_error",
                f"Unexpected error while processing video: {exc}",
            )
        finally:
            remove_file(video_path)

    def _embed_personality(self, personality: PersonalitySummary) -> dict[str, list[float]]:
        descriptions = [
            getattr(personality, category_name).description
            for category_name in CATEGORY_NAMES
        ]
        embedded_descriptions = self.gemini_client.embed_texts(descriptions)
        return dict(zip(CATEGORY_NAMES, embedded_descriptions, strict=True))
