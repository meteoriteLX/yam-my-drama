import pytest

from app.models.scene import CharacterMentioned
from app.models.script_block import CharacterRef
from app.services.character_registry import GlobalCharacterRegistry


class TestGlobalCharacterRegistry:
    def test_register_and_merge_same_name(self) -> None:
        registry = GlobalCharacterRegistry()
        first = registry.register("林晚", role="supporting", act=1, scene_id="1-1")
        second = registry.register("林晚", role="protagonist", act=1, scene_id="1-2")

        assert first.id == second.id
        assert second.role == "protagonist"
        assert len(registry) == 1

    def test_register_mentioned(self) -> None:
        registry = GlobalCharacterRegistry()
        registry.register_mentioned(
            [CharacterMentioned(name="陈野", role_hint="protagonist")],
            act=1,
            scene_id="1-1",
        )

        ref = registry.get_ref("陈野")
        assert ref is not None
        assert ref.role == "protagonist"

    def test_merge_refs_keeps_existing_id(self) -> None:
        registry = GlobalCharacterRegistry()
        registry.register("王姨", act=1, scene_id="1-1")

        incoming = CharacterRef(id="char_other", name="王姨", role="supporting")
        registry.merge_refs([incoming], act=1, scene_id="1-2")

        assert incoming.id == registry.get_ref("王姨").id

    def test_to_script_characters(self) -> None:
        registry = GlobalCharacterRegistry()
        registry.register("林晚", role="protagonist", act=1, scene_id="1-1")
        registry.register("陈野", role="protagonist", act=1, scene_id="1-1")

        characters = registry.to_script_characters()
        assert len(characters) == 2
        assert characters[0].first_appeared.scene == "1-1"
