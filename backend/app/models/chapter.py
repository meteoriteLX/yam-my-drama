from pydantic import BaseModel, Field, field_validator


class ChapterParseRequest(BaseModel):
    text: str = Field(..., min_length=1, description="待解析的小说全文")

    @field_validator("text")
    @classmethod
    def strip_and_validate_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("小说文本不能为空。")
        return stripped


class ChapterItem(BaseModel):
    chapter_number: int
    title: str
    heading: str
    content: str
    char_count: int
    paragraph_count: int


class ChapterParseResponse(BaseModel):
    valid: bool
    chapter_count: int
    min_chapters_required: int
    message: str
    preamble: str = ""
    chapters: list[ChapterItem]
