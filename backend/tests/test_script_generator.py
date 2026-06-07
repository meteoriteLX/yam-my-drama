import json

import pytest

from app.models.scene import SceneSplitItem
from app.models.script_block import (
    CharacterRef,
    ScriptBlockParseError,
    ScriptSceneBlock,
    parse_script_block_response,
)
from app.services.script_generator import ScriptGeneratorService
from app.utils.character import build_character_registry, name_to_character_id


SAMPLE_SCRIPT_JSON = {
    "scene_id": "1-1",
    "scene_number": 1,
    "heading": {
        "int_ext": "INT",
        "location": "旧时光书店",
        "time": "NIGHT",
    },
    "source_mapping": {
        "chapter": 1,
        "excerpt": "雨下得很大。林晚合上书，门铃响了。",
    },
    "action_blocks": [
        "窗外暴雨如注，雨水顺着玻璃蜿蜒而下。",
        "林晚将一本旧书合上。门铃清脆地响起。",
    ],
    "dialogues": [
        {
            "character_id": "char_linwan",
            "line": "欢迎光临。",
            "parenthetical": "停顿后",
            "emotion": "平静",
        },
        {
            "character_id": "char_chenye",
            "line": "……好久不见。",
            "emotion": "克制",
        },
    ],
    "transition": "CUT TO:",
    "notes": "心理描写外化为动作。",
}


@pytest.fixture
def sample_scene() -> SceneSplitItem:
    return SceneSplitItem(
        scene_number=1,
        location="旧时光书店",
        int_ext="INT",
        time="NIGHT",
        summary="林晚与陈野雨夜重逢",
        characters=["林晚", "陈野"],
        source_excerpt="雨下得很大。",
    )


@pytest.fixture
def sample_characters() -> list[CharacterRef]:
    return [
        CharacterRef(id="char_linwan", name="林晚", role="protagonist"),
        CharacterRef(id="char_chenye", name="陈野", role="protagonist"),
    ]


class TestScriptBlockParser:
    def test_parse_valid_json(self) -> None:
        result = parse_script_block_response(json.dumps(SAMPLE_SCRIPT_JSON, ensure_ascii=False))
        assert result.scene_id == "1-1"
        assert len(result.action_blocks) == 2
        assert len(result.dialogues) == 2

    def test_parse_invalid_json_raises(self) -> None:
        with pytest.raises(ScriptBlockParseError):
            parse_script_block_response("not json")


class TestCharacterRegistry:
    def test_name_to_character_id(self) -> None:
        assert name_to_character_id("Lin Wan").startswith("char_")

    def test_build_registry_from_scene(self) -> None:
        registry = build_character_registry(["林晚", "陈野"])
        assert len(registry) == 2
        assert registry[0].name in {"林晚", "陈野"}


class TestScriptGeneratorService:
    def test_generate_scene_script_success(
        self,
        sample_scene: SceneSplitItem,
        sample_characters: list[CharacterRef],
    ) -> None:
        class FakeLLM:
            def chat(self, messages, *, temperature=0.7, max_tokens=None):
                return json.dumps(SAMPLE_SCRIPT_JSON, ensure_ascii=False)

        service = ScriptGeneratorService(FakeLLM())
        block, registry = service.generate_scene_script(
            act=1,
            scene_id="1-1",
            chapter_number=1,
            chapter_content="雨下得很大。林晚看见陈野。",
            scene=sample_scene,
            characters=sample_characters,
        )

        assert isinstance(block, ScriptSceneBlock)
        assert block.scene_id == "1-1"
        assert len(block.action_blocks) >= 1
        assert block.dialogues[0].character_id == "char_linwan"
        assert len(registry) == 2

    def test_generate_retries_on_invalid_json(
        self,
        sample_scene: SceneSplitItem,
        sample_characters: list[CharacterRef],
    ) -> None:
        calls = {"count": 0}

        class FakeLLM:
            def chat(self, messages, *, temperature=0.7, max_tokens=None):
                calls["count"] += 1
                if calls["count"] == 1:
                    return "bad"
                return json.dumps(SAMPLE_SCRIPT_JSON, ensure_ascii=False)

        service = ScriptGeneratorService(FakeLLM())
        block, _ = service.generate_scene_script(
            act=1,
            scene_id="1-1",
            chapter_number=1,
            chapter_content="正文",
            scene=sample_scene,
            characters=sample_characters,
        )
        assert block.scene_id == "1-1"
        assert calls["count"] == 2
