from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.scene import SceneSplitRequest, SceneSplitResponse
from app.models.script_block import ScriptGenerateRequest, ScriptGenerateResponse
from app.services.llm_client import LLMNotConfiguredError, LLMRequestError
from app.services.scene_splitter import SceneSplitError, get_scene_split_service
from app.services.script_generator import (
    ScriptGenerateError,
    get_script_generator_service,
)

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


@router.post("/generate-script", response_model=ScriptGenerateResponse)
def generate_scene_script(payload: ScriptGenerateRequest) -> ScriptGenerateResponse:
    service = get_script_generator_service()

    try:
        scene_block, characters = service.generate_scene_script(
            act=payload.act,
            scene_id=payload.scene_id,
            chapter_number=payload.chapter_number,
            chapter_content=payload.chapter_content,
            scene=payload.scene,
            characters=payload.characters,
        )
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ScriptGenerateError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ScriptGenerateResponse(
        act=payload.act,
        scene=scene_block,
        characters=characters,
        model=settings.llm_model,
    )
