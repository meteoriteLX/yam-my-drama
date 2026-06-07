import pytest

from app.config import Settings
from app.services.llm_client import (
    LLMClient,
    LLMNotConfiguredError,
    LLMRequestError,
    reset_llm_client,
)


@pytest.fixture(autouse=True)
def cleanup_llm_client() -> None:
    reset_llm_client()
    yield
    reset_llm_client()


@pytest.fixture
def llm_settings() -> Settings:
    return Settings(
        llm_api_key="test-api-key",
        llm_base_url="https://llm.example.com/v1/",
        llm_model="test-model",
        llm_timeout=5.0,
        llm_max_retries=2,
    )


@pytest.fixture
def configured_client(llm_settings: Settings) -> LLMClient:
    return LLMClient(llm_settings)


class TestLLMClient:
    def test_not_configured_raises(self) -> None:
        client = LLMClient(Settings(llm_api_key=""))

        with pytest.raises(LLMNotConfiguredError, match="LLM 未配置"):
            client.chat([{"role": "user", "content": "hello"}])

    def test_chat_success(self, configured_client: LLMClient, monkeypatch) -> None:
        class FakeResponse:
            status_code = 200

            @staticmethod
            def json() -> dict:
                return {"choices": [{"message": {"content": "OK"}}]}

        class FakeHttpClient:
            def __init__(self, *args, **kwargs) -> None:
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args) -> None:
                return None

            def post(self, url, headers, json):
                assert url == "https://llm.example.com/v1/chat/completions"
                assert headers["Authorization"] == "Bearer test-api-key"
                assert json["model"] == "test-model"
                return FakeResponse()

        monkeypatch.setattr("app.services.llm_client.httpx.Client", FakeHttpClient)

        reply = configured_client.chat([{"role": "user", "content": "hello"}])
        assert reply == "OK"

    def test_retry_on_server_error(self, configured_client: LLMClient, monkeypatch) -> None:
        calls = {"count": 0}

        class FakeResponse:
            def __init__(self, status_code: int, payload: dict | None = None) -> None:
                self.status_code = status_code
                self._payload = payload or {}

            def json(self) -> dict:
                return self._payload

            @property
            def text(self) -> str:
                return "server error"

        class FakeHttpClient:
            def __init__(self, *args, **kwargs) -> None:
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args) -> None:
                return None

            def post(self, url, headers, json):
                calls["count"] += 1
                if calls["count"] == 1:
                    return FakeResponse(503)
                return FakeResponse(
                    200,
                    {"choices": [{"message": {"content": "retry ok"}}]},
                )

        monkeypatch.setattr("app.services.llm_client.httpx.Client", FakeHttpClient)
        monkeypatch.setattr("app.services.llm_client.time.sleep", lambda _: None)

        reply = configured_client.chat([{"role": "user", "content": "hello"}])
        assert reply == "retry ok"
        assert calls["count"] == 2

    def test_invalid_response_raises(self, configured_client: LLMClient, monkeypatch) -> None:
        class FakeResponse:
            status_code = 200

            @staticmethod
            def json() -> dict:
                return {"choices": []}

        class FakeHttpClient:
            def __init__(self, *args, **kwargs) -> None:
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args) -> None:
                return None

            def post(self, url, headers, json):
                return FakeResponse()

        monkeypatch.setattr("app.services.llm_client.httpx.Client", FakeHttpClient)

        with pytest.raises(LLMRequestError, match="响应格式异常"):
            configured_client.chat([{"role": "user", "content": "hello"}])

    def test_test_connection_uses_default_prompt(
        self, configured_client: LLMClient, monkeypatch
    ) -> None:
        captured: dict = {}

        def fake_chat(messages, *, temperature=0.7, max_tokens=None):
            captured["messages"] = messages
            captured["temperature"] = temperature
            captured["max_tokens"] = max_tokens
            return "OK"

        monkeypatch.setattr(configured_client, "chat", fake_chat)

        reply = configured_client.test_connection()
        assert reply == "OK"
        assert captured["temperature"] == 0
        assert captured["max_tokens"] == 32
