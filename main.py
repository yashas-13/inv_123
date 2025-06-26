"""FastAPI app exposing inventory endpoints.

WHY: Provide backend API to access DB data.
WHAT: Adds /products endpoint for listing products.
HOW: Extend by adding CRUD routes; rollback by removing this file.
Closes: #2.
"""

from fastapi import FastAPI, Depends, HTTPException
from auth import verify_api_key  # ensure only authorized clients call the API
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
    create_user,
    get_user_by_username,
)

from database import get_db, Base, engine
from models import Product, Batch, StockMovement, Location, User
from datetime import date, timedelta

# Create tables if not already present (initial migration)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Arivu Foods Inventory API")
# Individual routes use verify_api_key dependency to allow open login/register
auth_dep = Depends(verify_api_key)


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
    return {"message": "Movement recorded", "movement_id": db_move.movement_id}


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
    return {
        "current_stock": get_store_current_stock(db, store_id),
        "sales_today": get_store_sales_today(db, store_id),
    }


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


@app.get("/locations", dependencies=[auth_dep])
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
