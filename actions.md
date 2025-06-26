## **Python Development Action Plan for Arivu Foods Inventory System**

This action plan outlines the steps to build a robust inventory management system in Python, leveraging the previously defined SQL schema.

### **Phase 1: Environment Setup and Database Initialization**

**Goal:** Get your development environment ready and set up the database.

1. **Choose a Python Version:**  
   * **Action:** Standardize on Python 3.8+ (e.g., 3.9, 3.10, 3.11).  
2. **Select a Database:**  
   * **Action:**  
     * For quick prototyping and learning: **SQLite** (built-in, no server needed).  
     * For production and scalability: **PostgreSQL** or **MySQL** (requires installation and setup of the respective database server).  
   * **Reasoning:** SQLite is easiest to start, but PostgreSQL/MySQL offer better concurrency and features for multi-user environments.  
3. **Create a Virtual Environment:**  
   * **Action:**  
     python3 \-m venv venv  
     source venv/bin/activate \# On Windows: venv\\Scripts\\activate

   * **Reasoning:** Isolates project dependencies.  
4. **Install Database Driver & ORM:**  
   * **Action:**  
     * For SQLite: pip install sqlalchemy (SQLAlchemy includes SQLite support)  
     * For PostgreSQL: pip install sqlalchemy psycopg2-binary  
     * For MySQL: pip install sqlalchemy mysql-connector-python  
   * **Reasoning:** An ORM (Object-Relational Mapper) like SQLAlchemy simplifies database interactions by letting you work with Python objects instead of raw SQL queries for most operations.  
5. **Database Connection Module (database.py):**  
   * **Action:** Create a Python module responsible for connecting to the database and managing the session.  
   * **Example (SQLAlchemy with SQLite):**  
     \# database.py  
     from sqlalchemy import create\_engine  
     from sqlalchemy.orm import sessionmaker, declarative\_base

     DATABASE\_URL \= "sqlite:///./arivu\_foods\_inventory.db" \# Or your PostgreSQL/MySQL connection string

     engine \= create\_engine(DATABASE\_URL, echo=True) \# echo=True for SQL logging  
     SessionLocal \= sessionmaker(autocommit=False, autoflush=False, bind=engine)  
     Base \= declarative\_base() \# Base class for our ORM models

     def get\_db():  
         db \= SessionLocal()  
         try:  
             yield db  
         finally:  
             db.close()

6. **Initialize Database Schema:**  
   * **Action:** Write a script (init\_db.py) to create all tables defined in your SQL schema.  
   * **Reasoning:** Ensures your database has the correct structure.  
   * **Example:**  
     \# init\_db.py  
     from database import Base, engine  
     from models import \* \# Import all your ORM models here

     def create\_tables():  
         Base.metadata.create\_all(bind=engine)  
         print("Database tables created successfully\!")

     if \_\_name\_\_ \== "\_\_main\_\_":  
         create\_tables()

### **Phase 2: Data Models (ORM Definitions \- models.py)**

**Goal:** Translate your SQL schema into Python classes using SQLAlchemy's ORM.

1. **Define ORM Models:**  
   * **Action:** Create a models.py file. For each table in your SQL schema (products, locations, retail\_partners, agents, batches, current\_stock, stock\_movements, retail\_sales), define a corresponding SQLAlchemy model class.  
   * **Reasoning:** This allows you to interact with database rows as Python objects, making your code cleaner and more maintainable.  
   * **Example (Partial):**  
     \# models.py  
     from sqlalchemy import Column, Integer, String, Date, DateTime, DECIMAL, ForeignKey  
     from sqlalchemy.orm import relationship  
     from database import Base  
     import datetime

     class Product(Base):  
         \_\_tablename\_\_ \= 'products'  
         product\_id \= Column(String(50), primary\_key=True)  
         product\_name \= Column(String(255), nullable=False)  
         unit\_of\_measure \= Column(String(50), nullable=False)  
         standard\_pack\_size \= Column(DECIMAL(10, 2), nullable=False)  
         mrp \= Column(DECIMAL(10, 2))

         batches \= relationship("Batch", back\_populates="product")  
         current\_stocks \= relationship("CurrentStock", back\_populates="product")  
         stock\_movements \= relationship("StockMovement", back\_populates="product")  
         retail\_sales \= relationship("RetailSale", back\_populates="product")

     class Location(Base):  
         \_\_tablename\_\_ \= 'locations'  
         location\_id \= Column(String(50), primary\_key=True)  
         location\_name \= Column(String(255), nullable=False)  
         location\_type \= Column(String(50), nullable=False)  
         address \= Column(String(500))  
         city \= Column(String(100))  
         state \= Column(String(100))  
         zip\_code \= Column(String(20))  
         country \= Column(String(100), default='India')

         current\_stocks \= relationship("CurrentStock", back\_populates="location")  
         source\_movements \= relationship("StockMovement", foreign\_keys="\[StockMovement.source\_location\_id\]", back\_populates="source\_location")  
         destination\_movements \= relationship("StockMovement", foreign\_keys="\[StockMovement.destination\_location\_id\]", back\_populates="destination\_location")  
         retail\_partner \= relationship("RetailPartner", uselist=False, back\_populates="location\_obj")

     class Batch(Base):  
         \_\_tablename\_\_ \= 'batches'  
         batch\_id \= Column(String(50), primary\_key=True)  
         product\_id \= Column(String(50), ForeignKey('products.product\_id'), nullable=False)  
         date\_manufactured \= Column(Date, nullable=False)  
         quantity\_produced \= Column(Integer, nullable=False)  
         expiry\_date \= Column(Date) \# CRUCIAL for expiry tracking  
         remarks \= Column(String)

         product \= relationship("Product", back\_populates="batches")  
         current\_stocks \= relationship("CurrentStock", back\_populates="batch")  
         stock\_movements \= relationship("StockMovement", back\_populates="batch")  
         retail\_sales \= relationship("RetailSale", back\_populates="batch")

     class CurrentStock(Base):  
         \_\_tablename\_\_ \= 'current\_stock'  
         stock\_id \= Column(String(50), primary\_key=True)  
         product\_id \= Column(String(50), ForeignKey('products.product\_id'), nullable=False)  
         batch\_id \= Column(String(50), ForeignKey('batches.batch\_id'), nullable=False)  
         location\_id \= Column(String(50), ForeignKey('locations.location\_id'), nullable=False)  
         quantity \= Column(Integer, nullable=False, default=0)  
         last\_updated \= Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

         product \= relationship("Product", back\_populates="current\_stocks")  
         batch \= relationship("Batch", back\_populates="current\_stocks")  
         location \= relationship("Location", back\_populates="current\_stocks")

     \# ... (Define other models: RetailPartner, Agent, StockMovement, RetailSale similarly)

### **Phase 3: Core Business Logic and Services (services.py / crud.py)**

**Goal:** Implement functions to interact with the database and encapsulate business rules.

1. **CRUD Functions for Each Entity:**  
   * **Action:** Create functions to create, get\_by\_id, get\_all, update, and delete records for each of your ORM models.  
   * **Reasoning:** Provides a clean interface for database operations.  
2. **Stock Management Logic:**  
   * **Action:**  
     * **add\_new\_batch\_to\_inventory(db, product\_id, batch\_id, qty, expiry\_date):** When a new batch is manufactured, add it to the batches table and update the current\_stock at the main warehouse.  
     * **dispatch\_stock(db, product\_id, batch\_id, source\_loc\_id, dest\_loc\_id, qty, agent\_id):**  
       * Record movement in stock\_movements.  
       * Decrement current\_stock at source\_loc\_id.  
       * Increment current\_stock at dest\_loc\_id. Handle cases where stock for that product/batch doesn't exist at the destination yet.  
     * **record\_retail\_sale(db, store\_id, product\_id, batch\_id, qty\_sold, sales\_agent\_id):**  
       * Record sale in retail\_sales.  
       * Decrement current\_stock at the store\_id location.  
     * **record\_stock\_adjustment(db, product\_id, batch\_id, location\_id, qty\_change, type, remarks):** For handling spoilage, returns, etc.  
   * **Reasoning:** These functions enforce the business rules for inventory flow.  
3. **Expiry Tracking Logic:**  
   * **Action:**  
     * **get\_expiring\_stock(db, days\_threshold, location\_type=None, location\_id=None):**  
       * Query current\_stock table joined with batches table.  
       * Filter batches.expiry\_date to be within CURRENT\_DATE and CURRENT\_DATE \+ days\_threshold.  
       * Add optional filters for location\_type (e.g., 'Warehouse', 'Retail Store') or specific location\_id.  
   * **Reasoning:** This is a key requirement for your business.

### **Phase 4: API Layer (Using FastAPI \- Recommended for Scalability)**

**Goal:** Create a set of endpoints that external applications (like a web UI or your sales agents' tools) can use to interact with your inventory system.

1. **Install FastAPI and Uvicorn:**  
   * **Action:** pip install fastapi uvicorn  
   * **Reasoning:** FastAPI is a modern, fast (high-performance) web framework for building APIs, with automatic data validation and documentation.  
2. **Define API Endpoints (main.py):**  
   * **Action:** Create routes for each major operation (e.g., /products, /batches, /stock\_movements, /expiring\_stock).  
   * **Reasoning:** Allows different parts of your system (or external systems) to communicate programmatically.  
   * **Example (Partial):**  
     \# main.py  
     from fastapi import FastAPI, Depends, HTTPException  
     from sqlalchemy.orm import Session  
     from typing import List, Optional  
     from datetime import date, timedelta

     from database import get\_db, Base, engine  
     from models import Product, Batch, CurrentStock, Location, RetailPartner, StockMovement, RetailSale, Agent  
     \# Import your service functions  
     \# import services

     app \= FastAPI(title="Arivu Foods Inventory API")

     \# Create tables on startup (or run init\_db.py separately)  
     @app.on\_event("startup")  
     def on\_startup():  
         Base.metadata.create\_all(bind=engine)

     @app.get("/products", response\_model=List\[dict\]) \# You'd define Pydantic models for response\_model  
     def get\_all\_products(db: Session \= Depends(get\_db)):  
         return db.query(Product).all()

     @app.post("/batches/")  
     def create\_batch(batch\_data: dict, db: Session \= Depends(get\_db)): \# Use Pydantic models for request body  
         \# Call your service function here  
         \# new\_batch \= services.add\_new\_batch\_to\_inventory(db, ...)  
         pass

     @app.post("/stock-movements/")  
     def record\_movement(movement\_data: dict, db: Session \= Depends(get\_db)):  
         \# services.dispatch\_stock(db, ...)  
         pass

     @app.get("/expiring-stock/", response\_model=List\[dict\])  
     def get\_expiring\_products\_api(days\_threshold: int \= 30, db: Session \= Depends(get\_db)):  
         \# This would call the get\_expiring\_stock service function  
         threshold\_date \= date.today() \+ timedelta(days=days\_threshold)  
         expiring\_items \= db.query(  
             Product.product\_name,  
             Batch.batch\_id,  
             Batch.expiry\_date,  
             CurrentStock.quantity,  
             Location.location\_name,  
             Location.location\_type  
         ).join(Batch, CurrentStock.batch\_id \== Batch.batch\_id)\\  
          .join(Product, CurrentStock.product\_id \== Product.product\_id)\\  
          .join(Location, CurrentStock.location\_id \== Location.location\_id)\\  
          .filter(Batch.expiry\_date.isnot(None))\\  
          .filter(Batch.expiry\_date.between(date.today(), threshold\_date))\\  
          .order\_by(Batch.expiry\_date.asc())\\  
          .all()

         \# Convert to list of dictionaries for JSON response  
         result \= \[\]  
         for item in expiring\_items:  
             result.append({  
                 "product\_name": item.product\_name,  
                 "batch\_id": item.batch\_id,  
                 "expiry\_date": item.expiry\_date.isoformat() if item.expiry\_date else None,  
                 "current\_stock\_quantity": item.current\_stock\_quantity,  
                 "location\_name": item.location\_name,  
                 "location\_type": item.location\_type  
             })  
         return result

     \# To run this: uvicorn main:app \--reload

### **Phase 5: User Interface (Optional \- Initial CLI)**

**Goal:** Provide a basic way to interact with the system without a full web frontend.

1. **Command-Line Interface (CLI):**  
   * **Action:** Create a cli.py script that uses your service functions to perform operations. This can be menu-driven.  
   * **Example:**  
     \# cli.py  
     from database import get\_db  
     from services import add\_new\_batch\_to\_inventory, dispatch\_stock, get\_expiring\_stock  
     import uuid \# For generating unique IDs

     def main():  
         db\_gen \= get\_db()  
         db \= next(db\_gen) \# Get a session

         while True:  
             print("\\n--- Arivu Foods Inventory CLI \---")  
             print("1. Add New Batch")  
             print("2. Dispatch Stock")  
             print("3. View Expiring Stock (Next 30 Days)")  
             print("4. Exit")  
             choice \= input("Enter your choice: ")

             try:  
                 if choice \== '1':  
                     product\_id \= input("Enter Product ID: ")  
                     qty \= int(input("Enter Quantity Produced: "))  
                     expiry\_date\_str \= input("Enter Expiry Date (YYYY-MM-DD): ")  
                     expiry\_date \= datetime.strptime(expiry\_date\_str, "%Y-%m-%d").date()  
                     batch\_id \= f"BATCH-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())\[:4\]}"  
                     add\_new\_batch\_to\_inventory(db, product\_id, batch\_id, qty, expiry\_date)  
                     print("Batch added.")  
                 elif choice \== '2':  
                     product\_id \= input("Enter Product ID: ")  
                     batch\_id \= input("Enter Batch ID: ")  
                     source\_loc \= input("Enter Source Location ID (e.g., MAIN\_WH): ")  
                     dest\_loc \= input("Enter Destination Location ID: ")  
                     qty \= int(input("Enter Quantity to Dispatch: "))  
                     agent\_id \= input("Enter Agent ID: ")  
                     dispatch\_stock(db, product\_id, batch\_id, source\_loc, dest\_loc, qty, agent\_id)  
                     print("Stock dispatched.")  
                 elif choice \== '3':  
                     expiring\_products \= get\_expiring\_stock(db, 30\)  
                     print("\\n--- Expiring Products \---")  
                     if not expiring\_products:  
                         print("No products expiring in the next 30 days.")  
                     for p in expiring\_products:  
                         print(f"Product: {p.product\_name}, Batch: {p.batch\_id}, Expiry: {p.expiry\_date}, Quantity: {p.current\_stock\_quantity}, Location: {p.location\_name}")  
                 elif choice \== '4':  
                     break  
                 else:  
                     print("Invalid choice. Please try again.")  
             except Exception as e:  
                 print(f"An error occurred: {e}")  
         db.close() \# Close the session  
     if \_\_name\_\_ \== "\_\_main\_\_":  
         main()

   * **Reasoning:** Allows for initial testing and manual operations. Later, this can be replaced by a more sophisticated web UI.

### **Phase 6: Testing and Deployment Considerations**

**Goal:** Ensure the system works correctly and plan for making it accessible.

1. **Unit and Integration Tests:**  
   * **Action:** Write tests using pytest to verify individual functions and the interaction between modules.  
   * **Reasoning:** Ensures code quality, prevents regressions, and validates business logic.  
2. **Error Handling and Logging:**  
   * **Action:** Implement robust error handling (try-except blocks) and logging to capture issues.  
   * **Reasoning:** Essential for debugging and monitoring in production.  
3. **Deployment (Future Consideration):**  
   * **Action:** For a web API, consider deployment on platforms like Heroku, AWS (EC2/ECS), Google Cloud (Cloud Run/App Engine), or a private server. Containerization with Docker is highly recommended.  
   * **Reasoning:** Makes your system accessible and scalable.

### **Next Steps After Development:**

* **Data Migration:** If you have existing data (e.g., in spreadsheets), plan how to import it into your new database.  
* **User Training:** Train your team (sales agents, warehouse staff) on how to use the system.  
* **Reporting Dashboard:** Build a dashboard (e.g., using a separate frontend app, or a tool like Metabase/Superset if your database is accessible) to visualize key metrics like current stock levels, expiring products, sales trends, etc.

This action plan provides a structured approach to building your Arivu Foods inventory system using Python. Remember to iterate, test, and gather feedback as you develop each phase.