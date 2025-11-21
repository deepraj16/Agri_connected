from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import pymysql
from datetime import datetime
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="1234",
        database="agri",
        cursorclass=pymysql.cursors.DictCursor
    )

# -------------------- MODELS --------------------
class CustomerLogin(BaseModel):
    username: str
    password: str

class CustomerCreate(BaseModel):
    name: str
    username: str
    phone: str
    email: str
    password: str

class OrderCreate(BaseModel):
    customer_id: int
    product_id: int
    quantity: int
    total_price: float

class ServiceBookingCreate(BaseModel):
    customer_id: int
    service_id: int
    hours: int
    total_price: float
    booking_date: str

class PaymentUpdate(BaseModel):
    transaction_id: int
    payment_status: str
    transaction_type: str  # 'product' or 'service'

# -------------------- AUTH ENDPOINTS --------------------
@app.post("/api/customer/login")
def customer_login(credentials: CustomerLogin):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM customers WHERE username=%s AND password=%s",
        (credentials.username, credentials.password)
    )
    customer = cursor.fetchone()
    conn.close()
    
    if not customer:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "success": True,
        "customer_id": customer['id'],
        "name": customer['name'],
        "email": customer['email']
    }

@app.post("/api/customer/register")
def customer_register(customer: CustomerCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO customers (name, username, phone, email, password) 
               VALUES (%s, %s, %s, %s, %s)""",
            (customer.name, customer.username, customer.phone, customer.email, 
             customer.password)
        )
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        
        return {"success": True, "customer_id": customer_id, "message": "Account created successfully"}
    except pymysql.err.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username, phone or email already exists")

# ==================== PRODUCTS ENDPOINTS ====================
@app.get("/api/products")
def get_all_products(search: Optional[str] = None, status: Optional[str] = "available", conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT p.*, f.name as farmer_name, f.phone as farmer_phone
            FROM products p
            JOIN farmers f ON p.farmer_id = f.id
            WHERE p.status = %s
        """
        params = [status]
        
        if search:
            query += " AND (p.name LIKE %s OR p.description LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        query += " ORDER BY p.created_at DESC"
        
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        for product in products:
            if 'price' in product:
                product['price'] = float(product['price'])
        
        return products
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/api/products/{product_id}")
def get_product(product_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT p.*, f.name as farmer_name, f.phone as farmer_phone
            FROM products p
            JOIN farmers f ON p.farmer_id = f.id
            WHERE p.id = %s
        """
        cursor.execute(query, (product_id,))
        product = cursor.fetchone()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product['price'] = float(product['price'])
        return product
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

# ==================== SERVICES ENDPOINTS ====================
@app.get("/api/services")
def get_all_services(search: Optional[str] = None, service_type: Optional[str] = None, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT s.*, sp.name as provider_name, sp.phone as provider_phone
            FROM services s
            JOIN service_providers sp ON s.service_provider_id = sp.id
            WHERE s.available = 1
        """
        params = []
        
        if search:
            query += " AND (s.service_name LIKE %s OR s.description LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        if service_type:
            query += " AND s.service_type = %s"
            params.append(service_type)
        
        query += " ORDER BY s.created_at DESC"
        
        cursor.execute(query, params if params else None)
        services = cursor.fetchall()
        
        for service in services:
            if 'price_per_hour' in service:
                service['price_per_hour'] = float(service['price_per_hour'])
            if 'available' in service:
                service['available'] = bool(service['available'])
        
        return services
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/api/services/{service_id}")
def get_service(service_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT s.*, sp.name as provider_name, sp.phone as provider_phone
            FROM services s
            JOIN service_providers sp ON s.service_provider_id = sp.id
            WHERE s.id = %s
        """
        cursor.execute(query, (service_id,))
        service = cursor.fetchone()
        
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        service['price_per_hour'] = float(service['price_per_hour'])
        service['available'] = bool(service['available'])
        return service
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

# ==================== ORDERS ENDPOINTS (Using farmer_transactions) ====================
@app.post("/api/orders")
def create_order(order: OrderCreate, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        # Check product availability and get product details
        cursor.execute("""
            SELECT p.quantity, p.name, p.farmer_id 
            FROM products p 
            WHERE p.id = %s
        """, (order.product_id,))
        product = cursor.fetchone()
        
        if not product or product['quantity'] < order.quantity:
            raise HTTPException(status_code=400, detail="Insufficient product quantity")
        
        # Generate payment ID
        payment_id = f"PAY{random.randint(10000000, 99999999)}"
        
        # Create order in farmer_transactions table with 'pending' payment status
        cursor.execute(
            """INSERT INTO farmer_transactions 
               (farmer_id, product_id, product_name, payment_id, customer_id, quantity, 
                total_amount, payment_status, order_status, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', 'processing', NOW())""",
            (product['farmer_id'], order.product_id, product['name'], payment_id,
             order.customer_id, order.quantity, order.total_price)
        )
        
        # Update product quantity
        new_quantity = product['quantity'] - order.quantity
        cursor.execute(
            "UPDATE products SET quantity = %s WHERE id = %s",
            (new_quantity, order.product_id)
        )
        
        conn.commit()
        order_id = cursor.lastrowid
        
        return {
            "success": True, 
            "order_id": order_id, 
            "payment_id": payment_id,
            "message": "Order created successfully. Please complete payment."
        }
    except pymysql.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/api/orders/customer/{customer_id}")
def get_customer_orders(customer_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT ft.*, f.name as farmer_name, p.image_url
            FROM farmer_transactions ft
            JOIN farmers f ON ft.farmer_id = f.id
            LEFT JOIN products p ON ft.product_id = p.id
            WHERE ft.customer_id = %s
            ORDER BY ft.created_at DESC
        """
        cursor.execute(query, (customer_id,))
        orders = cursor.fetchall()
        
        # Transform to match frontend expectations
        transformed_orders = []
        for order in orders:
            transformed_orders.append({
                'id': order['id'],
                'product_name': order['product_name'],
                'farmer_name': order['farmer_name'],
                'quantity': order['quantity'],
                'total_price': float(order['total_amount']),
                'status': order['order_status'],
                'payment_status': order['payment_status'],
                'payment_id': order['payment_id'],
                'order_date': order['created_at'],
                'image_url': order.get('image_url')
            })
        
        return transformed_orders
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/api/orders/{order_id}")
def get_order_details(order_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT ft.*, f.name as farmer_name, f.phone as farmer_phone, p.image_url
            FROM farmer_transactions ft
            JOIN farmers f ON ft.farmer_id = f.id
            LEFT JOIN products p ON ft.product_id = p.id
            WHERE ft.id = %s
        """
        cursor.execute(query, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            'id': order['id'],
            'product_name': order['product_name'],
            'farmer_name': order['farmer_name'],
            'farmer_phone': order['farmer_phone'],
            'quantity': order['quantity'],
            'total_price': float(order['total_amount']),
            'status': order['order_status'],
            'payment_status': order['payment_status'],
            'payment_id': order['payment_id'],
            'order_date': order['created_at'],
            'image_url': order.get('image_url')
        }
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

# ==================== SERVICE BOOKINGS ENDPOINTS (Using transactions) ====================
@app.post("/api/service-bookings")
def create_service_booking(booking: ServiceBookingCreate, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        # Check service availability and get service details
        cursor.execute("""
            SELECT s.available, s.service_name, s.service_type, s.service_provider_id
            FROM services s 
            WHERE s.id = %s
        """, (booking.service_id,))
        service = cursor.fetchone()
        
        if not service or not service['available']:
            raise HTTPException(status_code=400, detail="Service not available")
        
        # Create booking in transactions table with 'pending' status
        description = f"{service['service_name']} - {booking.hours} hours on {booking.booking_date}"
        cursor.execute(
            """INSERT INTO transactions 
               (service_provider_id, customer_id, service_type, amount, description, 
                status, created_at, updated_at) 
               VALUES (%s, %s, %s, %s, %s, 'pending', NOW(), NOW())""",
            (service['service_provider_id'], booking.customer_id, service['service_type'],
             booking.total_price, description)
        )
        
        conn.commit()
        booking_id = cursor.lastrowid
        
        return {
            "success": True, 
            "booking_id": booking_id, 
            "message": "Service booking created. Please complete payment."
        }
    except pymysql.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/api/service-bookings/customer/{customer_id}")
def get_customer_bookings(customer_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT t.*, sp.name as provider_name
            FROM transactions t
            JOIN service_providers sp ON t.service_provider_id = sp.id
            WHERE t.customer_id = %s
            ORDER BY t.created_at DESC
        """
        cursor.execute(query, (customer_id,))
        bookings = cursor.fetchall()
        
        # Transform to match frontend expectations
        transformed_bookings = []
        for booking in bookings:
            # Extract hours and date from description if possible
            desc = booking['description']
            hours = 1  # Default
            booking_date = booking['created_at']
            
            # Try to parse hours from description
            if ' - ' in desc and ' hours' in desc:
                try:
                    hours_part = desc.split(' - ')[1].split(' hours')[0]
                    hours = int(hours_part)
                except:
                    pass
            
            transformed_bookings.append({
                'id': booking['id'],
                'service_name': desc.split(' - ')[0] if ' - ' in desc else booking['service_type'],
                'service_type': booking['service_type'],
                'provider_name': booking['provider_name'],
                'hours': hours,
                'total_price': float(booking['amount']),
                'status': booking['status'],
                'booking_date': booking_date
            })
        
        return transformed_bookings
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/api/service-bookings/{booking_id}")
def get_booking_details(booking_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT t.*, sp.name as provider_name, sp.phone as provider_phone
            FROM transactions t
            JOIN service_providers sp ON t.service_provider_id = sp.id
            WHERE t.id = %s
        """
        cursor.execute(query, (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        desc = booking['description']
        hours = 1
        
        if ' - ' in desc and ' hours' in desc:
            try:
                hours_part = desc.split(' - ')[1].split(' hours')[0]
                hours = int(hours_part)
            except:
                pass
        
        return {
            'id': booking['id'],
            'service_name': desc.split(' - ')[0] if ' - ' in desc else booking['service_type'],
            'service_type': booking['service_type'],
            'provider_name': booking['provider_name'],
            'provider_phone': booking['provider_phone'],
            'hours': hours,
            'total_price': float(booking['amount']),
            'status': booking['status'],
            'booking_date': booking['created_at'],
            'description': booking['description']
        }
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

# ==================== PAYMENT UPDATE ENDPOINTS ====================
@app.post("/api/payment/update")
def update_payment_status(payment: PaymentUpdate, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        if payment.transaction_type == 'product':
            # Update farmer_transactions
            cursor.execute(
                """UPDATE farmer_transactions 
                   SET payment_status = %s, order_status = %s, updated_at = NOW()
                   WHERE id = %s""",
                (payment.payment_status, 
                 'delivered' if payment.payment_status == 'paid' else 'processing',
                 payment.transaction_id)
            )
        elif payment.transaction_type == 'service':
            # Update transactions
            cursor.execute(
                """UPDATE transactions 
                   SET status = %s, updated_at = NOW()
                   WHERE id = %s""",
                ('completed' if payment.payment_status == 'paid' else 'pending',
                 payment.transaction_id)
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid transaction type")
        
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return {
            "success": True,
            "message": "Payment status updated successfully"
        }
    except pymysql.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)