from pathlib import Path

import pytest
import yaml

from app.services.script_validator import (
    ScriptValidationError,
    validate_script_data,
    validate_script_yaml,
)

SAMPLE_SCRIPT_YAML = (
    Path(__file__).resolve().parents[2] / "examples" / "sample_script.yaml"
)


class TestScriptValidator:
    def test_sample_script_yaml_is_valid(self) -> None:
        yaml_text = SAMPLE_SCRIPT_YAML.read_text(encoding="utf-8")
        result = validate_script_yaml(yaml_text)

        assert result.valid is True
        assert result.errors == []

    def test_invalid_schema_missing_meta(self) -> None:
        result = validate_script_data({"schema_version": "1.0.0", "characters": [], "acts": []})

        assert result.valid is False
        assert any(issue.code == "schema" for issue in result.errors)

    def test_unknown_character_id(self) -> None:
        data = yaml.safe_load(SAMPLE_SCRIPT_YAML.read_text(encoding="utf-8"))
        data["acts"][0]["scenes"][0]["dialogues"][0]["character_id"] = "char_unknown"

        result = validate_script_data(data)

        assert result.valid is False
        assert any(issue.code == "unknown_character" for issue in result.errors)

    def test_duplicate_scene_id(self) -> None:
        data = yaml.safe_load(SAMPLE_SCRIPT_YAML.read_text(encoding="utf-8"))
        data["acts"][1]["scenes"][0]["scene_id"] = "1-1"

        result = validate_script_data(data)

        assert result.valid is False
        assert any(issue.code == "duplicate_scene_id" for issue in result.errors)

    def test_empty_yaml_raises(self) -> None:
        with pytest.raises(ScriptValidationError, match="不能为空"):
            validate_script_yaml("   ")

    def test_invalid_yaml_syntax_raises(self) -> None:
        with pytest.raises(ScriptValidationError, match="YAML 解析失败"):
            validate_script_yaml("meta: [unclosed")
