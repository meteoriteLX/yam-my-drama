from __future__ import annotations

import yaml

from app.models.script import ScriptDocument


def script_to_yaml(script: ScriptDocument) -> str:
    payload = script.model_dump(mode="json", exclude_none=True)
    return yaml.dump(
        payload,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
