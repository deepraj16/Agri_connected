import pymysql

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "1234"
DB_NAME = "agri_market"


# ---------------------------
# DB CONNECTION FUNCTIONS
# ---------------------------
def get_server_connection():
    """Connect to MySQL server without selecting database."""
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        autocommit=True
    )


def get_db_connection():
    """Connect to specific database."""
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        autocommit=True
    )


# ---------------------------
# CREATE DATABASE
# ---------------------------
def create_database():
    conn = get_server_connection()
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4;")
    print(f"Database `{DB_NAME}` created or already exists.")
    cursor.close()
    conn.close()


# ---------------------------
# TABLE CREATION QUERIES
# ---------------------------
TABLES = {}

TABLES['customers'] = """
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    username VARCHAR(100),
    phone VARCHAR(15),
    email VARCHAR(100),
    password VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
"""

TABLES['farmers'] = """
CREATE TABLE IF NOT EXISTS farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    username VARCHAR(100),
    phone VARCHAR(15),
    email VARCHAR(100),
    password VARCHAR(255),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
"""

TABLES['products'] = """
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT,
    name VARCHAR(200),
    description TEXT,
    price DECIMAL(10,2),
    quantity INT,
    image_url VARCHAR(255),
    status ENUM('available','out_of_stock') DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (farmer_id)
) ENGINE=InnoDB;
"""

TABLES['farmer_transactions'] = """
CREATE TABLE IF NOT EXISTS farmer_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT,
    product_id INT,
    product_name VARCHAR(255),
    payment_id VARCHAR(50),
    customer_id INT,
    quantity INT,
    total_amount DECIMAL(10,2),
    payment_status ENUM('pending','paid','failed') DEFAULT 'pending',
    order_status ENUM('processing','shipped','delivered','cancelled') DEFAULT 'processing',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (farmer_id),
    INDEX (product_id),
    INDEX (customer_id)
) ENGINE=InnoDB;
"""

TABLES['service_providers'] = """
CREATE TABLE IF NOT EXISTS service_providers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    username VARCHAR(100),
    phone VARCHAR(15),
    email VARCHAR(100),
    password VARCHAR(255),
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
"""

TABLES['services'] = """
CREATE TABLE IF NOT EXISTS services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_provider_id INT,
    service_name VARCHAR(200),
    service_type ENUM('Tractor Service','JCB Service','Labour Supply','Harvester','Tiller','Other'),
    price_per_hour DECIMAL(10,2),
    available TINYINT(1) DEFAULT 1,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (service_provider_id)
) ENGINE=InnoDB;
"""

TABLES['transactions'] = """
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_provider_id INT,
    customer_id INT,
    service_type VARCHAR(100),
    amount DECIMAL(10,2),
    description TEXT,
    status ENUM('pending','completed','cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (service_provider_id),
    INDEX (customer_id)
) ENGINE=InnoDB;
"""


# ---------------------------
# CREATE ALL TABLES
# ---------------------------
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    for table_name, ddl in TABLES.items():
        print(f"Creating table `{table_name}`... ", end="")
        cursor.execute(ddl)
        print("OK")

    cursor.close()
    conn.close()


# ---------------------------
# SAMPLE INSERT FUNCTIONS
# ---------------------------
def insert_customer(name, username, phone, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO customers (name, username, phone, email, password)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (name, username, phone, email, password))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return new_id


def insert_farmer(name, username, phone, email, password, address):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO farmers (name, username, phone, email, password, address)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (name, username, phone, email, password, address))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return new_id


# ---------------------------
# RUN EVERYTHING
# ---------------------------
def main():
    create_database()
    create_tables()

    # demo insertion
    cid = insert_customer("Ramesh", "ramesh123", "9999999999", "ramesh@gmail.com", "pass123")
    print("Inserted customer ID:", cid)


if __name__ == "__main__":
    main()
