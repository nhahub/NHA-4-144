import sqlite3
import pandas as pd
import sqlglot

DB_PATH = "warehouse.db"

FORBIDDEN_KEYWORDS = {
    "DROP",
    "DELETE",
    "INSERT",
    "UPDATE",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "REPLACE",
    "ATTACH",
    "DETACH",
    "VACUUM",
    "PRAGMA",
}

MAX_RETURNED_ROWS = 1000


def is_safe_sql(sql: str) -> tuple[bool, str]:
    """
    Allow ONLY a single SELECT statement.
    """

    sql = sql.strip()

    if not sql:
        return False, "Empty SQL query."

    upper = sql.upper()

    # Only SELECT queries
    if not upper.startswith("SELECT"):
        return False, "Only SELECT statements are allowed."

    # Block dangerous keywords
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in upper:
            return False, f"Forbidden keyword detected: {keyword}"

    # Prevent multiple statements
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    if len(statements) > 1:
        return False, "Multiple SQL statements are not allowed."

    return True, ""


def validate_sql_syntax(sql: str) -> tuple[bool, str]:
    """
    Validate SQL using sqlglot.
    """

    try:
        sqlglot.parse_one(sql, dialect="sqlite")
        return True, ""
    except Exception as e:
        return False, str(e)


def execute_query(sql: str) -> tuple[pd.DataFrame | None, str | None]:
    """
    Execute a validated SELECT query.

    Returns:
        (DataFrame, None) on success
        (None, error_message) on failure
    """

    safe, message = is_safe_sql(sql)
    if not safe:
        return None, message

    valid, syntax_error = validate_sql_syntax(sql)
    if not valid:
        return None, f"SQL syntax error: {syntax_error}"

    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(sql, conn)

        # Prevent extremely large responses
        if len(df) > MAX_RETURNED_ROWS:
            df = df.head(MAX_RETURNED_ROWS)

        return df, None

    except sqlite3.Error as e:
        return None, f"SQLite Error: {e}"

    except Exception as e:
        return None, str(e)
