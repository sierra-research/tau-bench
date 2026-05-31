# Copyright Sierra
"""Tests for the opt-in reward-precision output matcher.

The default (non-strict) behaviour must remain byte-identical to upstream's
substring test; strict mode only tightens matching to token boundaries.
"""
from tau_bench.envs.base import output_matches


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
