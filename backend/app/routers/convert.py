from fastapi import APIRouter, HTTPException

from app.models.script import NovelConvertRequest, NovelConvertResponse
from app.services.conversion_jobs import ConversionJobSnapshot, get_conversion_job_store
from app.services.conversion_pipeline import ConversionPipelineError, get_conversion_pipeline
from app.services.llm_client import LLMNotConfiguredError, LLMRequestError

router = APIRouter(prefix="/api/convert", tags=["convert"])


@router.post("/novel-to-script", response_model=NovelConvertResponse)
def convert_novel_to_script(payload: NovelConvertRequest) -> NovelConvertResponse:
    pipeline = get_conversion_pipeline()

    try:
        return pipeline.convert_novel(
            payload.text,
            script_title=payload.script_title,
            author=payload.author,
            source_novel_title=payload.source_novel_title,
            source_novel_author=payload.source_novel_author,
        )
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ConversionPipelineError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/jobs", response_model=ConversionJobSnapshot, status_code=202)
def create_conversion_job(payload: NovelConvertRequest) -> ConversionJobSnapshot:
    return get_conversion_job_store().create_job(payload)


@router.get("/jobs/{job_id}", response_model=ConversionJobSnapshot)
def get_conversion_job(job_id: str) -> ConversionJobSnapshot:
    job = get_conversion_job_store().get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="转换任务不存在")
    return job
