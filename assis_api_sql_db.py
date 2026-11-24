# HOTFIX: OpenAI shut down the Assistants API, so this lesson now uses the Responses API.
# Same idea as the video, new names: the "assistant" is now a config dict (instructions + tools),
# the "thread" is a Conversation, a "run" is one responses.create() call, and
# submit_tool_outputs() becomes sending "function_call_output" items back. No polling loop needed.
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

import helpers
from helpers import (
    get_avg_salary_and_female_count_for_division,
    get_total_overtime_pay_for_department,
    get_total_longevity_pay_for_grade,
    get_employee_count_by_gender_in_department,
    get_employees_with_overtime_above,
)


# Load environment variables from .env file
load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")

llm_name = "gpt-6-luna"  # gpt-3.5-turbo was shut down; see HOTFIX-NOTES.md

client = OpenAI(api_key=openai_key)


# Step 1: "create the assistant"
# The Responses API has no assistant object. You keep the same settings in your code
# and send them with every request. Responses tools are "flat" (name/description/parameters
# at the top level), so we unwrap the Chat Completions style tools from helpers.py.
assistant = {
    "model": llm_name,
    "instructions": "You are a Salary Assistant. Help with salary data. Use the tools to look up the numbers.",
    "tools": [{"type": "function", **tool["function"]} for tool in helpers.tools_sql],
}

# create a thread -> create a conversation
conversation = client.conversations.create()
print(conversation.id)

# add the user message and "run the assistant" in one call
response = client.responses.create(
    **assistant,
    conversation=conversation.id,
    input=[
        {
            "role": "user",
            "content": """What is the total overtime pay for the Alcohol Beverage Services department?""",
        }
    ],
)

available_functions = {
    "get_avg_salary_and_female_count_for_division": get_avg_salary_and_female_count_for_division,
    "get_total_overtime_pay_for_department": get_total_overtime_pay_for_department,
    "get_total_longevity_pay_for_grade": get_total_longevity_pay_for_grade,
    "get_employee_count_by_gender_in_department": get_employee_count_by_gender_in_department,
    "get_employees_with_overtime_above": get_employees_with_overtime_above,
}

# "requires_action" -> the response contains function_call items
tool_calls = [item for item in response.output if item.type == "function_call"]

while tool_calls:
    tool_outputs = []

    for tool_call in tool_calls:
        function_name = tool_call.name
        function_to_call = available_functions[function_name]
        function_args = json.loads(tool_call.arguments)
        if function_name == "get_employees_with_overtime_above":
            function_response = function_to_call(amount=function_args.get("amount"))
        elif function_name == "get_total_longevity_pay_for_grade":
            function_response = function_to_call(grade=function_args.get("grade"))
        else:
            function_response = function_to_call(**function_args)

        print(f"Function response: {function_response}")
        print(tool_call.call_id)

        tool_outputs.append(
            {
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": str(function_response),
            }
        )

    # submit_tool_outputs -> send the outputs back into the same conversation
    response = client.responses.create(
        **assistant,
        conversation=conversation.id,
        input=tool_outputs,
    )
    tool_calls = [item for item in response.output if item.type == "function_call"]

# the final answer
print(response.output_text)

# list everything stored in the conversation (like threads.messages.list)
items = client.conversations.items.list(conversation.id, order="asc")
print(items.model_dump_json(indent=2))
