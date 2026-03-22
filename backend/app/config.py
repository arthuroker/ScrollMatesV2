import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    supabase_db_url: str
    supabase_jwt_secret: str
    admin_secret: str
    gemini_api_key: str
    gemini_model: str
    gemini_embedding_model: str
    match_top_k: int
    match_poll_interval_seconds: float
    cors_allow_origins: tuple[str, ...]


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    origins = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
        if origin.strip()
    )

    return Settings(
        supabase_db_url=_require_env("SUPABASE_DB_URL"),
        supabase_jwt_secret=_require_env("SUPABASE_JWT_SECRET"),
        admin_secret=_require_env("ADMIN_SECRET"),
        gemini_api_key=_require_env("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        gemini_embedding_model=os.getenv(
            "GEMINI_EMBEDDING_MODEL",
            "text-embedding-004",
        ),
        match_top_k=max(1, int(os.getenv("MATCH_TOP_K", "5"))),
        match_poll_interval_seconds=max(
            1.0,
            float(os.getenv("MATCH_POLL_INTERVAL_SECONDS", "10")),
        ),
        cors_allow_origins=origins or ("*",),
    )
