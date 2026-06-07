from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.scene import SceneSplitRequest, SceneSplitResponse
from app.services.llm_client import LLMNotConfiguredError, LLMRequestError
from app.services.scene_splitter import SceneSplitError, get_scene_split_service

router = APIRouter(prefix="/api/scenes", tags=["scenes"])


@router.post("/split-chapter", response_model=SceneSplitResponse)
def split_chapter(payload: SceneSplitRequest) -> SceneSplitResponse:
    service = get_scene_split_service()

    try:
        result = service.split_chapter(
            chapter_number=payload.chapter_number,
            chapter_title=payload.chapter_title,
            content=payload.content,
        )
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except SceneSplitError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return SceneSplitResponse(
        chapter_number=result.chapter_number,
        chapter_title=result.chapter_title,
        scene_count=len(result.scenes),
        scenes=result.scenes,
        characters_mentioned=result.characters_mentioned,
        model=settings.llm_model,
    )
