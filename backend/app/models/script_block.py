from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.models.scene import SceneSplitItem, SceneSplitParseError, extract_json_object


class CharacterRef(BaseModel):
    id: str = Field(..., pattern=r"^char_[a-z0-9_]+$")
    name: str = Field(..., min_length=1)
    role: str = "supporting"

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        allowed = {"protagonist", "antagonist", "supporting", "extra"}
        normalized = value.strip().lower()
        if normalized not in allowed:
            return "supporting"
        return normalized


class SceneHeading(BaseModel):
    int_ext: str
    location: str = Field(..., min_length=1)
    time: str

    @field_validator("int_ext")
    @classmethod
    def validate_int_ext(cls, value: str) -> str:
        allowed = {"INT", "EXT", "INT/EXT"}
        normalized = value.strip().upper()
        if normalized not in allowed:
            raise ValueError(f"int_ext 必须是 {allowed} 之一")
        return normalized

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        allowed = {"DAY", "NIGHT", "DAWN", "DUSK", "CONTINUOUS"}
        normalized = value.strip().upper()
        if normalized not in allowed:
            raise ValueError(f"time 必须是 {allowed} 之一")
        return normalized


class SourceMapping(BaseModel):
    chapter: int = Field(..., ge=1)
    paragraph_range: list[int] | None = None
    excerpt: str = ""


class DialogueItem(BaseModel):
    character_id: str = Field(..., pattern=r"^char_[a-z0-9_]+$")
    line: str
    parenthetical: str = ""
    emotion: str = ""
    voice_over: bool = False


class ScriptSceneBlock(BaseModel):
    scene_id: str = Field(..., min_length=1)
    scene_number: int = Field(..., ge=1)
    heading: SceneHeading
    source_mapping: SourceMapping
    action_blocks: list[str] = Field(default_factory=list)
    dialogues: list[DialogueItem] = Field(default_factory=list)
    transition: str = ""
    notes: str = ""


class ScriptGenerateRequest(BaseModel):
    act: int = Field(default=1, ge=1)
    scene_id: str = ""
    chapter_number: int = Field(..., ge=1)
    chapter_content: str = Field(..., min_length=1)
    scene: SceneSplitItem
    characters: list[CharacterRef] = Field(default_factory=list)

    @field_validator("chapter_content")
    @classmethod
    def strip_chapter_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("章节原文不能为空。")
        return stripped


class ScriptGenerateResponse(BaseModel):
    act: int
    scene: ScriptSceneBlock
    characters: list[CharacterRef]
    model: str


class ScriptBlockParseError(ValueError):
    """Raised when LLM script block output cannot be parsed."""


def parse_script_block_response(raw_text: str) -> ScriptSceneBlock:
    try:
        data = extract_json_object(raw_text)
    except SceneSplitParseError as exc:
        raise ScriptBlockParseError(str(exc)) from exc
    try:
        return ScriptSceneBlock.model_validate(data)
    except ValidationError as exc:
        raise ScriptBlockParseError(f"剧本块 JSON 结构校验失败：{exc}") from exc


def normalize_script_block(
    block: ScriptSceneBlock,
    *,
    act: int,
    scene_id: str,
    chapter_number: int,
    registry: list[CharacterRef],
) -> ScriptSceneBlock:
    valid_ids = {character.id for character in registry}

    normalized_dialogues: list[DialogueItem] = []
    for dialogue in block.dialogues:
        character_id = dialogue.character_id
        if character_id not in valid_ids:
            raise ScriptBlockParseError(f"未知 character_id: {character_id}")
        normalized_dialogues.append(dialogue)

    if block.source_mapping.chapter != chapter_number:
        block.source_mapping.chapter = chapter_number

    return ScriptSceneBlock(
        scene_id=scene_id or block.scene_id or f"{act}-{block.scene_number}",
        scene_number=block.scene_number,
        heading=block.heading,
        source_mapping=block.source_mapping,
        action_blocks=[item.strip() for item in block.action_blocks if item.strip()],
        dialogues=normalized_dialogues,
        transition=block.transition,
        notes=block.notes,
    )
