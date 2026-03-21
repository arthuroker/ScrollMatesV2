from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .errors import ApiError
from .job_repository import SummaryJobRepository, SupabaseJobRepository
from .models import SummaryJobKickoff, SummaryJobStatusResponse
from .summary_service import get_model_name, persist_upload, process_summary_job


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="ScrollMates API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_job_repository() -> SummaryJobRepository:
    return SupabaseJobRepository.from_env()


@app.exception_handler(ApiError)
async def api_error_handler(_, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "model": get_model_name()}


@app.post("/api/summarize", response_model=SummaryJobKickoff, status_code=202)
async def summarize(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    duration_seconds: float | None = Form(default=None),
    repository: SummaryJobRepository = Depends(get_job_repository),
):
    job_id = str(uuid4())
    source_filename = video.filename or "upload.video"
    job = repository.create_job(
        job_id=job_id,
        source_filename=source_filename,
        duration_seconds=duration_seconds,
    )

    try:
        job = repository.mark_started(job_id, "persisting_upload")
        video_path = await persist_upload(video)
    except ApiError as exc:
        failed_job = repository.fail_job(job_id, exc.code, exc.message)
        return failed_job.to_kickoff_response()
    except Exception as exc:
        failed_job = repository.fail_job(
            job_id,
            "upload_persist_failed",
            f"Unable to persist the uploaded video: {exc}",
        )
        return failed_job.to_kickoff_response()

    background_tasks.add_task(
        process_summary_job,
        job_id,
        video_path,
        video.content_type,
        source_filename,
        duration_seconds,
        repository,
    )
    return job.to_kickoff_response()


@app.get("/api/summarize/{job_id}", response_model=SummaryJobStatusResponse)
async def get_summary_job(
    job_id: str,
    repository: SummaryJobRepository = Depends(get_job_repository),
):
    job = repository.get_job(job_id)
    if job is None:
        raise ApiError(404, "summary_job_not_found", "Summary job not found.")
    return job.to_status_response()
