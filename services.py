
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
    StockMovement,
    CurrentStock,
    RetailSale,
    Location,
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
    return db.query(Batch).all()


def create_batch(db: Session, data: dict) -> Batch:
    batch = Batch(**data)
    db.add(batch)
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


def get_store_current_stock(db: Session, store_id: str) -> int:
    return (
        db.query(func.coalesce(func.sum(CurrentStock.quantity), 0))
        .filter(CurrentStock.location_id == store_id)
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
