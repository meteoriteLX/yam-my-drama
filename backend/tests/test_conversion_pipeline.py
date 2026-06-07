from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from app.models.scene import (
    CharacterMentioned,
    SceneSplitItem,
    SceneSplitResult,
)
from app.models.script_block import (
    CharacterRef,
    DialogueItem,
    SceneHeading,
    ScriptSceneBlock,
    SourceMapping,
)
from app.services.conversion_pipeline import ConversionPipeline, ConversionPipelineError
from app.services.conversion_pipeline import reset_conversion_pipeline

SAMPLE_NOVEL_PATH = (
    Path(__file__).resolve().parents[2] / "examples" / "sample_novel.txt"
)

SAMPLE_SCRIPT_BLOCK = ScriptSceneBlock(
    scene_id="1-1",
    scene_number=1,
    heading=SceneHeading(int_ext="INT", location="书店", time="NIGHT"),
    source_mapping=SourceMapping(chapter=1, excerpt="摘要"),
    action_blocks=["动作描述"],
    dialogues=[
        DialogueItem(character_id="char_linwan", line="欢迎光临。"),
    ],
)


@pytest.fixture(autouse=True)
def cleanup_pipeline() -> None:
    reset_conversion_pipeline()
    yield
    reset_conversion_pipeline()


def _make_split_result(chapter_number: int, title: str) -> SceneSplitResult:
    return SceneSplitResult(
        chapter_number=chapter_number,
        chapter_title=title,
        scenes=[
            SceneSplitItem(
                scene_number=1,
                location="书店" if chapter_number == 1 else "巷口",
                int_ext="INT" if chapter_number == 1 else "EXT",
                time="NIGHT" if chapter_number == 1 else "DAWN",
                summary=f"第{chapter_number}章场景",
                characters=["林晚", "陈野"],
                source_excerpt="原文",
            )
        ],
        characters_mentioned=[
            CharacterMentioned(name="林晚", role_hint="protagonist"),
            CharacterMentioned(name="陈野", role_hint="protagonist"),
        ],
    )


class TestConversionPipeline:
    def test_convert_sample_novel_with_mocks(self) -> None:
        text = SAMPLE_NOVEL_PATH.read_text(encoding="utf-8")

        mock_splitter = MagicMock()
        mock_splitter.split_chapter.side_effect = [
            _make_split_result(1, "雨夜"),
            _make_split_result(2, "旧书"),
            _make_split_result(3, "未完成的句子"),
        ]

        mock_generator = MagicMock()

        def fake_generate(*, act, scene_id, chapter_number, chapter_content, scene, characters=None):
            char_id = characters[0].id if characters else "char_linwan"
            block = ScriptSceneBlock(
                scene_id=scene_id,
                scene_number=scene.scene_number,
                heading=SceneHeading(
                    int_ext=scene.int_ext,
                    location=scene.location,
                    time=scene.time,
                ),
                source_mapping=SourceMapping(chapter=chapter_number, excerpt="excerpt"),
                action_blocks=["动作"],
                dialogues=[
                    DialogueItem(character_id=char_id, line="台词"),
                ],
            )
            refs = characters or [
                CharacterRef(id="char_linwan", name="林晚", role="protagonist"),
                CharacterRef(id="char_chenye", name="陈野", role="protagonist"),
            ]
            return block, refs

        mock_generator.generate_scene_script.side_effect = fake_generate

        pipeline = ConversionPipeline(mock_splitter, mock_generator)
        result = pipeline.convert_novel(
            text,
            script_title="雨夜重逢",
            source_novel_title="城市边缘",
            source_novel_author="李四",
        )

        assert result.stats.chapter_count == 3
        assert result.stats.act_count == 3
        assert result.stats.scene_count == 3
        assert result.stats.character_count >= 2
        assert result.script.schema_version == "1.0.0"
        assert len(result.script.acts[0].scenes) == 1
        assert "雨夜重逢" in result.yaml

        parsed_yaml = yaml.safe_load(result.yaml)
        assert parsed_yaml["meta"]["title"] == "雨夜重逢"
        assert parsed_yaml["characters"]
        assert result.validation.valid is True

    def test_convert_rejects_less_than_three_chapters(self) -> None:
        text = """
第一章 一
内容一。

第二章 二
内容二。
"""
        pipeline = ConversionPipeline(MagicMock(), MagicMock())
        with pytest.raises(ConversionPipelineError, match="至少需要"):
            pipeline.convert_novel(text)
