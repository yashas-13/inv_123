"""Initialize database tables from schema.sql.

WHY: Guarantee all tables including new `users` table exist.
WHAT: Reads schema.sql and executes it using SQLite connection.
HOW: Run once after updates; drop DB to roll back.
Closes: #1 and #9 (user login support).
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
