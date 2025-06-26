"""FastAPI app exposing inventory endpoints.

WHY: Provide backend API to access DB data.
WHAT: Adds /products endpoint for listing products.
HOW: Extend by adding CRUD routes; rollback by removing this file.
Closes: #2.
"""

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database import get_db, Base, engine
from models import Product

# Create tables if not already present (initial migration)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Arivu Foods Inventory API")

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
