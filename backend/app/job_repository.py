import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from urllib import error, parse, request

from .errors import ApiError
from .models import SummaryJobRecord, SummaryJobStage, TraitSummary


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SummaryJobRepository(ABC):
    @abstractmethod
    def create_job(
        self,
        *,
        job_id: str,
        source_filename: str,
        duration_seconds: float | None,
    ) -> SummaryJobRecord:
        raise NotImplementedError

    @abstractmethod
    def mark_started(self, job_id: str, stage: SummaryJobStage) -> SummaryJobRecord:
        raise NotImplementedError

    @abstractmethod
    def update_stage(
        self,
        job_id: str,
        stage: SummaryJobStage,
        *,
        mime_type: str | None = None,
        duration_seconds: float | None = None,
    ) -> SummaryJobRecord:
        raise NotImplementedError

    @abstractmethod
    def complete_job(self, job_id: str, summary: TraitSummary) -> SummaryJobRecord:
        raise NotImplementedError

    @abstractmethod
    def fail_job(self, job_id: str, code: str, message: str) -> SummaryJobRecord:
        raise NotImplementedError

    @abstractmethod
    def get_job(self, job_id: str) -> SummaryJobRecord | None:
        raise NotImplementedError


class SupabaseJobRepository(SummaryJobRepository):
    def __init__(
        self,
        *,
        supabase_url: str,
        service_role_key: str,
        table_name: str = "summary_jobs",
        timeout_seconds: float = 30.0,
    ):
        self.endpoint = (
            f"{supabase_url.rstrip('/')}/rest/v1/{table_name}"
        )
        self.service_role_key = service_role_key
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "SupabaseJobRepository":
        supabase_url = os.getenv("SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        table_name = os.getenv("SUPABASE_SUMMARY_JOBS_TABLE", "summary_jobs")

        if not supabase_url or not service_role_key:
            raise ApiError(
                500,
                "missing_supabase_config",
                "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY before using summary jobs.",
            )

        return cls(
            supabase_url=supabase_url,
            service_role_key=service_role_key,
            table_name=table_name,
        )

    def create_job(
        self,
        *,
        job_id: str,
        source_filename: str,
        duration_seconds: float | None,
    ) -> SummaryJobRecord:
        now = utc_now().isoformat()
        row = self._request_single_row(
            "POST",
            payload={
                "id": job_id,
                "status": "queued",
                "stage": "queued",
                "created_at": now,
                "updated_at": now,
                "started_at": None,
                "completed_at": None,
                "source_filename": source_filename,
                "mime_type": None,
                "duration_seconds": duration_seconds,
                "summary_json": None,
                "error_code": None,
                "error_message": None,
            },
            prefer_representation=True,
        )
        return SummaryJobRecord.model_validate(row)

    def mark_started(self, job_id: str, stage: SummaryJobStage) -> SummaryJobRecord:
        return self._update_row(
            job_id,
            {
                "status": "processing",
                "stage": stage,
                "started_at": utc_now().isoformat(),
                "updated_at": utc_now().isoformat(),
            },
        )

    def update_stage(
        self,
        job_id: str,
        stage: SummaryJobStage,
        *,
        mime_type: str | None = None,
        duration_seconds: float | None = None,
    ) -> SummaryJobRecord:
        payload: dict[str, Any] = {
            "status": "processing",
            "stage": stage,
            "updated_at": utc_now().isoformat(),
        }
        if mime_type is not None:
            payload["mime_type"] = mime_type
        if duration_seconds is not None:
            payload["duration_seconds"] = duration_seconds
        return self._update_row(job_id, payload)

    def complete_job(self, job_id: str, summary: TraitSummary) -> SummaryJobRecord:
        completed_at = utc_now().isoformat()
        return self._update_row(
            job_id,
            {
                "status": "completed",
                "stage": "completed",
                "summary_json": summary.model_dump(mode="json"),
                "error_code": None,
                "error_message": None,
                "completed_at": completed_at,
                "updated_at": completed_at,
            },
        )

    def fail_job(self, job_id: str, code: str, message: str) -> SummaryJobRecord:
        completed_at = utc_now().isoformat()
        return self._update_row(
            job_id,
            {
                "status": "failed",
                "stage": "failed",
                "error_code": code,
                "error_message": message,
                "completed_at": completed_at,
                "updated_at": completed_at,
            },
        )

    def get_job(self, job_id: str) -> SummaryJobRecord | None:
        rows = self._request_json(
            "GET",
            query_params={"id": f"eq.{job_id}", "select": "*"},
        )
        if not rows:
            return None
        return SummaryJobRecord.model_validate(rows[0])

    def _update_row(self, job_id: str, payload: dict[str, Any]) -> SummaryJobRecord:
        row = self._request_single_row(
            "PATCH",
            query_params={"id": f"eq.{job_id}"},
            payload=payload,
            prefer_representation=True,
        )
        return SummaryJobRecord.model_validate(row)

    def _request_single_row(
        self,
        method: str,
        *,
        query_params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        prefer_representation: bool = False,
    ) -> dict[str, Any]:
        rows = self._request_json(
            method,
            query_params=query_params,
            payload=payload,
            prefer_representation=prefer_representation,
        )
        if not rows:
            raise ApiError(404, "summary_job_not_found", "Summary job not found.")
        return rows[0]

    def _request_json(
        self,
        method: str,
        *,
        query_params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        prefer_representation: bool = False,
    ) -> Any:
        url = self.endpoint
        if query_params:
            url = f"{url}?{parse.urlencode(query_params)}"

        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }
        if prefer_representation:
            headers["Prefer"] = "return=representation"

        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        req = request.Request(url, data=body, headers=headers, method=method)

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                data = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ApiError(
                502,
                "supabase_request_failed",
                f"Supabase request failed with status {exc.code}: {detail or exc.reason}",
            ) from exc
        except error.URLError as exc:
            raise ApiError(
                502,
                "supabase_request_failed",
                f"Supabase request failed: {exc.reason}",
            ) from exc

        if not data:
            return None
        return json.loads(data)
