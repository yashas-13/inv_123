# Arivu Foods Inventory System

Version: 0.7.8

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
- **Changed:** Authentication now uses HTTP Basic credentials stored in `users` table
- **New:** Login page served at `/` via FastAPI
- **New:** `users` table added to schema and init scripts
- **New:** `/register` and `/login` API endpoints with `login.html` and `register.html`
- **Updated:** store dashboard auto-loads when `store_id` query parameter is present
- **New:** current stock now updates automatically when batches are created or dispatched
- **New:** `/retail-sales` endpoint records store sales and adjusts stock
- **New:** detailed store dashboard endpoints `/dashboard/store/{id}/stock` and `/dashboard/store/{id}/deliveries`
- **New:** `/retail-partners` API for listing and creating partners
- **New:** `/store-partner-accounts` API creates partner record and login user
- **Changed:** HTML pages load API key from `localStorage`
- **Removed:** legacy `sqlscema.md` file
- **New:** Static routes serve HTML pages (`register.html`, `arivu_Dashboard.html`,
  etc.) directly from root to fix 404s after login
- **New:** `/warehouse-stock` endpoint lists main warehouse inventory and dashboard form allows adding batches
- **New:** "Create Batch" modal on Arivu dashboard for quick batch entry
- **New:** `/login.html` route serves the login page alongside root
- **New:** Dispatch form on Arivu dashboard posts to `/stock-movements`
- **New:** `init_db.py` now loads sample products from `products.csv`
- **New:** `products.html` embedded in `arivu_Dashboard.html` showing product table
- **Changed:** Batches now support multiple products via new `batch_products` table and auto-calculate expiry 90 days from manufacturing

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Run `python init_db.py` to (re)create `arivu_foods_inventory.db` with all tables.
3. Start the server: `uvicorn main:app --reload` (set `DATABASE_URL` as needed)
4. Visit `http://localhost:8000/` to access the login page. Credentials will be used for HTTP Basic auth on API requests.

## API Example
Fetch products via cURL:

```bash
curl -u <user>:<pass> http://localhost:8000/products
```

Fetch batches via cURL:

```bash
curl -u <user>:<pass> http://localhost:8000/batches
```

Create a stock movement via cURL:

```bash
curl -X POST http://localhost:8000/stock-movements \
     -H 'Content-Type: application/json' \
     -u <user>:<pass> \
     -d '{"movement_id":"MOVE1","product_id":"AFCMA1KG","batch_id":"B1","movement_type":"dispatch","quantity":10}'
```

Dispatch stock to a store via cURL:

```bash
curl -X POST http://localhost:8000/stock-movements \
     -H 'Content-Type: application/json' \
     -u <user>:<pass> \
     -d '{"movement_id":"MOVE2","product_id":"AFCMA1KG","batch_id":"B1","movement_type":"dispatch","source_location_id":"MAIN_WH","destination_location_id":"LOC1","quantity":5}'
```

Create a new product via cURL:

```bash
curl -X POST http://localhost:8000/products \
     -H 'Content-Type: application/json' \
     -u <user>:<pass> \
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
curl -u <user>:<pass> http://localhost:8000/dashboard/arivu
```

Fetch locations via cURL:

```bash
curl http://localhost:8000/locations
```

Fetch recent sales via cURL:

```bash
curl -u <user>:<pass> http://localhost:8000/dashboard/recent-sales
```

Record a sale via cURL:

```bash
curl -X POST http://localhost:8000/retail-sales \
     -H 'Content-Type: application/json' \
     -u <user>:<pass> \
     -d '{"sale_id":"S1","sale_date":"2024-01-01","store_id":"STORE1","product_id":"AFCMA1KG","quantity_sold":5}'
```

Fetch store stock via cURL:

```bash
curl -u <user>:<pass> http://localhost:8000/dashboard/store/STORE1/stock
```

Fetch upcoming deliveries via cURL:

```bash
curl -u <user>:<pass> http://localhost:8000/dashboard/store/STORE1/deliveries
```

Fetch retail partners via cURL:

```bash
curl -u <user>:<pass> http://localhost:8000/retail-partners
```

Create a batch via cURL:

```bash
curl -X POST http://localhost:8000/batches \
     -H 'Content-Type: application/json' \
     -u <user>:<pass> \
     -d '{"batch_id":"B1","date_manufactured":"2024-01-01","items":[{"product_id":"AFCMA1KG","quantity_produced":50},{"product_id":"AFDMIX","quantity_produced":50}]}'
```

Fetch warehouse stock via cURL:

```bash
curl -u <user>:<pass> http://localhost:8000/warehouse-stock
```

Create a store partner account via cURL:

```bash
curl -X POST http://localhost:8000/store-partner-accounts \
     -H 'Content-Type: application/json' \
     -u <user>:<pass> \
     -d '{"store_id":"NEWSTORE","location_id":"LOC1","store_name":"Test Store","username":"storeuser","password":"secret"}'
```

Fetch the registration page via cURL (no auth required):

```bash
curl http://localhost:8000/register.html
```

Fetch the login page via cURL (no auth required):

```bash
curl http://localhost:8000/login.html
```

Fetch the Arivu dashboard HTML via cURL (after login):

```bash
curl -u <user>:<pass> http://localhost:8000/arivu_Dashboard.html
```

Fetch the product list page via cURL:

```bash
curl http://localhost:8000/products.html
```

## Project Status
Version 0.7.8 introduces `batch_products` for recording multiple products per batch. Expiry dates are now auto-set 90 days from manufacturing if omitted. Run `python init_db.py` after pulling to recreate the database, then `uvicorn main:app --reload`.
