from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


CATEGORY_NAMES = (
    "relational_orientation",
    "creativity",
    "intellectualism",
    "humor",
    "interests",
    "cultural_identity",
    "political_orientation",
)
EMBEDDING_DIMENSION = 768
COMPOSITE_DIMENSION = EMBEDDING_DIMENSION * len(CATEGORY_NAMES)

JobStatus = Literal["pending", "processing", "completed", "failed"]
JobStage = Literal["upload", "gemini_analysis", "embedding", "done"]


class TraitEntry(BaseModel):
    description: str = Field(min_length=1)
    weight: float = Field(ge=0.0, le=1.0)


class PersonalitySummary(BaseModel):
    relational_orientation: TraitEntry
    creativity: TraitEntry
    intellectualism: TraitEntry
    humor: TraitEntry
    interests: TraitEntry
    cultural_identity: TraitEntry
    political_orientation: TraitEntry


class UploadJobResponse(BaseModel):
    job_id: str


class SummaryJobResponse(BaseModel):
    id: str
    status: JobStatus
    stage: JobStage
    created_at: datetime
    updated_at: datetime
    error_code: str | None = None
    error_message: str | None = None


class ProfileWeights(BaseModel):
    w_relational_orientation: float
    w_creativity: float
    w_intellectualism: float
    w_humor: float
    w_interests: float
    w_cultural_identity: float
    w_political_orientation: float


class ProfileResponse(BaseModel):
    id: str
    profile_version: int
    created_at: datetime
    personality_json: PersonalitySummary
    weights: ProfileWeights


class MatchResponse(BaseModel):
    rank: int
    similarity_score: float
    score_breakdown: dict[str, float]
    matched_user_id: str
    week_start: date


class TriggerMatchRunResponse(BaseModel):
    match_run_id: str
    week_start: date
    already_existed: bool


class SummaryJobRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str
    status: JobStatus
    stage: JobStage
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    source_filename: str | None = None
    mime_type: str | None = None
    duration_seconds: float | None = None
    summary_json: Any | None = None
    error_code: str | None = None
    error_message: str | None = None


class ProfileRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str
    job_id: str
    profile_version: int
    created_at: datetime
    personality_json: PersonalitySummary
    weights: ProfileWeights


class MatchRunRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    week_start: date
    status: Literal["pending", "running", "completed", "failed"]
    triggered_by: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    user_count: int | None = None
    error_message: str | None = None
    created_at: datetime


class LatestProfileEmbeddingRow(BaseModel):
    user_id: str
    embeddings: list[list[float]]
    weights: list[float]


class MatchInsertRow(BaseModel):
    user_id: str
    matched_user_id: str
    rank: int
    similarity_score: float
    score_breakdown: dict[str, float]
