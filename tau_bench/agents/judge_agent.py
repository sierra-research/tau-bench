from openai import OpenAI
import os
client = OpenAI(
    base_url="http://localhost:8000/v1", 
    api_key=os.environ["ATLA_DEV_API_KEY"]
    )

def call_selene_mini(prompt: str) -> str:
    response = client.chat.completions.create(
        model="atla-selene-mini-20250127",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content



PROMPT = """You are an expert evaluator of agent tool calls.
Your task is to evaluate if a tool call has been generated correctly.
You will be given the following:
- The previous messages
- The tool description
- The generated tool call

Evaluate the generated tool call for correctness, returning a score of Y/N. If the score is N, provide a brief reasoning for why.
Y: The tool call has correctly formatted arguments for the given function, and all of the arguments are correct given the instructions and previous messages. In this case, no reasoning is needed.
N: The tool call string is either incorrectly formatted for the given function, OR the arguments are incorrect given the instructions and previous messages. 
In this case, provide a brief reasoning for why the tool call is incorrect.

Your response should strictly follow the format:
**Result:** <your score>

**Reasoning:** <Your reasoning if the score is N>

Example 1:
**Previous messages:**
User: I don't know my user id. My name is Yusuf Rossi and my zip code is 19122.
Assistant: Let me locate your user id using your name and zip code. I'll use the find_user_id_by_name_zip function to do that.
**Tool description:**
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
**Tool description:**
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
**Tool description:**
{tool_description}
**Generated tool call:**
{tool_call}
"""

def evaluate_tool_call(
    messages: str,
    tool_description: str,
    tool_call: str
) -> str:
    result = call_selene_mini(
        PROMPT.format(
            messages=messages,
            tool_description=tool_description,
            tool_call=tool_call
        )
    )
    return result