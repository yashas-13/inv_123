"""SQLAlchemy models for FastAPI backend.

WHY: Translate tables to ORM for use in API.
WHAT: Defines Product and Location models.
HOW: Extend by adding remaining tables; rollback by deleting this file.
Closes: #2 (basic API models).
"""

from sqlalchemy import Column, String, DECIMAL, Date, Integer, ForeignKey, TIMESTAMP

# WHY: add remaining tables from schema for fuller tracking (Closes: #6)
# WHAT: new ORM models for partners, agents, stock and sales
# HOW: extend queries with relationships; remove models to roll back

from database import Base

class Product(Base):
    __tablename__ = 'products'
    product_id = Column(String(50), primary_key=True)
    product_name = Column(String(255), nullable=False)
    unit_of_measure = Column(String(50), nullable=False)
    standard_pack_size = Column(DECIMAL(10, 2), nullable=False)
    mrp = Column(DECIMAL(10, 2))

class Location(Base):
    __tablename__ = 'locations'
    location_id = Column(String(50), primary_key=True)
    location_name = Column(String(255), nullable=False)
    location_type = Column(String(50), nullable=False)
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(100))
    zip_code = Column(String(20))
    country = Column(String(100), default='India')


class Batch(Base):
    """Batches of manufactured products."""
    # WHY: represent production lots for expiry tracking
    # WHAT: maps to batches table
    # HOW: extend with relationships if needed; delete class to rollback
    __tablename__ = 'batches'
    batch_id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey('products.product_id'), nullable=False)
    date_manufactured = Column(Date, nullable=False)
    quantity_produced = Column(Integer, nullable=False)
    expiry_date = Column(Date)
    remarks = Column(String)


class StockMovement(Base):
    """Log of product movements between locations."""
    # WHY: track transfers, sales, adjustments (Closes: #4)
    # HOW: remove table or alter columns to rollback/extend
    __tablename__ = 'stock_movements'
    movement_id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey('products.product_id'), nullable=False)
    batch_id = Column(String(50), ForeignKey('batches.batch_id'), nullable=False)
    movement_date = Column(TIMESTAMP)
    movement_type = Column(String(50), nullable=False)
    source_location_id = Column(String(50), ForeignKey('locations.location_id'))
    destination_location_id = Column(String(50), ForeignKey('locations.location_id'))
    quantity = Column(Integer, nullable=False)
    agent_id = Column(String(50), ForeignKey('agents.agent_id'))
    remarks = Column(String)


class RetailPartner(Base):
    """Retail stores carrying products."""
    __tablename__ = 'retail_partners'
    store_id = Column(String(50), primary_key=True)
    location_id = Column(String(50), ForeignKey('locations.location_id'), nullable=False)
    store_name = Column(String(255), nullable=False)
    contact_person = Column(String(255))
    contact_number = Column(String(50))
    email = Column(String(255))


class Agent(Base):
    """Sales/dispatch agents."""
    __tablename__ = 'agents'
    agent_id = Column(String(50), primary_key=True)
    agent_name = Column(String(255), nullable=False)
    contact_number = Column(String(50))
    email = Column(String(255))


class CurrentStock(Base):
    """Current quantity of each batch at each location."""
    __tablename__ = 'current_stock'
    stock_id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey('products.product_id'), nullable=False)
    batch_id = Column(String(50), ForeignKey('batches.batch_id'), nullable=False)
    location_id = Column(String(50), ForeignKey('locations.location_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    last_updated = Column(TIMESTAMP)


class RetailSale(Base):
    """Sales recorded at partner stores."""
    __tablename__ = 'retail_sales'
    sale_id = Column(String(50), primary_key=True)
    sale_date = Column(Date, nullable=False)
    store_id = Column(String(50), ForeignKey('retail_partners.store_id'), nullable=False)
    product_id = Column(String(50), ForeignKey('products.product_id'), nullable=False)
    batch_id = Column(String(50), ForeignKey('batches.batch_id'))
    quantity_sold = Column(Integer, nullable=False)
    sales_agent_id = Column(String(50), ForeignKey('agents.agent_id'))
    sale_price_per_unit = Column(DECIMAL(10, 2))
    remarks = Column(String)

