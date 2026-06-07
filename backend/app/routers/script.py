from fastapi import APIRouter, HTTPException

from app.models.validation import ScriptValidateRequest, ScriptValidateResponse
from app.services.script_validator import ScriptValidationError, validate_script_data, validate_script_yaml

router = APIRouter(prefix="/api/script", tags=["script"])


@router.post("/validate", response_model=ScriptValidateResponse)
def validate_script(payload: ScriptValidateRequest) -> ScriptValidateResponse:
    try:
        if payload.script is not None:
            result = validate_script_data(payload.script)
        else:
            result = validate_script_yaml(payload.yaml)
    except ScriptValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ScriptValidateResponse(
        valid=result.valid,
        errors=result.errors,
        warnings=result.warnings,
    )
