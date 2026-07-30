import streamlit as st
from groq import Groq

from core.config import load_config
from core.db import run_sql
from core.utils import clean_sql

config = load_config()

SCHEMA = """
Tables:

employee(emp_id, first_name, last_name, birth_day, sex, salary, super_id, branch_id)
branch(branch_id, branch_name, mgr_id, mgr_start_date)
client(client_id, client_name, branch_id)
works_with(emp_id, client_id, total_sales)
branch_supplier(branch_id, supplier_name, supply_type)

Relationships:
- employee.branch_id → branch.branch_id
- works_with.emp_id → employee.emp_id
- works_with.client_id → client.client_id
- client.branch_id → branch.branch_id
"""


# ---------------- GROQ CLIENT ----------------
@st.cache_resource
def get_client():
    return Groq(api_key=config["groq_api"]["api_key"])


client = get_client()


# ---------------- SQL GENERATION ----------------
def generate_sql(question, history=None):
    messages = [
        {
            "role": "system",
            "content": f"""
You are a PostgreSQL expert.

Rules:
- ONLY return raw SQL
- NO markdown
- NO explanations
- Only SELECT queries

IMPORTANT:
- Prefer human-readable columns over IDs
- employee → first_name, last_name
- client → client_name
- branch → branch_name
- Only include IDs if explicitly asked

- Use proper JOIN conditions
- Use GROUP BY when needed
- Never hallucinate columns

Use conversation context if relevant.

Schema:
{SCHEMA}
"""
        }
    ]

    # Add conversation history (last few messages)
    if history:
        for msg in history[-6:]:
            if msg["role"] == "user":
                messages.append({
                    "role": "user",
                    "content": msg["content"]
                })

            elif msg["role"] == "assistant":
                # Only pass SQL, NOT dataframe
                if "sql" in msg:
                    messages.append({
                        "role": "assistant",
                        "content": f"Previous SQL: {msg['sql']}"
                    })

    # Current question
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )

    return clean_sql(response.choices[0].message.content)


# ---------------- SQL FIXING ----------------
def fix_sql(query, error):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"""
You are a PostgreSQL expert.

Fix the SQL query.

STRICT RULES:
- ONLY return raw SQL
- NO explanations
- NO markdown
- Output must start with SELECT
- Only SELECT queries

Schema:
{SCHEMA}
"""
            },
            {
                "role": "user",
                "content": f"Query:\n{query}\n\nError:\n{error}"
            }
        ]
    )

    return clean_sql(response.choices[0].message.content)


# ---------------- EXECUTION WITH RETRY ----------------
def execute_with_retry(question, history=None):
    # Step 1: Generate SQL
    sql_query = generate_sql(question, history)

    # Step 2: Execute
    df, error = run_sql(sql_query)

    if error:
        # Step 3: Fix
        fixed_sql = fix_sql(sql_query, error)

        # Step 4: Retry
        df, error = run_sql(fixed_sql)

        return {
            "initial_query": sql_query,
            "fixed_query": fixed_sql,
            "data": df,
            "error": error
        }

    return {
        "initial_query": sql_query,
        "fixed_query": None,
        "data": df,
        "error": None
    }
