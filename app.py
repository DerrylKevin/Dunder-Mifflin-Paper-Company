import streamlit as st

from ui.components import render_ask_questions, render_editor, render_view_tables

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Dunder Mifflin Portal",
    layout="centered"
)

st.title("📄 Dunder Mifflin Data Portal")

# ---------------- SIDEBAR ----------------
tab1, tab2, tab3 = st.tabs(["📊 Tables", "🤖 AI Queries", "🛠️ Editor"])

with tab1:
    render_view_tables()

with tab2:
    render_ask_questions()

with tab3:
    render_editor()
