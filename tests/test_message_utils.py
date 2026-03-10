# Copyright Sierra
# Tests for message_utils: strip_think_tags, sanitize_user_observation.

import pytest

from tau_bench.orchestration.message_utils import strip_think_tags, sanitize_user_observation


def test_strip_think_tags_removes_single_block():
    text = "Hello <think>internal reasoning</think> world"
    assert strip_think_tags(text) == "Hello  world"


def test_strip_think_tags_removes_multiline():
    text = "Before\n<think>line1\nline2</think>\nAfter"
    assert strip_think_tags(text) == "Before\n\nAfter"


def test_strip_think_tags_removes_nested():
    text = "A <think>outer <think>inner</think> still_outer</think> B"
    assert "<think>" not in strip_think_tags(text)
    assert "</think>" not in strip_think_tags(text)
    assert "A" in strip_think_tags(text) and "B" in strip_think_tags(text)


def test_strip_think_tags_empty_or_none():
    assert strip_think_tags("") == ""
    assert strip_think_tags(None) is None


def test_strip_think_tags_no_tags_unchanged():
    text = "No think tags here"
    assert strip_think_tags(text) == text


def test_sanitize_user_observation_strips_think_and_trim():
    text = "  \n <think>reasoning</think> \n yes please  \n"
    assert sanitize_user_observation(text) == "yes please"


def test_sanitize_user_observation_empty():
    assert sanitize_user_observation("") == ""
    assert sanitize_user_observation(None) is None
