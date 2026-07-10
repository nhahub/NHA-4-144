import sqlite3

DB_PATH = "warehouse.db"

def get_schema_context() -> str:
    """
    Returns a detailed schema string including:
    - All table names and column names with types
    - Sample rows so the LLM understands data formats
    - Explicit JOIN relationships for the star schema
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    schema_parts = []

    for table in tables:
        # Get columns
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        col_defs = ", ".join(
            f"{col[1]} ({col[2]})" for col in columns
        )

        # Sample rows
        cursor.execute(f"SELECT * FROM {table} LIMIT 3")
        sample_rows = cursor.fetchall()

        col_names = [col[1] for col in columns]

        sample_str = "\n".join(
            "  " + ", ".join(str(v) for v in row)
            for row in sample_rows
        )

        schema_parts.append(
            f"TABLE: {table}\n"
            f"COLUMNS: {col_defs}\n"
            f"SAMPLE DATA (columns: {', '.join(col_names)}):\n"
            f"{sample_str}"
        )

    conn.close()

    relationships = """
=========================
STAR SCHEMA RELATIONSHIPS
=========================

FactSales.City_Key
    -> DimCity.City_Key

FactSales.Customer_Key
    -> DimCustomer.Customer_Key

FactSales.Stock_Item_Key
    -> DimStockItem.Stock_Item_Key

FactSales.Invoice_Date_Key
    -> DimDate.Date

FactSales.Delivery_Date_Key
    -> DimDate.Date

FactSales.Salesperson_Key
    -> DimEmployee.Employee_Key


=========================
SQL GENERATION RULES
=========================

1. Always alias tables.

Examples:
FactSales      AS fs
DimDate        AS d
DimCustomer    AS c
DimStockItem   AS s
DimCity        AS city
DimEmployee    AS e

--------------------------------------------------

2. Sales Metrics

Total Sales
SUM(fs.Total_Including_Tax)

Revenue Before Tax
SUM(fs.Total_Excluding_Tax)

Profit
SUM(fs.Profit)

Tax
SUM(fs.Tax_Amount)

Quantity Sold
SUM(fs.Quantity)

Average Order Value
AVG(fs.Total_Including_Tax)

--------------------------------------------------

3. Date Analysis

Use DimDate for:

d.Calendar_Year
d.Calendar_Month_Number
d.Calendar_Month_Label
d.Month
d.Short_Month
d.Day
d.ISO_Week_Number
d.Fiscal_Year
d.Fiscal_Month_Number

Never extract year/month directly from FactSales.

--------------------------------------------------

4. Geographic Analysis

Use DimCity columns:

City
State_Province
Country
Sales_Territory

--------------------------------------------------

5. Customer Analysis

Use DimCustomer columns:

Customer
Category
Buying_Group
Bill_To_Customer

--------------------------------------------------

6. Product Analysis

Use DimStockItem columns:

Stock_Item
Color
Selling_Package
Buying_Package
Size
Unit_Price
Recommended_Retail_Price
Is_Chiller_Stock

--------------------------------------------------

7. Employee Analysis

Use DimEmployee columns:

Employee
Preferred_Name
Is_Salesperson

--------------------------------------------------

8. Ranking

Use:

ROW_NUMBER()

RANK()

DENSE_RANK()

--------------------------------------------------

9. Running Totals

Use:

SUM(...) OVER(
ORDER BY ...
)

--------------------------------------------------

10. Moving Average

Use:

AVG(...) OVER(
ORDER BY ...
ROWS BETWEEN ...
)

--------------------------------------------------

11. Growth Analysis

Use:

LAG()

LEAD()

Month-over-Month

Year-over-Year

--------------------------------------------------

12. Aggregation

Always use GROUP BY whenever aggregates are used.

--------------------------------------------------

13. SQLite Rules

SQLite does NOT support:

RIGHT JOIN
FULL OUTER JOIN

Use LEFT JOIN instead.

--------------------------------------------------

14. Prefer Invoice_Date_Key for all sales trend analysis.

Delivery_Date_Key should only be used when analyzing delivery performance.

--------------------------------------------------

15. Preferred Fact Measures

SUM(fs.Total_Including_Tax)
SUM(fs.Total_Excluding_Tax)
SUM(fs.Profit)
SUM(fs.Quantity)
SUM(fs.Tax_Amount)

Avoid COUNT(*) unless counting records.
"""

    return "\n\n---\n\n".join(schema_parts) + "\n\n" + relationships
