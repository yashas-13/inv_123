# Arivu Foods Inventory System

Version: 0.2.0

This repository contains initial scripts to set up the inventory database and a basic FastAPI backend.

## Changes
- Added `schema.sql` extracted from documentation
- Added `database.py` for SQLAlchemy connection
- Added `init_db.py` to create tables
- Added `analyze_schema.py` for quick schema inspection
- **New:** `models.py` with ORM models
- **New:** `main.py` FastAPI app exposing `/products` endpoint
- **Updated:** `product_list.html` now loads products from API

## Quick Start
1. Install dependencies: `pip install fastapi uvicorn sqlalchemy`
2. Run `python init_db.py` to create `arivu_foods_inventory.db`.
3. Start API server: `uvicorn main:app --reload`
4. Open `product_list.html` in browser to see product list.

## API Example
Fetch products via cURL:

```bash
curl http://localhost:8000/products
```

## Project Status
Basic API running; database schema and product listing implemented.
