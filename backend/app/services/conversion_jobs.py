from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.script import NovelConvertRequest, NovelConvertResponse
from app.services.conversion_pipeline import ConversionPipelineError, get_conversion_pipeline
from app.services.llm_client import LLMNotConfiguredError, LLMRequestError

JobStatus = Literal["queued", "running", "succeeded", "failed"]


class ConversionJobSnapshot(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(..., ge=0, le=100)
    stage: str
    message: str
    created_at: str
    updated_at: str
    result: NovelConvertResponse | None = None
    error: str | None = None


class ConversionJobStore:
    """轻量级内存任务队列，适合实训 Demo 的单进程异步转换场景。"""

    def __init__(self) -> None:
        self._jobs: dict[str, ConversionJobSnapshot] = {}
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="convert-job")

    def create_job(self, payload: NovelConvertRequest) -> ConversionJobSnapshot:
        now = self._now()
        job = ConversionJobSnapshot(
            job_id=uuid4().hex,
            status="queued",
            progress=0,
            stage="queued",
            message="转换任务已创建，等待执行",
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._jobs[job.job_id] = job

        self._executor.submit(self._run_job, job.job_id, payload)
        return job

    def get_job(self, job_id: str) -> ConversionJobSnapshot | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _run_job(self, job_id: str, payload: NovelConvertRequest) -> None:
        self._update_job(job_id, status="running", progress=3, stage="starting", message="正在启动转换 Pipeline")

        def report(progress: int, stage: str, message: str) -> None:
            self._update_job(
                job_id,
                status="running",
                progress=max(0, min(99, progress)),
                stage=stage,
                message=message,
            )

        try:
            pipeline = get_conversion_pipeline()
            result = pipeline.convert_novel(
                payload.text,
                script_title=payload.script_title,
                author=payload.author,
                source_novel_title=payload.source_novel_title,
                source_novel_author=payload.source_novel_author,
                progress_callback=report,
            )
        except LLMNotConfiguredError as exc:
            self._fail_job(job_id, f"LLM 未配置：{exc}")
        except LLMRequestError as exc:
            self._fail_job(job_id, f"LLM 请求失败：{exc}")
        except ConversionPipelineError as exc:
            self._fail_job(job_id, str(exc))
        except Exception as exc:  # pragma: no cover - 防止后台线程异常吞没任务状态
            self._fail_job(job_id, f"转换任务异常：{exc}")
        else:
            self._update_job(
                job_id,
                status="succeeded",
                progress=100,
                stage="completed",
                message="转换完成，可预览并导出 YAML",
                result=result,
                error=None,
            )

    def _fail_job(self, job_id: str, error: str) -> None:
        self._update_job(
            job_id,
            status="failed",
            progress=100,
            stage="failed",
            message="转换失败，请查看错误信息后重试",
            error=error,
        )

    def _update_job(self, job_id: str, **changes) -> None:
        with self._lock:
            current = self._jobs.get(job_id)
            if current is None:
                return
            data = current.model_dump()
            data.update(changes)
            data["updated_at"] = self._now()
            self._jobs[job_id] = ConversionJobSnapshot(**data)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


_job_store: ConversionJobStore | None = None


def get_conversion_job_store() -> ConversionJobStore:
    global _job_store
    if _job_store is None:
        _job_store = ConversionJobStore()
    return _job_store


def reset_conversion_job_store() -> None:
    global _job_store
    _job_store = None
