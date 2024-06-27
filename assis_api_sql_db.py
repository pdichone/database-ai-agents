import json
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import pandas as pd

from sqlalchemy import create_engine
import numpy as np
from sqlalchemy import text
from openai import OpenAI
import streamlit as st

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

llm_name = "gpt-3.5-turbo"
model = ChatOpenAI(api_key=openai_key, model=llm_name)


# for the weather function calling
client = OpenAI(api_key=openai_key)


# Step 1: create the assistant
assistant = client.beta.assistants.create(
    name="Salary Assistant",
    description="Assistant to help with salary data",
    model=llm_name,
    tools=helpers.tools_sql,
)

# create a thread
thread = client.beta.threads.create()
print(thread.id)

message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="""What is the total overtime pay for the Alcohol Beverage Services department?""",
)

messages = client.beta.threads.messages.list(thread_id=thread.id)
print(messages)

# Run the assistant
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
)

import time

start_time = time.time()

status = run.status

while status not in ["completed", "cancelled", "expired", "failed"]:
    time.sleep(5)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    print(
        "Elapsed time: {} minutes {} seconds".format(
            int((time.time() - start_time) // 60), int((time.time() - start_time) % 60)
        )
    )
    status = run.status
    print(f"Status: {status}")
    if status == "requires_action":
        available_functions = {
            "get_avg_salary_and_female_count_for_division": get_avg_salary_and_female_count_for_division,
            "get_total_overtime_pay_for_department": get_total_overtime_pay_for_department,
            "get_total_longevity_pay_for_grade": get_total_longevity_pay_for_grade,
            "get_employee_count_by_gender_in_department": get_employee_count_by_gender_in_department,
            "get_employees_with_overtime_above": get_employees_with_overtime_above,
        }

        tool_outputs = []

        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            if function_name == "get_employees_with_overtime_above":
                function_response = function_to_call(amount=function_args.get("amount"))
            elif function_name == "get_total_longevity_pay_for_grade":
                function_response = function_to_call(grade=function_args.get("grade"))
            else:
                function_response = function_to_call(**function_args)

            print(f"Function response: {function_response}")
            print(tool_call.id)

            tool_outputs.append(
                {"tool_call_id": tool_call.id, "output": str(function_response)}
            )

            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs,
            )

messages = client.beta.threads.messages.list(thread_id=thread.id)

print(messages.model_dump_json(indent=2))
