from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_SCRIPT_YAML = (
    Path(__file__).resolve().parents[2] / "examples" / "sample_script.yaml"
)


class TestScriptValidateAPI:
    def test_validate_sample_yaml_success(self) -> None:
        yaml_text = SAMPLE_SCRIPT_YAML.read_text(encoding="utf-8")
        response = client.post("/api/script/validate", json={"yaml": yaml_text})

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["errors"] == []

    def test_validate_script_json_success(self) -> None:
        script = yaml.safe_load(SAMPLE_SCRIPT_YAML.read_text(encoding="utf-8"))
        response = client.post("/api/script/validate", json={"script": script})

        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_validate_invalid_script(self) -> None:
        response = client.post(
            "/api/script/validate",
            json={"script": {"schema_version": "1.0.0"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    def test_validate_missing_payload_422(self) -> None:
        response = client.post("/api/script/validate", json={})
        assert response.status_code == 422

    def test_validate_bad_yaml_400(self) -> None:
        response = client.post("/api/script/validate", json={"yaml": "meta: [bad"})
        assert response.status_code == 400
