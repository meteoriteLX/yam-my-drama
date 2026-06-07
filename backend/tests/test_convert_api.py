from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.script import (
    ConversionStats,
    NovelConvertResponse,
    SceneRef,
    ScriptAct,
    ScriptCharacter,
    ScriptDocument,
    ScriptMeta,
    SourceNovelMeta,
)
from app.models.script_block import ScriptSceneBlock, SceneHeading, SourceMapping
from app.services.conversion_pipeline import reset_conversion_pipeline

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_pipeline() -> None:
    reset_conversion_pipeline()
    yield
    reset_conversion_pipeline()


class TestConvertAPI:
    def test_convert_novel_success(self, monkeypatch) -> None:
        mock_document = ScriptDocument(
            meta=ScriptMeta(
                title="测试剧本",
                author="test",
                source_novel=SourceNovelMeta(
                    title="小说",
                    author="作者",
                    chapters_covered=[1, 2, 3],
                ),
                created_at="2026-06-06",
            ),
            characters=[
                ScriptCharacter(
                    id="char_linwan",
                    name="林晚",
                    role="protagonist",
                    first_appeared=SceneRef(act=1, scene="1-1"),
                )
            ],
            acts=[
                ScriptAct(
                    act=1,
                    title="第一章",
                    scenes=[
                        ScriptSceneBlock(
                            scene_id="1-1",
                            scene_number=1,
                            heading=SceneHeading(
                                int_ext="INT",
                                location="书店",
                                time="NIGHT",
                            ),
                            source_mapping=SourceMapping(chapter=1, excerpt="x"),
                            action_blocks=["动作"],
                            dialogues=[],
                        )
                    ],
                )
            ],
        )

        mock_response = NovelConvertResponse(
            script=mock_document,
            yaml="schema_version: '1.0.0'\n",
            stats=ConversionStats(
                chapter_count=3,
                act_count=3,
                scene_count=3,
                character_count=2,
            ),
            model="deepseek-chat",
        )

        mock_pipeline = MagicMock()
        mock_pipeline.convert_novel.return_value = mock_response
        monkeypatch.setattr(
            "app.routers.convert.get_conversion_pipeline",
            lambda: mock_pipeline,
        )

        response = client.post(
            "/api/convert/novel-to-script",
            json={
                "text": "第一章 一\n内容\n\n第二章 二\n内容\n\n第三章 三\n内容",
                "script_title": "测试剧本",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["chapter_count"] == 3
        assert data["script"]["meta"]["title"] == "测试剧本"
        assert "yaml" in data

    def test_convert_novel_pipeline_error(self, monkeypatch) -> None:
        from app.services.conversion_pipeline import ConversionPipelineError

        mock_pipeline = MagicMock()
        mock_pipeline.convert_novel.side_effect = ConversionPipelineError("章节不足")
        monkeypatch.setattr(
            "app.routers.convert.get_conversion_pipeline",
            lambda: mock_pipeline,
        )

        response = client.post(
            "/api/convert/novel-to-script",
            json={"text": "第一章\n内容\n\n第二章\n内容"},
        )
        assert response.status_code == 422
