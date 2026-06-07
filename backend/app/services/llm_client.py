from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import Settings, settings

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class LLMError(Exception):
    """Base error for LLM client."""


class LLMNotConfiguredError(LLMError):
    """Raised when LLM API key is missing."""


class LLMRequestError(LLMError):
    """Raised when the LLM provider returns an error response."""


class LLMClient:
    """OpenAI-compatible chat completions client with timeout and retry."""

    def __init__(self, app_settings: Settings | None = None) -> None:
        self._settings = app_settings or settings

    @property
    def is_configured(self) -> bool:
        return self._settings.llm_configured

    @property
    def model(self) -> str:
        return self._settings.llm_model

    @property
    def base_url(self) -> str:
        return self._settings.llm_base_url.rstrip("/")

    @property
    def timeout(self) -> float:
        return self._settings.llm_timeout

    @property
    def max_retries(self) -> int:
        return self._settings.llm_max_retries

    def _chat_completions_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _ensure_configured(self) -> None:
        if not self.is_configured:
            raise LLMNotConfiguredError(
                "LLM 未配置。请在 backend/.env 中设置 LLM_API_KEY，或在前端界面输入密钥。"
            )

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        api_key: str | None = None,
    ) -> str:
        if not api_key:
            self._ensure_configured()
            api_key = self._settings.llm_api_key

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        data = self._post_with_retry(payload, api_key=api_key)
        return self._extract_content(data)

    def test_connection(self, prompt: str = "请只回复：OK", api_key: str | None = None) -> str:
        messages = [
            {"role": "system", "content": "你是一个连通性测试助手，请简短回复。"},
            {"role": "user", "content": prompt},
        ]
        return self.chat(messages, temperature=0, max_tokens=32, api_key=api_key)

    def _post_with_retry(self, payload: dict[str, Any], api_key: str) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None

        with httpx.Client(timeout=self.timeout) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = client.post(
                        self._chat_completions_url(),
                        headers=headers,
                        json=payload,
                    )
                except httpx.TimeoutException as exc:
                    last_error = LLMRequestError(f"LLM 请求超时（{self.timeout}s）")
                    if attempt >= self.max_retries:
                        raise last_error from exc
                except httpx.HTTPError as exc:
                    last_error = LLMRequestError(f"LLM 网络请求失败：{exc}")
                    if attempt >= self.max_retries:
                        raise last_error from exc
                else:
                    if response.status_code == 200:
                        return response.json()

                    if (
                        response.status_code in RETRYABLE_STATUS_CODES
                        and attempt < self.max_retries
                    ):
                        time.sleep(2**attempt)
                        continue

                    detail = self._extract_error_detail(response)
                    raise LLMRequestError(
                        f"LLM 请求失败 ({response.status_code}): {detail}"
                    )

                time.sleep(2**attempt)

        raise last_error or LLMRequestError("LLM 请求失败")

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMRequestError("LLM 响应格式异常，缺少 choices.message.content") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMRequestError("LLM 返回空内容")
        return content.strip()

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            body = response.json()
            if isinstance(body, dict) and "error" in body:
                error = body["error"]
                if isinstance(error, dict):
                    return str(error.get("message", error))
                return str(error)
            return response.text[:200]
        except ValueError:
            return response.text[:200]


_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient(settings)
    return _client


def reset_llm_client() -> None:
    global _client
    _client = None
