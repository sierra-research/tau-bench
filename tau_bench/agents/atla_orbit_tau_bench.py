import logfire
import json
from typing import List, Dict, Any, Tuple, Callable
from tau_bench.agents.atla_orbit_base import AtlaOrbitBase
from tau_bench.types import RESPOND_ACTION_NAME, Action
from tau_bench.agents.atla_orbit_tau_bench_prompts import AUTO_EVALUATOR_PROMPT

## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TAU Bench specific agent
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class AtlaOrbitTauBench(AtlaOrbitBase):
    def __init__(self, mode: str, **kwargs):
        super().__init__(mode)
        self.tools_info = kwargs.get('tools_info', []) # Extra context for the decorator
        self.kwargs = kwargs

    # Function to evaluate the response
    def evaluate_response(self, func: Callable, *args, **kwargs) -> Tuple[Any, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute the completion function, evaluate the response, and return the result along with the evaluation.
        
        Args:
           func (Callable): The completion function to be executed.
           *args: Variable length argument list for the completion function.
           **kwargs: Arbitrary keyword arguments for the completion function.
           
        Returns:
            Tuple[Any, List[Dict[str, Any]], Dict[str, Any]]: The result of the completion function, the list of messages, and the evaluation result.
            The evaluation result is a dictionary containing the score and critique.
        """
        
        # Call the function to get the result
        result = func(*args, **kwargs)

        # Extract next message and action
        messages = kwargs.get('messages', [])
        next_message = result.choices[0].message.model_dump()
        action = message_to_action(next_message)
        
        # Only evaluate tool calls
        if action.name != RESPOND_ACTION_NAME:
            next_message["tool_calls"] = next_message["tool_calls"][:1]
            tool_name = next_message["tool_calls"][0]["function"]["name"]
            
            # EXTRACT STRUCTURED DATA
            prompt_inputs = {
                "messages": messages,
                "tool_description": [t for t in self.tools_info if t['function']['name'] == tool_name][0],
                "tool_call": str(next_message["tool_calls"][0])
            }
            
            # EVALUATE - PROMPT SPECIFIC INPUTS/OUTPUTS
            evaluation_result = self.call_selene_mini(
                AUTO_EVALUATOR_PROMPT.format(**prompt_inputs)
            )
            evaluation_result_parsed = {
                "critique": evaluation_result.split("**Reasoning:**")[1].strip() if "**Reasoning:**" in evaluation_result else "",
                "score": "**Result:** Y" in evaluation_result,
            }
            
            # LOG EVALUATION
            if not evaluation_result_parsed["score"]:
                logfire.warn("Tool called failed check: {critique}", critique=evaluation_result_parsed["critique"], _tags = [f"failed_{tool_name}"])
                
            return result, messages, evaluation_result_parsed
    
        # If not a tool call, return True
        else:    
          return result, messages, {"score": True, "critique": ""}

    # Function to improve the response
    def improve_response(self, func: Callable, *args, **kwargs) -> Tuple[Any, List[Dict[str, Any]]]:
        max_attempts = kwargs.get('max_attempts', 3)
        
        # Call the function a maximum of max_attempts times to try to improve the response
        for attempt in range(max_attempts):
            result, messages, eval_result = self.evaluate_response(func, *args, **kwargs)
            
            if eval_result["score"]:
                return result, messages, {"score": True, "critique": "", "retries": attempt}
            else:
                logfire.warn(f"Retry attempt {attempt + 1}: Tool call failed check: {eval_result['critique']}")
                messages.append(
                    {"role": "user", "content": f"You didn't generate the tool call correctly, please try again: {eval_result['critique']}"}
                )
                
        logfire.warning(f"Failed to improve response after {max_attempts} attempts")
        return result, messages
    
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
