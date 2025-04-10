import logfire
import json
import re
from typing import List, Dict, Any, Tuple, Callable, TypeVar
from atla.satellite_agent import AtlaSatelliteAgent
from tau_bench.types import RESPOND_ACTION_NAME, Action
from tau_bench.agents.atla_prompts import AUTO_EVALUATOR_PROMPT, SELECTOR_PROMPT

## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TAU Bench specific AtlaSatellite agent
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
T = TypeVar('T')

class TauBenchSatelliteAgent(AtlaSatelliteAgent):
    def __init__(self, mode: str, **kwargs: Any) -> None:
        super().__init__()
        self.mode = mode
        self.kwargs = kwargs

    # Function to evaluate the response
    def evaluate_response(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> Tuple[T, Dict[str, Any]]:
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

        messages: List[Dict[str, Any]] = kwargs.get('messages', [])
        tools_info: List[Dict[str, Any]] = kwargs.get('tools', [])
        next_message: Dict[str, Any] = result.choices[0].message.model_dump()
        action: Action = message_to_action(next_message)
        
        metadata: Dict[str, Any] = {"messages": messages, "score": True, "critique": "", "mode": self.mode}
        
        if action.name != RESPOND_ACTION_NAME:
            next_message["tool_calls"] = next_message["tool_calls"][:1]
            tool_name: str = next_message["tool_calls"][0]["function"]["name"]
            
            prompt_inputs: Dict[str, Any] = {
                "messages": messages,
                "tool_description": [t for t in tools_info if t['function']['name'] == tool_name][0],
                "tool_call": str(next_message["tool_calls"][0])
            }
            
            evaluation_result_str: str = self.call_selene_mini(
                AUTO_EVALUATOR_PROMPT.format(**prompt_inputs)
            )
            evaluation_result: Dict[str, Any] = {
                "critique": evaluation_result_str.split("**Reasoning:**")[1].strip() if "**Reasoning:**" in evaluation_result_str else "",
                "score": "**Result:** Y" in evaluation_result_str,
            }
            logfire.log('info', "evaluation_result: {evaluation_result}", attributes={"evaluation_result": evaluation_result}, tags=[f"eval_{tool_name}"])
            
            if not evaluation_result["score"]:
                logfire.warn("Tool called failed check: {critique}", critique=evaluation_result["critique"], _tags=[f"failed_{tool_name}"])
                metadata.update(evaluation_result)
        
        return result, metadata

    # Function to improve the response
    def improve_response(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> Tuple[T, Dict[str, Any]]:
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
        max_attempts: int = kwargs.get('max_attempts', 3)
        
        for attempt in range(max_attempts):
            result, metadata = self.evaluate_response(func, *args, **kwargs)
            
            if metadata["score"]:
                metadata["retries"] = attempt + 1
                if attempt > 0:
                    logfire.info(f"Improved response after {attempt + 1} attempts")
                return result, metadata
            elif attempt < max_attempts - 1:
                logfire.warn(f"Retry attempt {attempt + 1}: Tool call failed again: {metadata['critique']}")
                metadata['messages'] = kwargs.get('messages', []) + [
                    {"role": "assistant", "content": f"{metadata['critique']}"}
                ]
            else:
                logfire.warning(f"Failed to improve response after {max_attempts} attempts")
        return result, metadata
    
    # Function to select the best response from multiple attempts
    def select_response(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> Tuple[T, Dict[str, Any]]:
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
        messages: List[Dict[str, Any]] = kwargs.get('messages', [])
        tools_info: List[Dict[str, Any]] = kwargs.get('tools', [])
        
        attempts: int = kwargs.get('attempts', 3)
        results: List[Dict[str, Any]] = []
        options = []
        for attempt in range(attempts):
            result = func(*args, **kwargs)
            results.append(result)
            next_message: Dict[str, Any] = result.choices[0].message.model_dump()
            options.append(next_message)
            
        
        evaluation_results_str: str = self.call_selene_mini(
            prompt = SELECTOR_PROMPT.format(
                messages=messages,
                tool_description=tools_info,
                tool_calls=options
            )
        )
        
        # extract choice as int after **Choice:** 
        choice = int(evaluation_results_str.split("**Choice:**")[1].strip().split("\n")[0])
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
    def orbit(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> Tuple[T, Dict[str, Any]]:
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
    if "tool_calls" in message and message["tool_calls"] is not None and len(message["tool_calls"]) > 0 and message["tool_calls"][0]["function"] is not None:
        tool_call = message["tool_calls"][0]
        return Action(
            name=tool_call["function"]["name"],
            kwargs=json.loads(tool_call["function"]["arguments"]),
        )
    else:
        return Action(name=RESPOND_ACTION_NAME, kwargs={"content": message["content"]})


evaluator = TauBenchSatelliteAgent(mode = "evaluate")    
improver = TauBenchSatelliteAgent(mode = "improve")
selector = TauBenchSatelliteAgent(mode = "select")