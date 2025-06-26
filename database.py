"""Database connection setup.

WHY: Provide a simple SQLite connection using SQLAlchemy.
WHAT: sets up engine, session, and Base classes.
HOW: modify DATABASE_URL or extend with env vars to change DB later.
Closes: #1 (initial db setup).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# WHY: allow DB path configuration via environment variable for deployment
# WHAT: reads DATABASE_URL from os.environ, defaulting to local SQLite file
# HOW: set DATABASE_URL env var to new connection string to extend; remove env var usage to roll back
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./arivu_foods_inventory.db")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
