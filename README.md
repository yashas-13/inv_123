# Arivu Foods Inventory System

Version: 0.5.3

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
- **New:** service layer (`services.py`) with aggregation logic
- **New:** dashboard endpoints `/dashboard/arivu` and `/dashboard/store/{id}`
- **New:** environment variable `DATABASE_URL` controls database connection
- **New:** `/dashboard/recent-sales` API returning latest partner sales
- **Updated:** Arivu dashboard now displays recent sales table
- **New:** Simple API key authentication using `X-API-Key` header (`API_KEY` env var)
- **New:** `users` table added to schema and init scripts
- **New:** `/register` and `/login` API endpoints with `login.html` and `register.html`
- **Updated:** store dashboard auto-loads when `store_id` query parameter is present

## Quick Start
1. Install dependencies: `pip install fastapi uvicorn sqlalchemy`
2. Run `python init_db.py` to (re)create `arivu_foods_inventory.db` with all tables.
3. Set `API_KEY` environment variable (default `changeme`) and start server: `uvicorn main:app --reload` (set `DATABASE_URL` as needed)
4. Open `login.html` in your browser to sign in (or register first).

## API Example
Fetch products via cURL:

```bash
curl -H 'X-API-Key: <API_KEY>' http://localhost:8000/products
```

Fetch batches via cURL:

```bash
curl -H 'X-API-Key: <API_KEY>' http://localhost:8000/batches
```

Create a stock movement via cURL:

```bash
curl -X POST http://localhost:8000/stock-movements \
     -H 'Content-Type: application/json' \
     -H 'X-API-Key: <API_KEY>' \
     -d '{"movement_id":"MOVE1","product_id":"AFCMA1KG","batch_id":"B1","movement_type":"dispatch","quantity":10}'
```

Create a new product via cURL:

```bash
curl -X POST http://localhost:8000/products \
     -H 'Content-Type: application/json' \
     -H 'X-API-Key: <API_KEY>' \
     -d '{"product_id":"NEW1","product_name":"Sample","unit_of_measure":"kg","standard_pack_size":1,"mrp":100}'
```

Register a new user via cURL:

```bash
curl -X POST http://localhost:8000/register \
     -H 'Content-Type: application/json' \
     -d '{"username":"admin","password":"secret","role":"arivu"}'
```

Login via cURL:

```bash
curl -X POST http://localhost:8000/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"admin","password":"secret"}'
```

Fetch dashboard summary via cURL:

```bash
curl -H 'X-API-Key: <API_KEY>' http://localhost:8000/dashboard/arivu
```

Fetch locations via cURL:

```bash
curl -H 'X-API-Key: <API_KEY>' http://localhost:8000/locations
```

Fetch recent sales via cURL:

```bash
curl -H 'X-API-Key: <API_KEY>' http://localhost:8000/dashboard/recent-sales
```

## Project Status
Version 0.5.3 adds user accounts with login and registration pages. Run `python init_db.py` after pulling to create the new users table.
