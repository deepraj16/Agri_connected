from fastapi import FastAPI, Request, Depends, HTTPException, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import pymysql
from datetime import datetime, timedelta
import secrets
from email_service import EmailService

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Admin credentials
ADMIN_USERNAME = "admin26"
ADMIN_PASSWORD = "admin@123"

# Session storage
sessions = {}

# Database configuration - UPDATE THESE WITH YOUR CREDENTIALS
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',  # CHANGE THIS
    'database': 'agri_market',   # CHANGE THIS
    'cursorclass': pymysql.cursors.DictCursor
}

# Database connection
def get_db():
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        yield connection
    except pymysql.Error as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    finally:
        if connection:
            connection.close()

# Authentication functions
def create_session_token():
    return secrets.token_urlsafe(32)

def verify_session(session_token: Optional[str] = Cookie(None)):
    if not session_token or session_token not in sessions:
        return None
    session = sessions[session_token]
    if datetime.now() > session['expires']:
        del sessions[session_token]
        return None
    return session

# ==================== AUTHENTICATION ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session_token = create_session_token()
        sessions[session_token] = {
            'username': username,
            'expires': datetime.now() + timedelta(hours=24)
        }
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="session_token", value=session_token, httponly=True, max_age=86400)
        return response
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/logout")
async def logout(session_token: Optional[str] = Cookie(None)):
    if session_token and session_token in sessions:
        del sessions[session_token]
    response = RedirectResponse(url="/login")
    response.delete_cookie("session_token")
    return response

# ==================== DASHBOARD ROUTES ====================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, session=Depends(verify_session), conn=Depends(get_db)):
    if not session:
        return RedirectResponse(url="/login")
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) as total FROM farmer_transactions")
        total_orders = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as pending FROM farmer_transactions WHERE order_status = 'processing'")
        pending_orders = cursor.fetchone()['pending']
        
        cursor.execute("SELECT COUNT(*) as delivered FROM farmer_transactions WHERE order_status = 'delivered'")
        delivered_orders = cursor.fetchone()['delivered']
        
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as revenue FROM farmer_transactions WHERE payment_status = 'paid'")
        total_revenue = cursor.fetchone()['revenue']
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "delivered_orders": delivered_orders,
            "total_revenue": float(total_revenue)
        })
    except Exception as e:
        print(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request, session=Depends(verify_session)):
    if not session:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("orders.html", {"request": request})

@app.get("/orders/{order_id}", response_class=HTMLResponse)
async def order_details_page(request: Request, order_id: int, session=Depends(verify_session)):
    if not session:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("order_details.html", {"request": request, "order_id": order_id})

# ==================== API ENDPOINTS ====================

@app.get("/api/admin/orders")
async def get_all_orders(
    session=Depends(verify_session),
    status: Optional[str] = None,
    search: Optional[str] = None,
    conn=Depends(get_db)
):
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cursor = conn.cursor()
    try:
        query = """
            SELECT 
                ft.id,
                ft.farmer_id,
                ft.product_id,
                ft.product_name,
                ft.payment_id,
                ft.customer_id,
                ft.quantity,
                ft.total_amount,
                ft.payment_status,
                ft.order_status,
                ft.created_at,
                COALESCE(c.name, 'N/A') as customer_name,
                COALESCE(c.phone, 'N/A') as customer_phone,
                COALESCE(f.name, 'N/A') as farmer_name,
                COALESCE(f.phone, 'N/A') as farmer_phone
            FROM farmer_transactions ft
            LEFT JOIN customers c ON ft.customer_id = c.id
            LEFT JOIN farmers f ON ft.farmer_id = f.id
            WHERE 1=1
        """
        params = []
        
        if status and status in ['processing', 'shipped', 'delivered', 'cancelled']:
            query += " AND ft.order_status = %s"
            params.append(status)
        
        if search:
            query += " AND (ft.product_name LIKE %s OR c.name LIKE %s OR f.name LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY ft.created_at DESC"
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        orders = cursor.fetchall()
        
        result = []
        for order in orders:
            result.append({
                'id': order['id'],
                'farmer_id': order['farmer_id'],
                'product_id': order['product_id'],
                'product_name': order['product_name'],
                'payment_id': order['payment_id'],
                'customer_id': order['customer_id'],
                'quantity': order['quantity'],
                'total_amount': float(order['total_amount']) if order['total_amount'] else 0,
                'payment_status': order['payment_status'],
                'order_status': order['order_status'],
                'created_at': str(order['created_at']),
                'customer_name': order['customer_name'],
                'customer_phone': order['customer_phone'],
                'farmer_name': order['farmer_name'],
                'farmer_phone': order['farmer_phone']
            })
        
        return result
    except Exception as e:
        print(f"Error in get_all_orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/api/admin/orders/{order_id}")
async def get_order_detail(order_id: int, session=Depends(verify_session), conn=Depends(get_db)):
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cursor = conn.cursor()
    try:
        query = """
            SELECT 
                ft.id,
                ft.farmer_id,
                ft.product_id,
                ft.product_name,
                ft.payment_id,
                ft.customer_id,
                ft.quantity,
                ft.total_amount,
                ft.payment_status,
                ft.order_status,
                ft.created_at,
                COALESCE(c.name, 'N/A') as customer_name,
                COALESCE(c.username, 'N/A') as customer_username,
                COALESCE(c.phone, 'N/A') as customer_phone,
                COALESCE(c.email, 'N/A') as customer_email,
                COALESCE(f.name, 'N/A') as farmer_name,
                COALESCE(f.username, 'N/A') as farmer_username,
                COALESCE(f.phone, 'N/A') as farmer_phone,
                COALESCE(f.email, 'N/A') as farmer_email,
                COALESCE(f.address, 'N/A') as farmer_address
            FROM farmer_transactions ft
            LEFT JOIN customers c ON ft.customer_id = c.id
            LEFT JOIN farmers f ON ft.farmer_id = f.id
            WHERE ft.id = %s
        """
        cursor.execute(query, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order['total_amount'] = float(order['total_amount']) if order.get('total_amount') else 0
        
        return order
    except pymysql.Error as e:
        print(f"Database error in get_order_detail: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Error in get_order_detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.put("/api/admin/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    order_status: str = Form(...),
    send_email: bool = Form(False),
    session=Depends(verify_session),
    conn=Depends(get_db)
):
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cursor = conn.cursor()
    try:
        # Get order details before update
        cursor.execute("""
            SELECT ft.*, 
                   c.email as customer_email, 
                   c.name as customer_name
            FROM farmer_transactions ft
            LEFT JOIN customers c ON ft.customer_id = c.id
            WHERE ft.id = %s
        """, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        old_status = order['order_status']
        
        # Validate status
        valid_statuses = ['processing', 'shipped', 'delivered', 'cancelled']
        if order_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Update order status
        cursor.execute(
            "UPDATE farmer_transactions SET order_status = %s WHERE id = %s",
            (order_status, order_id)
        )
        conn.commit()
        
        # Send email if requested
        email_sent = False
        if send_email and order.get('customer_email') and order['customer_email'] != 'N/A':
            try:
                EmailService.send_status_update_to_customer(
                    customer_email=order['customer_email'],
                    customer_name=order.get('customer_name', 'Customer'),
                    order_id=order_id,
                    product_name=order['product_name'],
                    old_status=old_status,
                    new_status=order_status
                )
                email_sent = True
            except Exception as e:
                print(f"Email sending failed: {e}")
        
        return {
            "success": True, 
            "message": "Order status updated successfully",
            "email_sent": email_sent
        }
    except pymysql.Error as e:
        conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.put("/api/admin/orders/{order_id}/payment")
async def update_payment_status(
    order_id: int,
    payment_status: str = Form(...),
    send_email: bool = Form(False),
    session=Depends(verify_session),
    conn=Depends(get_db)
):
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cursor = conn.cursor()
    try:
        # Get order details
        cursor.execute("""
            SELECT ft.*, 
                   c.email as customer_email, 
                   c.name as customer_name
            FROM farmer_transactions ft
            LEFT JOIN customers c ON ft.customer_id = c.id
            WHERE ft.id = %s
        """, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Validate payment status
        valid_statuses = ['pending', 'paid', 'failed']
        if payment_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid payment status. Must be one of: {', '.join(valid_statuses)}")
        
        # Update payment status
        cursor.execute(
            "UPDATE farmer_transactions SET payment_status = %s WHERE id = %s",
            (payment_status, order_id)
        )
        conn.commit()
        
        # Send email if payment is confirmed
        email_sent = False
        if send_email and payment_status == 'paid' and order.get('customer_email') and order['customer_email'] != 'N/A':
            try:
                EmailService.send_payment_confirmation(
                    customer_email=order['customer_email'],
                    customer_name=order.get('customer_name', 'Customer'),
                    order_id=order_id,
                    amount=float(order['total_amount']),
                    payment_id=order['payment_id']
                )
                email_sent = True
            except Exception as e:
                print(f"Email sending failed: {e}")
        
        return {
            "success": True, 
            "message": "Payment status updated successfully",
            "email_sent": email_sent
        }
    except pymysql.Error as e:
        conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.post("/api/admin/orders/{order_id}/send-email")
async def send_order_email(
    order_id: int,
    email_type: str = Form(...),
    session=Depends(verify_session),
    conn=Depends(get_db)
):
    """Send specific email for order"""
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cursor = conn.cursor()
    try:
        # Get full order details
        cursor.execute("""
            SELECT 
                ft.*,
                c.email as customer_email,
                c.name as customer_name,
                c.phone as customer_phone,
                f.email as farmer_email,
                f.name as farmer_name
            FROM farmer_transactions ft
            LEFT JOIN customers c ON ft.customer_id = c.id
            LEFT JOIN farmers f ON ft.farmer_id = f.id
            WHERE ft.id = %s
        """, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        email_sent = False
        message = ""
        
        # Customer confirmation email
        if email_type == 'customer_confirmation':
            if order.get('customer_email') and order['customer_email'] != 'N/A':
                EmailService.send_order_confirmation_to_customer(
                    customer_email=order['customer_email'],
                    customer_name=order.get('customer_name', 'Customer'),
                    order_id=order_id,
                    product_name=order['product_name'],
                    quantity=order['quantity'],
                    total_amount=float(order['total_amount'])
                )
                email_sent = True
                message = f"Order confirmation sent to {order['customer_email']}"
            else:
                message = "Customer email not available"
        
        # Farmer notification email
        elif email_type == 'farmer_notification':
            if order.get('farmer_email') and order['farmer_email'] != 'N/A':
                EmailService.send_order_notification_to_farmer(
                    farmer_email=order['farmer_email'],
                    farmer_name=order.get('farmer_name', 'Farmer'),
                    order_id=order_id,
                    product_name=order['product_name'],
                    quantity=order['quantity'],
                    customer_name=order.get('customer_name', 'N/A'),
                    customer_phone=order.get('customer_phone', 'N/A')
                )
                email_sent = True
                message = f"Order notification sent to farmer {order['farmer_email']}"
            else:
                message = "Farmer email not available"
        
        # Status update email
        elif email_type == 'status_update':
            if order.get('customer_email') and order['customer_email'] != 'N/A':
                EmailService.send_status_update_to_customer(
                    customer_email=order['customer_email'],
                    customer_name=order.get('customer_name', 'Customer'),
                    order_id=order_id,
                    product_name=order['product_name'],
                    old_status='',
                    new_status=order['order_status']
                )
                email_sent = True
                message = f"Status update sent to {order['customer_email']}"
            else:
                message = "Customer email not available"
        
        # Payment confirmation email
        elif email_type == 'payment_confirmation':
            if order.get('customer_email') and order['customer_email'] != 'N/A':
                if order['payment_status'] == 'paid':
                    EmailService.send_payment_confirmation(
                        customer_email=order['customer_email'],
                        customer_name=order.get('customer_name', 'Customer'),
                        order_id=order_id,
                        amount=float(order['total_amount']),
                        payment_id=order['payment_id']
                    )
                    email_sent = True
                    message = f"Payment confirmation sent to {order['customer_email']}"
                else:
                    message = "Payment is not marked as paid yet"
            else:
                message = "Customer email not available"
        else:
            message = "Invalid email type"
        
        return {
            "success": email_sent,
            "message": message,
            "email_sent": email_sent
        }
        
    except Exception as e:
        print(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.delete("/api/admin/orders/{order_id}")
async def delete_order(order_id: int, session=Depends(verify_session), conn=Depends(get_db)):
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM farmer_transactions WHERE id = %s", (order_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {"success": True, "message": "Order deleted successfully"}
    except pymysql.Error as e:
        conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/api/admin/stats")
async def get_dashboard_stats(session=Depends(verify_session), conn=Depends(get_db)):
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                ft.id, 
                ft.product_name, 
                ft.order_status, 
                ft.created_at,
                COALESCE(c.name, 'N/A') as customer_name
            FROM farmer_transactions ft
            LEFT JOIN customers c ON ft.customer_id = c.id
            ORDER BY ft.created_at DESC
            LIMIT 5
        """)
        recent_orders = cursor.fetchall()
        
        cursor.execute("""
            SELECT order_status, COUNT(*) as count
            FROM farmer_transactions
            GROUP BY order_status
        """)
        status_distribution = cursor.fetchall()
        
        return {
            "recent_orders": recent_orders,
            "status_distribution": status_distribution
        }
    except Exception as e:
        print(f"Error in get_dashboard_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
