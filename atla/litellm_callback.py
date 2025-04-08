# Adapted from https://github.com/BerriAI/litellm/blob/main/litellm/integrations/logfire_logger.py
import traceback
import uuid
from enum import Enum
from typing import Any, Dict, NamedTuple

from litellm._logging import print_verbose, verbose_logger
from litellm.integrations.custom_logger import CustomLogger
from litellm.litellm_core_utils.redact_messages import redact_user_api_key_info
from typing_extensions import LiteralString


class SpanConfig(NamedTuple):
    message_template: LiteralString
    span_data: Dict[str, Any]


class LogfireLevel(str, Enum):
    INFO = "info"
    ERROR = "error"


class AtlaLogfireLogger(CustomLogger):
    def __init__(self):
        # In the original implementation, litellm makes an additional call to
        # logfire.configure() in the __init__ method. This is extraneous and leads
        # to weird behavior, so we turn it off and handle all configuration
        # in run.py
        # https://github.com/BerriAI/litellm/blob/ff3a6830a441d232eaada541018d9d42b5d28783/litellm/integrations/logfire_logger.py#L28-L39
        super().__init__()

    def _get_span_config(self, payload) -> SpanConfig:
        if (
            payload["call_type"] == "completion"
            or payload["call_type"] == "acompletion"
        ):
            return SpanConfig(
                message_template="Chat Completion with {request_data[model]!r}",
                span_data={"request_data": payload},
            )
        elif (
            payload["call_type"] == "embedding" or payload["call_type"] == "aembedding"
        ):
            return SpanConfig(
                message_template="Embedding Creation with {request_data[model]!r}",
                span_data={"request_data": payload},
            )
        elif (
            payload["call_type"] == "image_generation"
            or payload["call_type"] == "aimage_generation"
        ):
            return SpanConfig(
                message_template="Image Generation with {request_data[model]!r}",
                span_data={"request_data": payload},
            )
        else:
            return SpanConfig(
                message_template="Litellm Call with {request_data[model]!r}",
                span_data={"request_data": payload},
            )

    async def _async_log_event(self, kwargs, response_obj, start_time, end_time):
        self.log_success_event(
            kwargs=kwargs,
            response_obj=response_obj,
            start_time=start_time,
            end_time=end_time,
        )

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        try:
            import logfire

            verbose_logger.debug(
                f"logfire Logging - Enters logging function for model {kwargs}"
            )

            if not response_obj:
                response_obj = {}
            litellm_params = kwargs.get("litellm_params", {})
            metadata = (
                litellm_params.get("metadata", {}) or {}
            )  # if litellm_params['metadata'] == None
            messages = kwargs.get("messages")
            optional_params = kwargs.get("optional_params", {})
            call_type = kwargs.get("call_type", "completion")
            cache_hit = kwargs.get("cache_hit", False)
            usage = response_obj.get("usage", {})
            id = response_obj.get("id", str(uuid.uuid4()))
            try:
                response_time = (end_time - start_time).total_seconds()
            except Exception:
                response_time = None

            # Clean Metadata before logging - never log raw metadata
            # the raw metadata can contain circular references which leads to infinite recursion
            # we clean out all extra litellm metadata params before logging
            clean_metadata = {}
            if isinstance(metadata, dict):
                for key, value in metadata.items():
                    # clean litellm metadata before logging
                    if key in [
                        "endpoint",
                        "caching_groups",
                        "previous_models",
                    ]:
                        continue
                    else:
                        clean_metadata[key] = value

            clean_metadata = redact_user_api_key_info(metadata=clean_metadata)

            # Build the initial payload
            payload = {
                "id": id,
                "call_type": call_type,
                "cache_hit": cache_hit,
                "startTime": start_time,
                "endTime": end_time,
                "responseTime (seconds)": response_time,
                "model": kwargs.get("model", ""),
                "user": kwargs.get("user", ""),
                "modelParameters": optional_params,
                "spend": kwargs.get("response_cost", 0),
                "messages": messages,
                "response": response_obj,
                "usage": usage,
                "metadata": clean_metadata,
            }
            logfire_openai = logfire.with_settings(custom_scope_suffix="openai")
            message_template, span_data = self._get_span_config(payload)
            logfire_openai.info(message_template, **span_data)
            print_verbose(f"\ndd Logger - Logging payload = {payload}")

            print_verbose(
                f"Logfire Layer Logging - final response object: {response_obj}"
            )
        except Exception as e:
            verbose_logger.debug(
                f"Logfire Layer Error - {str(e)}\n{traceback.format_exc()}"
            )
            pass


atla_logfire_logger = AtlaLogfireLogger()
