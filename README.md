# Arivu Foods Inventory System

Version: 0.1.0

This repository contains initial scripts to set up the inventory database.

## Changes
- Added `schema.sql` extracted from documentation
- Added `database.py` for SQLAlchemy connection
- Added `init_db.py` to create tables
- Added `analyze_schema.py` for quick schema inspection

## Quick Start
1. Install dependencies: `pip install sqlalchemy`
2. Run `python init_db.py` to create `arivu_foods_inventory.db`.
3. Inspect tables via `python analyze_schema.py`.

## Project Status
Early setup phase: database schema creation scripts only.
