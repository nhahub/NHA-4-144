import streamlit as st
import pandas as pd
from loader import load_all_tables
from schema_builder import get_schema_context
from llm import generate_sql, generate_answer
from sql_executor import execute_query
import os

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Chatbot",
    page_icon="📊",
    layout="wide"
)

# ── One-time setup ────────────────────────────────────────────────────────────
@st.cache_resource
def setup():
    """Load data and build schema context once."""
    load_all_tables()
    schema = get_schema_context()
    return schema

schema_context = setup()

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []   # [{role, content}]  for display
if "history" not in st.session_state:
    st.session_state.history = []    # [{question, sql}]  for LLM context

# ── UI ─────────────────────────────────────────────────────────────────────────
st.title("📊 Data Chatbot")
st.caption("Ask questions about your data in plain English.")

# Sidebar — show schema info
with st.sidebar:
    st.header("Schema info")
    st.text(schema_context[:2000] + "...")  # preview
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(msg["answer"])
            if msg.get("sql"):
                with st.expander("SQL query used"):
                    st.code(msg["sql"], language="sql")
            if msg.get("dataframe") is not None:
                st.dataframe(msg["dataframe"], use_container_width=True)
        else:
            st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
if question := st.chat_input("E.g. Which countries generate the most profit?"):

    # Show user message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            # 1. Generate SQL
            sql = generate_sql(schema_context, question, st.session_state.history)

            if sql == "CANNOT_ANSWER":
                answer = "I couldn't find the data needed to answer that question based on your schema."
                st.markdown(answer)
                st.session_state.messages.append({
                    "role": "assistant", "answer": answer, "sql": None, "dataframe": None
                })
            else:
                # 2. Execute SQL (with auto-retry on error)
                df, error = execute_query(sql)

                if error:
                    # Retry: send error back to Gemini for self-correction
                    retry_question = (
                        f"The SQL you generated caused this error: {error}\n"
                        f"Original question: {question}\n"
                        f"Fix the SQL query."
                    )
                    sql = generate_sql(schema_context, retry_question, st.session_state.history)
                    df, error = execute_query(sql)

                if error:
                    answer = f"I ran into a problem executing the query: `{error}`"
                    st.markdown(answer)
                    st.code(sql, language="sql")
                else:
                    # 3. Generate natural language answer
                    answer = generate_answer(question, sql, df)
                    st.markdown(answer)
                    with st.expander("SQL query used"):
                        st.code(sql, language="sql")
                    st.dataframe(df, use_container_width=True)

                    # Update history for multi-turn context
                    st.session_state.history.append({"question": question, "sql": sql})

                    st.session_state.messages.append({
                        "role": "assistant",
                        "answer": answer,
                        "sql": sql,
                        "dataframe": df
                    })
