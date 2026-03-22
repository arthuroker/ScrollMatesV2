from __future__ import annotations

import json
from datetime import date, datetime, timezone
from uuid import uuid4

import asyncpg

from .models import (
    CATEGORY_NAMES,
    LatestProfileEmbeddingRow,
    MatchInsertRow,
    MatchRunRecord,
    MatchResponse,
    PersonalitySummary,
    ProfileRecord,
    ProfileResponse,
    ProfileWeights,
    SummaryJobRecord,
    SummaryJobResponse,
    TriggerMatchRunResponse,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_vector(value: str) -> list[float]:
    stripped = value.strip()
    if not stripped or stripped == "[]":
        return []
    return [float(component) for component in stripped.strip("[]").split(",")]


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.12g}" for value in values) + "]"


def _ensure_json(value):
    if value is None or isinstance(value, dict):
        return value
    return json.loads(value)


class PostgresRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_summary_job(
        self,
        *,
        job_id: str,
        user_id: str,
        source_filename: str,
        mime_type: str | None,
        duration_seconds: float | None,
    ) -> SummaryJobRecord:
        row = await self.pool.fetchrow(
            """
            INSERT INTO summary_jobs (
                id,
                user_id,
                status,
                stage,
                source_filename,
                mime_type,
                duration_seconds
            )
            VALUES ($1, $2, 'pending', 'upload', $3, $4, $5)
            RETURNING *
            """,
            job_id,
            user_id,
            source_filename,
            mime_type,
            duration_seconds,
        )
        return SummaryJobRecord.model_validate(dict(row))

    async def mark_job_processing(
        self,
        job_id: str,
        stage: str,
        *,
        mime_type: str | None = None,
        duration_seconds: float | None = None,
        summary: PersonalitySummary | None = None,
    ) -> SummaryJobRecord:
        row = await self.pool.fetchrow(
            """
            UPDATE summary_jobs
            SET status = 'processing',
                stage = $2,
                mime_type = COALESCE($3, mime_type),
                duration_seconds = COALESCE($4, duration_seconds),
                summary_json = COALESCE($5::jsonb, summary_json),
                started_at = COALESCE(started_at, NOW()),
                updated_at = NOW()
            WHERE id = $1
            RETURNING *
            """,
            job_id,
            stage,
            mime_type,
            duration_seconds,
            json.dumps(summary.model_dump(mode="json")) if summary is not None else None,
        )
        return SummaryJobRecord.model_validate(dict(row))

    async def complete_job(self, job_id: str) -> SummaryJobRecord:
        row = await self.pool.fetchrow(
            """
            UPDATE summary_jobs
            SET status = 'completed',
                stage = 'done',
                completed_at = NOW(),
                updated_at = NOW(),
                error_code = NULL,
                error_message = NULL
            WHERE id = $1
            RETURNING *
            """,
            job_id,
        )
        return SummaryJobRecord.model_validate(dict(row))

    async def fail_job(self, job_id: str, code: str, message: str) -> SummaryJobRecord:
        row = await self.pool.fetchrow(
            """
            UPDATE summary_jobs
            SET status = 'failed',
                completed_at = NOW(),
                updated_at = NOW(),
                error_code = $2,
                error_message = $3
            WHERE id = $1
            RETURNING *
            """,
            job_id,
            code,
            message,
        )
        return SummaryJobRecord.model_validate(dict(row))

    async def get_summary_job_for_user(
        self,
        job_id: str,
        user_id: str,
    ) -> SummaryJobResponse | None:
        row = await self.pool.fetchrow(
            """
            SELECT id, status, stage, created_at, updated_at, error_code, error_message
            FROM summary_jobs
            WHERE id = $1 AND user_id = $2
            """,
            job_id,
            user_id,
        )
        if row is None:
            return None
        return SummaryJobResponse.model_validate(dict(row))

    async def insert_user_profile(
        self,
        *,
        user_id: str,
        job_id: str,
        profile_version: int,
        personality_json: PersonalitySummary,
        embeddings: dict[str, list[float]],
        weights: dict[str, float],
        composite_embedding: list[float],
    ) -> ProfileRecord:
        row = await self.pool.fetchrow(
            """
            INSERT INTO user_profiles (
                id,
                user_id,
                job_id,
                profile_version,
                personality_json,
                emb_relational_orientation,
                emb_creativity,
                emb_intellectualism,
                emb_humor,
                emb_interests,
                emb_cultural_identity,
                emb_political_orientation,
                w_relational_orientation,
                w_creativity,
                w_intellectualism,
                w_humor,
                w_interests,
                w_cultural_identity,
                w_political_orientation,
                emb_composite
            )
            VALUES (
                $1,
                $2,
                $3,
                $4,
                $5::jsonb,
                $6::vector,
                $7::vector,
                $8::vector,
                $9::vector,
                $10::vector,
                $11::vector,
                $12::vector,
                $13,
                $14,
                $15,
                $16,
                $17,
                $18,
                $19,
                $20::vector
            )
            RETURNING id, user_id, job_id, profile_version, created_at, personality_json,
                w_relational_orientation,
                w_creativity,
                w_intellectualism,
                w_humor,
                w_interests,
                w_cultural_identity,
                w_political_orientation
            """,
            str(uuid4()),
            user_id,
            job_id,
            profile_version,
            json.dumps(personality_json.model_dump(mode="json")),
            _vector_literal(embeddings["relational_orientation"]),
            _vector_literal(embeddings["creativity"]),
            _vector_literal(embeddings["intellectualism"]),
            _vector_literal(embeddings["humor"]),
            _vector_literal(embeddings["interests"]),
            _vector_literal(embeddings["cultural_identity"]),
            _vector_literal(embeddings["political_orientation"]),
            weights["relational_orientation"],
            weights["creativity"],
            weights["intellectualism"],
            weights["humor"],
            weights["interests"],
            weights["cultural_identity"],
            weights["political_orientation"],
            _vector_literal(composite_embedding),
        )
        return self._profile_record_from_row(row)

    async def get_latest_profile_for_user(self, user_id: str) -> ProfileResponse | None:
        row = await self.pool.fetchrow(
            """
            SELECT id, profile_version, created_at, personality_json,
                w_relational_orientation,
                w_creativity,
                w_intellectualism,
                w_humor,
                w_interests,
                w_cultural_identity,
                w_political_orientation
            FROM user_profiles
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            user_id,
        )
        if row is None:
            return None

        return ProfileResponse(
            id=row["id"],
            profile_version=row["profile_version"],
            created_at=row["created_at"],
            personality_json=PersonalitySummary.model_validate(_ensure_json(row["personality_json"])),
            weights=ProfileWeights(
                w_relational_orientation=row["w_relational_orientation"],
                w_creativity=row["w_creativity"],
                w_intellectualism=row["w_intellectualism"],
                w_humor=row["w_humor"],
                w_interests=row["w_interests"],
                w_cultural_identity=row["w_cultural_identity"],
                w_political_orientation=row["w_political_orientation"],
            ),
        )

    async def get_latest_matches_for_user(self, user_id: str) -> list[MatchResponse]:
        rows = await self.pool.fetch(
            """
            WITH latest_completed_run AS (
                SELECT id, week_start
                FROM match_runs
                WHERE status = 'completed'
                ORDER BY week_start DESC
                LIMIT 1
            )
            SELECT um.rank, um.similarity_score, um.score_breakdown, um.matched_user_id, lr.week_start
            FROM latest_completed_run lr
            JOIN user_matches um
                ON um.match_run_id = lr.id
            WHERE um.user_id = $1
            ORDER BY um.rank ASC
            """,
            user_id,
        )
        return [
            MatchResponse(
                rank=row["rank"],
                similarity_score=row["similarity_score"],
                score_breakdown=_ensure_json(row["score_breakdown"]) or {},
                matched_user_id=row["matched_user_id"],
                week_start=row["week_start"],
            )
            for row in rows
        ]

    async def trigger_match_run(self, week_start: date) -> TriggerMatchRunResponse:
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                INSERT INTO match_runs (id, week_start, status, triggered_by)
                VALUES ($1, $2, 'pending', 'manual')
                ON CONFLICT (week_start) DO NOTHING
                RETURNING id, week_start
                """,
                str(uuid4()),
                week_start,
            )

            if row is not None:
                return TriggerMatchRunResponse(
                    match_run_id=row["id"],
                    week_start=row["week_start"],
                    already_existed=False,
                )

            existing = await connection.fetchrow(
                """
                SELECT id, week_start
                FROM match_runs
                WHERE week_start = $1
                """,
                week_start,
            )
            return TriggerMatchRunResponse(
                match_run_id=existing["id"],
                week_start=existing["week_start"],
                already_existed=True,
            )

    async def claim_pending_match_run(self) -> MatchRunRecord | None:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                row = await connection.fetchrow(
                    """
                    WITH claimed AS (
                        SELECT id
                        FROM match_runs
                        WHERE status = 'pending'
                        ORDER BY week_start ASC
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                    )
                    UPDATE match_runs mr
                    SET status = 'running',
                        started_at = NOW(),
                        completed_at = NULL,
                        error_message = NULL
                    FROM claimed
                    WHERE mr.id = claimed.id
                    RETURNING mr.*
                    """
                )
                if row is None:
                    return None
                return MatchRunRecord.model_validate(dict(row))

    async def load_latest_profiles_for_matching(self) -> list[LatestProfileEmbeddingRow]:
        rows = await self.pool.fetch(
            """
            SELECT DISTINCT ON (user_id)
                user_id,
                emb_relational_orientation::text AS emb_relational_orientation,
                emb_creativity::text AS emb_creativity,
                emb_intellectualism::text AS emb_intellectualism,
                emb_humor::text AS emb_humor,
                emb_interests::text AS emb_interests,
                emb_cultural_identity::text AS emb_cultural_identity,
                emb_political_orientation::text AS emb_political_orientation,
                w_relational_orientation,
                w_creativity,
                w_intellectualism,
                w_humor,
                w_interests,
                w_cultural_identity,
                w_political_orientation
            FROM user_profiles
            ORDER BY user_id, created_at DESC
            """
        )

        profiles: list[LatestProfileEmbeddingRow] = []
        for row in rows:
            profiles.append(
                LatestProfileEmbeddingRow(
                    user_id=row["user_id"],
                    embeddings=[
                        _parse_vector(row["emb_relational_orientation"]),
                        _parse_vector(row["emb_creativity"]),
                        _parse_vector(row["emb_intellectualism"]),
                        _parse_vector(row["emb_humor"]),
                        _parse_vector(row["emb_interests"]),
                        _parse_vector(row["emb_cultural_identity"]),
                        _parse_vector(row["emb_political_orientation"]),
                    ],
                    weights=[
                        float(row["w_relational_orientation"]),
                        float(row["w_creativity"]),
                        float(row["w_intellectualism"]),
                        float(row["w_humor"]),
                        float(row["w_interests"]),
                        float(row["w_cultural_identity"]),
                        float(row["w_political_orientation"]),
                    ],
                )
            )
        return profiles

    async def replace_user_matches(
        self,
        match_run_id: str,
        rows: list[MatchInsertRow],
    ) -> None:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    "DELETE FROM user_matches WHERE match_run_id = $1",
                    match_run_id,
                )
                if not rows:
                    return
                await connection.executemany(
                    """
                    INSERT INTO user_matches (
                        id,
                        match_run_id,
                        user_id,
                        matched_user_id,
                        rank,
                        similarity_score,
                        score_breakdown
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
                    """,
                    [
                        (
                            str(uuid4()),
                            match_run_id,
                            row.user_id,
                            row.matched_user_id,
                            row.rank,
                            row.similarity_score,
                            json.dumps(row.score_breakdown),
                        )
                        for row in rows
                    ],
                )

    async def complete_match_run(self, match_run_id: str, user_count: int) -> None:
        await self.pool.execute(
            """
            UPDATE match_runs
            SET status = 'completed',
                completed_at = NOW(),
                user_count = $2,
                error_message = NULL
            WHERE id = $1
            """,
            match_run_id,
            user_count,
        )

    async def fail_match_run(self, match_run_id: str, error_message: str) -> None:
        await self.pool.execute(
            """
            UPDATE match_runs
            SET status = 'failed',
                completed_at = NOW(),
                error_message = $2
            WHERE id = $1
            """,
            match_run_id,
            error_message,
        )

    def _profile_record_from_row(self, row: asyncpg.Record) -> ProfileRecord:
        return ProfileRecord(
            id=row["id"],
            user_id=row["user_id"],
            job_id=row["job_id"],
            profile_version=row["profile_version"],
            created_at=row["created_at"],
            personality_json=PersonalitySummary.model_validate(_ensure_json(row["personality_json"])),
            weights=ProfileWeights(
                w_relational_orientation=row["w_relational_orientation"],
                w_creativity=row["w_creativity"],
                w_intellectualism=row["w_intellectualism"],
                w_humor=row["w_humor"],
                w_interests=row["w_interests"],
                w_cultural_identity=row["w_cultural_identity"],
                w_political_orientation=row["w_political_orientation"],
            ),
        )
