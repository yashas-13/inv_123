
"""Business logic functions for FastAPI routes.

WHY: separate DB queries from routes for reuse and testing.
WHAT: CRUD helpers and dashboard aggregations.
HOW: extend with more complex queries; remove usages to roll back.
Closes: #6
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date, timedelta

from models import (
    Product,
    Batch,
    BatchProduct,
    StockMovement,
    CurrentStock,
    RetailSale,
    Location,
    RetailPartner,
    User,
)

# --- CRUD helpers ---

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
    # WHY: support multi-product batches after schema change
    batches = db.query(Batch).all()
    result = []
    for b in batches:
        items = (
            db.query(BatchProduct)
            .filter(BatchProduct.batch_id == b.batch_id)
            .all()
        )
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

# --- Dashboard aggregations ---

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
    return db.query(StockMovement).order_by(StockMovement.movement_date.desc()).limit(limit).all()


def get_warehouse_stock(db: Session, warehouse_id: str = "MAIN_WH"):
    """Return current stock for the given warehouse location.

    WHY: display detailed inventory on Arivu dashboard (Closes: #14)
    WHAT: query CurrentStock filtered by location_id
    HOW: change warehouse_id or remove endpoint to roll back
    """
    return (
        db.query(CurrentStock)
        .filter(CurrentStock.location_id == warehouse_id)
        .all()
    )


def get_store_current_stock(db: Session, store_id: str) -> int:
    """Sum current stock for a store by resolving its location."""
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
    """Return recent retail sales records."""
    # WHY: Provide dashboard view of latest partner sales
    # WHAT: Query retail_sales ordered by sale_date desc
    # HOW: adjust limit parameter to extend; remove endpoint to rollback
    return (
        db.query(RetailSale)
        .order_by(RetailSale.sale_date.desc())
        .limit(limit)
        .all()
    )

# --- User management ---
def get_user_by_username(db: Session, username: str):
    """Return user by username or None."""
    # WHY: needed for login endpoint (Closes: #9)
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, data: dict) -> User:
    """Create new user account."""
    # WHAT: inserts into users table, hashing already done upstream
    user = User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# --- Inventory adjustments ---
def add_new_batch_to_inventory(db: Session, batch: Batch, warehouse_id: str = "MAIN_WH") -> None:
    """Insert batch item quantities into CurrentStock at the main warehouse."""
    items = (
        db.query(BatchProduct)
        .filter(BatchProduct.batch_id == batch.batch_id)
        .all()
    )
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
    """Update CurrentStock for a dispatch/transfer movement.

    WHY: synchronize inventory counts when stock moves between locations.
    WHAT: decrement source and increment destination quantities.
    HOW: modify logic or remove call from POST /stock-movements to roll back."""
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
    """Insert a RetailSale and decrement CurrentStock for the store."""
    sale = RetailSale(**data)
    db.add(sale)
    # get store location id to update stock
    partner = db.query(RetailPartner).filter(RetailPartner.store_id == sale.store_id).first()
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
    """Return list of products and quantities for the given store."""
    partner = db.query(RetailPartner).filter(RetailPartner.store_id == store_id).first()
    if not partner:
        return []
    return (
        db.query(CurrentStock)
        .filter(CurrentStock.location_id == partner.location_id)
        .all()
    )


def get_store_upcoming_deliveries(db: Session, store_id: str):
    """Return future dispatch movements destined for this store."""
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
    """List all registered retail partners."""
    return db.query(RetailPartner).all()


def create_retail_partner(db: Session, data: dict) -> RetailPartner:
    """Insert a new retail partner record."""
    partner = RetailPartner(**data)
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


def create_store_partner_account(db: Session, data: dict) -> tuple[RetailPartner, User]:
    """Create a retail partner and login user in one transaction."""
    # WHY: allow Arivu admin to register store partners with credentials (Closes: #12)
    # WHAT: inserts into retail_partners and users tables together
    # HOW: extend with email confirmation or remove call for rollback
    partner_fields = {
        k: data.get(k)
        for k in ["store_id", "location_id", "store_name", "contact_person", "contact_number", "email"]
    }
    partner = RetailPartner(**partner_fields)
    user = User(
        username=data["username"],
        password=data["password"],  # hashed upstream
        role="store",
        store_id=data["location_id"],
    )
    db.add(partner)
    db.add(user)
    db.commit()
    db.refresh(partner)
    db.refresh(user)
    return partner, user

