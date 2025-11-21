import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="1234",
        database="agri",
        cursorclass=pymysql.cursors.DictCursor
    )
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    farmer_table = """
    CREATE TABLE IF NOT EXISTS farmers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        username VARCHAR(100) UNIQUE,
        phone VARCHAR(15) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE,
        password VARCHAR(255) NOT NULL,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    customer_table = """
    CREATE TABLE IF NOT EXISTS customers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        username VARCHAR(100) UNIQUE,
        phone VARCHAR(15) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE,
        password VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    provider_table = """
    CREATE TABLE IF NOT EXISTS service_providers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        username VARCHAR(100) UNIQUE,
        phone VARCHAR(15) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE,
        password VARCHAR(255) NOT NULL,
        location VARCHAR(255),
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    cursor.execute(farmer_table)
    cursor.execute(customer_table)
    cursor.execute(provider_table)

    conn.commit()
    conn.close()
    print("Tables created successfully!")


def insert_data(table, data_dict):
    """
    table: table name (string)
    data_dict: {"column": "value", ... }
    """

    conn = get_connection()
    cursor = conn.cursor()

    columns = ", ".join(data_dict.keys())
    values = ", ".join(["%s"] * len(data_dict))

    sql = f"INSERT INTO {table} ({columns}) VALUES ({values})"

    cursor.execute(sql, list(data_dict.values()))
    conn.commit()
    conn.close()

    print("Inserted into", table)



def view_data(table):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()

    conn.close()
    return rows
create_tables()
def add_username_column():
    conn = get_connection()
    cursor = conn.cursor()

    queries = [
        "ALTER TABLE farmers ADD COLUMN username VARCHAR(100) UNIQUE AFTER name;",
        "ALTER TABLE customers ADD COLUMN username VARCHAR(100) UNIQUE AFTER name;",
        "ALTER TABLE service_providers ADD COLUMN username VARCHAR(100) UNIQUE AFTER name;"
    ]

    for q in queries:
        try:
            cursor.execute(q)
            print("Column added:", q)
        except Exception as e:
            print("Already exists or error:", e)

    conn.commit()
    conn.close()

def delete_all_data():
    conn = get_connection()
    cursor = conn.cursor()

    queries = [
        "DELETE FROM farmers;",
        "DELETE FROM customers;",
        "DELETE FROM service_providers;",
        "ALTER TABLE farmers AUTO_INCREMENT = 1;",
        "ALTER TABLE customers AUTO_INCREMENT = 1;",
        "ALTER TABLE service_providers AUTO_INCREMENT = 1;"
    ]

    for q in queries:
        cursor.execute(q)

    conn.commit()
    conn.close()
    print("All data deleted and auto_increment reset!")


providers = [
        {"name": "Vikram Chauhan", "username": "vikram_c", "phone": "9000000021", "email": "vikram@example.com", "password": "pass123", "location": "Hisar", "description": "Tractor service"},
        {"name": "Harish Naik", "username": "harish_n", "phone": "9000000022", "email": "harish@example.com", "password": "pass123", "location": "Belgaum", "description": "JCB service"},
        {"name": "Karan Deshmukh", "username": "karan_d", "phone": "9000000023", "email": "karan@example.com", "password": "pass123", "location": "Nagpur", "description": "Harvester service"},
        {"name": "Ravi Pillai", "username": "ravi_p", "phone": "9000000024", "email": "ravi@example.com", "password": "pass123", "location": "Kochi", "description": "Labour supply"},
        {"name": "Santosh Singh", "username": "santosh_s", "phone": "9000000025", "email": "santosh@example.com", "password": "pass123", "location": "Gorakhpur", "description": "Tractor with trailer"},
         {"name": "deepraj", "username": "deep27", "phone": "9511655600", "email": "deep@example.com", "password": "pass123", "location": "Gorakhpur", "description": "Tractor with trailer"}
    ]

for p in providers:
    insert_data("service_providers", p)

# insert_data("customers", {
#     "name": "Deepraj Sharma",
#     "username": "dee26",
#     "phone": "9511655600",
#     "email": "deep@example.com",
#     "password": "deep@123",
    
# })

# insert_data("customers", {
#     "name": "Rahul Sharma",
#     "username": "rahul_s",
#     "phone": "9000000011",
#     "email": "rahul.sharma@example.com",
#     "password": "rahul123"
# })

# insert_data("customers", {
#     "name": "Neha Verma",
#     "username": "neha_v",
#     "phone": "9000000012",
#     "email": "neha.verma@example.com",
#     "password": "neha123"
# })

# insert_data("customers", {
#     "name": "Amit Kumar",
#     "username": "amit_k",
#     "phone": "9000000013",
#     "email": "amit.kumar@example.com",
#     "password": "amit456"
# })

# insert_data("customers", {
#     "name": "Priya Reddy",
#     "username": "priya_r",
#     "phone": "9000000014",
#     "email": "priya.reddy@example.com",
#     "password": "priya444"
# })

# insert_data("customers", {
#     "name": "Arjun Mehta",
#     "username": "arjun_m",
#     "phone": "9000000015",
#     "email": "arjun.mehta@example.com",
#     "password": "arjun321"
# })


# insert_data("farmers", {
#     "name": "Ramesh Patil",
#     "username": "ramesh_p",
#     "phone": "9000000001",
#     "email": "ramesh.patil@example.com",
#     "password": "farmer123",
#     "address": "Nashik, Maharashtra"
# })

# insert_data("farmers", {
#     "name": "Suresh Jadhav",
#     "username": "suresh_j",
#     "phone": "9000000002",
#     "email": "suresh.jadhav@example.com",
#     "password": "pass456",
#     "address": "Kolhapur, Maharashtra"
# })

# insert_data("farmers", {
#     "name": "Mahendra Singh",
#     "username": "mahendra_s",
#     "phone": "9000000003",
#     "email": "mahendra.singh@example.com",
#     "password": "mahendra123",
#     "address": "Jaipur, Rajasthan"
# })

# insert_data("farmers", {
#     "name": "Prakash Yadav",
#     "username": "prakash_y",
#     "phone": "9000000004",
#     "email": "prakash.yadav@example.com",
#     "password": "prakash789",
#     "address": "Varanasi, Uttar Pradesh"
# })

# insert_data("farmers", {
#     "name": "Anand Gowda",
#     "username": "anand_g",
#     "phone": "9000000005",
#     "email": "anand.gowda@example.com",
#     "password": "gowda123",
#     "address": "Bengaluru, Karnataka"
# })

for f in view_data("customers"):
    print(f)



#if __name__ == "__main__":
    
    # Create all tables
    # create_tables()

   
    # insert_data("farmers", {
    #     "name": "Ramesh Sharma",
    #     "phone": "9999999999",
    #     "email": "ramesh@example.com",
    #     "password": "pass123",
    #     "address": "Village 1"
    # })

    # # Insert customer example
    # insert_data("customers", {
    #     "name": "Mahesh Kumar",
    #     "phone": "8888888888",
    #     "email": "mahesh@example.com",
    #     "password": "cust123"
    # })

    # # Insert service provider example
    # insert_data("service_providers", {
    #     "name": "Suresh Patel",
    #     "phone": "7777777777",
    #     "email": "suresh@example.com",
    #     "password": "prov123",
    #     "service_type": "tractor",
    #     "price_per_hour": 500,
    #     "location": "Village 2",
    #     "description": "Brand new tractor"
    # })


    # print("\nFarmers:")
    # for f in view_data("farmers"):
    #     print(f)

    # # View customers
    # print("\nCustomers:")
    # for c in view_data("customers"):
    #     print(c)

    # # View service providers
    # print("\nService Providers:")
    # for s in view_data("service_providers"):
    #     print(s)
