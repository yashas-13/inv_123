"""FastAPI app exposing inventory endpoints.

WHY: Provide backend API to access DB data.
WHAT: Adds /products endpoint for listing products.
HOW: Extend by adding CRUD routes; rollback by removing this file.
Closes: #2.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from auth import verify_basic_auth  # ensure only authorized clients call the API
from sqlalchemy.orm import Session
from pydantic import BaseModel
import hashlib

from services import (
    get_all_products,
    create_product as svc_create_product,
    get_all_batches,
    create_batch as svc_create_batch,
    get_all_movements,
    create_movement as svc_create_movement,
    get_total_products_count,
    get_total_warehouse_stock,
    get_total_retail_stock,
    get_expiring_units_count,
    get_recent_movements,
    get_recent_sales,
    get_store_current_stock,
    get_store_sales_today,
    add_new_batch_to_inventory,
    dispatch_stock,
    create_retail_sale,
    get_store_current_stock_summary,
    get_store_upcoming_deliveries,
    get_all_retail_partners,
    create_retail_partner,
    create_user,
    get_user_by_username,
)

from database import get_db, Base, engine
from models import Product, Batch, StockMovement, Location, RetailPartner, User
from datetime import date, timedelta

# Create tables if not already present (initial migration)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Arivu Foods Inventory API")
# Serve frontend HTML from /ui and show login page at root
app.mount("/ui", StaticFiles(directory="."), name="ui")

@app.get("/", response_class=HTMLResponse)
def serve_login():
    """Return login page so users can authenticate via browser."""
    return FileResponse("login.html")
# Individual routes use HTTP Basic auth dependency so endpoints require login
auth_dep = Depends(verify_basic_auth)


class ProductCreate(BaseModel):
    """Schema for creating a product."""
    product_id: str
    product_name: str
    unit_of_measure: str
    standard_pack_size: float
    mrp: float | None = None


class BatchCreate(BaseModel):
    """Schema for creating batches."""
    # WHY: validate incoming batch data for POST /batches
    batch_id: str
    product_id: str
    date_manufactured: date
    quantity_produced: int
    expiry_date: date | None = None
    remarks: str | None = None


class StockMovementCreate(BaseModel):
    """Schema for recording stock movement."""
    movement_id: str
    product_id: str
    batch_id: str
    movement_type: str
    source_location_id: str | None = None
    destination_location_id: str | None = None
    quantity: int
    agent_id: str | None = None
    remarks: str | None = None


class RetailSaleCreate(BaseModel):
    """Schema for recording a retail sale."""
    sale_id: str
    sale_date: date
    store_id: str
    product_id: str
    batch_id: str | None = None
    quantity_sold: int
    sales_agent_id: str | None = None
    sale_price_per_unit: float | None = None
    remarks: str | None = None


class RetailPartnerCreate(BaseModel):
    """Schema to register a retail partner."""
    store_id: str
    location_id: str
    store_name: str
    contact_person: str | None = None
    contact_number: str | None = None
    email: str | None = None


class UserCreate(BaseModel):
    """Signup schema."""
    # WHY: allow front-end registration of users (Closes: #9)
    username: str
    password: str
    role: str
    store_id: str | None = None


class UserLogin(BaseModel):
    """Login schema."""
    username: str
    password: str


@app.post("/register", status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Create a user account."""
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = hashlib.sha256(user.password.encode()).hexdigest()
    db_user = create_user(db, {**user.dict(exclude={'password'}), 'password': hashed})
    return {"message": "User registered", "id": db_user.id}


@app.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Verify credentials and return role info."""
    user = get_user_by_username(db, credentials.username)
    hashed = hashlib.sha256(credentials.password.encode()).hexdigest()
    if not user or user.password != hashed:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"role": user.role, "store_id": user.store_id}

@app.get("/products", dependencies=[auth_dep])
def list_products(db: Session = Depends(get_db)):
    """Return all products."""
    products = get_all_products(db)
    return [
        {
            "product_id": p.product_id,
            "product_name": p.product_name,
            "unit_of_measure": p.unit_of_measure,
            "standard_pack_size": float(p.standard_pack_size),
            "mrp": float(p.mrp) if p.mrp else None,
        }
        for p in products
    ]


@app.post("/products", status_code=201, dependencies=[auth_dep])
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product in the database."""
    # WHY: allow backend to manage DB by inserting products (Closes: #3)
    # WHAT: adds POST /products route for creating new products
    # HOW: check for existing ID then insert; rollback by removing this func
    existing = db.get(Product, product.product_id)
    if existing:
        raise HTTPException(status_code=400, detail="Product ID already exists")
    db_product = svc_create_product(db, product.dict())
    return {"message": "Product created", "product_id": db_product.product_id}


@app.get("/batches", dependencies=[auth_dep])
def list_batches(db: Session = Depends(get_db)):
    """Return all batches."""
    # WHY: list production batches for inventory tracking (Closes: #4)
    batches = get_all_batches(db)
    return [
        {
            "batch_id": b.batch_id,
            "product_id": b.product_id,
            "date_manufactured": b.date_manufactured.isoformat(),
            "quantity_produced": b.quantity_produced,
            "expiry_date": b.expiry_date.isoformat() if b.expiry_date else None,
            "remarks": b.remarks,
        }
        for b in batches
    ]


@app.post("/batches", status_code=201, dependencies=[auth_dep])
def create_batch(batch: BatchCreate, db: Session = Depends(get_db)):
    """Create a new batch."""
    existing = db.get(Batch, batch.batch_id)
    if existing:
        raise HTTPException(status_code=400, detail="Batch ID already exists")
    db_batch = svc_create_batch(db, batch.dict())
    # WHY: update warehouse inventory when a batch is produced
    add_new_batch_to_inventory(db, db_batch)
    return {"message": "Batch created", "batch_id": db_batch.batch_id}


@app.get("/stock-movements", dependencies=[auth_dep])
def list_movements(db: Session = Depends(get_db)):
    """Return all stock movements."""
    movements = get_all_movements(db)
    return [
        {
            "movement_id": m.movement_id,
            "product_id": m.product_id,
            "batch_id": m.batch_id,
            "movement_date": m.movement_date.isoformat() if m.movement_date else None,
            "movement_type": m.movement_type,
            "source_location_id": m.source_location_id,
            "destination_location_id": m.destination_location_id,
            "quantity": m.quantity,
            "agent_id": m.agent_id,
            "remarks": m.remarks,
        }
        for m in movements
    ]


@app.post("/stock-movements", status_code=201, dependencies=[auth_dep])
def create_movement(movement: StockMovementCreate, db: Session = Depends(get_db)):
    """Record a stock movement."""
    existing = db.get(StockMovement, movement.movement_id)
    if existing:
        raise HTTPException(status_code=400, detail="Movement ID already exists")
    db_move = svc_create_movement(db, {**movement.dict(), "movement_date": date.today()})
    # WHY: adjust CurrentStock on dispatch or receipt
    dispatch_stock(db, db_move)
    return {"message": "Movement recorded", "movement_id": db_move.movement_id}


@app.post("/retail-sales", status_code=201, dependencies=[auth_dep])
def record_retail_sale(sale: RetailSaleCreate, db: Session = Depends(get_db)):
    """Record sale at a retail partner and adjust stock."""
    db_sale = create_retail_sale(db, sale.dict())
    return {"message": "Sale recorded", "sale_id": db_sale.sale_id}


@app.get("/expiring-stock", dependencies=[auth_dep])
def get_expiring_stock(days: int = 30, db: Session = Depends(get_db)):
    """Return batches expiring within given days."""
    cutoff = date.today() + timedelta(days=days)
    batches = db.query(Batch).filter(Batch.expiry_date != None, Batch.expiry_date <= cutoff).all()
    return [
        {
            "batch_id": b.batch_id,
            "product_id": b.product_id,
            "expiry_date": b.expiry_date.isoformat() if b.expiry_date else None,
        }
        for b in batches
    ]


# --- Dashboard endpoints ---

@app.get("/dashboard/arivu", dependencies=[auth_dep])
def arivu_dashboard(db: Session = Depends(get_db)):
    """Aggregate metrics for manufacturer dashboard."""
    return {
        "total_products": get_total_products_count(db),
        "warehouse_stock": get_total_warehouse_stock(db),
        "retail_stock": get_total_retail_stock(db),
        "expiring_soon": get_expiring_units_count(db, 60),
        "recent_movements": [
            {
                "movement_id": m.movement_id,
                "product_id": m.product_id,
                "quantity": m.quantity,
                "movement_date": m.movement_date.isoformat() if m.movement_date else None,
            }
            for m in get_recent_movements(db)
        ],
    }


@app.get("/dashboard/store/{store_id}", dependencies=[auth_dep])
def store_dashboard(store_id: str, db: Session = Depends(get_db)):
    """Return stock and sales info for a retail partner."""
    partner = db.get(RetailPartner, store_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Store not found")
    return {
        "current_stock": get_store_current_stock(db, store_id),
        "sales_today": get_store_sales_today(db, store_id),
    }


@app.get("/dashboard/store/{store_id}/stock", dependencies=[auth_dep])
def store_stock_details(store_id: str, db: Session = Depends(get_db)):
    """Detailed stock table for a store."""
    partner = db.get(RetailPartner, store_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Store not found")
    records = get_store_current_stock_summary(db, store_id)
    return [
        {
            "product_id": r.product_id,
            "batch_id": r.batch_id,
            "quantity": r.quantity,
        }
        for r in records
    ]


@app.get("/dashboard/store/{store_id}/deliveries", dependencies=[auth_dep])
def store_upcoming_deliveries(store_id: str, db: Session = Depends(get_db)):
    """Upcoming dispatches destined for the store."""
    partner = db.get(RetailPartner, store_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Store not found")
    deliveries = get_store_upcoming_deliveries(db, store_id)
    return [
        {
            "movement_id": d.movement_id,
            "product_id": d.product_id,
            "quantity": d.quantity,
            "movement_date": d.movement_date.isoformat() if d.movement_date else None,
        }
        for d in deliveries
    ]


@app.get("/dashboard/recent-sales", dependencies=[auth_dep])
def recent_sales(limit: int = 5, db: Session = Depends(get_db)):
    """Return recent retail sales for overview."""
    # WHY: show latest sales data on dashboards (Closes: #7)
    sales = get_recent_sales(db, limit)
    return [
        {
            "sale_id": s.sale_id,
            "store_id": s.store_id,
            "product_id": s.product_id,
            "quantity_sold": s.quantity_sold,
            "sale_date": s.sale_date.isoformat() if s.sale_date else None,
        }
        for s in sales
    ]


@app.get("/locations")
def list_locations(db: Session = Depends(get_db)):
    """List all locations."""
    locations = db.query(Location).all()
    return [
        {
            "location_id": l.location_id,
            "location_name": l.location_name,
            "location_type": l.location_type,
        }
        for l in locations
    ]


@app.get("/retail-partners", dependencies=[auth_dep])
def list_retail_partners(db: Session = Depends(get_db)):
    """Return all retail partners."""
    partners = get_all_retail_partners(db)
    return [
        {
            "store_id": p.store_id,
            "location_id": p.location_id,
            "store_name": p.store_name,
        }
        for p in partners
    ]


@app.post("/retail-partners", status_code=201, dependencies=[auth_dep])
def create_retail_partner_endpoint(partner: RetailPartnerCreate, db: Session = Depends(get_db)):
    """Create a new retail partner."""
    if db.get(RetailPartner, partner.store_id):
        raise HTTPException(status_code=400, detail="Store ID already exists")
    db_partner = create_retail_partner(db, partner.dict())
    return {"message": "Retail partner created", "store_id": db_partner.store_id}


if __name__ == "__main__":
    """Run the dev server and auto-open the login page."""
    import webbrowser
    webbrowser.open("http://127.0.0.1:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
