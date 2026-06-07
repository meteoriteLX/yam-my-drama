from fastapi import APIRouter, HTTPException, Header

from app.config import settings
from app.models.llm import LLMStatusResponse, LLMTestRequest, LLMTestResponse
from app.services.llm_client import (
    LLMNotConfiguredError,
    LLMRequestError,
    get_llm_client,
)

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/status", response_model=LLMStatusResponse)
def llm_status(
    x_llm_api_key: str | None = Header(None, alias="X-LLM-API-Key"),
) -> LLMStatusResponse:
    client = get_llm_client()
    configured = client.is_configured or bool(x_llm_api_key)

    return LLMStatusResponse(
        configured=configured,
        model=client.model,
        base_url=client.base_url,
        timeout=client.timeout,
        max_retries=client.max_retries,
        message=(
            "LLM 已配置，可调用 /api/llm/test 进行连通性测试。"
            if configured
            else "LLM 未配置。请在 backend/.env 中设置 LLM_API_KEY，或在请求头中传入 X-LLM-API-Key。"
        ),
    )


@router.post("/test", response_model=LLMTestResponse)
def llm_test(
    payload: LLMTestRequest,
    x_llm_api_key: str | None = Header(None, alias="X-LLM-API-Key"),
) -> LLMTestResponse:
    client = get_llm_client()

    try:
        reply = client.test_connection(payload.prompt, api_key=x_llm_api_key)
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return LLMTestResponse(
        model=settings.llm_model,
        prompt=payload.prompt,
        reply=reply,
    )
