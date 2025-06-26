"""FastAPI app exposing inventory endpoints.

WHY: Provide backend API to access DB data.
WHAT: Adds /products endpoint for listing products.
HOW: Extend by adding CRUD routes; rollback by removing this file.
Closes: #2.
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, Base, engine
from models import Product

# Create tables if not already present (initial migration)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Arivu Foods Inventory API")


class ProductCreate(BaseModel):
    """Schema for creating a product."""
    product_id: str
    product_name: str
    unit_of_measure: str
    standard_pack_size: float
    mrp: float | None = None

@app.get("/products")
def list_products(db: Session = Depends(get_db)):
    """Return all products."""
    products = db.query(Product).all()
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


@app.post("/products", status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product in the database."""
    # WHY: allow backend to manage DB by inserting products (Closes: #3)
    # WHAT: adds POST /products route for creating new products
    # HOW: check for existing ID then insert; rollback by removing this func
    existing = db.get(Product, product.product_id)
    if existing:
        raise HTTPException(status_code=400, detail="Product ID already exists")
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return {"message": "Product created", "product_id": db_product.product_id}
