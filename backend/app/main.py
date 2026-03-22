from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .auth import AuthenticatedUser, get_current_user, require_admin
from .config import Settings, get_settings
from .db import create_pool
from .errors import ApiError
from .gemini_client import GeminiClient
from .match_service import MatchRunService, run_match_worker
from .media import persist_upload
from .models import (
    MatchResponse,
    ProfileResponse,
    SummaryJobResponse,
    TriggerMatchRunResponse,
    UploadJobResponse,
)
from .profile_service import ProfilePipelineService
from .repository import PostgresRepository


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@dataclass
class AppServices:
    settings: Settings
    repository: PostgresRepository
    profile_service: ProfilePipelineService
    match_service: MatchRunService
    match_worker_task: asyncio.Task | None = None


def _current_week_start_utc() -> datetime.date:
    current_date = datetime.now(timezone.utc).date()
    return current_date - timedelta(days=current_date.weekday())


def create_app(services: AppServices | None = None, *, start_worker: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if services is None:
            settings = get_settings()
            pool = await create_pool(settings.supabase_db_url)
            repository = PostgresRepository(pool)
            profile_service = ProfilePipelineService(repository, GeminiClient(settings))
            match_service = MatchRunService(repository, settings.match_top_k)
            app_services = AppServices(
                settings=settings,
                repository=repository,
                profile_service=profile_service,
                match_service=match_service,
            )
            if start_worker:
                app_services.match_worker_task = asyncio.create_task(
                    run_match_worker(
                        match_service,
                        settings.match_poll_interval_seconds,
                    )
                )
            app.state.services = app_services
            try:
                yield
            finally:
                if app_services.match_worker_task is not None:
                    app_services.match_worker_task.cancel()
                    await asyncio.gather(app_services.match_worker_task, return_exceptions=True)
                await pool.close()
        else:
            app.state.services = services
            yield

    settings = services.settings if services is not None else Settings(
        supabase_db_url="",
        supabase_jwt_secret="",
        admin_secret="",
        gemini_api_key="",
        gemini_model="gemini-2.5-flash",
        gemini_embedding_model="text-embedding-004",
        match_top_k=5,
        match_poll_interval_seconds=10.0,
        cors_allow_origins=("*",),
    )
    app = FastAPI(title="ScrollMates API", lifespan=lifespan)
    if services is not None:
        app.dependency_overrides[get_settings] = lambda: services.settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ApiError)
    async def api_error_handler(_, exc: ApiError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    def get_services() -> AppServices:
        return app.state.services

    @app.get("/api/health")
    async def health_check():
        return {"status": "ok"}

    @app.post("/api/upload", response_model=UploadJobResponse, status_code=202)
    async def upload_video(
        background_tasks: BackgroundTasks,
        video: UploadFile = File(...),
        duration_seconds: float | None = Form(default=None),
        current_user: AuthenticatedUser = Depends(get_current_user),
        app_services: AppServices = Depends(get_services),
    ):
        job_id = str(uuid4())
        source_filename = video.filename or "upload.video"
        await app_services.repository.create_summary_job(
            job_id=job_id,
            user_id=current_user.user_id,
            source_filename=source_filename,
            mime_type=video.content_type,
            duration_seconds=duration_seconds,
        )

        try:
            video_path = await persist_upload(video)
        except ApiError as exc:
            await app_services.repository.fail_job(job_id, exc.code, exc.message)
            raise
        except Exception as exc:
            await app_services.repository.fail_job(
                job_id,
                "upload_persist_failed",
                f"Unable to persist the uploaded video: {exc}",
            )
            raise ApiError(
                500,
                "upload_persist_failed",
                "Unable to persist the uploaded video.",
            ) from exc

        background_tasks.add_task(
            app_services.profile_service.process_job,
            job_id=job_id,
            user_id=current_user.user_id,
            video_path=video_path,
            content_type=video.content_type,
            filename=source_filename,
            client_duration_seconds=duration_seconds,
        )
        return UploadJobResponse(job_id=job_id)

    @app.get("/api/jobs/{job_id}", response_model=SummaryJobResponse)
    async def get_job(
        job_id: str,
        current_user: AuthenticatedUser = Depends(get_current_user),
        app_services: AppServices = Depends(get_services),
    ):
        job = await app_services.repository.get_summary_job_for_user(job_id, current_user.user_id)
        if job is None:
            raise ApiError(404, "summary_job_not_found", "Summary job not found.")
        return job

    @app.get("/api/profile", response_model=ProfileResponse)
    async def get_profile(
        current_user: AuthenticatedUser = Depends(get_current_user),
        app_services: AppServices = Depends(get_services),
    ):
        profile = await app_services.repository.get_latest_profile_for_user(current_user.user_id)
        if profile is None:
            raise ApiError(404, "profile_not_found", "Personality profile not found.")
        return profile

    @app.get("/api/matches", response_model=list[MatchResponse])
    async def get_matches(
        current_user: AuthenticatedUser = Depends(get_current_user),
        app_services: AppServices = Depends(get_services),
    ):
        return await app_services.repository.get_latest_matches_for_user(current_user.user_id)

    @app.post("/api/admin/trigger-match-run", response_model=TriggerMatchRunResponse)
    async def trigger_match_run(
        _: AuthenticatedUser = Depends(require_admin),
        app_services: AppServices = Depends(get_services),
    ):
        return await app_services.repository.trigger_match_run(_current_week_start_utc())

    return app


app = create_app()
