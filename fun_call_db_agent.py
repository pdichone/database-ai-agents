import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import pandas as pd

from sqlalchemy import create_engine
import numpy as np
from sqlalchemy import text
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


llm_name = "gpt-3.5-turbo"
model = ChatOpenAI(api_key=openai_key, model=llm_name)

# for the weather function calling
client = OpenAI(api_key=openai_key)

from langchain.agents import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase

# create a db from csv file

# Path to your SQLite database file
database_file_path = "./db/salary.db"


# Create an engine to connect to the SQLite database
# SQLite only requires the path to the database file
engine = create_engine(f"sqlite:///{database_file_path}")
file_url = "./data/salaries_2023.csv"
os.makedirs(os.path.dirname(database_file_path), exist_ok=True)
df = pd.read_csv(file_url).fillna(value=0)
df.to_sql("salaries_2023", con=engine, if_exists="replace", index=False)


def run_conversation(
    query="""What is the average salary and the count of female employees
    #                   in the ABS 85 Administrative Services division?""",
):

    messages = [
        # {
        #     "role": "user",
        #     "content": """What is the average salary and the count of female employees
        #               in the ABS 85 Administrative Services division?""",
        # },
        {
            "role": "user",
            "content": query,
        },
        # {
        #     "role": "user", # gives error request too large
        #     "content": """How many employees have overtime pay above 5000?""",
        # },
    ]

    # Call the model with the conversation and available functions
    response = client.chat.completions.create(
        model=llm_name,
        messages=messages,
        tools=helpers.tools_sql,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    # print(response_message.model_dump_json(indent=2))
    # print("tool calls: ", response_message.tool_calls)

    tool_calls = response_message.tool_calls
    if tool_calls:
        # Step 3: call the function
        available_functions = {
            "get_avg_salary_and_female_count_for_division": get_avg_salary_and_female_count_for_division,
            "get_total_overtime_pay_for_department": get_total_overtime_pay_for_department,
            "get_total_longevity_pay_for_grade": get_total_longevity_pay_for_grade,
            "get_employee_count_by_gender_in_department": get_employee_count_by_gender_in_department,
            "get_employees_with_overtime_above": get_employees_with_overtime_above,
        }
        messages.append(response_message)  # extend conversation with assistant's reply

        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            if function_name == "get_employees_with_overtime_above":
                function_response = function_to_call(amount=function_args.get("amount"))
            elif function_name == "get_total_longevity_pay_for_grade":
                function_response = function_to_call(grade=function_args.get("grade"))
            else:
                function_response = function_to_call(**function_args)
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                }
            )  # extend conversation with function responses
            second_response = client.chat.completions.create(
                model=llm_name,
                messages=messages,
            )  # get a new response from the model where it can see the function response

        return second_response


# Example calls to the functions
if __name__ == "__main__":
    res = (
        run_conversation(
            query="""What is the total longevity pay for employees with the grade 'M3'?"""
        )
        .choices[0]
        .message.content
    )

    print(res)
    # run_conversation()
    # Step 1: First direct call to the functions =
    # division_name = "ABS 85 Administrative Services"
    # department_name = "Alcohol Beverage Services"
    # grade = "M3"
    # overtime_amount = 5000

    # avg_salary_and_female_count = get_avg_salary_and_female_count_for_division(
    #     division_name
    # )
    # total_overtime_pay = get_total_overtime_pay_for_department(department_name)
    # total_longevity_pay = get_total_longevity_pay_for_grade(grade)
    # employee_count_by_gender = get_employee_count_by_gender_in_department(
    #     department_name
    # )
    # employees_with_high_overtime = get_employees_with_overtime_above(overtime_amount)

    # print(
    #     f"Average Salary and Female Count for Division '{division_name}': {avg_salary_and_female_count}"
    # )
    # print(
    #     f"Total Overtime Pay for Department '{department_name}': {total_overtime_pay}"
    # )
    # # print(f"Total Longevity Pay for Grade '{grade}': {total_longevity_pay}")
    # # print(
    # #     f"Employee Count by Gender in Department '{department_name}': {employee_count_by_gender}"
    # # )
    # # print(
    # #     f"Employees with Overtime Pay Above {overtime_amount}: {employees_with_high_overtime}"
    # # )
