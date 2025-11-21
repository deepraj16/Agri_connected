import pymysql
import random

# ---------------- CONNECTION ----------------
connection = pymysql.connect(
    host="localhost",
    user="root",
    password="1234",
    database="agri"
)

cursor = connection.cursor()

# ---------------- CREATE TABLES ----------------

orders_table = """
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_status ENUM('pending','paid','failed') DEFAULT 'pending',
    order_status ENUM('processing','shipped','delivered','cancelled') DEFAULT 'processing',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
"""

order_items_table = """
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
"""

cursor.execute(orders_table)
cursor.execute(order_items_table)
connection.commit()

print("Orders & Order Items tables created successfully!")

# ---------------- SAMPLE ORDER GENERATION ----------------

# assuming you already inserted customers (1–5)
# assuming products table has at least 10 products
cursor.execute("SELECT id, price FROM products")
product_data = cursor.fetchall()

if len(product_data) == 0:
    print("❌ No products found. Insert products first.")
    exit()

product_ids = [row[0] for row in product_data]
product_prices = {row[0]: float(row[1]) for row in product_data}

# ---------------- INSERT SAMPLE ORDERS ----------------

for order_no in range(1, 11):  # 10 sample orders
    customer_id = random.randint(1, 5)  # customers 1–5
    
    # choose some products for this order
    selected_products = random.sample(product_ids, random.randint(2, 4))
    
    order_total = 0
    order_items = []
    
    for pid in selected_products:
        qty = random.randint(1, 5)
        price = product_prices[pid]
        order_total += qty * price
        order_items.append((pid, qty, price))
    
    # Insert order
    cursor.execute(
        "INSERT INTO orders (customer_id, total_amount, payment_status, order_status) VALUES (%s, %s, %s, %s)",
        (customer_id, round(order_total, 2), 'paid', 'delivered')
    )
    
    order_id = cursor.lastrowid
    
    # Insert order_items
    for (pid, qty, price) in order_items:
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
            (order_id, pid, qty, price)
        )

connection.commit()

print("10 Sample orders with items inserted successfully!")

cursor.close()
connection.close()
