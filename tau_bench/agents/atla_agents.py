import logfire
import json
import re
from typing import List, Dict, Any, Tuple, Callable, TypeVar, Literal
from atla.satellite_agent import AtlaSatelliteAgent
from tau_bench.types import RESPOND_ACTION_NAME, Action
from tau_bench.agents.atla_prompts import SELECTOR_PROMPT, EVALUATOR_PROMPT_TEMPLATE
from ast import literal_eval
from jinja2 import Template

## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TAU Bench specific AtlaSatellite agent
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
T = TypeVar("T")


def format_interactions(interactions: list[dict[str, Any]]) -> str:
    return "\n\n".join([format_interaction(interaction) for interaction in interactions])


def format_interaction(interaction: dict[str, Any]) -> str:
    role = interaction['role']
    content = format_content(interaction)
    name = interaction.get('name', "agent" if role == "assistant" else "")
    name_str = f": {name}" if name else ""
    return f"[{role}{name_str}]\n{content}"


def format_content(interaction: dict[str, Any]) -> str:
    if interaction.get("tool_calls") is None:
        return interaction["content"]

    function_name = interaction["tool_calls"][0]["function"]["name"]
    function_kwargs = interaction["tool_calls"][0]["function"]["arguments"]
    function_kwargs = json.dumps(literal_eval(function_kwargs), indent=4)
    function_kwargs = ",\n    ".join([f"{k}={v}" for k, v in literal_eval(function_kwargs).items()])
    function_str = f"{function_name}(\n    {function_kwargs},\n)"
    return f"Tool call: {function_str}"


class TauBenchSatelliteAgent(AtlaSatelliteAgent):
    def __init__(self, mode: str, **kwargs: Any) -> None:
        super().__init__()
        self.mode = mode
        self.actionable_actions = kwargs.get("actionable_actions", "all")
        self.max_attempts = kwargs.get("max_attempts", 3)
        self.kwargs = kwargs

    # Function to evaluate the response
    def evaluate_response(
        self, func: Callable[..., T], *args: Any, **kwargs: Any
    ) -> Tuple[T, Dict[str, Any]]:
        """
        Execute the completion function, evaluate the response, and return the result along with metadata.

        Args:
           func (Callable): The completion function to be executed.
           *args: Variable length argument list for the completion function.
           **kwargs: Arbitrary keyword arguments for the completion function.

        Returns:
            Tuple[Any, Dict[str, Any]]: The result of the completion function and the metadata.
            The metadata is a dictionary containing the messages, evaluation score, critique, and mode.
        """
        result = func(*args, **kwargs)

        messages: List[Dict[str, Any]] = kwargs.get("messages", [])
        next_message: Dict[str, Any] = result.choices[0].message.model_dump()
        action: Action = message_to_action(next_message)
        if action.name != RESPOND_ACTION_NAME:
            num_tool_calls = len(next_message.get("tool_calls", []))
            if num_tool_calls > 1:
                next_message["tool_calls"] = next_message["tool_calls"][:1]
                result.choices[0].message.tool_calls = result.choices[0].message.tool_calls[:1]
            assert action.name == next_message["tool_calls"][0]["function"]["name"]
            tools_info = [t for t in kwargs["tools"] if t["function"]["name"] == action.name][0]
        else:
            tools_info = None


        metadata: dict[str, Any] = {
            "messages": messages,
            "mode": self.mode,
        }

        interactions_str = format_interactions(messages)
        response_str = format_interactions([next_message])

        evaluator_prompt = Template(EVALUATOR_PROMPT_TEMPLATE).render(
            interactions=interactions_str,
            assistant_response=response_str,
            tool_info=tools_info,
        )
        evaluation_result_str: str = self.call_selene_mini(evaluator_prompt)

        reasoning_match = re.search(r"\*\*Reasoning:\*\*\s*(.*?)(?=\n\*\*Result:|$)", evaluation_result_str, re.DOTALL)
        result_match = re.search(r"\*\*Result:\*\*\s*(Yes|No)", evaluation_result_str)

        if reasoning_match is None:
            logfire.warn("No feedback found in evaluator response")
        if result_match is None:
            logfire.warn("No judgement found in evaluator response, assuming OK.")

        evaluation_result = {
            "judgement": (result_match.group(1) == "Yes") if result_match else True,
            "feedback": reasoning_match.group(1).strip() if reasoning_match else "",
            "evaluation": evaluation_result_str,
            "evaluator_prompt": evaluator_prompt,
        }
        metadata.update(evaluation_result)

        logfire.log(
            "info",
            "evaluation_result: {evaluation_result}",
            attributes={"evaluation_result": evaluation_result},
            tags=[f"eval_{action.name}"],
        )

        if not evaluation_result["judgement"]:
            logfire.warn(
                "Tool called failed check: {feedback}",
                feedback=evaluation_result["feedback"],
                _tags=[f"failed_{action.name}"],
            )

        return result, metadata

    # Function to improve the response
    def improve_response(
        self, func: Callable[..., T], *args: Any, **kwargs: Any
    ) -> Tuple[T, Dict[str, Any]]:
        """
        Improve the response by retrying the completion function if the evaluation score is False.

        Args:
            func (Callable[..., T]): The completion function to be executed.
            *args: Variable length argument list for the completion function.
            **kwargs: Arbitrary keyword arguments for the completion function.

        Returns:
            Tuple[T, Dict[str, Any]]: The result of the completion function and metadata.
            The metadata is a dictionary containing the original and final responses, evaluation score, critique, and number of retries.
        """
        metadata: dict[str, Any] = {"messages": kwargs.get("messages", [])}

        for attempt in range(1, self.max_attempts + 1):
            kwargs["messages"] = metadata["messages"]
            result, metadata = self.evaluate_response(func, *args, **kwargs)
            next_message = result.choices[0].message.model_dump()
            action = message_to_action(next_message)
            metadata["attempts"] = attempt

            actionable: bool = (self.actionable_actions == "all") or (self.actionable_actions == action.name == RESPOND_ACTION_NAME) or ((self.actionable_actions == "tool_calls") and (action.name != RESPOND_ACTION_NAME))
            if not actionable:
                logfire.warn(f"Not improving response in attempt {attempt + 1} because the {action.name} action is not actionable")
                break

            if metadata["judgement"]:
                logfire.info(f"Response OK after {metadata['attempts']} attempts")
                break
            elif attempt < self.max_attempts:
                logfire.warn(f"Attempt {attempt} failed. Feedback: {metadata['feedback']}")
                metadata["messages"] += [
                    {"role": "assistant", "content": format_content(next_message)}
                ]
                metadata["messages"] += [
                    {
                        "role": "assistant",
                        "content": f"{metadata['feedback']}",
                        "name": "evaluator",
                    }
                ]

            else:
                logfire.warning(f"Failed to pass after {self.max_attempts} attempts. Feedback: {metadata['feedback']}")

        return result, metadata

    # Function to select the best response from multiple attempts
    def select_response(
        self, func: Callable[..., T], *args: Any, **kwargs: Any
    ) -> Tuple[T, Dict[str, Any]]:
        """
        Selects the best response from multiple attempts.

        Args:
            func (Callable[..., T]): The completion function to be executed.
            *args: Variable length argument list for the completion function.
            **kwargs: Arbitrary keyword arguments for the completion function.

        Returns:
            Tuple[T, Dict[str, Any]]: The selected response and metadata.
            The metadata contains all responses and their evaluations.
        """
        messages: List[Dict[str, Any]] = kwargs.get("messages", [])
        tools_info: List[Dict[str, Any]] = kwargs.get("tools", [])
        kwargs["temperature"] = (
            0.8  # Overriding temperature so that we have some variation to select from
        )

        attempts: int = kwargs.get("attempts", 3)
        results: List[Dict[str, Any]] = []
        options = []
        for attempt in range(attempts):
            result = func(*args, **kwargs)
            results.append(result)
            next_message: Dict[str, Any] = result.choices[0].message.model_dump()
            options.append(next_message)

        evaluation_results_str: str = self.call_selene_mini(
            prompt=SELECTOR_PROMPT.format(
                messages=messages, tool_description=tools_info, tool_calls=options
            )
        )

        # extract choice as int after **Choice:** after handling any possible errors
        try:
            choice = int(
                evaluation_results_str.split("**Choice:**")[1].strip().split("\n")[0]
            )
        except (IndexError, ValueError):
            choice = 0
            logfire.error(
                "Failed to extract choice from evaluation results. Defaulting to choice 0."
            )
        justification = evaluation_results_str.split("**Justification:**")[1].strip()
        logfire.info(f"Selected choice: {choice} with justification: {justification}")
        next_message: Dict[str, Any] = options[choice]

        return results[choice], {
            "mode": "select",
            "messages": messages,
            "options": options,
            "choice": choice,
            "justification": justification,
        }

    # Orbit function to handle different modes
    def orbit(
        self, func: Callable[..., T], *args: Any, **kwargs: Any
    ) -> Tuple[T, Dict[str, Any]]:
        """
        This method is invoked by the __call__ method when the TauBenchSatellite is used as a decorator or wrapper.
        It defines the "orbit" function that wraps around a completion function, adding evaluation, improvement,
        and other functionalities based on the specified mode.

        Args:
            func (Callable): The completion function to be executed with a return type of T.
            *args: Variable length argument list for the completion function.
            **kwargs: Arbitrary keyword arguments for the completion function.

        Returns:
            Tuple[T, Dict[str, Any]]: The result of the completion function and a dictionary with metadata.
            The type of the result is determined by the completion function.
            The metadata dictionary contains evaluation results, messages, and other relevant information.

        Note:
            This method is automatically called when the TauBenchSatellite instance is used as a decorator
            (@satellite_instance()) or as a wrapper (satellite_instance(func)). The behavior of the orbit
            method depends on the mode specified during the TauBenchSatellite initialization.

        Example:
            satellite = TauBenchSatellite(mode="evaluate")

            @satellite()
            def my_function(x):
                return x * 2

            result, metadata = my_function(5)  # This implicitly calls orbit
        """
        if self.mode == "evaluate":
            return self.evaluate_response(func, *args, **kwargs)
        elif self.mode == "improve":
            return self.improve_response(func, *args, **kwargs)
        elif self.mode == "select":
            return self.select_response(func, *args, **kwargs)
        else:
            result = func(*args, **kwargs)
            return result, {"mode": "passthrough"}


# Copied over from the tool calling agent to avoid circular imports
@logfire.instrument("Extracting action from message")
def message_to_action(
    message: Dict[str, Any],
) -> Action:
    if (
        "tool_calls" in message
        and message["tool_calls"] is not None
        and len(message["tool_calls"]) > 0
        and message["tool_calls"][0]["function"] is not None
    ):
        tool_call = message["tool_calls"][0]
        return Action(
            name=tool_call["function"]["name"],
            kwargs=json.loads(tool_call["function"]["arguments"]),
        )
    else:
        return Action(name=RESPOND_ACTION_NAME, kwargs={"content": message["content"]})


evaluator = TauBenchSatelliteAgent(mode="evaluate")
improver = TauBenchSatelliteAgent(mode="improve", actionable_actions="respond", max_attempts=2)
selector = TauBenchSatelliteAgent(mode="select")
