from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from backend.app.job_repository import SummaryJobRepository, utc_now
from backend.app.main import app, get_job_repository
from backend.app.models import SummaryJobRecord, TraitEntry, TraitSummary


class InMemoryJobRepository(SummaryJobRepository):
    def __init__(self):
        self.jobs: dict[str, SummaryJobRecord] = {}
        self.stage_history: dict[str, list[str]] = {}

    def create_job(
        self,
        *,
        job_id: str,
        source_filename: str,
        duration_seconds: float | None,
    ) -> SummaryJobRecord:
        now = utc_now()
        job = SummaryJobRecord(
            id=job_id,
            status="queued",
            stage="queued",
            created_at=now,
            updated_at=now,
            started_at=None,
            completed_at=None,
            source_filename=source_filename,
            mime_type=None,
            duration_seconds=duration_seconds,
            summary_json=None,
            error_code=None,
            error_message=None,
        )
        self.jobs[job_id] = job
        self.stage_history[job_id] = ["queued"]
        return job

    def mark_started(self, job_id: str, stage: str) -> SummaryJobRecord:
        return self._update(
            job_id,
            status="processing",
            stage=stage,
            started_at=utc_now(),
        )

    def update_stage(
        self,
        job_id: str,
        stage: str,
        *,
        mime_type: str | None = None,
        duration_seconds: float | None = None,
    ) -> SummaryJobRecord:
        updates = {"status": "processing", "stage": stage}
        if mime_type is not None:
            updates["mime_type"] = mime_type
        if duration_seconds is not None:
            updates["duration_seconds"] = duration_seconds
        return self._update(job_id, **updates)

    def complete_job(self, job_id: str, summary: TraitSummary) -> SummaryJobRecord:
        return self._update(
            job_id,
            status="completed",
            stage="completed",
            completed_at=utc_now(),
            summary_json=summary,
            error_code=None,
            error_message=None,
        )

    def fail_job(self, job_id: str, code: str, message: str) -> SummaryJobRecord:
        return self._update(
            job_id,
            status="failed",
            stage="failed",
            completed_at=utc_now(),
            error_code=code,
            error_message=message,
        )

    def get_job(self, job_id: str) -> SummaryJobRecord | None:
        return self.jobs.get(job_id)

    def _update(self, job_id: str, **updates) -> SummaryJobRecord:
        job = self.jobs[job_id]
        next_job = job.model_copy(
            update={
                **updates,
                "updated_at": utc_now(),
            }
        )
        self.jobs[job_id] = next_job
        self.stage_history.setdefault(job_id, []).append(next_job.stage)
        return next_job


@pytest.fixture
def repository() -> InMemoryJobRepository:
    return InMemoryJobRepository()


@pytest.fixture
def client(repository: InMemoryJobRepository) -> Iterator[TestClient]:
    app.dependency_overrides[get_job_repository] = lambda: repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_summary() -> TraitSummary:
    return TraitSummary(
        relational_orientation=TraitEntry(
            description="warm and community-driven",
            weight=0.15,
        ),
        creativity=TraitEntry(
            description="high appetite for visual experimentation",
            weight=0.15,
        ),
        intellectualism=TraitEntry(
            description="drawn to explanatory and reflective content",
            weight=0.14,
        ),
        humor=TraitEntry(
            description="responds to playful absurdity",
            weight=0.11,
        ),
        interests=TraitEntry(
            description="likes design, self-improvement, and commentary",
            weight=0.16,
        ),
        cultural_identity=TraitEntry(
            description="strong orientation toward internet-native culture",
            weight=0.1,
        ),
        political_orientation=TraitEntry(
            description="leans toward civic-minded progressive discourse",
            weight=0.19,
        ),
    )
