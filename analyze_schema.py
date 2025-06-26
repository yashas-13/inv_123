"""Simple analyzer for schema.sql to list tables and columns.

WHY: provide quick insight into schema structure for developers.
WHAT: Parses schema.sql for CREATE TABLE blocks.
HOW: run `python analyze_schema.py` after updates to verify tables.
"""

import re
from pathlib import Path

SCHEMA_FILE = Path(__file__).parent / "schema.sql"

create_re = re.compile(r"CREATE TABLE (\w+) \(")
column_re = re.compile(r"\s*(\w+) [A-Z]+")


def analyze():
    tables = {}
    lines = SCHEMA_FILE.read_text().splitlines()
    current = None
    for line in lines:
        m = create_re.match(line)
        if m:
            current = m.group(1)
            tables[current] = []
            continue
        if current and line.startswith("    "):
            col = column_re.match(line)
            if col:
                tables[current].append(col.group(1))
        elif line.startswith(");"):
            current = None
    for tbl, cols in tables.items():
        print(f"{tbl}: {', '.join(cols)}")


if __name__ == "__main__":
    analyze()
