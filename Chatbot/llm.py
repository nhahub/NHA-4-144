import os
import re

from google import genai
from google.genai import types

client = genai.Client(
    api_key="YOUR_API_KEY"
)

MODEL_NAME = "YOUR_MODEL"


def clean_sql(sql: str) -> str:
    """
    Remove markdown and extra text that Gemini sometimes returns.
    """

    sql = sql.strip()

    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")

    sql = re.sub(
        r"^Here('?s| is)?\s+(the\s+)?SQL\s+(query)?\s*:\s*",
        "",
        sql,
        flags=re.IGNORECASE,
    )

    sql = sql.strip()

    return sql


def build_history(chat_history: list) -> str:
    """
    Convert previous conversation into context.
    """

    if not chat_history:
        return "No previous conversation."

    history = []

    for turn in chat_history[-8:]:
        history.append(
            f"""
User Question:
{turn.get("question","")}

SQL:
{turn.get("sql","")}

Answer:
{turn.get("answer","")}
"""
        )

    return "\n".join(history)


def generate_sql(schema_context: str,
                 user_question: str,
                 chat_history: list) -> str:

    history = build_history(chat_history)

    prompt = f"""
You are a senior SQLite data analyst.

Generate ONE valid SQLite SQL query.

Rules:

- Return ONLY SQL.
- Never explain.
- Never use markdown.
- Never invent columns.
- Never invent tables.
- Use only the provided schema.
- Use SQLite syntax only.
- If impossible return CANNOT_ANSWER.

DATABASE SCHEMA

{schema_context}

----------------------------------------

CONVERSATION HISTORY

{history}

----------------------------------------

CURRENT QUESTION

{user_question}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            top_p=0.95,
            max_output_tokens=1024,
        ),
    )

    return clean_sql(response.text)


def generate_answer(question: str,
                    sql: str,
                    result_df) -> str:

    if result_df.empty:
        result = "No rows returned."

    elif len(result_df) > 30:
        result = result_df.head(30).to_string(index=False)
        result += "\n\n(Result truncated to first 30 rows.)"

    else:
        result = result_df.to_string(index=False)

    prompt = f"""
You are a professional business analyst.

Answer the user's question using the query result.

Rules:

- Never mention SQL.
- Never mention databases.
- Keep the answer under four sentences.

Original Question

{question}

--------------------------------

Query Result

{result}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.95,
            max_output_tokens=512,
        ),
    )

    return response.text.strip()
