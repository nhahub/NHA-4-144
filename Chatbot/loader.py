import pandas as pd
import sqlite3
import os

DATA_DIR = "data"
DB_PATH = "warehouse.db"

def load_all_tables():
    """Load every CSV/Excel in data/ into SQLite. Run once at startup."""
    conn = sqlite3.connect(DB_PATH)
    for fname in os.listdir(DATA_DIR):
        fpath = os.path.join(DATA_DIR, fname)
        table_name = os.path.splitext(fname)[0]
        if fname.endswith(".csv"):
            df = pd.read_csv(fpath)
        elif fname.endswith((".xlsx", ".xls")):
            df = pd.read_excel(fpath)
        else:
            continue
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"Loaded {table_name} ({len(df)} rows)")
    conn.close()

if __name__ == "__main__":
    load_all_tables()
