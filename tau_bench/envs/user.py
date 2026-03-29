# Copyright Sierra
import json
import os
import sys
import abc
import enum
from tau_bench.litellm_retry import completion_with_retry

from typing import Optional, List, Dict, Any, Union

# Temporary debug flag for respond-path investigation. When set, raw/parsed user-sim output is logged to stderr.
# See: .cursor/plans/respond-path-debug-instrumentation_9fb3f737.plan.md
_DEBUG_RESPOND_PATH = os.environ.get("TAU_BENCH_DEBUG_RESPOND_PATH", "").lower() in ("1", "true", "yes")


def _respond_path_debug_user(extra: Dict[str, Any]) -> None:
    """Emit one structured debug line to stderr when TAU_BENCH_DEBUG_RESPOND_PATH is set."""
    if not _DEBUG_RESPOND_PATH:
        return
    payload = {"respond_path_debug": "user_sim", **extra}
    print(json.dumps(payload, default=str), file=sys.stderr)


def strip_think_tags(content: str) -> str:
    """
    Remove <think>...</think> blocks from text (one or nested).
    Uses depth counting so inner tags are matched correctly; removes orphan tags.
    """
    if not content or not isinstance(content, str):
        return content

    # Fallback for models that open <think> but never close it.
    # In this case, treat <think> as a marker and keep its contents,
    # optionally extracting the portion after "User Response:" if present.
    if "<think>" in content and "</think>" not in content:
        after_think = content.split("<think>", 1)[1]
        if "User Response:" in after_think:
            _, user_response = after_think.split("User Response:", 1)
            return user_response.strip()
        return after_think.strip()

    out_parts: List[str] = []
    i = 0
    n = len(content)
    while i < n:
        if content[i : i + 7] == "<think>":
            depth = 1
            i += 7
            while i < n and depth > 0:
                if content[i : i + 7] == "<think>":
                    depth += 1
                    i += 7
                elif content[i : i + 8] == "</think>":
                    depth -= 1
                    i += 8
                    if depth == 0:
                        break
                else:
                    i += 1
            continue
        if content[i : i + 8] == "</think>":
            # Orphan close tag; skip it
            i += 8
            continue
        out_parts.append(content[i])
        i += 1
    return "".join(out_parts)


class BaseUserSimulationEnv(abc.ABC):
    metadata = {}

    @abc.abstractmethod
    def reset(self, instruction: Optional[str] = None) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def step(self, content: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_total_cost(self) -> float:
        raise NotImplementedError


class HumanUserSimulationEnv(BaseUserSimulationEnv):
    def reset(self, instruction: str) -> str:
        return input(f"{instruction}\n")

    def step(self, content: str) -> str:
        return input(f"{content}\n")

    def get_total_cost(self) -> float:
        return 0


class LLMUserSimulationEnv(BaseUserSimulationEnv):
    def __init__(self, model: str, provider: str) -> None:
        super().__init__()
        self.messages: List[Dict[str, Any]] = []
        self.model = model
        self.provider = provider
        self.total_cost = 0.0
        self.reset()

    def generate_next_message(self, messages: List[Dict[str, Any]]) -> str:
        api_base = os.getenv('USER_MODEL_API_BASE', None)
        res = completion_with_retry(
            model=self.model, 
            custom_llm_provider=self.provider, 
            messages=messages,
            api_base=api_base,
            timeout=3600
        )
        message = res.choices[0].message
        self.messages.append(message.model_dump())
        self.total_cost = res._hidden_params["response_cost"]
        raw_llm_output = message.content or ""
        if _DEBUG_RESPOND_PATH and messages:
            last_user = next((m for m in reversed(messages) if m.get("role") == "user"), None)
            agent_content_preview = (last_user.get("content") or "")[:300] if last_user else None
            _respond_path_debug_user({
                "source": "LLMUserSimulationEnv",
                "agent_content_preview": agent_content_preview,
                "raw_llm_output_preview": raw_llm_output[:300],
            })
        return raw_llm_output

    def build_system_prompt(self, instruction: Optional[str]) -> str:
        instruction_display = (
            ("\n\nInstruction: " + instruction + "\n")
            if instruction is not None
            else ""
        )
        return f"""You are a user interacting with an agent.{instruction_display}
Rules:
- Just generate one line at a time to simulate the user's message.
- Do not output <think> tags or internal reasoning; output only the user's reply.
- Do not give away all the instruction at once. Only provide the information that is necessary for the current step.
- Do not hallucinate information that is not provided in the instruction. For example, if the agent asks for the order id but it is not mentioned in the instruction, do not make up an order id, just say you do not remember or have it.
- If the instruction goal is satisified, generate '###STOP###' as a standalone message without anything else to end the conversation.
- Do not repeat the exact instruction in the conversation. Instead, use your own words to convey the same information.
- You are the customer, not the agent. Reply in first person as the user (\"I\"), never as the airline agent.
- Never start your message with templates like \"Your booking is confirmed\" or similar agent-style confirmations; those are produced only by the agent.
- Answer concisely to the last agent message, and do not paraphrase the agent's responses back to them.
- Try to make the conversation as natural as possible, and stick to the personalities in the instruction."""

    def reset(self, instruction: Optional[str] = None) -> str:
        self.messages = [
            {
                "role": "system",
                "content": self.build_system_prompt(instruction=instruction),
            },
            {"role": "user", "content": "Hi! How can I help you today?"},
        ]
        return self.generate_next_message(self.messages)

    def step(self, content: str) -> str:
        self.messages.append({"role": "user", "content": content})
        return self.generate_next_message(self.messages)

    def get_total_cost(self) -> float:
        return self.total_cost


class ReactUserSimulationEnv(LLMUserSimulationEnv):
    def __init__(self, model: str, provider: str) -> None:
        super().__init__(model=model, provider=provider)
        self.reset()

    def build_system_prompt(self, instruction: Optional[str]) -> str:
        instruction_display = (
            ("\n\nInstruction: " + instruction + "\n")
            if instruction is not None
            else ""
        )
        return f"""You are a user interacting with an agent.{instruction_display}
Rules:
- First, generate a Thought about what to do next (this message will not be sent to the agent).
- Then, generate a one line User Response to simulate the user's message (this message will be sent to the agent).
- Do not use <think> tags in your Thought or User Response; output plain text only.
- Do not give away all the instruction at once. Only provide the information that is necessary for the current step.
- Do not hallucinate information that is not provided in the instruction. For example, if the agent asks for the order id but it is not mentioned in the instruction, do not make up an order id, just say you do not remember or have it.
- If the instruction goal is satisified, generate '###STOP###' as the User Response without anything else to end the conversation.
- Do not repeat the exact instruction in the conversation. Instead, use your own words to convey the same information.
- You are the customer, not the agent. In the User Response, reply in first person as the user (\"I\"), never as the airline agent.
- Never start the User Response with templates like \"Your booking is confirmed\" or similar agent-style confirmations; those are produced only by the agent.
- Keep the User Response concise and focused on answering the last agent message.
- Try to make the conversation as natural as possible, and stick to the personalities in the instruction.

Format:

Thought:
<the thought>

User Response:
<the user response (this will be parsed and sent to the agent)>"""

    def generate_next_message(self, messages: List[Dict[str, Any]]) -> str:
        api_base = os.getenv('USER_MODEL_API_BASE', None)
        res = completion_with_retry(
            model=self.model, 
            custom_llm_provider=self.provider, 
            messages=messages,
            api_base=api_base,
            timeout=3600
        )

        message = res.choices[0].message
        self.messages.append(message.model_dump())
         
        if hasattr(res, "_hidden_params"):
            self.total_cost = res._hidden_params.get("response_cost", 0.0)
        else:
            self.total_cost = 0.0
        raw_llm_output = message.content or ""
        parsed = self.parse_response(raw_llm_output)
        if _DEBUG_RESPOND_PATH and messages:
            last_user = next((m for m in reversed(messages) if m.get("role") == "user"), None)
            agent_content_preview = (last_user.get("content") or "")[:300] if last_user else None
            _respond_path_debug_user({
                "source": "ReactUserSimulationEnv",
                "agent_content_preview": agent_content_preview,
                "raw_llm_output_preview": raw_llm_output[:300],
                "parsed_user_reply_preview": (parsed or "")[:300],
            })
        return parsed

    def reset(self, instruction: Optional[str] = None) -> str:
        self.messages = [
            {
                "role": "system",
                "content": self.build_system_prompt(instruction=instruction),
            },
            {"role": "user", "content": "Hi! How can I help you today?"},
        ]
        return self.generate_next_message(self.messages)

    def parse_response(self, response: str) -> str:
        """
        Parse raw LLM output from the user model into the single-line
        user reply that will be sent to the agent.

        Supports both:
          - The preferred React-style framing:
                Thought:
                <...>

                User Response:
                <the user reply>
          - And more generic reasoning formats that may include <think>...</think>
            blocks without explicit Thought/User Response headers.
        """
        # First, strip any <think>...</think> blocks so we never leak chain-of-thought.
        cleaned = strip_think_tags(response or "").strip()

        # STOP handling on the cleaned text.
        if "###STOP###" in cleaned:
            return "###STOP###"

        # Prefer explicit React-style User Response headers when present.
        if "User Response:" in cleaned:
            _, user_response = cleaned.split("User Response:", 1)
            out = user_response.strip()
            # Best-effort clean-up: if the model accidentally repeated framing
            # markers inside the User Response block, strip everything up to
            # the last occurrence so we return only the actual reply.
            for marker in ("User Response:", "Thought:"):
                if marker in out:
                    # Keep the text after the last marker instance.
                    out = out.split(marker, 1)[-1].strip()
            return out

        # Fallback: Thought-only framing; return its body.
        if "Thought:" in cleaned:
            _, user_response = cleaned.split("Thought:", 1)
            return user_response.strip()

        # Final fallback: no explicit framing, but we may still have a mix of
        # reasoning and a user-facing line (e.g. after stripping <think>).
        # In that case, return the last non-empty line as the user reply.
        lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
        if lines:
            return lines[-1]

        # Truly malformed output: nothing usable.
        raise ValueError(f"Invalid response format: {response}")

    def step(self, content: str) -> str:
        self.messages.append({"role": "user", "content": content})
        return self.generate_next_message(self.messages)

    def get_total_cost(self) -> float:
        return self.total_cost


class VerifyUserSimulationEnv(LLMUserSimulationEnv):
    def __init__(self, model: str, provider: str, max_attempts: int = 3) -> None:
        self.model = model
        self.provider = provider
        self.max_attempts = max_attempts
        self.reset()

    def generate_next_message(self, messages: List[Dict[str, Any]]) -> str:
        attempts = 0
        cur_message = None
        while attempts < self.max_attempts:
            api_base = os.getenv('USER_MODEL_API_BASE', None)
            res = completion_with_retry(
                model=self.model, 
                custom_llm_provider=self.provider, 
                messages=messages,
                api_base=api_base,
                timeout=3600
            )

            cur_message = res.choices[0].message
            self.total_cost = res._hidden_params["response_cost"]
            if verify(self.model, self.provider, cur_message, messages):
                self.messages.append(cur_message.model_dump())
                return cur_message.content
            attempts += 1
        assert cur_message is not None
        return cur_message.content

    def reset(self, instruction: Optional[str] = None) -> str:
        self.messages = [
            {
                "role": "system",
                "content": self.build_system_prompt(instruction=instruction),
            },
            {"role": "user", "content": "Hi! How can I help you today?"},
        ]
        return self.generate_next_message(self.messages)

    def step(self, content: str) -> str:
        self.messages.append({"role": "user", "content": content})
        return self.generate_next_message(self.messages)

    def get_total_cost(self) -> float:
        return self.total_cost


def map_role_label(role: str) -> str:
    if role == "user":
        return "Customer"
    elif role == "assistant":
        return "Agent"
    else:
        return role.capitalize()


def verify(
    model: str, provider: str, response: str, messages: List[Dict[str, Any]]
) -> bool:
    transcript = "\n".join(
        [
            f"{map_role_label(message['role'])}: {message['content']}"
            for message in messages
        ]
    )
    prompt = f"""You are a supervisor of the Agent in the conversation. You are given a Transcript of a conversation between a Customer and an Agent. The Customer has generated a Response, and you need to verify if it is satisfactory (true) or not (false).
Your answer will be parsed, so do not include any other text than the classification (true or false).
    
# Transcript:
{transcript}

# Response:
{response}

-----

Classification:"""
    api_base = os.getenv('USER_MODEL_API_BASE', None)
    res = completion_with_retry(
        model=model,
        custom_llm_provider=provider,
        messages=[{"role": "user", "content": prompt}],
        api_base=api_base,
        timeout=3600
    )
    return "true" in res.choices[0].message.content.lower()


def reflect(
    model: str, provider: str, response: str, messages: List[Dict[str, Any]]
) -> str:
    transcript = "\n".join(
        [
            f"{map_role_label(message['role'])}: {message['content']}"
            for message in messages
        ]
    )
    prompt = f"""You are a supervisor of the Agent in the conversation. You are given a Transcript of a conversation between a (simulated) Customer and an Agent. The Customer generated a Response that was marked as unsatisfactory by you.
You need to generate a Reflection on what went wrong in the conversation, and propose a new Response that should fix the issues.
Your answer will be parsed, so do not include any other text than the classification (true or false).
    
# Transcript:
{transcript}

# Response:
{response}

# Format:

Reflection:
<the reflection>

Response:
<the response (this will be parsed and sent to the agent)>"""
    api_base = os.getenv('USER_MODEL_API_BASE', None)
    res = completion_with_retry(
        model=model,
        custom_llm_provider=provider,
        messages=[{"role": "user", "content": prompt}],
        api_base=api_base,
        timeout=3600
    )
    _, response = res.choices[0].message.content.split("Response:")
    return response.strip()


class ReflectionUserSimulationEnv(LLMUserSimulationEnv):
    def __init__(self, model: str, provider: str, max_attempts: int = 2) -> None:
        self.model = model
        self.provider = provider
        self.max_attempts = max_attempts
        self.reset()

    def generate_next_message(self, messages: List[Dict[str, Any]]) -> str:
        cur_messages = messages.copy()
        initial_response = super().generate_next_message(cur_messages)
        if verify(self.model, self.provider, initial_response, cur_messages):
            return initial_response
        attempts = 1
        while attempts < self.max_attempts:
            new_message = reflect(
                self.model, self.provider, initial_response, cur_messages
            )
            cur_messages.append({"role": "user", "content": new_message})
            new_response = super().generate_next_message(cur_messages)
            if verify(self.model, self.provider, new_response, cur_messages):
                return new_response
            attempts += 1
        return initial_response

    def reset(self, instruction: Optional[str] = None) -> str:
        self.messages = [
            {
                "role": "system",
                "content": self.build_system_prompt(instruction=instruction),
            },
            {"role": "user", "content": "Hi! How can I help you today?"},
        ]
        return self.generate_next_message(self.messages)

    def step(self, content: str) -> str:
        self.messages.append({"role": "user", "content": content})
        return self.generate_next_message(self.messages)

    def get_total_cost(self) -> float:
        return self.total_cost


class UserStrategy(enum.Enum):
    HUMAN = "human"
    LLM = "llm"
    REACT = "react"
    VERIFY = "verify"
    REFLECTION = "reflection"


def load_user(
    user_strategy: Union[str, UserStrategy],
    model: Optional[str] = "gpt-4o",
    provider: Optional[str] = None,
) -> BaseUserSimulationEnv:
    if isinstance(user_strategy, str):
        user_strategy = UserStrategy(user_strategy)
    if user_strategy == UserStrategy.HUMAN:
        return HumanUserSimulationEnv()
    elif user_strategy == UserStrategy.LLM:
        if model is None:
            raise ValueError("LLM user strategy requires a model")
        if provider is None:
            raise ValueError("LLM user strategy requires a model provider")
        return LLMUserSimulationEnv(model=model, provider=provider)
    elif user_strategy == UserStrategy.REACT:
        if model is None:
            raise ValueError("React user strategy requires a model")
        if provider is None:
            raise ValueError("React user strategy requires a model provider")
        return ReactUserSimulationEnv(model=model, provider=provider)
    elif user_strategy == UserStrategy.VERIFY:
        if model is None:
            raise ValueError("Verify user strategy requires a model")
        if provider is None:
            raise ValueError("Verify user strategy requires a model provider")
        return VerifyUserSimulationEnv(model=model, provider=provider)
    elif user_strategy == UserStrategy.REFLECTION:
        if model is None:
            raise ValueError("Reflection user strategy requires a model")
        if provider is None:
            raise ValueError("Reflection user strategy requires a model provider")
        return ReflectionUserSimulationEnv(model=model, provider=provider)
    raise ValueError(f"Unknown user strategy {user_strategy}")
