import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from core.config import load_config

config = load_config()


@st.cache_resource
def get_engine():
    db = config["dunder_mifflin_db"]

    return create_engine(
        f"postgresql+psycopg2://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}",
        pool_pre_ping=True
    )


engine = get_engine()

ALLOWED_TABLES = {
    "employee",
    "branch",
    "client",
    "works_with",
    "branch_supplier"
}


def validate_table_name(table_name):
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Unsupported table: {table_name}")


def run_sql(query, params=None):
    try:
        df = pd.read_sql(text(query), engine, params=params)
        return df, None
    except Exception as e:
        return None, str(e)


def fetch_rows(table_name, limit=500):
    validate_table_name(table_name)
    query = f"SELECT * FROM {table_name} LIMIT :limit"
    return run_sql(query, {"limit": limit})


def execute_write(query, params=None):
    try:
        with engine.begin() as connection:
            connection.execute(text(query), params or {})
        return None
    except Exception as e:
        return str(e)


def insert_record(table_name, values):
    validate_table_name(table_name)

    columns = list(values.keys())
    placeholders = ", ".join(f":{column}" for column in columns)
    query = f"""
    INSERT INTO {table_name} ({", ".join(columns)})
    VALUES ({placeholders})
    """

    return execute_write(query, values)


def update_record(table_name, primary_key_values, updated_values):
    validate_table_name(table_name)

    if not updated_values:
        return "No editable fields were provided."

    set_clauses = []
    params = {}

    for column, value in updated_values.items():
        param_name = f"set_{column}"
        set_clauses.append(f"{column} = :{param_name}")
        params[param_name] = value

    where_clauses = []
    for column, value in primary_key_values.items():
        param_name = f"pk_{column}"
        where_clauses.append(f"{column} = :{param_name}")
        params[param_name] = value

    query = f"""
    UPDATE {table_name}
    SET {", ".join(set_clauses)}
    WHERE {" AND ".join(where_clauses)}
    """

    return execute_write(query, params)


def delete_record(table_name, primary_key_values):
    validate_table_name(table_name)

    params = {}
    where_clauses = []

    for column, value in primary_key_values.items():
        param_name = f"pk_{column}"
        where_clauses.append(f"{column} = :{param_name}")
        params[param_name] = value

    query = f"""
    DELETE FROM {table_name}
    WHERE {" AND ".join(where_clauses)}
    """

    return execute_write(query, params)
