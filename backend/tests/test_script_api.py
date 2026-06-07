from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.scene import SceneSplitItem
from app.models.script_block import (
    CharacterRef,
    DialogueItem,
    SceneHeading,
    ScriptSceneBlock,
    SourceMapping,
)
from app.services.script_generator import reset_script_generator_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_services() -> None:
    reset_script_generator_service()
    yield
    reset_script_generator_service()


class TestScriptGenerateAPI:
    def test_generate_script_success(self, monkeypatch) -> None:
        mock_block = ScriptSceneBlock(
            scene_id="1-1",
            scene_number=1,
            heading=SceneHeading(int_ext="INT", location="旧时光书店", time="NIGHT"),
            source_mapping=SourceMapping(chapter=1, excerpt="雨下得很大。"),
            action_blocks=["林晚合上书。"],
            dialogues=[
                DialogueItem(
                    character_id="char_linwan",
                    line="欢迎光临。",
                    emotion="平静",
                )
            ],
            transition="CUT TO:",
        )
        mock_characters = [
            CharacterRef(id="char_linwan", name="林晚", role="protagonist"),
        ]

        mock_service = MagicMock()
        mock_service.generate_scene_script.return_value = (mock_block, mock_characters)
        monkeypatch.setattr(
            "app.routers.scenes.get_script_generator_service",
            lambda: mock_service,
        )

        response = client.post(
            "/api/scenes/generate-script",
            json={
                "act": 1,
                "scene_id": "1-1",
                "chapter_number": 1,
                "chapter_content": "雨下得很大。林晚看见陈野。",
                "scene": {
                    "scene_number": 1,
                    "location": "旧时光书店",
                    "int_ext": "INT",
                    "time": "NIGHT",
                    "summary": "重逢",
                    "characters": ["林晚", "陈野"],
                    "source_excerpt": "雨下得很大。",
                },
                "characters": [
                    {"id": "char_linwan", "name": "林晚", "role": "protagonist"},
                    {"id": "char_chenye", "name": "陈野", "role": "protagonist"},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["scene"]["scene_id"] == "1-1"
        assert len(data["scene"]["action_blocks"]) == 1
        assert data["scene"]["dialogues"][0]["line"] == "欢迎光临。"

    def test_generate_script_empty_content_422(self) -> None:
        response = client.post(
            "/api/scenes/generate-script",
            json={
                "chapter_number": 1,
                "chapter_content": "   ",
                "scene": {
                    "scene_number": 1,
                    "location": "书店",
                    "int_ext": "INT",
                    "time": "NIGHT",
                    "summary": "test",
                },
            },
        )
        assert response.status_code == 422

    def test_generate_script_llm_not_configured(self, monkeypatch) -> None:
        from app.services.llm_client import LLMNotConfiguredError

        mock_service = MagicMock()
        mock_service.generate_scene_script.side_effect = LLMNotConfiguredError("未配置")
        monkeypatch.setattr(
            "app.routers.scenes.get_script_generator_service",
            lambda: mock_service,
        )

        response = client.post(
            "/api/scenes/generate-script",
            json={
                "chapter_number": 1,
                "chapter_content": "足够长的章节正文内容",
                "scene": {
                    "scene_number": 1,
                    "location": "书店",
                    "int_ext": "INT",
                    "time": "NIGHT",
                    "summary": "test",
                },
            },
        )
        assert response.status_code == 503
