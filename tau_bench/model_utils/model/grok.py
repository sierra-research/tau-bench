import os

from tau_bench.model_utils.api.datapoint import Datapoint
from tau_bench.model_utils.model.chat import ChatModel, Message
from tau_bench.model_utils.model.completion import approx_cost_for_datapoint, approx_prompt_str
from tau_bench.model_utils.model.general_model import wrap_temperature
from tau_bench.model_utils.model.utils import approx_num_tokens

DEFAULT_GROK_MODEL = "grok-3"
API_KEY_ENV_VAR = "XAI_API_KEY"

# Pricing information for Grok models (as of 2024)
PRICE_PER_INPUT_TOKEN_MAP = {
    "grok-beta": 5 / 1000000,  # $5 per million tokens (estimated)
    "grok-vision-beta": 5 / 1000000,
    "grok-3": 3 / 1000000,  # Updated pricing for grok-3
}

INPUT_PRICE_PER_TOKEN_FALLBACK = 5 / 1000000

CAPABILITY_SCORE_MAP = {
    "grok-beta": 0.9,  # Grok is quite capable
    "grok-vision-beta": 0.9,
    "grok-3": 0.95,  # grok-3 is the latest and most capable
}

CAPABILITY_SCORE_FALLBACK = 0.8

# TODO: implement latency tracking
LATENCY_MS_PER_OUTPUT_TOKEN_MAP = {}
LATENCY_MS_PER_OUTPUT_TOKEN_FALLBACK = 0.0

MAX_CONTEXT_LENGTH_MAP = {
    "grok-beta": 128000,
    "grok-vision-beta": 128000,
    "grok-3": 128000,  # grok-3 context length
}

MAX_CONTEXT_LENGTH_FALLBACK = 128000


class GrokModel(ChatModel):
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.0,
    ) -> None:
        if model is None:
            self.model = DEFAULT_GROK_MODEL
        else:
            self.model = model

        if api_key is None:
            api_key = os.getenv(API_KEY_ENV_VAR)
            if api_key is None:
                raise ValueError(f"{API_KEY_ENV_VAR} environment variable is not set")

        self.api_key = api_key
        self.temperature = temperature

    def generate_message(
        self,
        messages: list[Message],
        force_json: bool,
        temperature: float | None = None,
    ) -> Message:
        import litellm

        if temperature is None:
            temperature = self.temperature

        # Convert messages to the format expected by litellm
        msgs = []
        for msg in messages:
            if msg.obj is not None:
                import json
                content = json.dumps(msg.obj)
            else:
                content = msg.content
            msgs.append({"role": msg.role.value, "content": content})

        try:
            response = litellm.completion(
                model=f"xai/{self.model}",
                messages=msgs,
                temperature=wrap_temperature(temperature),
                api_key=self.api_key,
                response_format={"type": "json_object" if force_json else "text"},
            )

            content = response.choices[0].message.content
            return self.handle_generate_message_response(
                prompt=msgs, content=content, force_json=force_json
            )
        except Exception as e:
            # Handle litellm errors
            from tau_bench.model_utils.model.exception import ModelError
            raise ModelError(
                short_message=f"Grok API error: {str(e)}",
                prompt=msgs,
                response=str(e),
            ) from e

    def get_approx_cost(self, dp: Datapoint) -> float:
        cost_per_token = PRICE_PER_INPUT_TOKEN_MAP.get(self.model, INPUT_PRICE_PER_TOKEN_FALLBACK)
        return approx_cost_for_datapoint(dp=dp, price_per_input_token=cost_per_token)

    def get_latency(self, dp: Datapoint) -> float:
        latency_per_output_token = LATENCY_MS_PER_OUTPUT_TOKEN_MAP.get(
            self.model, LATENCY_MS_PER_OUTPUT_TOKEN_FALLBACK
        )
        return approx_cost_for_datapoint(dp=dp, price_per_input_token=latency_per_output_token)

    def get_capability(self) -> float:
        return CAPABILITY_SCORE_MAP.get(self.model, CAPABILITY_SCORE_FALLBACK)

    def supports_dp(self, dp: Datapoint) -> bool:
        prompt = approx_prompt_str(dp)
        return approx_num_tokens(prompt) <= MAX_CONTEXT_LENGTH_MAP.get(
            self.model, MAX_CONTEXT_LENGTH_FALLBACK
        )
