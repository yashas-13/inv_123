"""SQLAlchemy models for FastAPI backend.

WHY: Translate tables to ORM for use in API.
WHAT: Defines Product and Location models.
HOW: Extend by adding remaining tables; rollback by deleting this file.
Closes: #2 (basic API models).
"""

from sqlalchemy import Column, String, DECIMAL
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
