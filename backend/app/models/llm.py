from pydantic import BaseModel, Field


class LLMStatusResponse(BaseModel):
    configured: bool
    model: str
    base_url: str
    timeout: float
    max_retries: int
    message: str


class LLMTestRequest(BaseModel):
    prompt: str = Field(
        default="请只回复：OK",
        min_length=1,
        max_length=500,
        description="发送给 LLM 的测试提示词",
    )


class LLMTestResponse(BaseModel):
    model: str
    prompt: str
    reply: str
