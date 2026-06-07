from __future__ import annotations

from app.models.scene import SceneSplitParseError, SceneSplitResult, parse_scene_split_response
from app.prompts.scene_split import build_scene_split_prompt
from app.services.llm_client import LLMClient, get_llm_client


class SceneSplitError(Exception):
    """Raised when scene splitting fails after retries."""


class SceneSplitService:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client or get_llm_client()

    def split_chapter(
        self,
        chapter_number: int,
        chapter_title: str,
        content: str,
    ) -> SceneSplitResult:
        system_prompt, user_prompt = build_scene_split_prompt(
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            content=content,
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
                temperature=0.2,
                max_tokens=4096,
            )
            try:
                result = parse_scene_split_response(raw_text)
                break
            except SceneSplitParseError as exc:
                last_error = exc
                if attempt == 0:
                    messages.extend(
                        [
                            {"role": "assistant", "content": raw_text},
                            {
                                "role": "user",
                                "content": (
                                    "输出格式有误。请只返回合法 JSON 对象，"
                                    "不要 Markdown 代码块，不要额外文字。"
                                ),
                            },
                        ]
                    )
                    continue
                raise SceneSplitError(str(exc)) from exc
        else:
            raise SceneSplitError(str(last_error or "场景切分失败"))

        if result.chapter_number != chapter_number:
            result.chapter_number = chapter_number
        if chapter_title and not result.chapter_title:
            result.chapter_title = chapter_title

        return result


_service: SceneSplitService | None = None


def get_scene_split_service() -> SceneSplitService:
    global _service
    if _service is None:
        _service = SceneSplitService()
    return _service


def reset_scene_split_service() -> None:
    global _service
    _service = None
