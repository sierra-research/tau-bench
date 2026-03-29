# Copyright Sierra
"""LiteLLM completion wrapper with retry and exponential backoff for connection errors."""

import os
import time
from typing import Any

from litellm import completion as _completion

# Optional: for narrower exception handling
try:
    from openai import APIConnectionError as OpenAIAPIConnectionError
except ImportError:
    OpenAIAPIConnectionError = None  # type: ignore[misc, assignment]

import litellm

_DEFAULT_MAX_RETRIES = int(os.environ.get("LITELLM_RETRY_MAX_RETRIES", "3"))
_DEFAULT_BASE_DELAY = float(os.environ.get("LITELLM_RETRY_BASE_DELAY", "2.0"))
_MAX_DELAY = 60.0


def _is_retryable_connection_error(e: BaseException) -> bool:
    """True if the exception is a connection/client-closed error we should retry."""
    if OpenAIAPIConnectionError is not None and isinstance(e, OpenAIAPIConnectionError):
        return True
    if hasattr(litellm, "exceptions") and hasattr(litellm.exceptions, "InternalServerError"):
        if isinstance(e, litellm.exceptions.InternalServerError):
            msg = (getattr(e, "message", None) or str(e)).lower()
            if "connection error" in msg or "openaiException - connection" in msg:
                return True
    if isinstance(e, RuntimeError) and "client has been closed" in str(e):
        return True
    # LiteLLM may wrap in OpenAIError / InternalServerError with "Connection error" in chain
    cause = getattr(e, "__cause__", None)
    if cause is not None:
        return _is_retryable_connection_error(cause)
    return False


def completion_with_retry(
    *args: Any,
    _max_retries: int | None = None,
    _base_delay: float | None = None,
    **kwargs: Any,
) -> Any:
    """
    Call litellm.completion with retry and exponential backoff on connection errors.
    Strips _max_retries and _base_delay from kwargs before passing to litellm.
    """
    max_retries = _max_retries if _max_retries is not None else _DEFAULT_MAX_RETRIES
    base_delay = _base_delay if _base_delay is not None else _DEFAULT_BASE_DELAY
    # Do not pass internal params to litellm
    kwargs = {k: v for k, v in kwargs.items() if k not in ("_max_retries", "_base_delay")}
    last_exception = None
    for attempt in range(max_retries):
        try:
            return _completion(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if not _is_retryable_connection_error(e) or attempt == max_retries - 1:
                raise
            delay = min(base_delay * (2 ** attempt), _MAX_DELAY)
            time.sleep(delay)
    if last_exception is not None:
        raise last_exception
    raise RuntimeError("completion_with_retry: unexpected state")
