-- Schema extracted from sqlscema.md
-- Contains table definitions for Arivu Foods Inventory

CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    unit_of_measure VARCHAR(50) NOT NULL,
    standard_pack_size DECIMAL(10, 2) NOT NULL,
    mrp DECIMAL(10, 2)
);

CREATE TABLE locations (
    location_id VARCHAR(50) PRIMARY KEY,
    location_name VARCHAR(255) NOT NULL,
    location_type VARCHAR(50) NOT NULL,
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'India'
);

CREATE TABLE retail_partners (
    store_id VARCHAR(50) PRIMARY KEY,
    location_id VARCHAR(50) NOT NULL,
    store_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    contact_number VARCHAR(50),
    email VARCHAR(255),
    CONSTRAINT fk_retail_location FOREIGN KEY (location_id) REFERENCES locations(location_id)
);

CREATE TABLE agents (
    agent_id VARCHAR(50) PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    contact_number VARCHAR(50),
    email VARCHAR(255)
);

CREATE TABLE batches (
    batch_id VARCHAR(50) PRIMARY KEY,
    date_manufactured DATE NOT NULL,
    expiry_date DATE,
    remarks TEXT
);

-- New mapping table allowing multiple products per batch
CREATE TABLE batch_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    quantity_produced INT NOT NULL,
    CONSTRAINT fk_bp_batch FOREIGN KEY (batch_id) REFERENCES batches(batch_id),
    CONSTRAINT fk_bp_product FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE current_stock (
    stock_id VARCHAR(50) PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    batch_id VARCHAR(50) NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    quantity INT NOT NULL CHECK (quantity >= 0),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_product_batch_location UNIQUE (product_id, batch_id, location_id),
    CONSTRAINT fk_current_stock_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT fk_current_stock_batch FOREIGN KEY (batch_id) REFERENCES batches(batch_id),
    CONSTRAINT fk_current_stock_location FOREIGN KEY (location_id) REFERENCES locations(location_id)
);

CREATE TABLE stock_movements (
    movement_id VARCHAR(50) PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    batch_id VARCHAR(50) NOT NULL,
    movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    movement_type VARCHAR(50) NOT NULL,
    source_location_id VARCHAR(50),
    destination_location_id VARCHAR(50),
    quantity INT NOT NULL CHECK (quantity > 0),
    agent_id VARCHAR(50),
    remarks TEXT,
    CONSTRAINT fk_movement_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT fk_movement_batch FOREIGN KEY (batch_id) REFERENCES batches(batch_id),
    CONSTRAINT fk_movement_source_location FOREIGN KEY (source_location_id) REFERENCES locations(location_id),
    CONSTRAINT fk_movement_destination_location FOREIGN KEY (destination_location_id) REFERENCES locations(location_id),
    CONSTRAINT fk_movement_agent FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

CREATE TABLE retail_sales (
    sale_id VARCHAR(50) PRIMARY KEY,
    sale_date DATE NOT NULL,
    store_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    batch_id VARCHAR(50),
    quantity_sold INT NOT NULL CHECK (quantity_sold > 0),
    sales_agent_id VARCHAR(50),
    sale_price_per_unit DECIMAL(10, 2),
    remarks TEXT,
    CONSTRAINT fk_retail_sale_store FOREIGN KEY (store_id) REFERENCES retail_partners(store_id),
    CONSTRAINT fk_retail_sale_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT fk_retail_sale_batch FOREIGN KEY (batch_id) REFERENCES batches(batch_id),
    CONSTRAINT fk_retail_sale_agent FOREIGN KEY (sales_agent_id) REFERENCES agents(agent_id)
);

-- User accounts table for login management
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    store_id VARCHAR(50),
    CONSTRAINT fk_user_store FOREIGN KEY (store_id) REFERENCES locations(location_id)
);
