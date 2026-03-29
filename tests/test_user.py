# Copyright Sierra
# Tests for user simulation envs, including parse_response for ReactUserSimulationEnv.

import pytest
from unittest.mock import MagicMock

from tau_bench.envs.user import ReactUserSimulationEnv, strip_think_tags


def _parse_response(env, response: str) -> str:
    """Call parse_response on the class with a mock instance (no API)."""
    return ReactUserSimulationEnv.parse_response(env, response)


def test_react_parse_response_returns_only_user_response_when_both_thought_and_user_response():
    """When both Thought: and User Response: exist, extract only the User Response segment."""
    env = MagicMock(spec=ReactUserSimulationEnv)
    raw = "Thought:\n<think> I need to confirm ... </think>\n\nUser Response:\nbar"
    assert _parse_response(env, raw) == "bar"


def test_react_parse_response_stop():
    env = MagicMock(spec=ReactUserSimulationEnv)
    assert _parse_response(env, "###STOP###") == "###STOP###"
    assert _parse_response(env, "Something ###STOP### else") == "###STOP###"


def test_react_parse_response_only_thought():
    env = MagicMock(spec=ReactUserSimulationEnv)
    assert _parse_response(env, "Thought:\nfoo bar") == "foo bar"


def test_react_parse_response_only_user_response():
    env = MagicMock(spec=ReactUserSimulationEnv)
    assert _parse_response(env, "User Response:\nbar") == "bar"


def test_react_parse_response_invalid_raises():
    env = MagicMock(spec=ReactUserSimulationEnv)
    # Now only truly empty / whitespace-only responses are treated as invalid.
    with pytest.raises(ValueError, match="Invalid response format"):
        _parse_response(env, "")
    with pytest.raises(ValueError, match="Invalid response format"):
        _parse_response(env, "   ")


def test_react_parse_response_fallback_last_line_used():
    """When there are no explicit markers, parser falls back to last non-empty line."""
    env = MagicMock(spec=ReactUserSimulationEnv)
    assert _parse_response(env, "No markers here") == "No markers here"
    assert _parse_response(env, "Line one\n\nLine two") == "Line two"


def test_strip_think_tags_unclosed_think_with_user_response():
    """Unclosed <think> with User Response: should return only the user response portion."""
    raw = "<think>\nThought about what to say.\n\nUser Response:\nI'd like to book a flight.\n"
    assert strip_think_tags(raw) == "I'd like to book a flight."
