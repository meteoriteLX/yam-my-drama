import json

import pytest

from app.models.scene import SceneSplitParseError, parse_scene_split_response
from app.prompts.scene_split import build_scene_split_prompt
from app.services.scene_splitter import SceneSplitService


SAMPLE_LLM_JSON = {
    "chapter_number": 1,
    "chapter_title": "雨夜",
    "scenes": [
        {
            "scene_number": 1,
            "location": "旧时光书店",
            "int_ext": "INT",
            "time": "NIGHT",
            "summary": "林晚与陈野雨夜重逢",
            "characters": ["林晚", "陈野"],
            "source_excerpt": "雨下得很大。林晚合上书，门铃响了。",
        },
        {
            "scene_number": 2,
            "location": "书店门口",
            "int_ext": "EXT",
            "time": "NIGHT",
            "summary": "王姨招呼两人",
            "characters": ["林晚", "陈野", "王姨"],
            "source_excerpt": "王姨从杂货铺探出头来",
        },
    ],
    "characters_mentioned": [
        {"name": "林晚", "role_hint": "protagonist"},
        {"name": "陈野", "role_hint": "protagonist"},
        {"name": "王姨", "role_hint": "supporting"},
    ],
}


class TestSceneSplitParser:
    def test_parse_plain_json(self) -> None:
        result = parse_scene_split_response(json.dumps(SAMPLE_LLM_JSON, ensure_ascii=False))
        assert result.chapter_number == 1
        assert len(result.scenes) == 2
        assert result.scenes[0].location == "旧时光书店"

    def test_parse_json_code_block(self) -> None:
        wrapped = f"```json\n{json.dumps(SAMPLE_LLM_JSON, ensure_ascii=False)}\n```"
        result = parse_scene_split_response(wrapped)
        assert len(result.scenes) == 2

    def test_parse_invalid_json_raises(self) -> None:
        with pytest.raises(SceneSplitParseError):
            parse_scene_split_response("这不是 JSON")

    def test_build_prompt_contains_chapter_info(self) -> None:
        system_prompt, user_prompt = build_scene_split_prompt(
            1, "雨夜", "雨下得很大。"
        )
        assert "场景" in system_prompt
        assert "雨夜" in user_prompt
        assert "雨下得很大" in user_prompt


class TestSceneSplitService:
    def test_split_chapter_success(self) -> None:
        class FakeLLM:
            def chat(self, messages, *, temperature=0.7, max_tokens=None):
                return json.dumps(SAMPLE_LLM_JSON, ensure_ascii=False)

        service = SceneSplitService(FakeLLM())
        result = service.split_chapter(1, "雨夜", "雨下得很大。林晚看见陈野。")

        assert result.chapter_number == 1
        assert len(result.scenes) == 2
        assert result.scenes[0].int_ext == "INT"

    def test_split_chapter_retries_on_bad_json(self) -> None:
        calls = {"count": 0}

        class FakeLLM:
            def chat(self, messages, *, temperature=0.7, max_tokens=None):
                calls["count"] += 1
                if calls["count"] == 1:
                    return "invalid json"
                return json.dumps(SAMPLE_LLM_JSON, ensure_ascii=False)

        service = SceneSplitService(FakeLLM())
        result = service.split_chapter(1, "雨夜", "正文")
        assert len(result.scenes) == 2
        assert calls["count"] == 2
