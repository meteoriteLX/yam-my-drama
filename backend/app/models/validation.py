from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ValidationIssue(BaseModel):
    code: str
    path: str
    message: str


class ScriptValidationResult(BaseModel):
    valid: bool
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)


class ScriptValidateRequest(BaseModel):
    yaml: str = ""
    script: dict | None = None

    @model_validator(mode="after")
    def require_payload(self) -> ScriptValidateRequest:
        if not self.yaml.strip() and self.script is None:
            raise ValueError("请提供 yaml 或 script 字段之一。")
        return self


class ScriptValidateResponse(BaseModel):
    valid: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
