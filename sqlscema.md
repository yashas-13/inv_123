\-- Database: ArivuFoodsInventory

\-- Table for Products  
\-- Stores information about each unique product Arivu Foods manufactures.  
CREATE TABLE products (  
    product\_id VARCHAR(50) PRIMARY KEY, \-- Unique identifier for each product (e.g., 'AFCMA1KG')  
    product\_name VARCHAR(255) NOT NULL, \-- Full name of the product (e.g., 'Low-Carb Multi Seeds Atta')  
    unit\_of\_measure VARCHAR(50) NOT NULL, \-- Unit in which the product is measured (e.g., 'kg', 'L', 'g')  
    standard\_pack\_size DECIMAL(10, 2\) NOT NULL, \-- The quantity in one standard unit (e.g., 1 for 1kg, 0.5 for 500g)  
    mrp DECIMAL(10, 2\) \-- Maximum Retail Price, if applicable  
);

\-- Table for Locations  
\-- Stores all physical locations where inventory can be held (main warehouse, retail stores).  
CREATE TABLE locations (  
    location\_id VARCHAR(50) PRIMARY KEY, \-- Unique identifier for each location (e.g., 'MAIN\_WH', 'STORE\_DELHI\_001')  
    location\_name VARCHAR(255) NOT NULL, \-- Descriptive name of the location  
    location\_type VARCHAR(50) NOT NULL, \-- Type of location ('Warehouse', 'Retail Store', 'Transit', 'Customer')  
    address VARCHAR(500), \-- Full address of the location  
    city VARCHAR(100),  
    state VARCHAR(100),  
    zip\_code VARCHAR(20),  
    country VARCHAR(100) DEFAULT 'India'  
);

\-- Table for Retail Partners  
\-- Specific details about your retail store partners, linking to their location.  
CREATE TABLE retail\_partners (  
    store\_id VARCHAR(50) PRIMARY KEY, \-- Unique identifier for each retail store partner  
    location\_id VARCHAR(50) NOT NULL, \-- Foreign Key to locations table for the store's physical location  
    store\_name VARCHAR(255) NOT NULL, \-- Name of the retail store  
    contact\_person VARCHAR(255), \-- Main contact person at the store  
    contact\_number VARCHAR(50),  
    email VARCHAR(255),  
    CONSTRAINT fk\_retail\_location FOREIGN KEY (location\_id) REFERENCES locations(location\_id)  
);

\-- Table for Sales Agents  
\-- Details of your sales agents who manage relationships with retail partners.  
CREATE TABLE agents (  
    agent\_id VARCHAR(50) PRIMARY KEY, \-- Unique identifier for each sales agent  
    agent\_name VARCHAR(255) NOT NULL,  
    contact\_number VARCHAR(50),  
    email VARCHAR(255)  
);

\-- Table for Batches  
\-- Records details of each manufacturing batch for a product.  
CREATE TABLE batches (  
    batch\_id VARCHAR(50) PRIMARY KEY, \-- Unique identifier for the manufacturing batch (e.g., 'BATCH-20250701-001')  
    product\_id VARCHAR(50) NOT NULL, \-- Foreign Key to the products table  
    date\_manufactured DATE NOT NULL, \-- Date the batch was manufactured  
    quantity\_produced INT NOT NULL, \-- Total quantity produced in this batch (in product units)  
    expiry\_date DATE, \-- IMPORTANT: This column is crucial for tracking expiring products.  
    remarks TEXT, \-- Any specific notes about the batch (e.g., 'QC Passed')  
    CONSTRAINT fk\_batch\_product FOREIGN KEY (product\_id) REFERENCES products(product\_id)  
);

\-- Table for Current Stock  
\-- Shows the current quantity of a specific product from a specific batch at a specific location.  
\-- This table is dynamic and will be updated with every stock movement.  
CREATE TABLE current\_stock (  
    stock\_id VARCHAR(50) PRIMARY KEY, \-- Unique ID for this stock record  
    product\_id VARCHAR(50) NOT NULL, \-- Foreign Key to products table  
    batch\_id VARCHAR(50) NOT NULL, \-- Foreign Key to batches table  
    location\_id VARCHAR(50) NOT NULL, \-- Foreign Key to locations table (where the stock is currently located)  
    quantity INT NOT NULL CHECK (quantity \>= 0), \-- Current quantity of the product/batch at this location  
    last\_updated TIMESTAMP DEFAULT CURRENT\_TIMESTAMP, \-- Timestamp of the last update to this record  
    CONSTRAINT uk\_product\_batch\_location UNIQUE (product\_id, batch\_id, location\_id), \-- Ensures unique entry for product-batch-location  
    CONSTRAINT fk\_current\_stock\_product FOREIGN KEY (product\_id) REFERENCES products(product\_id),  
    CONSTRAINT fk\_current\_stock\_batch FOREIGN KEY (batch\_id) REFERENCES batches(batch\_id),  
    CONSTRAINT fk\_current\_stock\_location FOREIGN KEY (location\_id) REFERENCES locations(location\_id)  
);

\-- Table for Stock Movements  
\-- Logs every movement of stock between locations or out of the system (e.g., sales).  
CREATE TABLE stock\_movements (  
    movement\_id VARCHAR(50) PRIMARY KEY, \-- Unique identifier for each movement  
    product\_id VARCHAR(50) NOT NULL, \-- Foreign Key to products table  
    batch\_id VARCHAR(50) NOT NULL, \-- Foreign Key to batches table  
    movement\_date TIMESTAMP DEFAULT CURRENT\_TIMESTAMP, \-- Date and time of the movement  
    movement\_type VARCHAR(50) NOT NULL, \-- Type of movement ('Dispatch', 'Sale', 'Return', 'Adjustment\_In', 'Adjustment\_Out', 'Transfer')  
    source\_location\_id VARCHAR(50), \-- Foreign Key to locations (origin of stock, NULL for new production or returns from customer)  
    destination\_location\_id VARCHAR(50), \-- Foreign Key to locations (destination of stock, NULL for sales to customer)  
    quantity INT NOT NULL CHECK (quantity \> 0), \-- Quantity moved  
    agent\_id VARCHAR(50), \-- Foreign Key to agents (who handled the movement, if applicable)  
    remarks TEXT, \-- Any additional notes about the movement  
    CONSTRAINT fk\_movement\_product FOREIGN KEY (product\_id) REFERENCES products(product\_id),  
    CONSTRAINT fk\_movement\_batch FOREIGN KEY (batch\_id) REFERENCES batches(batch\_id),  
    CONSTRAINT fk\_movement\_source\_location FOREIGN KEY (source\_location\_id) REFERENCES locations(location\_id),  
    CONSTRAINT fk\_movement\_destination\_location FOREIGN KEY (destination\_location\_id) REFERENCES locations(location\_id),  
    CONSTRAINT fk\_movement\_agent FOREIGN KEY (agent\_id) REFERENCES agents(agent\_id)  
);

\-- Table for Retail Sales  
\-- Specifically records sales made at retail partner stores.  
\-- This can be populated via stock\_movements where movement\_type \= 'Sale' or directly from partner reports.  
CREATE TABLE retail\_sales (  
    sale\_id VARCHAR(50) PRIMARY KEY, \-- Unique identifier for each sale record  
    sale\_date DATE NOT NULL, \-- Date of the sale  
    store\_id VARCHAR(50) NOT NULL, \-- Foreign Key to retail\_partners (where the sale occurred)  
    product\_id VARCHAR(50) NOT NULL, \-- Foreign Key to products table  
    batch\_id VARCHAR(50), \-- Optional: Foreign Key to batches table, if batch-level sales tracking is available  
    quantity\_sold INT NOT NULL CHECK (quantity\_sold \> 0), \-- Quantity of product sold  
    sales\_agent\_id VARCHAR(50), \-- Foreign Key to agents (agent who recorded/verified this sale)  
    sale\_price\_per\_unit DECIMAL(10, 2), \-- Price per unit at which it was sold  
    remarks TEXT,  
    CONSTRAINT fk\_retail\_sale\_store FOREIGN KEY (store\_id) REFERENCES retail\_partners(store\_id),  
    CONSTRAINT fk\_retail\_sale\_product FOREIGN KEY (product\_id) REFERENCES products(product\_id),  
    CONSTRAINT fk\_retail\_sale\_batch FOREIGN KEY (batch\_id) REFERENCES batches(batch\_id),  
    CONSTRAINT fk\_retail\_sale\_agent FOREIGNem FOREIGN KEY (sales\_agent\_id) REFERENCES agents(agent\_id)  
);

**Explanation of the Schema (Updated):**

The expiry\_date column in the batches table is specifically designed to store the expiration date for each manufactured batch. This is paramount for managing perishable goods like food products. By recording this date, you can proactively identify products nearing their end-of-life.

### **SQL Queries to Identify About-to-Expire Products**

To identify products that are nearing their expiry date, you can query the current\_stock table joined with the batches table and locations table. You can define a "nearing expiry" threshold (e.g., products expiring within the next 30, 60, or 90 days).

Here are some example SQL queries:

**1\. Products About to Expire in the Next 30 Days (Across All Locations):**

This query will show you all stock (regardless of location) that is set to expire within the next 30 days from today's date.

SELECT  
    p.product\_name,  
    b.batch\_id,  
    b.expiry\_date,  
    cs.quantity AS current\_stock\_quantity,  
    l.location\_name,  
    l.location\_type  
FROM  
    current\_stock cs  
JOIN  
    products p ON cs.product\_id \= p.product\_id  
JOIN  
    batches b ON cs.batch\_id \= b.batch\_id  
JOIN  
    locations l ON cs.location\_id \= l.location\_id  
WHERE  
    b.expiry\_date IS NOT NULL  
    AND b.expiry\_date BETWEEN CURRENT\_DATE AND DATE('now', '+30 days') \-- For SQLite/PostgreSQL  
    \-- For MySQL: AND b.expiry\_date BETWEEN CURDATE() AND DATE\_ADD(CURDATE(), INTERVAL 30 DAY)  
    \-- For SQL Server: AND b.expiry\_date BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE())  
ORDER BY  
    b.expiry\_date ASC, p.product\_name, l.location\_name;

**2\. Products About to Expire at Your Main Warehouse:**

This query focuses specifically on stock at your central warehouse.

SELECT  
    p.product\_name,  
    b.batch\_id,  
    b.expiry\_date,  
    cs.quantity AS current\_stock\_quantity  
FROM  
    current\_stock cs  
JOIN  
    products p ON cs.product\_id \= p.product\_id  
JOIN  
    batches b ON cs.batch\_id \= b.batch\_id  
JOIN  
    locations l ON cs.location\_id \= l.location\_id  
WHERE  
    l.location\_type \= 'Warehouse' \-- Assuming 'Warehouse' is the type for your main unit  
    AND b.expiry\_date IS NOT NULL  
    AND b.expiry\_date BETWEEN CURRENT\_DATE AND DATE('now', '+60 days') \-- Adjust days as needed (e.g., 60 days)  
ORDER BY  
    b.expiry\_date ASC, p.product\_name;

**3\. Products About to Expire at Retail Store Partners:**

This query helps you see expiring stock specifically at your retail locations.

SELECT  
    p.product\_name,  
    rp.store\_name,  
    b.batch\_id,  
    b.expiry\_date,  
    cs.quantity AS current\_stock\_quantity  
FROM  
    current\_stock cs  
JOIN  
    products p ON cs.product\_id \= p.product\_id  
JOIN  
    batches b ON cs.batch\_id \= b.batch\_id  
JOIN  
    locations l ON cs.location\_id \= l.location\_id  
JOIN  
    retail\_partners rp ON l.location\_id \= rp.location\_id \-- Join to get store name easily  
WHERE  
    l.location\_type \= 'Retail Store' \-- Assuming 'Retail Store' is the type for your partners  
    AND b.expiry\_date IS NOT NULL  
    AND b.expiry\_date BETWEEN CURRENT\_DATE AND DATE('now', '+90 days') \-- Adjust days as needed (e.g., 90 days)  
ORDER BY  
    rp.store\_name, b.expiry\_date ASC, p.product\_name;

**Key Considerations for Implementation:**

* **Database Specific Date Functions:** Note the commented lines in the queries for different SQL dialects (SQLite/PostgreSQL, MySQL, SQL Server). Choose the one relevant to your database system.  
* **Defining "About to Expire":** The DATE('now', '+X days') part defines your threshold. You might want different thresholds for different product categories or for stock at your warehouse vs. retail stores.  
* **Automated Alerts:** In a real system, you would typically set up automated reports or alerts (e.g., daily emails) that run these queries and notify relevant personnel (e.g., sales agents, warehouse managers) about expiring stock.  
* **Proactive Measures:** Once identified, you can take action such as:  
  * **Promotions:** Offer discounts on products nearing expiry.  
  * **Returns/Transfers:** Arrange for returns from retail partners to your main warehouse if a large quantity is expiring and can be better managed centrally.  
  * **Prioritized Sales:** Instruct sales agents to push these products.  
  * **Donations/Disposal:** For products that cannot be sold, plan for appropriate disposal or donation before they become unsaleable.

By regularly running these queries and integrating them into your workflow, you can significantly reduce losses due to expired inventory.