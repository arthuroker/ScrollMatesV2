from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from jose import jwt

from backend.app.config import Settings
from backend.app.models import CATEGORY_NAMES, PersonalitySummary, ProfileWeights, TraitEntry


TEST_JWT_SECRET = "test-jwt-secret"
TEST_ADMIN_SECRET = "test-admin-secret"


def build_settings() -> Settings:
    return Settings(
        supabase_db_url="postgres://unused",
        supabase_jwt_secret=TEST_JWT_SECRET,
        admin_secret=TEST_ADMIN_SECRET,
        gemini_api_key="test-key",
        gemini_model="gemini-test",
        gemini_embedding_model="text-embedding-004",
        match_top_k=5,
        match_poll_interval_seconds=3600,
        cors_allow_origins=("*",),
    )


def create_token(user_id: str) -> str:
    return jwt.encode({"sub": user_id, "role": "authenticated"}, TEST_JWT_SECRET, algorithm="HS256")


def sample_personality() -> PersonalitySummary:
    return PersonalitySummary(
        relational_orientation=TraitEntry(description="warm and community-driven", weight=0.15),
        creativity=TraitEntry(description="likes visual experimentation", weight=0.15),
        intellectualism=TraitEntry(description="drawn to reflective content", weight=0.14),
        humor=TraitEntry(description="responds to playful absurdity", weight=0.11),
        interests=TraitEntry(description="likes design and self-improvement", weight=0.16),
        cultural_identity=TraitEntry(description="internet-native and global", weight=0.1),
        political_orientation=TraitEntry(description="civic-minded and progressive", weight=0.19),
    )


def sample_weights() -> ProfileWeights:
    personality = sample_personality()
    return ProfileWeights(
        w_relational_orientation=personality.relational_orientation.weight,
        w_creativity=personality.creativity.weight,
        w_intellectualism=personality.intellectualism.weight,
        w_humor=personality.humor.weight,
        w_interests=personality.interests.weight,
        w_cultural_identity=personality.cultural_identity.weight,
        w_political_orientation=personality.political_orientation.weight,
    )


def sample_embedding(value: float) -> list[float]:
    return [value] * 768


def sample_embeddings(base: float = 1.0) -> dict[str, list[float]]:
    return {
        category_name: sample_embedding(base + index)
        for index, category_name in enumerate(CATEGORY_NAMES)
    }


def make_now() -> datetime:
    return datetime.now(timezone.utc)


def make_week_start() -> date:
    current_date = datetime.now(timezone.utc).date()
    return current_date - timedelta(days=current_date.weekday())
