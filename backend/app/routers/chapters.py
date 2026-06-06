from fastapi import APIRouter, HTTPException

from app.models.chapter import ChapterItem, ChapterParseRequest, ChapterParseResponse
from app.services.chapter_parser import ChapterParseError, parse_novel

router = APIRouter(prefix="/api/chapters", tags=["chapters"])


@router.post("/parse", response_model=ChapterParseResponse)
def parse_chapters(payload: ChapterParseRequest) -> ChapterParseResponse:
    try:
        result = parse_novel(payload.text)
    except ChapterParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ChapterParseResponse(
        valid=result.is_valid,
        chapter_count=result.chapter_count,
        min_chapters_required=result.min_chapters_required,
        message=result.message,
        preamble=result.preamble,
        chapters=[
            ChapterItem(
                chapter_number=chapter.chapter_number,
                title=chapter.title,
                heading=chapter.heading,
                content=chapter.content,
                char_count=chapter.char_count,
                paragraph_count=chapter.paragraph_count,
            )
            for chapter in result.chapters
        ],
    )
