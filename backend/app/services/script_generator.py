from __future__ import annotations

from app.models.scene import SceneSplitItem
from app.models.script_block import (
    CharacterRef,
    ScriptBlockParseError,
    ScriptSceneBlock,
    normalize_script_block,
    parse_script_block_response,
)
from app.prompts.script_block import build_script_block_prompt, format_character_registry
from app.services.llm_client import LLMClient, get_llm_client
from app.utils.character import build_character_registry


class ScriptGenerateError(Exception):
    """Raised when script block generation fails after retries."""


class ScriptGeneratorService:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client or get_llm_client()

    def generate_scene_script(
        self,
        *,
        act: int,
        scene_id: str,
        chapter_number: int,
        chapter_content: str,
        scene: SceneSplitItem,
        characters: list[CharacterRef] | None = None,
        api_key: str | None = None,
    ) -> tuple[ScriptSceneBlock, list[CharacterRef]]:
        registry = build_character_registry(scene.characters, characters)
        resolved_scene_id = scene_id or f"{act}-{scene.scene_number}"

        system_prompt, user_prompt = build_script_block_prompt(
            act=act,
            scene_id=resolved_scene_id,
            chapter_number=chapter_number,
            chapter_content=chapter_content,
            scene_number=scene.scene_number,
            location=scene.location,
            int_ext=scene.int_ext,
            time=scene.time,
            summary=scene.summary,
            character_names=scene.characters,
            character_registry=format_character_registry(registry),
        )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_error: Exception | None = None
        raw_text = ""

        for attempt in range(2):
            raw_text = self._llm.chat(
                messages,
                temperature=0.3,
                max_tokens=4096,
                api_key=api_key,
            )
            try:
                block = parse_script_block_response(raw_text)
                normalized = normalize_script_block(
                    block,
                    act=act,
                    scene_id=resolved_scene_id,
                    chapter_number=chapter_number,
                    registry=registry,
                )
                if not normalized.action_blocks and not normalized.dialogues:
                    raise ScriptBlockParseError("剧本块至少需包含 action_blocks 或 dialogues")
                return normalized, registry
            except ScriptBlockParseError as exc:
                last_error = exc
                if attempt == 0:
                    messages.extend(
                        [
                            {"role": "assistant", "content": raw_text},
                            {
                                "role": "user",
                                "content": (
                                    "输出格式有误。请只返回合法 JSON，"
                                    "确保 dialogues 使用角色注册表中的 character_id。"
                                ),
                            },
                        ]
                    )
                    continue
                raise ScriptGenerateError(str(exc)) from exc

        raise ScriptGenerateError(str(last_error or "剧本块生成失败"))


_service: ScriptGeneratorService | None = None


def get_script_generator_service() -> ScriptGeneratorService:
    global _service
    if _service is None:
        _service = ScriptGeneratorService()
    return _service


def reset_script_generator_service() -> None:
    global _service
    _service = None
