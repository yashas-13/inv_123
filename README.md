# Arivu Foods Inventory System

Version: 0.4.0

This repository contains initial scripts to set up the inventory database and a basic FastAPI backend.

## Changes
- Added `schema.sql` extracted from documentation
- Added `database.py` for SQLAlchemy connection
- Added `init_db.py` to create tables
- Added `analyze_schema.py` for quick schema inspection
- **New:** `models.py` with ORM models
- **New:** `main.py` FastAPI app exposing `/products` endpoint
- **Updated:** `product_list.html` now loads products from API
- **New:** `POST /products` API to add products and frontend form
- **New:** `/batches`, `/stock-movements`, `/expiring-stock` API endpoints
- **Updated:** Dashboards and product list now use these endpoints

## Quick Start
1. Install dependencies: `pip install fastapi uvicorn sqlalchemy`
2. Run `python init_db.py` to (re)create `arivu_foods_inventory.db` with all tables.
3. Start API server: `uvicorn main:app --reload`
4. Open `product_list.html` in browser to see product list.

## API Example
Fetch products via cURL:

```bash
curl http://localhost:8000/products
```

Fetch batches via cURL:

```bash
curl http://localhost:8000/batches
```

Create a stock movement via cURL:

```bash
curl -X POST http://localhost:8000/stock-movements \
     -H 'Content-Type: application/json' \
     -d '{"movement_id":"MOVE1","product_id":"AFCMA1KG","batch_id":"B1","movement_type":"dispatch","quantity":10}'
```

Create a new product via cURL:

```bash
curl -X POST http://localhost:8000/products \
     -H 'Content-Type: application/json' \
     -d '{"product_id":"NEW1","product_name":"Sample","unit_of_measure":"kg","standard_pack_size":1,"mrp":100}'
```

## Project Status
Version 0.4.0 extends the API with batch tracking, stock movements, and expirying-stock reporting. Frontend pages now display batch data and show expiring counts.
