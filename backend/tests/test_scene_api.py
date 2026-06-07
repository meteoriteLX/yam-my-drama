import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.models.scene import CharacterMentioned, SceneSplitItem, SceneSplitResult
from app.services.scene_splitter import reset_scene_split_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_services() -> None:
    reset_scene_split_service()
    yield
    reset_scene_split_service()


class TestSceneSplitAPI:
    def test_split_chapter_success(self, monkeypatch) -> None:
        mock_result = SceneSplitResult(
            chapter_number=1,
            chapter_title="雨夜",
            scenes=[
                SceneSplitItem(
                    scene_number=1,
                    location="旧时光书店",
                    int_ext="INT",
                    time="NIGHT",
                    summary="重逢",
                    characters=["林晚"],
                    source_excerpt="雨下得很大",
                )
            ],
            characters_mentioned=[
                CharacterMentioned(name="林晚", role_hint="protagonist")
            ],
        )

        mock_service = MagicMock()
        mock_service.split_chapter.return_value = mock_result
        monkeypatch.setattr(
            "app.routers.scenes.get_scene_split_service",
            lambda: mock_service,
        )

        response = client.post(
            "/api/scenes/split-chapter",
            json={
                "chapter_number": 1,
                "chapter_title": "雨夜",
                "content": "雨下得很大。林晚看见陈野。",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chapter_number"] == 1
        assert data["scene_count"] == 1
        assert data["scenes"][0]["location"] == "旧时光书店"

    def test_split_chapter_empty_content_422(self) -> None:
        response = client.post(
            "/api/scenes/split-chapter",
            json={"chapter_number": 1, "chapter_title": "雨夜", "content": "   "},
        )
        assert response.status_code == 422

    def test_split_chapter_llm_not_configured(self, monkeypatch) -> None:
        from app.services.llm_client import LLMNotConfiguredError

        mock_service = MagicMock()
        mock_service.split_chapter.side_effect = LLMNotConfiguredError("未配置")
        monkeypatch.setattr(
            "app.routers.scenes.get_scene_split_service",
            lambda: mock_service,
        )

        response = client.post(
            "/api/scenes/split-chapter",
            json={"chapter_number": 1, "content": "正文内容足够长"},
        )
        assert response.status_code == 503
