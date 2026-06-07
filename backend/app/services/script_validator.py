from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from app.models.validation import ScriptValidationResult, ValidationIssue

SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "schemas" / "script.schema.json"
)


class ScriptValidationError(Exception):
    """Raised when script data cannot be validated due to parse or schema load errors."""


@lru_cache(maxsize=1)
def load_script_schema() -> dict[str, Any]:
    if not SCHEMA_PATH.exists():
        raise ScriptValidationError(f"Schema 文件不存在：{SCHEMA_PATH}")
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScriptValidationError("Schema 文件 JSON 格式无效") from exc


@lru_cache(maxsize=1)
def get_script_validator() -> Draft202012Validator:
    schema = load_script_schema()
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ScriptValidationError(f"Schema 定义无效：{exc.message}") from exc
    return Draft202012Validator(schema)


def parse_script_yaml(yaml_text: str) -> dict[str, Any]:
    stripped = yaml_text.strip()
    if not stripped:
        raise ScriptValidationError("YAML 内容不能为空。")
    try:
        data = yaml.safe_load(stripped)
    except yaml.YAMLError as exc:
        raise ScriptValidationError(f"YAML 解析失败：{exc}") from exc
    if not isinstance(data, dict):
        raise ScriptValidationError("YAML 根节点必须是对象。")
    return data


def normalize_script_payload(data: dict[str, Any]) -> dict[str, Any]:
    """补齐校验所需的缺省字段，便于 Pipeline 输出通过 Schema。"""
    normalized = deepcopy(data)

    for act in normalized.get("acts", []):
        if not isinstance(act, dict):
            continue
        for scene in act.get("scenes", []):
            if not isinstance(scene, dict):
                continue
            source_mapping = scene.get("source_mapping")
            if isinstance(source_mapping, dict):
                source_mapping.setdefault("excerpt", "")

    return normalized


def _format_json_path(path: tuple[Any, ...]) -> str:
    if not path:
        return "root"
    parts: list[str] = []
    for item in path:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        else:
            if parts:
                parts.append(f".{item}")
            else:
                parts.append(str(item))
    return "".join(parts)


def validate_schema(data: dict[str, Any]) -> list[ValidationIssue]:
    validator = get_script_validator()
    issues: list[ValidationIssue] = []

    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        issues.append(
            ValidationIssue(
                code="schema",
                path=_format_json_path(tuple(error.absolute_path)),
                message=error.message,
            )
        )
    return issues


def validate_business_rules(data: dict[str, Any]) -> tuple[list[ValidationIssue], list[ValidationIssue]]:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    characters = data.get("characters", [])
    if not isinstance(characters, list):
        return errors, warnings

    character_ids = {
        character.get("id")
        for character in characters
        if isinstance(character, dict) and character.get("id")
    }

    scene_ids: set[str] = set()
    acts = data.get("acts", [])
    if not isinstance(acts, list):
        return errors, warnings

    for act_index, act in enumerate(acts):
        if not isinstance(act, dict):
            continue
        act_number = act.get("act")
        for scene_index, scene in enumerate(act.get("scenes", [])):
            if not isinstance(scene, dict):
                continue

            scene_id = scene.get("scene_id")
            if isinstance(scene_id, str):
                if scene_id in scene_ids:
                    errors.append(
                        ValidationIssue(
                            code="duplicate_scene_id",
                            path=f"acts[{act_index}].scenes[{scene_index}].scene_id",
                            message=f"scene_id 重复：{scene_id}",
                        )
                    )
                scene_ids.add(scene_id)

            dialogues = scene.get("dialogues", [])
            if not isinstance(dialogues, list):
                continue
            for dialogue_index, dialogue in enumerate(dialogues):
                if not isinstance(dialogue, dict):
                    continue
                character_id = dialogue.get("character_id")
                if character_id and character_id not in character_ids:
                    errors.append(
                        ValidationIssue(
                            code="unknown_character",
                            path=(
                                f"acts[{act_index}].scenes[{scene_index}]"
                                f".dialogues[{dialogue_index}].character_id"
                            ),
                            message=f"对白引用了未注册角色：{character_id}",
                        )
                    )

            if not scene.get("action_blocks") and not scene.get("dialogues"):
                warnings.append(
                    ValidationIssue(
                        code="empty_scene",
                        path=f"acts[{act_index}].scenes[{scene_index}]",
                        message="场景缺少 action_blocks 与 dialogues，建议补充内容。",
                    )
                )

        if isinstance(act_number, int):
            covered = data.get("meta", {}).get("source_novel", {}).get("chapters_covered", [])
            if isinstance(covered, list) and act_number not in covered:
                warnings.append(
                    ValidationIssue(
                        code="chapter_not_covered",
                        path=f"acts[{act_index}].act",
                        message=f"幕号 {act_number} 不在 meta.source_novel.chapters_covered 中。",
                    )
                )

    for char_index, character in enumerate(characters):
        if not isinstance(character, dict):
            continue
        first_appeared = character.get("first_appeared")
        if not isinstance(first_appeared, dict):
            continue
        scene_ref = first_appeared.get("scene")
        if isinstance(scene_ref, str) and scene_ref not in scene_ids:
            errors.append(
                ValidationIssue(
                    code="missing_first_scene",
                    path=f"characters[{char_index}].first_appeared.scene",
                    message=f"角色首次出场场景不存在：{scene_ref}",
                )
            )

    return errors, warnings


def validate_script_data(data: dict[str, Any]) -> ScriptValidationResult:
    normalized = normalize_script_payload(data)
    schema_errors = validate_schema(normalized)
    business_errors, warnings = validate_business_rules(normalized)

    errors = schema_errors + business_errors
    return ScriptValidationResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
    )


def validate_script_yaml(yaml_text: str) -> ScriptValidationResult:
    data = parse_script_yaml(yaml_text)
    return validate_script_data(data)


def ensure_script_valid(data: dict[str, Any]) -> ScriptValidationResult:
    result = validate_script_data(data)
    if not result.valid:
        messages = [f"{issue.path}: {issue.message}" for issue in result.errors[:5]]
        extra = len(result.errors) - len(messages)
        suffix = f" 等 {extra} 项" if extra > 0 else ""
        raise ScriptValidationError("剧本 Schema 校验失败：" + "；".join(messages) + suffix)
    return result
