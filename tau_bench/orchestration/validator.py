# Copyright Sierra
# Validator v1: shared module for orchestrated agents. Prevents invalid/hallucinated actions before execution.
# Interface is generic for future ACT/ReAct; only wired to orchestrated-tool-calling run loop here.

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from tau_bench.envs.base import Env
from tau_bench.types import Action, RESPOND_ACTION_NAME


# Machine-readable codes for logging and trace
VALIDATOR_CODE_RESPOND = "respond"
VALIDATOR_CODE_ALLOWED = "allowed"
VALIDATOR_CODE_TOOL_NOT_FOUND = "tool_not_found"
VALIDATOR_CODE_SCHEMA_MISMATCH = "schema_mismatch"
VALIDATOR_CODE_GROUNDING = "grounding_fail"


@dataclass(frozen=True)
class ValidatorResult:
    """Structured validator output: not just boolean."""
    allowed: bool
    code: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {"allowed": self.allowed, "code": self.code, "message": self.message}


def _get_tool_schema(env: Env, tool_name: str) -> Optional[Dict[str, Any]]:
    """Return parameters schema (properties, required) for tool_name, or None if not found."""
    for info in env.tools_info:
        fn = info.get("function") or {}
        if fn.get("name") == tool_name:
            return (fn.get("parameters") or {}).copy()
    return None


def _schema_check(kwargs: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Minimal argument schema check: required keys present, types plausible.
    Returns (ok, error_message).
    """
    properties = schema.get("properties") or {}
    required = schema.get("required") or []
    for key in required:
        if key not in kwargs:
            return False, f"missing required argument: {key}"
        val = kwargs[key]
        prop = properties.get(key)
        if not prop:
            continue
        expected = prop.get("type")
        if expected == "string" and not isinstance(val, str):
            return False, f"argument '{key}' must be string, got {type(val).__name__}"
        if expected == "number" and not isinstance(val, (int, float)):
            return False, f"argument '{key}' must be number, got {type(val).__name__}"
        if expected == "integer" and not isinstance(val, int):
            return False, f"argument '{key}' must be integer, got {type(val).__name__}"
        if expected == "boolean" and not isinstance(val, bool):
            return False, f"argument '{key}' must be boolean, got {type(val).__name__}"
        if expected == "array" and not isinstance(val, list):
            return False, f"argument '{key}' must be array, got {type(val).__name__}"
        if expected == "object" and not isinstance(val, dict):
            return False, f"argument '{key}' must be object, got {type(val).__name__}"
    return True, ""


def _grounding_sanity(kwargs: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Minimal grounding checks: required strings not empty/whitespace-only.
    Safe and deterministic; no semantic checks.
    """
    properties = schema.get("properties") or {}
    required = schema.get("required") or []
    for key in required:
        if key not in kwargs:
            continue
        val = kwargs[key]
        prop = properties.get(key)
        if prop and prop.get("type") == "string" and isinstance(val, str):
            stripped = val.strip()
            if not stripped:
                return False, f"required string argument '{key}' is empty or whitespace"
    return True, ""


def validate_action(env: Env, action: Action, step_index: int) -> ValidatorResult:
    """
    Validate an action before execution. Shared across orchestrated agents.
    v1: tool existence, argument schema, basic grounding, explicit respond handling.
    """
    # 1) Explicit handling of respond actions
    if action.name == RESPOND_ACTION_NAME:
        if not isinstance(action.kwargs, dict):
            return ValidatorResult(
                allowed=False,
                code=VALIDATOR_CODE_SCHEMA_MISMATCH,
                message="respond action kwargs must be a dict",
            )
        if "content" not in action.kwargs:
            return ValidatorResult(
                allowed=False,
                code=VALIDATOR_CODE_SCHEMA_MISMATCH,
                message="respond action missing 'content'",
            )
        content = action.kwargs["content"]
        if not isinstance(content, str):
            return ValidatorResult(
                allowed=False,
                code=VALIDATOR_CODE_SCHEMA_MISMATCH,
                message="respond action 'content' must be string",
            )
        return ValidatorResult(allowed=True, code=VALIDATOR_CODE_RESPOND, message="respond allowed")

    # 2) Tool existence check
    if action.name not in env.tools_map:
        return ValidatorResult(
            allowed=False,
            code=VALIDATOR_CODE_TOOL_NOT_FOUND,
            message=f"unknown tool: {action.name}",
        )

    # 3) Argument schema check
    schema = _get_tool_schema(env, action.name)
    if schema is None:
        return ValidatorResult(
            allowed=False,
            code=VALIDATOR_CODE_SCHEMA_MISMATCH,
            message=f"no schema for tool: {action.name}",
        )
    if not isinstance(action.kwargs, dict):
        return ValidatorResult(
            allowed=False,
            code=VALIDATOR_CODE_SCHEMA_MISMATCH,
            message="tool kwargs must be a dict",
        )
    ok, err = _schema_check(action.kwargs, schema)
    if not ok:
        return ValidatorResult(allowed=False, code=VALIDATOR_CODE_SCHEMA_MISMATCH, message=err)

    # 4) Basic grounding sanity
    ok, err = _grounding_sanity(action.kwargs, schema)
    if not ok:
        return ValidatorResult(allowed=False, code=VALIDATOR_CODE_GROUNDING, message=err)

    return ValidatorResult(allowed=True, code=VALIDATOR_CODE_ALLOWED, message="ok")
