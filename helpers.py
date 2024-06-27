from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np
import json

# Create an engine to connect to the SQLite database
database_file_path = "./db/salary.db"
engine = create_engine(f"sqlite:///{database_file_path}")


tools_sql = [
    {
        "type": "function",
        "function": {
            "name": "get_avg_salary_and_female_count_for_division",
            "description": """Retrieves the average salary and the count of 
                              female employees in a specific division.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "division_name": {
                        "type": "string",
                        "description": """The name of the division 
                                          (e.g., 'ABS 85 Administrative Services').""",
                    }
                },
                "required": ["division_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_total_overtime_pay_for_department",
            "description": """Retrieves the total overtime pay for a 
                              specific department.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "department_name": {
                        "type": "string",
                        "description": """The name of the department
                                          (e.g., 'Alcohol Beverage Services').""",
                    }
                },
                "required": ["department_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_total_longevity_pay_for_grade",
            "description": """Retrieves the total longevity pay for a 
                              specific grade.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "grade": {
                        "type": "string",
                        "description": """The grade of the employees
                                          (e.g., 'M3', 'N25').""",
                    }
                },
                "required": ["grade"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_count_by_gender_in_department",
            "description": """Retrieves the count of employees by gender 
                              in a specific department.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "department_name": {
                        "type": "string",
                        "description": """The name of the department
                                          (e.g., 'Alcohol Beverage Services').""",
                    }
                },
                "required": ["department_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employees_with_overtime_above",
            "description": """Retrieves the employees with overtime pay 
                              above a specified amount.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": """The minimum amount of overtime pay
                                          (e.g., 1000.0).""",
                    }
                },
                "required": ["amount"],
            },
        },
    },
]


def get_avg_salary_and_female_count_for_division(division_name):
    try:
        query = f"""
        SELECT AVG(Base_Salary) AS avg_salary, COUNT(*) AS female_count
        FROM salaries_2023
        WHERE Division = '{division_name}' AND Gender = 'F';
        """
        query = text(query)

        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)
        if not result.empty:

            return result.to_dict("records")[0]
        else:
            return json.dumps({"avg_salary": np.nan, "female_count": 0})
            # return {"avg_salary": np.nan, "female_count": 0}
    except Exception as e:
        print(e)
        return json.dumps({"avg_salary": np.nan, "female_count": 0})
        # return {"avg_salary": np.nan, "female_count": 0}


def get_total_overtime_pay_for_department(department_name):
    try:
        query = f"""
        SELECT SUM(Overtime_Pay) AS total_overtime_pay
        FROM salaries_2023
        WHERE Department_Name = '{department_name}';
        """
        query = text(query)

        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)
        if not result.empty:

            return result.to_dict("records")[0]
        else:
            return {"total_overtime_pay": 0}
    except Exception as e:
        print(e)
        return {"total_overtime_pay": 0}


def get_employees_with_overtime_above(amount):
    try:
        query = f"""
        SELECT * 
        FROM salaries_2023
        WHERE Overtime_Pay > {amount};
        """
        query = text(query)

        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)
        if not result.empty:
            return result.to_dict("records")
        else:
            return []
    except Exception as e:
        print(e)
        return []


def get_employee_count_by_gender_in_department(department_name):
    try:
        query = f"""
        SELECT Gender, COUNT(*) AS employee_count
        FROM salaries_2023
        WHERE Department_Name = '{department_name}'
        GROUP BY Gender;
        """
        query = text(query)

        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)
        if not result.empty:
            return result.to_dict("records")
        else:
            return []
    except Exception as e:
        print(e)
        return []


def get_total_longevity_pay_for_grade(grade):
    try:
        query = f"""
        SELECT SUM(Longevity_Pay) AS total_longevity_pay
        FROM salaries_2023
        WHERE Grade = '{grade}';
        """
        query = text(query)

        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)
        if not result.empty:
            return result.to_dict("records")[0]
        else:
            return {"total_longevity_pay": 0}
    except Exception as e:
        print(e)
        return {"total_longevity_pay": 0}
