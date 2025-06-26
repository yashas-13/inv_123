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


def _generate_product_id(name: str, qty: str, unit: str, index: int) -> str:
    """Return simple ID from name initials or fallback to sequential."""
    # WHY: sample CSV lacks IDs; generate repeatable ones for demo data
    parts = [w[0] for w in name.upper().split() if w[0].isalnum()]
    base = "".join(parts) or f"PROD{index}"
    return f"{base}{qty}{unit.upper()}"


def load_sample_products():
    """Insert products from products.csv if table is empty."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    import csv

    csv_file = Path("products.csv")
    if not csv_file.exists():
        print("products.csv not found; skipping sample load")
        conn.close()
        return

    with csv_file.open(newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            name = row.get("Product Name", "").strip()
            if not name:
                continue
            qty = row.get("Quantity", "1").strip()
            unit = row.get("measurement", "").strip() or row.get("measurement ", "").strip()
            price = row.get("Price (₹)", "0").strip()
            product_id = _generate_product_id(name, qty, unit, idx)
            try:
                cur.execute(
                    "INSERT INTO products (product_id, product_name, unit_of_measure, standard_pack_size, mrp) VALUES (?,?,?,?,?)",
                    (product_id, name, unit or "unit", float(qty), float(price or 0)),
                )
            except Exception as exc:
                print(f"Failed to insert {name}: {exc}")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    # WHY: preload example product data for easier testing (Closes: #22)
    load_sample_products()
