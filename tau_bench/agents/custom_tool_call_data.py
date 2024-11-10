from cashier.prompts.base_prompt import BasePrompt
from cashier.prompts.node_system import NodeSystemPrompt
from cashier.prompts.general_guideline import GeneralGuidelinePrompt
from cashier.prompts.response_guideline import ResponseGuidelinePrompt
from cashier.prompts.state_guideline import StateGuidelinePrompt

class BackgroundPrompt(BasePrompt):

    f_string_prompt ="""The current time is 2024-05-15 15:00:00 EST. You are an airline agent, and you can help customers book, modify, or cancel flight reservations."""

class CustomToolGuideline(BasePrompt):
    f_string_prompt = (
        "<tools_guidelines>\n"
        "- You should not provide any information, knowledge, or procedures not provided by the customer or available tools, or give subjective recommendations or comments.\n"
        "- AVOID stating/mentioning that you can/will perform an action if there are no tools (including state updates) associated with that action.\n"
        "- Before taking any actions that update the booking database (booking, modifying flights, editing baggage, upgrading cabin class, or updating passenger information), you must list the action details and obtain explicit customer confirmation (yes) to proceed."
        "- if you need to perform an action, you can only state to the customer that you performed it after the associated tool (including state update) calls have been successfull.\n"
        "</tools_guidelines>\n"
    )

class AirlineNodeSystemPrompt(NodeSystemPrompt):
    BACKGROUND_PROMPT = BackgroundPrompt
    GUIDELINE_PROMPTS = [
        ResponseGuidelinePrompt,
        StateGuidelinePrompt,
        CustomToolGuideline,
        GeneralGuidelinePrompt,
    ]
