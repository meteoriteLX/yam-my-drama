from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


class SceneSplitItem(BaseModel):
    scene_number: int = Field(..., ge=1)
    location: str = Field(..., min_length=1)
    int_ext: str
    time: str
    summary: str = Field(..., min_length=1)
    characters: list[str] = Field(default_factory=list)
    source_excerpt: str = ""

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


class CharacterMentioned(BaseModel):
    name: str = Field(..., min_length=1)
    role_hint: str = "supporting"

    @field_validator("role_hint")
    @classmethod
    def validate_role_hint(cls, value: str) -> str:
        allowed = {"protagonist", "antagonist", "supporting", "extra"}
        normalized = value.strip().lower()
        if normalized not in allowed:
            return "supporting"
        return normalized


class SceneSplitResult(BaseModel):
    chapter_number: int = Field(..., ge=1)
    chapter_title: str = ""
    scenes: list[SceneSplitItem] = Field(..., min_length=1)
    characters_mentioned: list[CharacterMentioned] = Field(default_factory=list)


class SceneSplitRequest(BaseModel):
    chapter_number: int = Field(..., ge=1)
    chapter_title: str = ""
    content: str = Field(..., min_length=1)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("章节正文不能为空。")
        return stripped


class SceneSplitResponse(BaseModel):
    chapter_number: int
    chapter_title: str
    scene_count: int
    scenes: list[SceneSplitItem]
    characters_mentioned: list[CharacterMentioned]
    model: str


class SceneSplitParseError(ValueError):
    """Raised when LLM output cannot be parsed into scene split result."""


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise SceneSplitParseError("LLM 返回空内容")

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", stripped, re.IGNORECASE)
    if fenced:
        try:
            parsed = json.loads(fenced.group(1).strip())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            raise SceneSplitParseError("无法解析 LLM 返回的 JSON 代码块") from exc

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(stripped[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            raise SceneSplitParseError("无法从 LLM 响应中提取 JSON 对象") from exc

    raise SceneSplitParseError("LLM 响应中未找到有效 JSON")


def parse_scene_split_response(raw_text: str) -> SceneSplitResult:
    data = extract_json_object(raw_text)
    try:
        return SceneSplitResult.model_validate(data)
    except ValidationError as exc:
        raise SceneSplitParseError(f"场景 JSON 结构校验失败：{exc}") from exc
