from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.models.script_block import ScriptSceneBlock


class SceneRef(BaseModel):
    act: int = Field(..., ge=1)
    scene: str = Field(..., min_length=1)


class ScriptCharacter(BaseModel):
    id: str = Field(..., pattern=r"^char_[a-z0-9_]+$")
    name: str = Field(..., min_length=1)
    role: str
    first_appeared: SceneRef
    aliases: list[str] = Field(default_factory=list)
    description: str = ""
    traits: list[str] = Field(default_factory=list)


class ScriptAct(BaseModel):
    act: int = Field(..., ge=1)
    title: str = Field(..., min_length=1)
    summary: str = ""
    scenes: list[ScriptSceneBlock] = Field(default_factory=list)


class SourceNovelMeta(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    chapters_covered: list[int] = Field(..., min_length=1)


class ScriptMeta(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    source_novel: SourceNovelMeta
    created_at: str
    language: str = "zh-CN"
    subtitle: str = ""
    genre: str = ""
    logline: str = ""
    notes: str = ""


class ScriptDocument(BaseModel):
    schema_version: str = "1.0.0"
    meta: ScriptMeta
    characters: list[ScriptCharacter] = Field(..., min_length=1)
    acts: list[ScriptAct] = Field(..., min_length=1)


class NovelConvertRequest(BaseModel):
    text: str = Field(..., min_length=1)
    script_title: str = ""
    author: str = "yam-my-drama"
    source_novel_title: str = "未知"
    source_novel_author: str = "未知"

    @field_validator("text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("小说文本不能为空。")
        return stripped


class ConversionStats(BaseModel):
    chapter_count: int
    act_count: int
    scene_count: int
    character_count: int


class NovelConvertResponse(BaseModel):
    script: ScriptDocument
    yaml: str
    stats: ConversionStats
    model: str


def default_script_meta(
    *,
    script_title: str,
    author: str,
    source_novel_title: str,
    source_novel_author: str,
    chapters_covered: list[int],
) -> ScriptMeta:
    title = script_title or f"改编自《{source_novel_title}》"
    return ScriptMeta(
        title=title,
        author=author,
        source_novel=SourceNovelMeta(
            title=source_novel_title,
            author=source_novel_author,
            chapters_covered=chapters_covered,
        ),
        created_at=date.today().isoformat(),
        language="zh-CN",
        notes="由 yam-my-drama AI Pipeline 自动生成",
    )
