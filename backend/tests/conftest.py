from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from backend.app.main import AppServices, create_app
from backend.app.match_service import MatchRunService
from backend.app.models import LatestProfileEmbeddingRow, MatchInsertRow, MatchRunRecord, MatchResponse, PersonalitySummary, ProfileRecord, ProfileResponse, ProfileWeights, SummaryJobRecord, SummaryJobResponse, TriggerMatchRunResponse
from backend.app.profile_service import ProfilePipelineService
from backend.app.repository import utc_now
from backend.tests.helpers import build_settings, sample_embeddings, sample_personality


@dataclass
class FakeGeminiClient:
    personality: PersonalitySummary
    embeddings: dict[str, list[float]]
    analyze_error: Exception | None = None
    embedding_error: Exception | None = None

    def analyze_video(self, video_path: str, mime_type: str) -> PersonalitySummary:
        if self.analyze_error is not None:
            raise self.analyze_error
        return self.personality

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self.embedding_error is not None:
            raise self.embedding_error
        return [self.embeddings[key] for key in self.embeddings]


class FakeRepository:
    def __init__(self):
        self.jobs: dict[str, SummaryJobRecord] = {}
        self.profile_rows: list[ProfileRecord] = []
        self.profile_embeddings_by_id: dict[str, dict[str, list[float]]] = {}
        self.profile_composites_by_id: dict[str, list[float]] = {}
        self.match_runs: dict[str, MatchRunRecord] = {}
        self.match_rows_by_run: dict[str, list[MatchInsertRow]] = {}
        self.job_stage_history: dict[str, list[str]] = {}

    async def create_summary_job(
        self,
        *,
        job_id: str,
        user_id: str,
        source_filename: str,
        mime_type: str | None,
        duration_seconds: float | None,
    ) -> SummaryJobRecord:
        now = utc_now()
        record = SummaryJobRecord(
            id=job_id,
            user_id=user_id,
            status="pending",
            stage="upload",
            created_at=now,
            updated_at=now,
            started_at=None,
            completed_at=None,
            source_filename=source_filename,
            mime_type=mime_type,
            duration_seconds=duration_seconds,
            summary_json=None,
            error_code=None,
            error_message=None,
        )
        self.jobs[job_id] = record
        self.job_stage_history[job_id] = ["upload"]
        return record

    async def mark_job_processing(
        self,
        job_id: str,
        stage: str,
        *,
        mime_type: str | None = None,
        duration_seconds: float | None = None,
        summary: PersonalitySummary | None = None,
    ) -> SummaryJobRecord:
        current = self.jobs[job_id]
        updated = current.model_copy(
            update={
                "status": "processing",
                "stage": stage,
                "mime_type": mime_type or current.mime_type,
                "duration_seconds": duration_seconds if duration_seconds is not None else current.duration_seconds,
                "summary_json": summary.model_dump(mode="json") if summary is not None else current.summary_json,
                "started_at": current.started_at or utc_now(),
                "updated_at": utc_now(),
            }
        )
        self.jobs[job_id] = updated
        self.job_stage_history[job_id].append(stage)
        return updated

    async def complete_job(self, job_id: str) -> SummaryJobRecord:
        current = self.jobs[job_id]
        updated = current.model_copy(
            update={
                "status": "completed",
                "stage": "done",
                "completed_at": utc_now(),
                "updated_at": utc_now(),
                "error_code": None,
                "error_message": None,
            }
        )
        self.jobs[job_id] = updated
        self.job_stage_history[job_id].append("done")
        return updated

    async def fail_job(self, job_id: str, code: str, message: str) -> SummaryJobRecord:
        current = self.jobs[job_id]
        updated = current.model_copy(
            update={
                "status": "failed",
                "completed_at": utc_now(),
                "updated_at": utc_now(),
                "error_code": code,
                "error_message": message,
            }
        )
        self.jobs[job_id] = updated
        return updated

    async def get_summary_job_for_user(self, job_id: str, user_id: str) -> SummaryJobResponse | None:
        job = self.jobs.get(job_id)
        if job is None or job.user_id != user_id:
            return None
        return SummaryJobResponse(
            id=job.id,
            status=job.status,
            stage=job.stage,
            created_at=job.created_at,
            updated_at=job.updated_at,
            error_code=job.error_code,
            error_message=job.error_message,
        )

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
        now = utc_now()
        record = ProfileRecord(
            id=f"profile-{len(self.profile_rows) + 1}",
            user_id=user_id,
            job_id=job_id,
            profile_version=profile_version,
            created_at=now,
            personality_json=personality_json,
            weights=ProfileWeights(
                w_relational_orientation=weights["relational_orientation"],
                w_creativity=weights["creativity"],
                w_intellectualism=weights["intellectualism"],
                w_humor=weights["humor"],
                w_interests=weights["interests"],
                w_cultural_identity=weights["cultural_identity"],
                w_political_orientation=weights["political_orientation"],
            ),
        )
        self.profile_rows.append(record)
        self.profile_embeddings_by_id[record.id] = embeddings
        self.profile_composites_by_id[record.id] = composite_embedding
        return record

    async def get_latest_profile_for_user(self, user_id: str) -> ProfileResponse | None:
        rows = [row for row in self.profile_rows if row.user_id == user_id]
        if not rows:
            return None
        latest = rows[-1]
        return ProfileResponse(
            id=latest.id,
            profile_version=latest.profile_version,
            created_at=latest.created_at,
            personality_json=latest.personality_json,
            weights=latest.weights,
        )

    async def get_latest_matches_for_user(self, user_id: str) -> list[MatchResponse]:
        completed = [
            run for run in self.match_runs.values() if run.status == "completed"
        ]
        if not completed:
            return []
        latest_run = max(completed, key=lambda run: run.week_start)
        rows = self.match_rows_by_run.get(latest_run.id, [])
        return [
            MatchResponse(
                rank=row.rank,
                similarity_score=row.similarity_score,
                score_breakdown=row.score_breakdown,
                matched_user_id=row.matched_user_id,
                week_start=latest_run.week_start,
            )
            for row in rows
            if row.user_id == user_id
        ]

    async def trigger_match_run(self, week_start):
        for run in self.match_runs.values():
            if run.week_start == week_start:
                return TriggerMatchRunResponse(
                    match_run_id=run.id,
                    week_start=run.week_start,
                    already_existed=True,
                )

        run = MatchRunRecord(
            id=f"run-{len(self.match_runs) + 1}",
            week_start=week_start,
            status="pending",
            triggered_by="manual",
            started_at=None,
            completed_at=None,
            user_count=None,
            error_message=None,
            created_at=utc_now(),
        )
        self.match_runs[run.id] = run
        return TriggerMatchRunResponse(
            match_run_id=run.id,
            week_start=run.week_start,
            already_existed=False,
        )

    async def claim_pending_match_run(self):
        pending = sorted(
            (run for run in self.match_runs.values() if run.status == "pending"),
            key=lambda run: run.week_start,
        )
        if not pending:
            return None
        run = pending[0]
        updated = run.model_copy(update={"status": "running", "started_at": utc_now()})
        self.match_runs[run.id] = updated
        return updated

    async def load_latest_profiles_for_matching(self):
        latest_by_user = {}
        for row in self.profile_rows:
            latest_by_user[row.user_id] = row
        result = []
        for user_id, row in latest_by_user.items():
            result.append(
                LatestProfileEmbeddingRow(
                    user_id=user_id,
                    embeddings=list(self.profile_embeddings_by_id[row.id].values()),
                    weights=[
                        row.weights.w_relational_orientation,
                        row.weights.w_creativity,
                        row.weights.w_intellectualism,
                        row.weights.w_humor,
                        row.weights.w_interests,
                        row.weights.w_cultural_identity,
                        row.weights.w_political_orientation,
                    ],
                )
            )
        return result

    async def replace_user_matches(self, match_run_id: str, rows: list[MatchInsertRow]) -> None:
        self.match_rows_by_run[match_run_id] = rows

    async def complete_match_run(self, match_run_id: str, user_count: int) -> None:
        run = self.match_runs[match_run_id]
        self.match_runs[match_run_id] = run.model_copy(
            update={"status": "completed", "completed_at": utc_now(), "user_count": user_count}
        )

    async def fail_match_run(self, match_run_id: str, error_message: str) -> None:
        run = self.match_runs[match_run_id]
        self.match_runs[match_run_id] = run.model_copy(
            update={"status": "failed", "completed_at": utc_now(), "error_message": error_message}
        )


@pytest.fixture
def repository() -> FakeRepository:
    return FakeRepository()


@pytest.fixture
def profile_service(repository: FakeRepository) -> ProfilePipelineService:
    return ProfilePipelineService(
        repository=repository,
        gemini_client=FakeGeminiClient(
            personality=sample_personality(),
            embeddings=sample_embeddings(),
        ),
    )


@pytest.fixture
def match_service(repository: FakeRepository) -> MatchRunService:
    return MatchRunService(repository=repository, top_k=2)


@pytest.fixture
def client(repository: FakeRepository, profile_service: ProfilePipelineService, match_service: MatchRunService) -> Iterator[TestClient]:
    services = AppServices(
        settings=build_settings(),
        repository=repository,
        profile_service=profile_service,
        match_service=match_service,
    )
    app = create_app(services=services, start_worker=False)
    with TestClient(app) as test_client:
        yield test_client
