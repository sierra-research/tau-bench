
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