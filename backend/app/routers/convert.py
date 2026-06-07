from fastapi import APIRouter, HTTPException

from app.models.script import NovelConvertRequest, NovelConvertResponse
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
