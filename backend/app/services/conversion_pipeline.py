from __future__ import annotations

from app.models.scene import SceneSplitResult
from app.models.script import (
    ConversionStats,
    NovelConvertResponse,
    ScriptAct,
    ScriptDocument,
    default_script_meta,
)
from app.models.script_block import CharacterRef
from app.services.chapter_parser import ChapterParseError, parse_novel
from app.services.character_registry import GlobalCharacterRegistry
from app.services.scene_splitter import SceneSplitError, SceneSplitService, get_scene_split_service
from app.services.script_generator import ScriptGenerateError, ScriptGeneratorService, get_script_generator_service
from app.services.script_validator import ScriptValidationError, validate_script_data
from app.utils.yaml_export import script_to_yaml


class ConversionPipelineError(Exception):
    """Raised when the novel-to-script pipeline fails."""


class ConversionPipeline:
    """多章小说 → 场景切分 → 剧本块生成 → YAML 剧本合并。"""

    def __init__(
        self,
        scene_splitter: SceneSplitService | None = None,
        script_generator: ScriptGeneratorService | None = None,
    ) -> None:
        self._scene_splitter = scene_splitter or get_scene_split_service()
        self._script_generator = script_generator or get_script_generator_service()

    def convert_novel(
        self,
        text: str,
        *,
        script_title: str = "",
        author: str = "yam-my-drama",
        source_novel_title: str = "未知",
        source_novel_author: str = "未知",
    ) -> NovelConvertResponse:
        try:
            parsed = parse_novel(text)
        except ChapterParseError as exc:
            raise ConversionPipelineError(str(exc)) from exc

        if not parsed.is_valid:
            raise ConversionPipelineError(parsed.message)

        global_registry = GlobalCharacterRegistry()
        acts: list[ScriptAct] = []
        total_scenes = 0

        for chapter in parsed.chapters:
            act_number = chapter.chapter_number
            try:
                split_result = self._split_chapter(chapter)
            except SceneSplitError as exc:
                raise ConversionPipelineError(
                    f"第 {act_number} 章场景切分失败：{exc}"
                ) from exc

            act_scenes = []
            for index, scene_item in enumerate(split_result.scenes, start=1):
                scene_id = f"{act_number}-{index}"
                global_registry.register_many(
                    scene_item.characters,
                    act=act_number,
                    scene_id=scene_id,
                )
                global_registry.register_mentioned(
                    split_result.characters_mentioned,
                    act=act_number,
                    scene_id=scene_id,
                )

                scene_characters = global_registry.refs_for_scene(scene_item.characters)
                try:
                    scene_block, local_refs = self._script_generator.generate_scene_script(
                        act=act_number,
                        scene_id=scene_id,
                        chapter_number=act_number,
                        chapter_content=chapter.content,
                        scene=scene_item,
                        characters=scene_characters or None,
                    )
                except ScriptGenerateError as exc:
                    raise ConversionPipelineError(
                        f"第 {act_number} 章场景 {scene_id} 剧本生成失败：{exc}"
                    ) from exc

                global_registry.merge_refs(
                    local_refs,
                    act=act_number,
                    scene_id=scene_id,
                )
                act_scenes.append(scene_block)
                total_scenes += 1

            acts.append(
                ScriptAct(
                    act=act_number,
                    title=chapter.title or f"第 {act_number} 章",
                    summary=self._build_act_summary(split_result),
                    scenes=act_scenes,
                )
            )

        if not global_registry.all_refs():
            raise ConversionPipelineError("未能识别任何角色，无法生成剧本。")

        meta = default_script_meta(
            script_title=script_title,
            author=author,
            source_novel_title=source_novel_title,
            source_novel_author=source_novel_author,
            chapters_covered=[chapter.chapter_number for chapter in parsed.chapters],
        )

        document = ScriptDocument(
            meta=meta,
            characters=global_registry.to_script_characters(),
            acts=acts,
        )

        script_payload = document.model_dump(mode="json", exclude_none=True)
        try:
            validation = validate_script_data(script_payload)
        except ScriptValidationError as exc:
            raise ConversionPipelineError(str(exc)) from exc

        if not validation.valid:
            messages = [f"{issue.path}: {issue.message}" for issue in validation.errors[:5]]
            raise ConversionPipelineError("生成的剧本未通过 Schema 校验：" + "；".join(messages))

        from app.config import settings

        return NovelConvertResponse(
            script=document,
            yaml=script_to_yaml(document),
            stats=ConversionStats(
                chapter_count=len(parsed.chapters),
                act_count=len(acts),
                scene_count=total_scenes,
                character_count=len(global_registry),
            ),
            validation=validation,
            model=settings.llm_model,
        )

    def _split_chapter(self, chapter) -> SceneSplitResult:
        return self._scene_splitter.split_chapter(
            chapter_number=chapter.chapter_number,
            chapter_title=chapter.title,
            content=chapter.content,
        )

    @staticmethod
    def _build_act_summary(split_result: SceneSplitResult) -> str:
        if not split_result.scenes:
            return ""
        summaries = [scene.summary for scene in split_result.scenes if scene.summary]
        return "；".join(summaries[:3])


_pipeline: ConversionPipeline | None = None


def get_conversion_pipeline() -> ConversionPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ConversionPipeline()
    return _pipeline


def reset_conversion_pipeline() -> None:
    global _pipeline
    _pipeline = None
