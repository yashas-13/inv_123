"""Initialize database tables from schema.sql.

WHY: Create all tables for initial setup using raw SQL.
WHAT: Reads schema.sql and executes it using SQLite connection.
HOW: Use for initial deployments; roll back by dropping DB file.
Closes: #1.
"""

import sqlite3
from pathlib import Path

SCHEMA_FILE = Path(__file__).parent / "schema.sql"
DB_FILE = Path("arivu_foods_inventory.db")


def create_tables():
    sql = SCHEMA_FILE.read_text()
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.executescript(sql)
        conn.commit()
        print("Tables created successfully")
    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()
