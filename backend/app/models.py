from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SummaryJobStatus = Literal["queued", "processing", "completed", "failed"]
SummaryJobStage = Literal[
    "queued",
    "persisting_upload",
    "validating_video",
    "uploading_to_gemini",
    "waiting_for_gemini",
    "generating_summary",
    "completed",
    "failed",
]


class TraitEntry(BaseModel):
    description: str = Field(min_length=1)
    weight: float = Field(ge=0.0, le=1.0)


class TraitSummary(BaseModel):
    relational_orientation: TraitEntry
    creativity: TraitEntry
    intellectualism: TraitEntry
    humor: TraitEntry
    interests: TraitEntry
    cultural_identity: TraitEntry
    political_orientation: TraitEntry


class SummaryJobError(BaseModel):
    code: str
    message: str


class SummaryJobKickoff(BaseModel):
    job_id: str
    status: SummaryJobStatus
    stage: SummaryJobStage


class SummaryJobStatusResponse(BaseModel):
    job_id: str
    status: SummaryJobStatus
    stage: SummaryJobStage
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    summary: TraitSummary | None = None
    error: SummaryJobError | None = None


class SummaryJobRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    status: SummaryJobStatus
    stage: SummaryJobStage
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    source_filename: str | None = None
    mime_type: str | None = None
    duration_seconds: float | None = None
    summary_json: TraitSummary | None = None
    error_code: str | None = None
    error_message: str | None = None

    def to_kickoff_response(self) -> SummaryJobKickoff:
        return SummaryJobKickoff(job_id=self.id, status=self.status, stage=self.stage)

    def to_status_response(self) -> SummaryJobStatusResponse:
        error = None
        if self.error_code and self.error_message:
            error = SummaryJobError(code=self.error_code, message=self.error_message)

        return SummaryJobStatusResponse(
            job_id=self.id,
            status=self.status,
            stage=self.stage,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            summary=self.summary_json,
            error=error,
        )
