from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

import numpy as np

from .models import CATEGORY_NAMES, EMBEDDING_DIMENSION, LatestProfileEmbeddingRow, MatchInsertRow
from .repository import PostgresRepository


logger = logging.getLogger(__name__)


def _normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(embeddings, axis=2, keepdims=True)
    safe_norms = np.where(norms == 0, 1.0, norms)
    return embeddings / safe_norms


class MatchRunService:
    def __init__(self, repository: PostgresRepository, top_k: int):
        self.repository = repository
        self.top_k = top_k

    async def process_next_pending_run(self) -> bool:
        match_run = await self.repository.claim_pending_match_run()
        if match_run is None:
            return False

        try:
            profiles = await self.repository.load_latest_profiles_for_matching()
            match_rows = self._build_match_rows(profiles)
            await self.repository.replace_user_matches(match_run.id, match_rows)
            await self.repository.complete_match_run(match_run.id, len(profiles))
        except Exception as exc:
            logger.exception("Failed to process match run %s", match_run.id)
            await self.repository.fail_match_run(match_run.id, str(exc))
        return True

    def _build_match_rows(
        self,
        profiles: Sequence[LatestProfileEmbeddingRow],
    ) -> list[MatchInsertRow]:
        if len(profiles) < 2:
            return []

        embeddings = np.asarray([profile.embeddings for profile in profiles], dtype=np.float32)
        weights = np.asarray([profile.weights for profile in profiles], dtype=np.float32)

        if embeddings.shape[1:] != (len(CATEGORY_NAMES), EMBEDDING_DIMENSION):
            raise ValueError("Profile embeddings have an unexpected shape.")

        normalized = _normalize_embeddings(embeddings)
        per_category_cosine = np.einsum("acd,bcd->abc", normalized, normalized)
        average_weights = (weights[:, None, :] + weights[None, :, :]) / 2.0
        score_matrix = np.einsum("abc,abc->ab", per_category_cosine, average_weights)

        np.fill_diagonal(score_matrix, -np.inf)
        neighbor_count = min(self.top_k, len(profiles) - 1)
        match_rows: list[MatchInsertRow] = []

        for user_index, profile in enumerate(profiles):
            candidate_indices = np.argpartition(
                -score_matrix[user_index],
                neighbor_count - 1,
            )[:neighbor_count]
            sorted_indices = candidate_indices[
                np.argsort(-score_matrix[user_index][candidate_indices])
            ]

            for rank, matched_index in enumerate(sorted_indices, start=1):
                breakdown = {
                    category_name: float(per_category_cosine[user_index, matched_index, category_index])
                    for category_index, category_name in enumerate(CATEGORY_NAMES)
                }
                match_rows.append(
                    MatchInsertRow(
                        user_id=profile.user_id,
                        matched_user_id=profiles[matched_index].user_id,
                        rank=rank,
                        similarity_score=float(score_matrix[user_index, matched_index]),
                        score_breakdown=breakdown,
                    )
                )

        return match_rows


async def run_match_worker(
    service: MatchRunService,
    poll_interval_seconds: float,
) -> None:
    while True:
        processed = await service.process_next_pending_run()
        await asyncio.sleep(0 if processed else poll_interval_seconds)
