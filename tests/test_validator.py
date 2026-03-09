# Copyright Sierra
# Unit tests for Validator v1 (orchestration).

import pytest
from tau_bench.types import Action, RESPOND_ACTION_NAME
from tau_bench.orchestration.validator import (
    ValidatorResult,
    validate_action,
    VALIDATOR_CODE_RESPOND,
    VALIDATOR_CODE_ALLOWED,
    VALIDATOR_CODE_TOOL_NOT_FOUND,
    VALIDATOR_CODE_SCHEMA_MISMATCH,
    VALIDATOR_CODE_GROUNDING,
)


class _MockEnv:
    """Minimal env-like object for validator tests: tools_map (names) and tools_info (schemas)."""
    def __init__(self, tools_info):
        self.tools_info = tools_info
        self.tools_map = {t["function"]["name"]: None for t in tools_info}


# Schema: one required string, one optional number
TOOLS_INFO = [
    {
        "type": "function",
        "function": {
            "name": "get_user_details",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User id"},
                    "limit": {"type": "number"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_all_airports",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def test_respond_allowed():
    env = _MockEnv(TOOLS_INFO)
    action = Action(name=RESPOND_ACTION_NAME, kwargs={"content": "Here is the answer."})
    r = validate_action(env, action, 1)
    assert r.allowed is True
    assert r.code == VALIDATOR_CODE_RESPOND


def test_respond_missing_content():
    env = _MockEnv(TOOLS_INFO)
    action = Action(name=RESPOND_ACTION_NAME, kwargs={})
    r = validate_action(env, action, 1)
    assert r.allowed is False
    assert r.code == VALIDATOR_CODE_SCHEMA_MISMATCH
    assert "content" in r.message.lower()


def test_respond_content_not_string():
    env = _MockEnv(TOOLS_INFO)
    action = Action(name=RESPOND_ACTION_NAME, kwargs={"content": 123})
    r = validate_action(env, action, 1)
    assert r.allowed is False
    assert r.code == VALIDATOR_CODE_SCHEMA_MISMATCH


def test_tool_not_found():
    env = _MockEnv(TOOLS_INFO)
    action = Action(name="hallucinated_tool", kwargs={})
    r = validate_action(env, action, 1)
    assert r.allowed is False
    assert r.code == VALIDATOR_CODE_TOOL_NOT_FOUND
    assert "hallucinated_tool" in r.message or "unknown" in r.message.lower()


def test_schema_required_missing():
    env = _MockEnv(TOOLS_INFO)
    action = Action(name="get_user_details", kwargs={})
    r = validate_action(env, action, 1)
    assert r.allowed is False
    assert r.code == VALIDATOR_CODE_SCHEMA_MISMATCH
    assert "user_id" in r.message or "required" in r.message.lower()


def test_schema_type_wrong():
    env = _MockEnv(TOOLS_INFO)
    action = Action(name="get_user_details", kwargs={"user_id": 999})
    r = validate_action(env, action, 1)
    assert r.allowed is False
    assert r.code == VALIDATOR_CODE_SCHEMA_MISMATCH
    assert "string" in r.message.lower() or "user_id" in r.message


def test_grounding_empty_required_string():
    env = _MockEnv(TOOLS_INFO)
    action = Action(name="get_user_details", kwargs={"user_id": "   \t  "})
    r = validate_action(env, action, 1)
    assert r.allowed is False
    assert r.code == VALIDATOR_CODE_GROUNDING
    assert "empty" in r.message.lower() or "whitespace" in r.message.lower()


def test_tool_allowed():
    env = _MockEnv(TOOLS_INFO)
    action = Action(name="get_user_details", kwargs={"user_id": "sara_doe_496"})
    r = validate_action(env, action, 1)
    assert r.allowed is True
    assert r.code == VALIDATOR_CODE_ALLOWED


def test_tool_no_required_allowed():
    env = _MockEnv(TOOLS_INFO)
    action = Action(name="list_all_airports", kwargs={})
    r = validate_action(env, action, 1)
    assert r.allowed is True
    assert r.code == VALIDATOR_CODE_ALLOWED


def test_validator_result_to_dict():
    r = ValidatorResult(allowed=False, code=VALIDATOR_CODE_TOOL_NOT_FOUND, message="unknown tool: x")
    d = r.to_dict()
    assert d["allowed"] is False
    assert d["code"] == VALIDATOR_CODE_TOOL_NOT_FOUND
    assert "x" in d["message"]
