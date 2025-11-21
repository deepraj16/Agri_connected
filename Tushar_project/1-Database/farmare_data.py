import pymysql

# -----------------------------------------------------------
# CONNECT TO MYSQL
# -----------------------------------------------------------
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="1234",
        database="agri",
        cursorclass=pymysql.cursors.DictCursor
    )

# -----------------------------------------------------------
# CREATE PRODUCTS TABLE
# -----------------------------------------------------------
def create_products_table():
    conn = get_connection()
    cursor = conn.cursor()

    product_table = """
    CREATE TABLE IF NOT EXISTS products (
        id INT AUTO_INCREMENT PRIMARY KEY,
        farmer_id INT NOT NULL,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        quantity INT NOT NULL,
        image_url VARCHAR(255),
        status ENUM('available','out_of_stock') DEFAULT 'available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
    );
    """

    cursor.execute(product_table)
    conn.commit()
    conn.close()
    print("Products table created successfully!")

# -----------------------------------------------------------
# INSERT PRODUCT DATA
# -----------------------------------------------------------
def insert_product(data_dict):
    conn = get_connection()
    cursor = conn.cursor()

    columns = ", ".join(data_dict.keys())
    values = ", ".join(["%s"] * len(data_dict))

    sql = f"INSERT INTO products ({columns}) VALUES ({values})"
    cursor.execute(sql, list(data_dict.values()))

    conn.commit()
    conn.close()
    print(f"Inserted product: {data_dict['name']}")

# -----------------------------------------------------------
# MAIN INSERTION
# -----------------------------------------------------------
if __name__ == "__main__":
    create_products_table()

    products = [
        # Farmer 1 Products
        {"farmer_id": 1, "name": "Basmati Rice", "description": "Premium long-grain rice", "price": 55, "quantity": 100, "image_url": "https://m.media-amazon.com/images/I/81PMcOadyML._AC_UF1000,1000_QL80_.jpg"},
         {"farmer_id": 3, "name": "Basmati Rice", "description": "Premium long-grain rice", "price": 55, "quantity": 100, "image_url": "https://m.media-amazon.com/images/I/81PMcOadyML._AC_UF1000,1000_QL80_.jpg"},
        {"farmer_id": 1, "name": "Wheat", "description": "Fresh milling wheat", "price": 35, "quantity": 120, "image_url": "https://m.media-amazon.com/images/I/71XGCHV2nOL.jpg"},
        {"farmer_id": 1, "name": "Maize", "description": "Organic yellow maize", "price": 28, "quantity": 90, "image_url": "https://m.media-amazon.com/images/I/71HkYQ7EzPL.jpg"},
        {"farmer_id": 2, "name": "Toor Dal", "description": "Premium arhar dal", "price": 110, "quantity": 60, "image_url": "https://m.media-amazon.com/images/I/61tJTxPTC9L.jpg"},

        # Farmer 2 Products
        {"farmer_id": 2, "name": "Onions", "description": "Fresh red onions", "price": 22, "quantity": 150, "image_url": "https://m.media-amazon.com/images/I/71H1I85usML.jpg"},
        {"farmer_id": 1, "name": "Potatoes", "description": "Organic potatoes", "price": 30, "quantity": 200, "image_url": "https://m.media-amazon.com/images/I/71GlgwGAsNL.jpg"},
        {"farmer_id": 2, "name": "Tomatoes", "description": "Fresh farm tomatoes", "price": 25, "quantity": 130, "image_url": "https://m.media-amazon.com/images/I/71MZQjCEVqL.jpg"},
        {"farmer_id": 2, "name": "Groundnuts", "description": "Raw peanuts from farm", "price": 85, "quantity": 70, "image_url": "https://m.media-amazon.com/images/I/71Qaz9s7II._AC_UF1000,1000_QL80_.jpg"},

        # Farmer 3 Products
        {"farmer_id": 3, "name": "Sugarcane", "description": "Fresh sugarcane sticks", "price": 15, "quantity": 80, "image_url": "https://m.media-amazon.com/images/I/71GS8gJtHjL.jpg"},
        {"farmer_id": 3, "name": "Barley", "description": "High-quality barley", "price": 45, "quantity": 100, "image_url": "https://m.media-amazon.com/images/I/81ppiV3Qubu.jpg"},
        {"farmer_id": 1, "name": "Mustard Seeds", "description": "Organic small mustard seeds", "price": 120, "quantity": 50, "image_url": "https://m.media-amazon.com/images/I/71EUsWz7QEL.jpg"},
        {"farmer_id": 3, "name": "Green Gram", "description": "Moong dal whole", "price": 90, "quantity": 70, "image_url": "https://m.media-amazon.com/images/I/71RnpmK9Y8L.jpg"},

        # Farmer 4 Products
        {"farmer_id": 5, "name": "Bananas", "description": "Fresh cavendish bananas", "price": 60, "quantity": 80, "image_url": "https://m.media-amazon.com/images/I/71X1V9V38eL.jpg"},
        {"farmer_id": 4, "name": "Mangoes", "description": "Alphonso mangoes", "price": 150, "quantity": 40, "image_url": "https://m.media-amazon.com/images/I/71TqKqRRGL.jpg"},
        {"farmer_id": 3, "name": "Pomegranates", "description": "Fresh ruby pomegranates", "price": 140, "quantity": 60, "image_url": "https://m.media-amazon.com/images/I/71g6j6uVCal.jpg"},
        {"farmer_id": 2, "name": "Carrots", "description": "Organic carrots", "price": 45, "quantity": 90, "image_url": "https://m.media-amazon.com/images/I/71cJJxaQmmL.jpg"},

        # Farmer 5 Products
        {"farmer_id": 5, "name": "Coconut", "description": "Fresh brown coconuts", "price": 35, "quantity": 100, "image_url": "https://m.media-amazon.com/images/I/71AqfspDAjL._AC_UF1000,1000_QL80_.jpg"},
        {"farmer_id": 1, "name": "Black Pepper", "description": "Premium whole pepper", "price": 550, "quantity": 25, "image_url": "https://m.media-amazon.com/images/I/71WZKx5ZNhL.jpg"},
        {"farmer_id": 5, "name": "Curry Leaves", "description": "Fresh aromatic leaves", "price": 20, "quantity": 200, "image_url": "https://m.media-amazon.com/images/I/71OxOXqAW0L.jpg"},
        {"farmer_id": 3, "name": "Turmeric", "description": "Organic raw turmeric", "price": 160, "quantity": 60, "image_url": "https://m.media-amazon.com/images/I/71WnzU++uCL.jpg"}
    ]

    # Insert all 20 products
    for p in products:
        p["status"] = "available"  # all in stock
        insert_product(p)

    print("All 20 products inserted successfully!")
