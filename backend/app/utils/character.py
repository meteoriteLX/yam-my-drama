from __future__ import annotations

import hashlib
import re

from app.models.script_block import CharacterRef


def name_to_character_id(name: str) -> str:
    cleaned = re.sub(r"\s+", "", name.strip())
    ascii_slug = re.sub(r"[^a-zA-Z0-9]", "", cleaned).lower()
    if ascii_slug:
        return f"char_{ascii_slug[:24]}"
    digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:10]
    return f"char_{digest}"


def build_character_registry(
    scene_character_names: list[str],
    characters: list[CharacterRef] | None = None,
) -> list[CharacterRef]:
    registry = {item.name: item for item in (characters or [])}

    for name in scene_character_names:
        if name not in registry:
            registry[name] = CharacterRef(
                id=name_to_character_id(name),
                name=name,
                role="supporting",
            )

    return list(registry.values())
