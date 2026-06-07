from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.services.llm_client import LLMClient, reset_llm_client

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_llm_client() -> None:
    reset_llm_client()
    yield
    reset_llm_client()


class TestLLMAPI:
    def test_status_when_not_configured(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "app.routers.llm.get_llm_client",
            lambda: LLMClient(Settings(llm_api_key="")),
        )

        response = client.get("/api/llm/status")
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is False
        assert "未配置" in data["message"]

    def test_status_when_configured(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "app.routers.llm.get_llm_client",
            lambda: LLMClient(
                Settings(
                    llm_api_key="secret",
                    llm_base_url="https://llm.example.com/v1",
                    llm_model="demo-model",
                )
            ),
        )

        response = client.get("/api/llm/status")
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is True
        assert data["model"] == "demo-model"
        assert data["base_url"] == "https://llm.example.com/v1"

    def test_test_endpoint_success(self, monkeypatch) -> None:
        mock_client = MagicMock()
        mock_client.is_configured = True
        mock_client.test_connection.return_value = "OK"
        monkeypatch.setattr("app.routers.llm.get_llm_client", lambda: mock_client)

        response = client.post("/api/llm/test", json={"prompt": "ping"})
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "OK"
        assert data["prompt"] == "ping"
        mock_client.test_connection.assert_called_once_with("ping")

    def test_test_endpoint_not_configured(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "app.routers.llm.get_llm_client",
            lambda: LLMClient(Settings(llm_api_key="")),
        )

        response = client.post("/api/llm/test", json={})
        assert response.status_code == 503
        assert "LLM 未配置" in response.json()["detail"]

    def test_test_endpoint_provider_error(self, monkeypatch) -> None:
        from app.services.llm_client import LLMRequestError

        mock_client = MagicMock()
        mock_client.test_connection.side_effect = LLMRequestError("provider down")
        monkeypatch.setattr("app.routers.llm.get_llm_client", lambda: mock_client)

        response = client.post("/api/llm/test", json={})
        assert response.status_code == 502
        assert "provider down" in response.json()["detail"]
