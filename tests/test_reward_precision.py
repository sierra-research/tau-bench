# Copyright Sierra
"""Tests for the opt-in reward-precision output matcher.

The default (non-strict) behaviour must remain byte-identical to upstream's
substring test; strict mode only tightens matching to token boundaries.
"""
from unittest.mock import patch

from tau_bench.envs import get_env
from tau_bench.envs.base import output_matches


def _make_env(**flags):
    def fake_user_completion(*args, **kwargs):
        message = type("M", (), {"content": "Hi! ###STOP###"})()
        message.model_dump = lambda: {"role": "assistant", "content": "Hi! ###STOP###"}
        return type(
            "R",
            (),
            {"choices": [type("C", (), {"message": message})()], "_hidden_params": {"response_cost": 0.0}},
        )()

    with patch("tau_bench.envs.user.completion", side_effect=fake_user_completion):
        return get_env(
            "retail",
            user_strategy="llm",
            user_model="gpt-4o",
            task_split="test",
            user_provider="openai",
            task_index=0,
            **flags,
        )


def test_get_env_defaults_flags_off():
    env = _make_env()
    assert env.strict_output_match is False
    assert env.preserve_data_on_reward is False


def test_get_env_threads_flags_true():
    env = _make_env(strict_output_match=True, preserve_data_on_reward=True)
    assert env.strict_output_match is True
    assert env.preserve_data_on_reward is True


def test_env_var_fallback_when_flag_unset(monkeypatch):
    monkeypatch.setenv("TAU_STRICT_OUTPUT_MATCH", "1")
    env = _make_env()  # flags left unset -> env var fallback applies
    assert env.strict_output_match is True


def test_default_is_substring_match():
    # Upstream behaviour: bare substring, case-insensitive. Commas are stripped
    # from the reply content only (not from the required output).
    assert output_matches("10", "the total is 100")
    assert output_matches("1000", "you owe 1,000 dollars")
    assert output_matches("ABC", "order abc shipped")


def test_strict_rejects_substring_false_positive():
    # The motivating bug: required "10" satisfied by "100".
    assert not output_matches("10", "the total is 100", strict=True)
    assert not output_matches("12", "order 123 pending", strict=True)


def test_strict_still_matches_whole_token():
    assert output_matches("10", "your order 10 shipped", strict=True)
    assert output_matches("#w12", "order #w12 ok", strict=True)
    assert output_matches("1000", "you owe 1,000 dollars", strict=True)


def test_strict_is_case_insensitive():
    assert output_matches("ABC", "order abc shipped", strict=True)
