"""FastAPI app exposing inventory endpoints and utilities.

WHY: Provide backend API to access DB data in a single self-contained module.
WHAT: Consolidates previous multi-file backend into `main.py` with optional CLI commands.
HOW: Import this module and run with uvicorn or `python main.py <command>`.
Closes: #2 and #32.
"""

from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn

import os
import sqlite3
import hashlib
import secrets
import re
from pathlib import Path
from datetime import date, timedelta

from sqlalchemy import (
    create_engine,
    func,
    and_,
    Column,
    String,
    DECIMAL,
    Date,
    Integer,
    ForeignKey,
    TIMESTAMP,
)
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from pydantic import BaseModel

# --- Database setup ---
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


# --- ORM models ---
class Product(Base):
    __tablename__ = "products"
    product_id = Column(String(50), primary_key=True)
    product_name = Column(String(255), nullable=False)
    unit_of_measure = Column(String(50), nullable=False)
    standard_pack_size = Column(DECIMAL(10, 2), nullable=False)
    mrp = Column(DECIMAL(10, 2))


class Location(Base):
    __tablename__ = "locations"
    location_id = Column(String(50), primary_key=True)
    location_name = Column(String(255), nullable=False)
    location_type = Column(String(50), nullable=False)
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(100))
    zip_code = Column(String(20))
    country = Column(String(100), default="India")


class Batch(Base):
    """Batch metadata shared by contained products."""

    __tablename__ = "batches"
    batch_id = Column(String(50), primary_key=True)
    date_manufactured = Column(Date, nullable=False)
    expiry_date = Column(Date)
    remarks = Column(String)


class BatchProduct(Base):
    """Association of products and quantities for each batch."""

    __tablename__ = "batch_products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(50), ForeignKey("batches.batch_id"), nullable=False)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)
    quantity_produced = Column(Integer, nullable=False)


class StockMovement(Base):
    """Log of product movements between locations."""

    __tablename__ = "stock_movements"
    movement_id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)
    batch_id = Column(String(50), ForeignKey("batches.batch_id"), nullable=False)
    movement_date = Column(TIMESTAMP)
    movement_type = Column(String(50), nullable=False)
    source_location_id = Column(String(50), ForeignKey("locations.location_id"))
    destination_location_id = Column(String(50), ForeignKey("locations.location_id"))
    quantity = Column(Integer, nullable=False)
    agent_id = Column(String(50), ForeignKey("agents.agent_id"))
    remarks = Column(String)


class RetailPartner(Base):
    """Retail stores carrying products."""

    __tablename__ = "retail_partners"
    store_id = Column(String(50), primary_key=True)
    location_id = Column(
        String(50), ForeignKey("locations.location_id"), nullable=False
    )
    store_name = Column(String(255), nullable=False)
    contact_person = Column(String(255))
    contact_number = Column(String(50))
    email = Column(String(255))


class Agent(Base):
    """Sales/dispatch agents."""

    __tablename__ = "agents"
    agent_id = Column(String(50), primary_key=True)
    agent_name = Column(String(255), nullable=False)
    contact_number = Column(String(50))
    email = Column(String(255))


class CurrentStock(Base):
    """Current quantity of each batch at each location."""

    __tablename__ = "current_stock"
    stock_id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)
    batch_id = Column(String(50), ForeignKey("batches.batch_id"), nullable=False)
    location_id = Column(
        String(50), ForeignKey("locations.location_id"), nullable=False
    )
    quantity = Column(Integer, nullable=False)
    last_updated = Column(TIMESTAMP)


class RetailSale(Base):
    """Sales recorded at partner stores."""

    __tablename__ = "retail_sales"
    sale_id = Column(String(50), primary_key=True)
    sale_date = Column(Date, nullable=False)
    store_id = Column(
        String(50), ForeignKey("retail_partners.store_id"), nullable=False
    )
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)
    batch_id = Column(String(50), ForeignKey("batches.batch_id"))
    quantity_sold = Column(Integer, nullable=False)
    sales_agent_id = Column(String(50), ForeignKey("agents.agent_id"))
    sale_price_per_unit = Column(DECIMAL(10, 2))
    remarks = Column(String)


class User(Base):
    """Application user accounts."""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    store_id = Column(String(50), ForeignKey("locations.location_id"))


# Create tables if not already present (initial migration)
Base.metadata.create_all(bind=engine)


# --- Authentication helpers ---
API_KEY = os.getenv("API_KEY", "changeme")
security = HTTPBasic()


def verify_api_key(x_api_key: str = Header(...)):
    """Compare provided key with environment API_KEY."""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )


def verify_basic_auth(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Validate username/password against users table."""
    user = db.query(User).filter(User.username == credentials.username).first()
    hashed = hashlib.sha256(credentials.password.encode()).hexdigest()
    if not user or not secrets.compare_digest(user.password, hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return user


# --- Service layer functions ---
def get_all_products(db: Session):
    return db.query(Product).all()


def create_product(db: Session, data: dict) -> Product:
    product = Product(**data)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_all_batches(db: Session):
    """Return batches with their associated product items."""
    batches = db.query(Batch).all()
    result = []
    for b in batches:
        items = db.query(BatchProduct).filter(BatchProduct.batch_id == b.batch_id).all()
        result.append((b, items))
    return result


def create_batch(db: Session, data: dict, items: list[dict]) -> Batch:
    """Insert a batch and its product items."""
    batch = Batch(**data)
    db.add(batch)
    for itm in items:
        bp = BatchProduct(
            batch_id=batch.batch_id,
            product_id=itm["product_id"],
            quantity_produced=itm["quantity_produced"],
        )
        db.add(bp)
    db.commit()
    db.refresh(batch)
    return batch


def get_all_movements(db: Session):
    return db.query(StockMovement).all()


def create_movement(db: Session, data: dict) -> StockMovement:
    move = StockMovement(**data)
    db.add(move)
    db.commit()
    db.refresh(move)
    return move


def get_total_products_count(db: Session) -> int:
    return db.query(func.count(Product.product_id)).scalar() or 0


def get_total_warehouse_stock(db: Session) -> int:
    return (
        db.query(func.coalesce(func.sum(CurrentStock.quantity), 0))
        .join(Location, CurrentStock.location_id == Location.location_id)
        .filter(Location.location_type == "Warehouse")
        .scalar()
    )


def get_total_retail_stock(db: Session) -> int:
    return (
        db.query(func.coalesce(func.sum(CurrentStock.quantity), 0))
        .join(Location, CurrentStock.location_id == Location.location_id)
        .filter(Location.location_type == "Retail Store")
        .scalar()
    )


def get_expiring_units_count(db: Session, days: int = 60) -> int:
    cutoff = date.today() + timedelta(days=days)
    return (
        db.query(func.coalesce(func.sum(CurrentStock.quantity), 0))
        .join(Batch, CurrentStock.batch_id == Batch.batch_id)
        .filter(and_(Batch.expiry_date != None, Batch.expiry_date <= cutoff))
        .scalar()
    )


def get_recent_movements(db: Session, limit: int = 5):
    return (
        db.query(StockMovement)
        .order_by(StockMovement.movement_date.desc())
        .limit(limit)
        .all()
    )


def get_warehouse_stock(db: Session, warehouse_id: str = "MAIN_WH"):
    return db.query(CurrentStock).filter(CurrentStock.location_id == warehouse_id).all()


def get_warehouse_product_totals(db: Session, warehouse_id: str = "MAIN_WH"):
    return (
        db.query(
            CurrentStock.product_id,
            func.coalesce(func.sum(CurrentStock.quantity), 0).label("total_quantity"),
        )
        .filter(CurrentStock.location_id == warehouse_id)
        .group_by(CurrentStock.product_id)
        .all()
    )


def get_store_current_stock(db: Session, store_id: str) -> int:
    partner = db.query(RetailPartner).filter(RetailPartner.store_id == store_id).first()
    if not partner:
        return 0
    return (
        db.query(func.coalesce(func.sum(CurrentStock.quantity), 0))
        .filter(CurrentStock.location_id == partner.location_id)
        .scalar()
    )


def get_store_sales_today(db: Session, store_id: str) -> int:
    today = date.today()
    return (
        db.query(func.coalesce(func.sum(RetailSale.quantity_sold), 0))
        .filter(and_(RetailSale.store_id == store_id, RetailSale.sale_date == today))
        .scalar()
    )


def get_recent_sales(db: Session, limit: int = 5):
    return db.query(RetailSale).order_by(RetailSale.sale_date.desc()).limit(limit).all()


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, data: dict) -> User:
    user = User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def add_new_batch_to_inventory(
    db: Session, batch: Batch, warehouse_id: str = "MAIN_WH"
) -> None:
    items = db.query(BatchProduct).filter(BatchProduct.batch_id == batch.batch_id).all()
    for item in items:
        stock = (
            db.query(CurrentStock)
            .filter(
                CurrentStock.product_id == item.product_id,
                CurrentStock.batch_id == batch.batch_id,
                CurrentStock.location_id == warehouse_id,
            )
            .first()
        )
        if stock:
            stock.quantity += item.quantity_produced
        else:
            stock = CurrentStock(
                stock_id=f"{batch.batch_id}-{warehouse_id}-{item.product_id}",
                product_id=item.product_id,
                batch_id=batch.batch_id,
                location_id=warehouse_id,
                quantity=item.quantity_produced,
            )
            db.add(stock)
    db.commit()


def dispatch_stock(db: Session, movement: StockMovement) -> None:
    if movement.source_location_id:
        src = (
            db.query(CurrentStock)
            .filter(
                CurrentStock.product_id == movement.product_id,
                CurrentStock.batch_id == movement.batch_id,
                CurrentStock.location_id == movement.source_location_id,
            )
            .first()
        )
        if src:
            src.quantity = max(0, src.quantity - movement.quantity)
    if movement.destination_location_id:
        dest = (
            db.query(CurrentStock)
            .filter(
                CurrentStock.product_id == movement.product_id,
                CurrentStock.batch_id == movement.batch_id,
                CurrentStock.location_id == movement.destination_location_id,
            )
            .first()
        )
        if dest:
            dest.quantity += movement.quantity
        else:
            dest = CurrentStock(
                stock_id=f"{movement.batch_id}-{movement.destination_location_id}",
                product_id=movement.product_id,
                batch_id=movement.batch_id,
                location_id=movement.destination_location_id,
                quantity=movement.quantity,
            )
            db.add(dest)
    db.commit()


def create_retail_sale(db: Session, data: dict) -> RetailSale:
    sale = RetailSale(**data)
    db.add(sale)
    partner = (
        db.query(RetailPartner).filter(RetailPartner.store_id == sale.store_id).first()
    )
    if partner:
        stock = (
            db.query(CurrentStock)
            .filter(
                CurrentStock.product_id == sale.product_id,
                CurrentStock.batch_id == sale.batch_id,
                CurrentStock.location_id == partner.location_id,
            )
            .first()
        )
        if stock:
            stock.quantity = max(0, stock.quantity - sale.quantity_sold)
    db.commit()
    db.refresh(sale)
    return sale


def get_store_current_stock_summary(db: Session, store_id: str):
    partner = db.query(RetailPartner).filter(RetailPartner.store_id == store_id).first()
    if not partner:
        return []
    return (
        db.query(CurrentStock)
        .filter(CurrentStock.location_id == partner.location_id)
        .all()
    )


def get_store_upcoming_deliveries(db: Session, store_id: str):
    partner = db.query(RetailPartner).filter(RetailPartner.store_id == store_id).first()
    if not partner:
        return []
    today = date.today()
    return (
        db.query(StockMovement)
        .filter(
            StockMovement.destination_location_id == partner.location_id,
            StockMovement.movement_date >= today,
        )
        .order_by(StockMovement.movement_date)
        .all()
    )


def get_all_retail_partners(db: Session):
    return db.query(RetailPartner).all()


def create_retail_partner(db: Session, data: dict) -> RetailPartner:
    partner = RetailPartner(**data)
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


def create_store_partner_account(db: Session, data: dict) -> tuple[RetailPartner, User]:
    partner_fields = {
        k: data.get(k)
        for k in [
            "store_id",
            "location_id",
            "store_name",
            "contact_person",
            "contact_number",
            "email",
        ]
    }
    partner = RetailPartner(**partner_fields)
    user = User(
        username=data["username"],
        password=data["password"],
        role="store",
        store_id=data["location_id"],
    )
    db.add(partner)
    db.add(user)
    db.commit()
    db.refresh(partner)
    db.refresh(user)
    return partner, user


# --- Utility commands from init_db and analyze_schema ---
SCHEMA_FILE = Path(__file__).parent / "schema.sql"
DB_FILE = Path("arivu_foods_inventory.db")


def create_tables() -> None:
    sql = SCHEMA_FILE.read_text()
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.executescript(sql)
        conn.commit()
        print("Tables created successfully")
    finally:
        conn.close()


def _generate_product_id(name: str, qty: str, unit: str, index: int) -> str:
    parts = [w[0] for w in name.upper().split() if w[0].isalnum()]
    base = "".join(parts) or f"PROD{index}"
    return f"{base}{qty}{unit.upper()}"


def load_sample_products() -> None:
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
            unit = (
                row.get("measurement", "").strip()
                or row.get("measurement ", "").strip()
            )
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


# WHY: keep database products in sync with CSV file when new rows are added
# WHAT: update or insert each product from products.csv (Closes: #45)
# HOW: call sync_products_from_csv() via CLI or POST /products/sync; remove
#      function and route to roll back
def sync_products_from_csv(db: Session, csv_path: Path = Path("products.csv")) -> int:
    if not csv_path.exists():
        print("products.csv not found; nothing to sync")
        return 0
    import csv

    count = 0
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            name = row.get("Product Name", "").strip()
            if not name:
                continue
            qty = row.get("Quantity", "1").strip()
            unit = (
                row.get("measurement", "").strip()
                or row.get("measurement ", "").strip()
            )
            price = row.get("Price (₹)", "0").strip()
            product_id = _generate_product_id(name, qty, unit, idx)
            product = db.get(Product, product_id)
            if product:
                product.product_name = name
                product.unit_of_measure = unit or "unit"
                product.standard_pack_size = float(qty)
                product.mrp = float(price or 0)
            else:
                product = Product(
                    product_id=product_id,
                    product_name=name,
                    unit_of_measure=unit or "unit",
                    standard_pack_size=float(qty),
                    mrp=float(price or 0),
                )
                db.add(product)
            count += 1
    db.commit()
    return count


def analyze_schema() -> None:
    create_re = re.compile(r"CREATE TABLE (\w+) \(")
    column_re = re.compile(r"\s*(\w+) [A-Z]+")
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


app = FastAPI(title="Arivu Foods Inventory API")
# Serve frontend HTML from /ui and show login page at root
app.mount("/ui", StaticFiles(directory="."), name="ui")


@app.get("/", response_class=HTMLResponse)
def serve_login():
    """Return login page so users can authenticate via browser."""
    return FileResponse("login.html")


# WHY: allow direct access via /login.html as well as root (Closes: #20)
# WHAT: serve same login page when requested by filename
# HOW: remove this route if frontend uses a dedicated framework router
@app.get("/login.html", response_class=HTMLResponse)
def serve_login_page_alias():
    return FileResponse("login.html")


# Additional static file routes so relative links work from login page
# WHY: fix 404 errors for pages like register.html when accessed directly
# WHAT: expose key HTML pages at the root path
# HOW: remove these routes if StaticFiles mount is changed
@app.get("/register.html", response_class=HTMLResponse)
def serve_register_page():
    return FileResponse("register.html")


@app.get("/arivu_Dashboard.html", response_class=HTMLResponse)
def serve_arivu_dashboard_page():
    return FileResponse("arivu_Dashboard.html")


@app.get("/store_partner_dashboard.html", response_class=HTMLResponse)
def serve_store_dashboard_page():
    return FileResponse("store_partner_dashboard.html")


@app.get("/product_list.html", response_class=HTMLResponse)
def serve_product_list_page():
    return FileResponse("product_list.html")


# WHY: provide embedded product list for dashboard (Closes: #22)
@app.get("/products.html", response_class=HTMLResponse)
def serve_products_page():
    return FileResponse("products.html")


# Individual routes use HTTP Basic auth dependency so endpoints require login
auth_dep = Depends(verify_basic_auth)


class ProductCreate(BaseModel):
    """Schema for creating a product."""

    product_id: str
    product_name: str
    unit_of_measure: str
    standard_pack_size: float
    mrp: float | None = None


class BatchItem(BaseModel):
    """Single product entry within a batch."""

    product_id: str
    quantity_produced: int


class BatchCreate(BaseModel):
    """Schema for creating batches."""

    # WHY: validate incoming batch data for POST /batches
    batch_id: str
    date_manufactured: date
    expiry_date: date | None = None
    remarks: str | None = None
    items: list[BatchItem]


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


class StorePartnerAccountCreate(BaseModel):
    """Schema to create partner plus login user."""

    # WHY: combine partner and user creation for admin convenience (Closes: #12)
    store_id: str
    location_id: str
    store_name: str
    username: str
    password: str
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
    db_user = create_user(db, {**user.dict(exclude={"password"}), "password": hashed})
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
    db_product = create_product(db, product.dict())
    return {"message": "Product created", "product_id": db_product.product_id}


# WHY: bulk update products from CSV via API for admin automation (Closes: #45)
# WHAT: POST /products/sync reads products.csv and upserts records
# HOW: call sync_products_from_csv; remove route and CLI command to rollback
@app.post("/products/sync", dependencies=[auth_dep])
def sync_products(db: Session = Depends(get_db)):
    count = sync_products_from_csv(db)
    return {"message": f"{count} products synced"}


@app.get("/batches", dependencies=[auth_dep])
def list_batches(db: Session = Depends(get_db)):
    """Return all batches."""
    # WHY: list production batches for inventory tracking (Closes: #4)
    batches = get_all_batches(db)
    results = []
    for b, items in batches:
        results.append(
            {
                "batch_id": b.batch_id,
                "date_manufactured": b.date_manufactured.isoformat(),
                "expiry_date": b.expiry_date.isoformat() if b.expiry_date else None,
                "remarks": b.remarks,
                "items": [
                    {
                        "product_id": i.product_id,
                        "quantity_produced": i.quantity_produced,
                    }
                    for i in items
                ],
            }
        )
    return results


@app.post("/batches", status_code=201, dependencies=[auth_dep])
def create_batch(batch: BatchCreate, db: Session = Depends(get_db)):
    """Create a new batch."""
    existing = db.get(Batch, batch.batch_id)
    if existing:
        raise HTTPException(status_code=400, detail="Batch ID already exists")
    batch_data = batch.dict()
    items = batch_data.pop("items")
    if not batch_data.get("expiry_date"):
        batch_data["expiry_date"] = batch_data["date_manufactured"] + timedelta(days=90)
    db_batch = create_batch(db, batch_data, [i for i in items])
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
    db_move = create_movement(db, {**movement.dict(), "movement_date": date.today()})
    # WHY: adjust CurrentStock on dispatch or receipt
    # WHAT: front-end dashboard relies on this to update stock tables
    # HOW: remove this call if inventory syncing is handled elsewhere
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
    batches = (
        db.query(Batch)
        .filter(Batch.expiry_date != None, Batch.expiry_date <= cutoff)
        .all()
    )
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
                "movement_date": (
                    m.movement_date.isoformat() if m.movement_date else None
                ),
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


@app.get("/warehouse-stock", dependencies=[auth_dep])
def warehouse_stock(warehouse_id: str = "MAIN_WH", db: Session = Depends(get_db)):
    """Return current stock records for a warehouse."""
    stock = get_warehouse_stock(db, warehouse_id)
    return [
        {
            "product_id": s.product_id,
            "batch_id": s.batch_id,
            "quantity": s.quantity,
        }
        for s in stock
    ]


@app.get("/warehouse-stock/summary", dependencies=[auth_dep])
def warehouse_stock_summary(
    warehouse_id: str = "MAIN_WH", db: Session = Depends(get_db)
):
    """Return product totals for a warehouse for quick dashboard view."""
    records = get_warehouse_product_totals(db, warehouse_id)
    return [{"product_id": r.product_id, "quantity": r.total_quantity} for r in records]


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
def create_retail_partner_endpoint(
    partner: RetailPartnerCreate, db: Session = Depends(get_db)
):
    """Create a new retail partner."""
    if db.get(RetailPartner, partner.store_id):
        raise HTTPException(status_code=400, detail="Store ID already exists")
    db_partner = create_retail_partner(db, partner.dict())
    return {"message": "Retail partner created", "store_id": db_partner.store_id}


@app.post("/store-partner-accounts", status_code=201, dependencies=[auth_dep])
def create_store_partner_account_endpoint(
    account: StorePartnerAccountCreate, db: Session = Depends(get_db)
):
    """Create partner and associated user account."""
    # WHY: streamline store onboarding by creating login with partner (Closes: #12)
    if db.get(RetailPartner, account.store_id):
        raise HTTPException(status_code=400, detail="Store ID already exists")
    if get_user_by_username(db, account.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = hashlib.sha256(account.password.encode()).hexdigest()
    create_store_partner_account(
        db, {**account.dict(exclude={"password"}), "password": hashed}
    )
    return {"message": "Store partner account created", "store_id": account.store_id}


if __name__ == "__main__":
    """Entry point for command line usage."""
    import sys
    import webbrowser

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "init-db":
            create_tables()
            load_sample_products()
        elif cmd == "analyze-schema":
            analyze_schema()
        elif cmd == "sync-products":
            with SessionLocal() as db:
                sync_products_from_csv(db)
        else:
            print("Unknown command")
    else:
        webbrowser.open("http://127.0.0.1:8000")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
