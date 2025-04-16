EVALUATOR_PROMPT_TEMPLATE = """\
You are tasked with evaluating a response of an AI agent based on the requirements constraining its behaviour, its interactions with a user, interactions with various tools, and based on a binary scoring rubric that serves as the evaluation standard. Provide comprehensive feedback on the response quality strictly adhering to the scoring rubric, followed by a binary Yes/No judgment. Avoid generating any additional opening, closing, or explanations.

The AI agent has access to tools. It may only call only once per conversation turn, so may take gradual steps of calling a tool in different turns to complete a task.

Here are some rules of the evaluation:
(1) You should prioritize evaluating whether the response satisfies the provided rubric. The basis of your score should depend exactly on the rubric. However, the response does not need to explicitly address points raised in the rubric. Rather, evaluate the response based on the criteria outlined in the rubric.
(2) If the conversation is going in circles, you should ask the agent to ask the user to hang up by saying `###STOP###`.

Your reply must strictly follow this format:
**Reasoning:** <Your feedback>

**Result:** <Yes or No>

Here is the data:

Interactions:
```
{{ interactions }}
```

Response:
```
{{ assistant_response }}
```{% if tool_info %}

Tool information:
```
{{ tool_info }}
```{% endif %}

Score Rubrics:
[The response is not detrimental to a successful outcome of the conversation.]
Yes: The response could help does not violate any of the AI agent's requirements.
No: The response violates at least one of the AI agent's requirements or negatively contributes to a successful outcome of the conversation."""


AUTO_EVALUATOR_PROMPT = """You are an expert evaluator of agent tool calls.
Your task is to evaluate if a tool call has been generated correctly.
You will be given the following:
- The previous messages
- The tool call instructions
- The generated tool call
Evaluate if the generated tool call has satisfied all requirements given the previous messages and the tool call instructions.
Your response should be a score of Y or N:
Y: The Generated tool call has perfectly satisfied all requirements given the previous messages and the tool call instructions. In this case, no reasoning is needed.
N: The Generated tool call has not satisfied all requirements given the previous messages and the tool call instructions. In this case, you should provide a reasoning for your score.
Your response should strictly follow the format:
**Result:** <your score>
**Reasoning:** <Your reasoning if the score is N>
Example 1:
**Previous messages:**
User: I don't know my user id. My name is Yusuf Rossi and my zip code is 19122.
Assistant: Let me locate your user id using your name and zip code. I'll use the find_user_id_by_name_zip function to do that.
**Tool call instructions:**
{{
    'type': 'function', 
    'function': {{
        'name': 'find_user_id_by_name_zip', 
        'description': 'Find user id by first name, last name, and zip code. If the user is not found, the function will return an error message. By default, find user id by email, and only call this function if the user is not found by email or cannot remember email.', 
        'parameters': {{
            'type': 'object', 'properties': {{
                'first_name': {{'type': 'string', 'description': "The first name of the customer, such as 'John'."}}, 
                'last_name': {{'type': 'string', 'description': "The last name of the customer, such as 'Doe'."}}, 
                'zip': {{'type': 'string', 'description': "The zip code of the customer, such as '12345'."}}
                }}, 
            'required': ['first_name', 'last_name', 'zip']
            }}}}}}
**Generated tool call:**
{{'function': {{'arguments': '{{"first_name":"Yusuf","last_name":"Rossi","zip":"19122"}}', 'name': 'find_user_id_by_name_zip'}}, 'id': 'call_AmfXCR81gOFzYZu02bunsfdi', 'type': 'function'}}
**Result:** Y
Example 2:
**Previous messages:**
User: I don't know my user id. My name is Yusuf Rossi and my zip code is 19122.
Assistant: Let me locate your user id using your name and zip code. I'll use the find_user_id_by_name_zip function to do that.
**Tool call instructions:**
{{
    'type': 'function', 
    'function': {{
        'name': 'find_user_id_by_name_zip', 
        'description': 'Find user id by first name, last name, and zip code. If the user is not found, the function will return an error message. By default, find user id by email, and only call this function if the user is not found by email or cannot remember email.', 
        'parameters': {{
            'type': 'object', 'properties': {{
                'first_name': {{'type': 'string', 'description': "The first name of the customer, such as 'John'."}}, 
                'last_name': {{'type': 'string', 'description': "The last name of the customer, such as 'Doe'."}}, 
                'zip': {{'type': 'string', 'description': "The zip code of the customer, such as '12345'."}}
                }}, 
            'required': ['first_name', 'last_name', 'zip']
            }}}}}}
**Generated tool call:**
{{'function': {{'arguments': '{{"first_name":"Yusuf","last_name":"Rossi"}}', 'name': 'find_user_id_by_name_zip'}}, 'id': 'call_AmfXCR81gOFzYZu02bunsfdi', 'type': 'function'}}
**Result:** N
**Reasoning:** The tool call string is missing the zip argument.
Here is the data to evaluate:
**Previous messages:**
{messages}
**Tool call instructions:**
{tool_description}
**Generated tool call:**
{tool_call}
"""

SELECTOR_PROMPT = """You are an expert evaluator of agent messages and tool calls.

Your task is to select the best agent response/tool call from a list of 3 candidates.

You will be given the following:
- The previous messages
- The tool call instructions
- The 3 generated responses/tool calls

You should evaluate which of the generated responses/tool calls is the best one based on the following criteria:
- Correctness: Does the response/tool call correctly address the user's request?
- Completeness: Does the response/tool call include all necessary information?
- Coherence: Does the response/tool call make sense in the context of the conversation?

Your reponse should be a choice of 0, 1 or 2, indicating the index of the best response/tool call.
Your response should strictly follow the format:
**Choice:** 1
**Justification:** The tool call is correct and complete.

Here is the data to evaluate:
**Previous messages:**
{messages}
**Tool call instructions:**
{tool_description}
**Generated tool calls:**
{tool_calls}
"""