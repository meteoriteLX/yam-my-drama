from __future__ import annotations

from dataclasses import dataclass, field

from app.models.scene import CharacterMentioned
from app.models.script import ScriptCharacter, SceneRef
from app.models.script_block import CharacterRef
from app.utils.character import name_to_character_id

ROLE_PRIORITY = {
    "protagonist": 4,
    "antagonist": 3,
    "supporting": 2,
    "extra": 1,
}


@dataclass
class _CharacterEntry:
    ref: CharacterRef
    first_act: int
    first_scene: str


class GlobalCharacterRegistry:
    """跨章节角色表，按姓名合并并保持 ID 一致。"""

    def __init__(self) -> None:
        self._entries: dict[str, _CharacterEntry] = {}

    def __len__(self) -> int:
        return len(self._entries)

    def register(
        self,
        name: str,
        *,
        role: str = "supporting",
        act: int,
        scene_id: str,
        char_id: str | None = None,
    ) -> CharacterRef:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("角色名不能为空")

        if normalized_name in self._entries:
            entry = self._entries[normalized_name]
            if ROLE_PRIORITY.get(role, 0) > ROLE_PRIORITY.get(entry.ref.role, 0):
                entry.ref.role = role
            return entry.ref

        ref = CharacterRef(
            id=char_id or name_to_character_id(normalized_name),
            name=normalized_name,
            role=role if role in ROLE_PRIORITY else "supporting",
        )
        self._entries[normalized_name] = _CharacterEntry(
            ref=ref,
            first_act=act,
            first_scene=scene_id,
        )
        return ref

    def register_many(
        self,
        names: list[str],
        *,
        act: int,
        scene_id: str,
    ) -> list[CharacterRef]:
        return [
            self.register(name, act=act, scene_id=scene_id)
            for name in names
            if name.strip()
        ]

    def register_mentioned(
        self,
        mentioned: list[CharacterMentioned],
        *,
        act: int,
        scene_id: str,
    ) -> None:
        for item in mentioned:
            self.register(
                item.name,
                role=item.role_hint,
                act=act,
                scene_id=scene_id,
            )

    def merge_refs(
        self,
        refs: list[CharacterRef],
        *,
        act: int,
        scene_id: str,
    ) -> None:
        for ref in refs:
            if ref.name in self._entries:
                entry = self._entries[ref.name]
                if entry.ref.id != ref.id:
                    ref.id = entry.ref.id
                if ROLE_PRIORITY.get(ref.role, 0) > ROLE_PRIORITY.get(entry.ref.role, 0):
                    entry.ref.role = ref.role
            else:
                self.register(
                    ref.name,
                    role=ref.role,
                    act=act,
                    scene_id=scene_id,
                    char_id=ref.id,
                )

    def get_ref(self, name: str) -> CharacterRef | None:
        entry = self._entries.get(name.strip())
        return entry.ref if entry else None

    def refs_for_scene(self, character_names: list[str]) -> list[CharacterRef]:
        refs: list[CharacterRef] = []
        for name in character_names:
            ref = self.get_ref(name)
            if ref:
                refs.append(ref)
        return refs

    def all_refs(self) -> list[CharacterRef]:
        return [entry.ref for entry in self._entries.values()]

    def to_script_characters(self) -> list[ScriptCharacter]:
        characters: list[ScriptCharacter] = []
        for entry in self._entries.values():
            characters.append(
                ScriptCharacter(
                    id=entry.ref.id,
                    name=entry.ref.name,
                    role=entry.ref.role,
                    first_appeared=SceneRef(
                        act=entry.first_act,
                        scene=entry.first_scene,
                    ),
                )
            )
        return sorted(characters, key=lambda item: item.id)
