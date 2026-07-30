from datetime import date

import pandas as pd
import streamlit as st

from core.db import delete_record, fetch_rows, insert_record, run_sql, update_record
from core.llm import execute_with_retry

TABLE_EDITOR_CONFIG = {
    "employee": {
        "primary_key": ["emp_id"],
        "display_fields": ["emp_id", "first_name", "last_name"],
        "delete_warning": "Deleting an employee will delete related rows in works_with and set manager/supervisor references to NULL where applicable.",
        "columns": [
            {"name": "emp_id", "label": "Employee ID", "type": "int", "required": True},
            {"name": "first_name", "label": "First name", "type": "text", "required": True},
            {"name": "last_name", "label": "Last name", "type": "text", "required": True},
            {"name": "birth_day", "label": "Birth day", "type": "date", "required": False},
            {"name": "sex", "label": "Sex", "type": "enum", "required": False, "options": ["M", "F"]},
            {"name": "salary", "label": "Salary", "type": "int", "required": False},
            {"name": "super_id", "label": "Supervisor", "type": "fk", "required": False, "references": "employee"},
            {"name": "branch_id", "label": "Branch", "type": "fk", "required": False, "references": "branch"}
        ]
    },
    "branch": {
        "primary_key": ["branch_id"],
        "display_fields": ["branch_id", "branch_name"],
        "delete_warning": "Deleting a branch will cascade to branch_supplier and set related employee/client branch references to NULL.",
        "columns": [
            {"name": "branch_id", "label": "Branch ID", "type": "int", "required": True},
            {"name": "branch_name", "label": "Branch name", "type": "text", "required": True},
            {"name": "mgr_id", "label": "Manager", "type": "fk", "required": False, "references": "employee"},
            {"name": "mgr_start_date", "label": "Manager start date", "type": "date", "required": False}
        ]
    },
    "client": {
        "primary_key": ["client_id"],
        "display_fields": ["client_id", "client_name"],
        "delete_warning": "Deleting a client will cascade to related rows in works_with.",
        "columns": [
            {"name": "client_id", "label": "Client ID", "type": "int", "required": True},
            {"name": "client_name", "label": "Client name", "type": "text", "required": True},
            {"name": "branch_id", "label": "Branch", "type": "fk", "required": False, "references": "branch"}
        ]
    },
    "works_with": {
        "primary_key": ["emp_id", "client_id"],
        "display_fields": ["emp_id", "client_id", "total_sales"],
        "delete_warning": "This row links one employee to one client. Deleting it removes only that relationship record.",
        "columns": [
            {"name": "emp_id", "label": "Employee", "type": "fk", "required": True, "references": "employee"},
            {"name": "client_id", "label": "Client", "type": "fk", "required": True, "references": "client"},
            {"name": "total_sales", "label": "Total sales", "type": "int", "required": False}
        ]
    },
    "branch_supplier": {
        "primary_key": ["branch_id", "supplier_name"],
        "display_fields": ["branch_id", "supplier_name", "supply_type"],
        "delete_warning": "Deleting this row removes only the supplier relationship for the selected branch.",
        "columns": [
            {"name": "branch_id", "label": "Branch", "type": "fk", "required": True, "references": "branch"},
            {"name": "supplier_name", "label": "Supplier name", "type": "text", "required": True},
            {"name": "supply_type", "label": "Supply type", "type": "text", "required": False}
        ]
    }
}


def normalize_value(value):
    if pd.isna(value):
        return None

    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime().date()

    return value


def format_value(value):
    value = normalize_value(value)

    if value is None:
        return "None"

    if isinstance(value, date):
        return value.isoformat()

    return str(value)


def format_record_label(table_name, record):
    display_fields = TABLE_EDITOR_CONFIG[table_name]["display_fields"]
    return " | ".join(
        f"{field}: {format_value(record.get(field))}"
        for field in display_fields
    )


def get_reference_options(table_name):
    df, error = fetch_rows(table_name)

    if error or df is None:
        return [], error

    records = df.to_dict("records")
    options = []

    primary_key = TABLE_EDITOR_CONFIG[table_name]["primary_key"]
    if len(primary_key) != 1:
        return [], f"Foreign key dropdowns for {table_name} are not supported."

    key_name = primary_key[0]

    for record in records:
        normalized_record = {
            column: normalize_value(value)
            for column, value in record.items()
        }
        options.append({
            "value": normalized_record[key_name],
            "label": format_record_label(table_name, normalized_record)
        })

    return options, None


def render_field_input(table_name, action, column, default_value=None, disabled=False):
    field_key = f"editor_{table_name}_{action}_{column['name']}"
    field_type = column["type"]
    normalized_default = normalize_value(default_value)

    if field_type == "fk":
        reference_options, error = get_reference_options(column["references"])
        if error:
            st.error(error)
            return None

        option_values = [None] + [option["value"] for option in reference_options]
        option_labels = {None: "None"}
        for option in reference_options:
            option_labels[option["value"]] = option["label"]

        default_index = 0
        if normalized_default in option_values:
            default_index = option_values.index(normalized_default)

        return st.selectbox(
            column["label"],
            options=option_values,
            index=default_index,
            format_func=lambda value: option_labels[value],
            key=field_key,
            disabled=disabled
        )

    if field_type == "enum":
        option_values = [None] + column["options"] if not column["required"] else column["options"]
        default_index = 0
        if normalized_default in option_values:
            default_index = option_values.index(normalized_default)

        return st.selectbox(
            column["label"],
            options=option_values,
            index=default_index,
            format_func=lambda value: "None" if value is None else value,
            key=field_key,
            disabled=disabled
        )

    return st.text_input(
        column["label"],
        value="" if normalized_default is None else format_value(normalized_default),
        key=field_key,
        disabled=disabled
    )


def parse_field_value(column, raw_value):
    field_type = column["type"]

    if field_type in {"fk", "enum"}:
        if raw_value is None and column["required"]:
            return None, f"{column['label']} is required."
        return raw_value, None

    cleaned_value = raw_value.strip() if isinstance(raw_value, str) else raw_value

    if cleaned_value in ("", None):
        if column["required"]:
            return None, f"{column['label']} is required."
        return None, None

    if field_type == "int":
        try:
            return int(cleaned_value), None
        except ValueError:
            return None, f"{column['label']} must be an integer."

    if field_type == "date":
        try:
            return date.fromisoformat(cleaned_value), None
        except ValueError:
            return None, f"{column['label']} must use YYYY-MM-DD."

    return cleaned_value, None


def render_editor():
    st.header("🛠️ Record Editor")

    table_name = st.selectbox(
        "Select a table",
        list(TABLE_EDITOR_CONFIG.keys()),
        key="editor_table_select"
    )
    action = st.radio(
        "Choose an action",
        ["Insert", "Update", "Delete"],
        horizontal=True,
        key="editor_action_select"
    )

    df, error = fetch_rows(table_name)
    if error:
        st.error(error)
        return

    records = []
    if df is not None:
        records = [
            {column: normalize_value(value) for column, value in record.items()}
            for record in df.to_dict("records")
        ]

    selected_record = None
    if action in {"Update", "Delete"}:
        if not records:
            st.info(f"No records found in `{table_name}`.")
            return

        selected_index = st.selectbox(
            "Select a record",
            options=list(range(len(records))),
            format_func=lambda index: format_record_label(table_name, records[index]),
            key=f"editor_select_{table_name}_{action}"
        )
        selected_record = records[selected_index]

    with st.form(f"{table_name}_{action.lower()}_form"):
        parsed_values = {}

        if action != "Delete":
            for column in TABLE_EDITOR_CONFIG[table_name]["columns"]:
                default_value = None if selected_record is None else selected_record.get(column["name"])
                raw_value = render_field_input(
                    table_name,
                    action.lower(),
                    column,
                    default_value=default_value,
                    disabled=action == "Update" and column["name"] in TABLE_EDITOR_CONFIG[table_name]["primary_key"]
                )
                parsed_values[column["name"]] = raw_value

        if action == "Delete":
            st.warning(TABLE_EDITOR_CONFIG[table_name]["delete_warning"])
            for column in TABLE_EDITOR_CONFIG[table_name]["columns"]:
                st.markdown(f"**{column['label']}:** {format_value(selected_record.get(column['name']))}")
            confirm_delete = st.checkbox("I understand this action cannot be undone.", key=f"confirm_{table_name}")

        submitted = st.form_submit_button(action)

    if not submitted:
        return

    if action == "Delete":
        if not confirm_delete:
            st.error("Please confirm the delete action before continuing.")
            return

        primary_key_values = {
            column_name: selected_record[column_name]
            for column_name in TABLE_EDITOR_CONFIG[table_name]["primary_key"]
        }

        write_error = delete_record(table_name, primary_key_values)
        if write_error:
            st.error(write_error)
            return

        st.success(f"Deleted record from `{table_name}`.")
        st.rerun()

    validated_values = {}
    validation_errors = []

    for column in TABLE_EDITOR_CONFIG[table_name]["columns"]:
        parsed_value, field_error = parse_field_value(column, parsed_values[column["name"]])
        if field_error:
            validation_errors.append(field_error)
        validated_values[column["name"]] = parsed_value

    if validation_errors:
        for validation_error in validation_errors:
            st.error(validation_error)
        return

    if action == "Insert":
        write_error = insert_record(table_name, validated_values)
        if write_error:
            st.error(write_error)
            return

        st.success(f"Inserted record into `{table_name}`.")
        st.rerun()

    primary_key_values = {
        column_name: selected_record[column_name]
        for column_name in TABLE_EDITOR_CONFIG[table_name]["primary_key"]
    }
    updated_values = {
        column["name"]: validated_values[column["name"]]
        for column in TABLE_EDITOR_CONFIG[table_name]["columns"]
        if column["name"] not in TABLE_EDITOR_CONFIG[table_name]["primary_key"]
    }

    write_error = update_record(table_name, primary_key_values, updated_values)
    if write_error:
        st.error(write_error)
        return

    st.success(f"Updated record in `{table_name}`.")
    st.rerun()


# ---------------- VIEW TABLE COMPONENT ----------------
def render_view_tables():
    st.header("📊 View Tables")

    tables = ["employee", "branch", "client", "works_with", "branch_supplier"]
    selected_table = st.selectbox("Select a table", tables)

    if st.button("Load Table"):
        query = f"SELECT * FROM {selected_table} LIMIT 100;"
        df, error = run_sql(query)

        if error:
            st.error(error)
        else:
            st.dataframe(df)


# ---------------- ASK QUESTIONS COMPONENT ----------------
def render_ask_questions():
    st.header("🤖 Chat with Dunder Mifflin Data")

    # ---------------- INIT ----------------
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ---------------- DISPLAY HISTORY ----------------
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])

        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                if msg.get("data") is not None:
                    st.dataframe(msg["data"])
                if msg.get("sql") or msg.get("initial_sql"):
                    with st.expander("View SQL"):
                        if msg.get("initial_sql"):
                            st.code(msg["initial_sql"], language="sql")
                            if msg.get("fixed_sql"):
                                st.warning("Query was corrected automatically ⚠️")
                                st.code(msg["fixed_sql"], language="sql")
                        else:
                            st.code(msg["sql"], language="sql")

    # ---------------- INPUT (capture only) ----------------
    user_input = st.chat_input("Ask a question about the database...")

    # ---------------- PROCESS INPUT ----------------
    if user_input:
        # Store user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = execute_with_retry(
                    user_input,
                    st.session_state.messages
                )

            if result["error"]:
                response_text = f"❌ Error: {result['error']}"
                st.error(response_text)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "data": None,
                    "sql": result["initial_query"],
                    "initial_sql": result["initial_query"],
                    "fixed_sql": result["fixed_query"]
                })

            else:
                response_text = "Here’s what I found:"
                st.markdown(response_text)
                st.dataframe(result["data"])

                with st.expander("View SQL"):
                    st.code(result["initial_query"], language="sql")

                    if result["fixed_query"]:
                        st.warning("Query was corrected automatically ⚠️")
                        st.code(result["fixed_query"], language="sql")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "data": result["data"],
                    "sql": result["fixed_query"] or result["initial_query"],
                    "initial_sql": result["initial_query"],
                    "fixed_sql": result["fixed_query"]
                })

        # 🔥 RERUN to push input to bottom
        st.rerun()
