import pymysql
import random
import datetime

# ------------------ DB CONNECTION ------------------
connection = pymysql.connect(
    host="localhost",
    user="root",
    password="1234",
    database="agri",
    autocommit=True
)

cursor = connection.cursor()

# ------------------ CREATE TABLE ------------------
create_table = """
CREATE TABLE IF NOT EXISTS farmer_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    product_id INT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    payment_id VARCHAR(50) NOT NULL,
    customer_id INT NOT NULL,
    quantity INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_status ENUM('pending','paid','failed') DEFAULT 'paid',
    order_status ENUM('processing','shipped','delivered','cancelled') DEFAULT 'delivered',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
"""

cursor.execute(create_table)
print("✔ farmer_transactions table created successfully")


# ------------------ INSERT FUNCTION ------------------
def insert_transaction(farmer_id, product_id, customer_id, quantity):

    # Get product name and price
    cursor.execute("SELECT name, price FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        print(f"❌ Product ID {product_id} not found")
        return

    product_name = product[0]
    price = float(product[1])

    # Generate payment ID
    payment_id = "PAY" + str(random.randint(10000000, 99999999))

    # Calculate total amount
    total = price * quantity

    # Insert transaction
    sql = """
    INSERT INTO farmer_transactions
    (farmer_id, product_id, product_name, payment_id, customer_id, quantity, total_amount)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(sql, (
        farmer_id, product_id, product_name, payment_id,
        customer_id, quantity, total
    ))

    print(f"✔ Transaction added for product: {product_name}")


# ------------------ INSERT SAMPLE DATA ------------------

# Insert 10 sample transactions
sample_transactions = [
    (1, 1, 1, 5),
    (2, 2, 2, 3),
    (3, 3, 3, 8),
    (4, 4, 4, 2),
    (5, 5, 5, 6),
    (1, 6, 1, 4),
    (2, 7, 2, 7),
    (3, 8, 3, 1),
    (4, 9, 4, 10),
    (5, 10, 5, 9)
]

for t in sample_transactions:
    insert_transaction(*t)


# ------------------ FETCH AND DISPLAY ALL TRANSACTIONS ------------------
cursor.execute("SELECT * FROM farmer_transactions")
rows = cursor.fetchall()

print("\n=== ALL TRANSACTIONS ===")
for row in rows:
    print(row)
