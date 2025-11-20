from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import pymysql
from datetime import datetime
import json
from pydantic import BaseModel
from typing import List, Tuple, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime
import random
from langchain_mistralai import ChatMistralAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def initialize_llm():
    """Initialize LLM with optimized settings"""
    return ChatOpenAI(
    model="mistralai/ministral-8b",
    temperature=0.7,
    max_tokens=512,
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
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
class FarmerLogin(BaseModel):
    username: str
    password: str

class FarmerCreate(BaseModel):
    name: str
    username: str
    phone: str
    email: str
    password: str
    address: Optional[str] = None

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    quantity: int
    image_url: Optional[str] = None
    status: str = "available"

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    image_url: Optional[str] = None
    status: Optional[str] = None

# -------------------- AUTH ENDPOINTS --------------------
@app.post("/api/farmer/login")
def farmer_login(credentials: FarmerLogin):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM farmers WHERE username=%s AND password=%s",
        (credentials.username, credentials.password)
    )
    farmer = cursor.fetchone()
    conn.close()
    
    if not farmer:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "success": True,
        "farmer_id": farmer['id'],
        "name": farmer['name'],
        "email": farmer['email']
    }

@app.post("/api/farmer/register")
def farmer_register(farmer: FarmerCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO farmers (name, username, phone, email, password, address) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (farmer.name, farmer.username, farmer.phone, farmer.email, 
             farmer.password, farmer.address)
        )
        conn.commit()
        farmer_id = cursor.lastrowid
        conn.close()
        
        return {"success": True, "farmer_id": farmer_id, "message": "Account created successfully"}
    except pymysql.err.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username, phone or email already exists")

# -------------------- PRODUCT CRUD --------------------
@app.get("/api/farmer/{farmer_id}/products")
def get_farmer_products(farmer_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products WHERE farmer_id=%s ORDER BY created_at DESC", (farmer_id,))
    products = cursor.fetchall()
    conn.close()
    
    return {"products": products}

@app.post("/api/farmer/{farmer_id}/products")
def create_product(farmer_id: int, product: ProductCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        """INSERT INTO products (farmer_id, name, description, price, quantity, image_url, status) 
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (farmer_id, product.name, product.description, product.price, 
         product.quantity, product.image_url, product.status)
    )
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    
    return {"success": True, "product_id": product_id, "message": "Product added successfully"}

@app.put("/api/farmer/{farmer_id}/products/{product_id}")
def update_product(farmer_id: int, product_id: int, product: ProductUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products WHERE id=%s AND farmer_id=%s", (product_id, farmer_id))
    existing = cursor.fetchone()
    
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
    
    updates = []
    values = []
    
    if product.name: 
        updates.append("name=%s")
        values.append(product.name)
    if product.description is not None: 
        updates.append("description=%s")
        values.append(product.description)
    if product.price: 
        updates.append("price=%s")
        values.append(product.price)
    if product.quantity is not None: 
        updates.append("quantity=%s")
        values.append(product.quantity)
    if product.image_url is not None: 
        updates.append("image_url=%s")
        values.append(product.image_url)
    if product.status: 
        updates.append("status=%s")
        values.append(product.status)
    
    if updates:
        values.append(product_id)
        values.append(farmer_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE id=%s AND farmer_id=%s"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    return {"success": True, "message": "Product updated successfully"}

@app.delete("/api/farmer/{farmer_id}/products/{product_id}")
def delete_product(farmer_id: int, product_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM products WHERE id=%s AND farmer_id=%s", (product_id, farmer_id))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Product deleted successfully"}

# -------------------- TRANSACTION/ORDER ENDPOINTS --------------------
@app.get("/api/farmer/{farmer_id}/transactions")
def get_farmer_transactions(farmer_id: int):
    """Get all transactions for a farmer"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.*,
            c.name as customer_name,
            c.phone as customer_phone,
            c.email as customer_email
        FROM farmer_transactions t
        LEFT JOIN customers c ON t.customer_id = c.id
        WHERE t.farmer_id = %s
        ORDER BY t.created_at DESC
    """, (farmer_id,))
    
    transactions = cursor.fetchall()
    conn.close()
    
    return {"transactions": transactions}

@app.get("/api/farmer/{farmer_id}/orders")
def get_farmer_orders(farmer_id: int):
    """Get all orders for a farmer (alias for transactions)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.id as order_id,
            t.payment_id,
            t.product_name as items,
            t.quantity,
            t.total_amount,
            t.payment_status,
            t.order_status,
            t.created_at,
            c.name as customer_name,
            c.phone as customer_phone,
            c.email as customer_email
        FROM farmer_transactions t
        LEFT JOIN customers c ON t.customer_id = c.id
        WHERE t.farmer_id = %s
        ORDER BY t.created_at DESC
    """, (farmer_id,))
    
    orders = cursor.fetchall()
    conn.close()
    
    return {"orders": orders}

@app.get("/api/farmer/{farmer_id}/stats")
def get_farmer_stats(farmer_id: int):
    """Get dashboard statistics for farmer"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total products
    cursor.execute("SELECT COUNT(*) as count FROM products WHERE farmer_id=%s", (farmer_id,))
    total_products = cursor.fetchone()['count']
    
    # Total orders
    cursor.execute("SELECT COUNT(*) as count FROM farmer_transactions WHERE farmer_id=%s", (farmer_id,))
    total_orders = cursor.fetchone()['count']
    
    # Total revenue (only from paid transactions)
    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) as revenue 
        FROM farmer_transactions 
        WHERE farmer_id=%s AND payment_status='paid'
    """, (farmer_id,))
    total_revenue = float(cursor.fetchone()['revenue'])
    
    conn.close()
    
    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue
    }

@app.get("/api/farmer/{farmer_id}/transactions/{transaction_id}")
def get_transaction_details(farmer_id: int, transaction_id: int):
    """Get details of a specific transaction"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.*,
            c.name as customer_name,
            c.phone as customer_phone,
            c.email as customer_email,
            c.username as customer_username,
            p.name as product_name_full,
            p.description as product_description,
            p.image_url as product_image
        FROM farmer_transactions t
        LEFT JOIN customers c ON t.customer_id = c.id
        LEFT JOIN products p ON t.product_id = p.id
        WHERE t.id = %s AND t.farmer_id = %s
    """, (transaction_id, farmer_id))
    
    transaction = cursor.fetchone()
    conn.close()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"transaction": transaction}

@app.get("/api/farmer/{farmer_id}/report")
def get_sales_report(farmer_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get sales report with optional date filtering"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            DATE(created_at) as sale_date,
            product_name,
            COUNT(*) as total_orders,
            SUM(quantity) as total_quantity,
            SUM(total_amount) as total_revenue
        FROM farmer_transactions
        WHERE farmer_id = %s AND payment_status = 'paid'
    """
    params = [farmer_id]
    
    if start_date:
        query += " AND created_at >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND created_at <= %s"
        params.append(end_date)
    
    query += " GROUP BY DATE(created_at), product_name ORDER BY sale_date DESC"
    
    cursor.execute(query, params)
    daily_sales = cursor.fetchall()
    
    # Get summary statistics
    summary_query = """
        SELECT 
            COUNT(*) as total_transactions,
            SUM(quantity) as total_items_sold,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_order_value
        FROM farmer_transactions
        WHERE farmer_id = %s AND payment_status = 'paid'
    """
    summary_params = [farmer_id]
    
    if start_date:
        summary_query += " AND created_at >= %s"
        summary_params.append(start_date)
    
    if end_date:
        summary_query += " AND created_at <= %s"
        summary_params.append(end_date)
    
    cursor.execute(summary_query, summary_params)
    summary = cursor.fetchone()
    
    # Get top products
    cursor.execute("""
        SELECT 
            product_name,
            COUNT(*) as order_count,
            SUM(quantity) as total_quantity,
            SUM(total_amount) as total_revenue
        FROM farmer_transactions
        WHERE farmer_id = %s AND payment_status = 'paid'
        GROUP BY product_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """, (farmer_id,))
    
    top_products = cursor.fetchall()
    
    conn.close()
    
    return {
        "daily_sales": daily_sales,
        "summary": {
            "total_transactions": summary['total_transactions'] or 0,
            "total_items_sold": int(summary['total_items_sold'] or 0),
            "total_revenue": float(summary['total_revenue'] or 0),
            "avg_order_value": float(summary['avg_order_value'] or 0)
        },
        "top_products": top_products
    }

@app.get("/api/farmer/{farmer_id}/ai-report")
async def get_ai_sales_analysis(farmer_id: int):
    """Generate AI-powered sales analysis and insights"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get comprehensive sales data
        cursor.execute("""
            SELECT 
                product_name,
                COUNT(*) as order_count,
                SUM(quantity) as total_quantity,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_order_value
            FROM farmer_transactions
            WHERE farmer_id = %s AND payment_status = 'paid'
            GROUP BY product_name
            ORDER BY total_revenue DESC
        """, (farmer_id,))
        product_stats = cursor.fetchall()
        
        # Get time-based trends (last 30 days)
        cursor.execute("""
            SELECT 
                DATE(created_at) as sale_date,
                COUNT(*) as orders,
                SUM(total_amount) as revenue
            FROM farmer_transactions
            WHERE farmer_id = %s 
                AND payment_status = 'paid'
                AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(created_at)
            ORDER BY sale_date DESC
        """, (farmer_id,))
        recent_trends = cursor.fetchall()
        
        # Get overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_order_value,
                MIN(created_at) as first_sale,
                MAX(created_at) as last_sale
            FROM farmer_transactions
            WHERE farmer_id = %s AND payment_status = 'paid'
        """, (farmer_id,))
        overall_stats = cursor.fetchone()
        
        conn.close()
        
        # Prepare data for LLM
        sales_summary = {
            "total_orders": overall_stats['total_orders'],
            "total_revenue": float(overall_stats['total_revenue'] or 0),
            "avg_order_value": float(overall_stats['avg_order_value'] or 0),
            "products": [
                {
                    "name": p['product_name'],
                    "orders": p['order_count'],
                    "quantity_sold": int(p['total_quantity']),
                    "revenue": float(p['total_revenue'])
                }
                for p in product_stats[:10]  # Top 10 products
            ],
            "recent_performance": [
                {
                    "date": str(t['sale_date']),
                    "orders": t['orders'],
                    "revenue": float(t['revenue'])
                }
                for t in recent_trends[:7]  # Last 7 days
            ]
        }
        
        # Generate AI analysis
        llm = initialize_llm()
        
        prompt = f"""You are an agricultural business analyst. Analyze the following sales data and provide actionable insights.

Sales Data:
- Total Orders: {sales_summary['total_orders']}
- Total Revenue: ₹{sales_summary['total_revenue']:.2f}
- Average Order Value: ₹{sales_summary['avg_order_value']:.2f}

Top Products:
{chr(10).join([f"- {p['name']}: {p['orders']} orders, {p['quantity_sold']} units, ₹{p['revenue']:.2f} revenue" for p in sales_summary['products']])}

Recent 7-Day Performance:
{chr(10).join([f"- {p['date']}: {p['orders']} orders, ₹{p['revenue']:.2f}" for p in sales_summary['recent_performance']])}

Provide a comprehensive analysis including:
1. Overall Performance Summary (2-3 sentences)
2. Top Performing Products Analysis
3. Sales Trends & Patterns
4. Actionable Recommendations (at least 3 specific suggestions)
5. Potential Risks or Concerns

Keep the analysis practical, data-driven, and focused on helping the farmer improve their business."""

        response = llm.invoke([HumanMessage(content=prompt)])
        ai_analysis = response.content
        
        return {
            "success": True,
            "analysis": ai_analysis,
            "data_summary": sales_summary
        }
        
    except Exception as e:
        conn.close()
        return {
            "success": False,
            "error": str(e),
            "analysis": "Unable to generate AI analysis at this time. Please try again later."
        }



# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
commodity_dict = {
    "arhar": "static/Arhar.csv",
    "bajra": "static/Bajra.csv",
    "barley": "static/Barley.csv",
    "copra": "static/Copra.csv",
    "cotton": "static/Cotton.csv",
    "sesamum": "static/Sesamum.csv",
    "gram": "static/Gram.csv",
    "groundnut": "static/Groundnut.csv",
    "jowar": "static/Jowar.csv",
    "maize": "static/Maize.csv",
    "masoor": "static/Masoor.csv",
    "moong": "static/Moong.csv",
    "niger": "static/Niger.csv",
    "paddy": "static/Paddy.csv",
    "ragi": "static/Ragi.csv",
    "rape": "static/Rape.csv",
    "jute": "static/Jute.csv",
    "safflower": "static/Safflower.csv",
    "soyabean": "static/Soyabean.csv",
    "sugarcane": "static/Sugarcane.csv",
    "sunflower": "static/Sunflower.csv",
    "urad": "static/Urad.csv",
    "wheat": "static/Wheat.csv"
}

annual_rainfall = [29, 21, 37.5, 30.7, 52.6, 150, 299, 251.7, 179.2, 70.5, 39.8, 10.9]

base = {
    "Paddy": 1245.5,
    "Arhar": 3200,
    "Bajra": 1175,
    "Barley": 980,
    "Copra": 5100,
    "Cotton": 3600,
    "Sesamum": 4200,
    "Gram": 2800,
    "Groundnut": 3700,
    "Jowar": 1520,
    "Maize": 1175,
    "Masoor": 2800,
    "Moong": 3500,
    "Niger": 3500,
    "Ragi": 1500,
    "Rape": 2500,
    "Jute": 1675,
    "Safflower": 2500,
    "Soyabean": 2200,
    "Sugarcane": 2250,
    "Sunflower": 3700,
    "Urad": 4300,
    "Wheat": 1350
}

commodity_list = []

# Crop metadata
crop_metadata = {
    "paddy": {
        "image_url": "https://img.icons8.com/color/96/000000/rice-bowl.png",
        "prime_loc": "West Bengal, Punjab",
        "type_c": "Kharif",
        "export": "Basmati Rice"
    },
    "wheat": {
        "image_url": "https://img.icons8.com/color/96/000000/wheat.png",
        "prime_loc": "Punjab, Haryana",
        "type_c": "Rabi",
        "export": "Wheat Flour"
    },
    "cotton": {
        "image_url": "https://img.icons8.com/color/96/000000/cotton.png",
        "prime_loc": "Gujarat, Maharashtra",
        "type_c": "Kharif",
        "export": "Cotton Fiber"
    }
    # Add more crop metadata as needed
}


class Commodity:
    def __init__(self, csv_name):
        self.name = csv_name
        dataset = pd.read_csv(csv_name)
        self.X = dataset.iloc[:, :-1].values
        self.Y = dataset.iloc[:, 3].values

        from sklearn.tree import DecisionTreeRegressor
        depth = random.randrange(7, 18)
        self.regressor = DecisionTreeRegressor(max_depth=depth)
        self.regressor.fit(self.X, self.Y)

    def getPredictedValue(self, value):
        if value[1] >= 2019:
            fsa = np.array(value).reshape(1, 3)
            return self.regressor.predict(fsa)[0]
        else:
            c = self.X[:, 0:2]
            x = []
            for i in c:
                x.append(i.tolist())
            fsa = [value[0], value[1]]
            ind = 0
            for i in range(0, len(x)):
                if x[i] == fsa:
                    ind = i
                    break
            return self.Y[i]

    def getCropName(self):
        a = self.name.split('.')
        return a[0]

    def __str__(self):
        return self.getCropName().split('/')[-1].lower()


# Response Models
class CropPrice(BaseModel):
    name: str
    price: float
    change: float


class ForecastItem(BaseModel):
    month: str
    price: float
    change: float


class CropProfile(BaseModel):
    name: str
    current_price: float
    max_crop: List[Any]
    min_crop: List[Any]
    forecast_values: List[List[Any]]
    previous_values: List[List[Any]]
    image_url: str
    prime_loc: str
    type_c: str
    export: str


class DashboardData(BaseModel):
    top5: List[List[Any]]
    bottom5: List[List[Any]]
    sixmonths: List[List[Any]]


# Helper Functions
def get_commodity_by_name(name: str):
    name = name.lower()
    for commodity in commodity_list:
        if name == str(commodity):
            return commodity
    raise HTTPException(status_code=404, detail=f"Commodity '{name}' not found")


def TopFiveWinners():
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_rainfall = annual_rainfall[current_month - 1]
    prev_month = current_month - 1
    prev_rainfall = annual_rainfall[prev_month - 1]
    current_month_prediction = []
    prev_month_prediction = []
    change = []

    for i in commodity_list:
        current_predict = i.getPredictedValue([float(current_month), current_year, current_rainfall])
        current_month_prediction.append(current_predict)
        prev_predict = i.getPredictedValue([float(prev_month), current_year, prev_rainfall])
        prev_month_prediction.append(prev_predict)
        change.append((((current_predict - prev_predict) * 100 / prev_predict), commodity_list.index(i)))
    
    sorted_change = sorted(change, reverse=True)
    to_send = []
    for j in range(0, 5):
        perc, i = sorted_change[j]
        name = commodity_list[i].getCropName().split('/')[1]
        to_send.append([name, round((current_month_prediction[i] * base[name]) / 100, 2), round(perc, 2)])
    
    return to_send


def TopFiveLosers():
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_rainfall = annual_rainfall[current_month - 1]
    prev_month = current_month - 1
    prev_rainfall = annual_rainfall[prev_month - 1]
    current_month_prediction = []
    prev_month_prediction = []
    change = []

    for i in commodity_list:
        current_predict = i.getPredictedValue([float(current_month), current_year, current_rainfall])
        current_month_prediction.append(current_predict)
        prev_predict = i.getPredictedValue([float(prev_month), current_year, prev_rainfall])
        prev_month_prediction.append(prev_predict)
        change.append((((current_predict - prev_predict) * 100 / prev_predict), commodity_list.index(i)))
    
    sorted_change = sorted(change)
    to_send = []
    for j in range(0, 5):
        perc, i = sorted_change[j]
        name = commodity_list[i].getCropName().split('/')[1]
        to_send.append([name, round((current_month_prediction[i] * base[name]) / 100, 2), round(perc, 2)])
    
    return to_send


def SixMonthsForecast():
    month1, month2, month3, month4, month5, month6 = [], [], [], [], [], []
    
    for i in commodity_list:
        crop = SixMonthsForecastHelper(i.getCropName())
        k = 0
        for j in crop:
            time = j[0]
            price = j[1]
            change = j[2]
            if k == 0:
                month1.append((price, change, i.getCropName().split("/")[1], time))
            elif k == 1:
                month2.append((price, change, i.getCropName().split("/")[1], time))
            elif k == 2:
                month3.append((price, change, i.getCropName().split("/")[1], time))
            elif k == 3:
                month4.append((price, change, i.getCropName().split("/")[1], time))
            elif k == 4:
                month5.append((price, change, i.getCropName().split("/")[1], time))
            elif k == 5:
                month6.append((price, change, i.getCropName().split("/")[1], time))
            k += 1
    
    month1.sort()
    month2.sort()
    month3.sort()
    month4.sort()
    month5.sort()
    month6.sort()
    
    crop_month_wise = []
    for month in [month1, month2, month3, month4, month5, month6]:
        crop_month_wise.append([
            month[0][3], month[len(month)-1][2], month[len(month)-1][0], 
            month[len(month)-1][1], month[0][2], month[0][0], month[0][1]
        ])
    
    return crop_month_wise


def SixMonthsForecastHelper(name):
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_rainfall = annual_rainfall[current_month - 1]
    name_lower = name.split("/")[1].lower()
    
    commodity = get_commodity_by_name(name_lower)
    
    month_with_year = []
    for i in range(1, 7):
        if current_month + i <= 12:
            month_with_year.append((current_month + i, current_year, annual_rainfall[current_month + i - 1]))
        else:
            month_with_year.append((current_month + i - 12, current_year + 1, annual_rainfall[current_month + i - 13]))
    
    wpis = []
    current_wpi = commodity.getPredictedValue([float(current_month), current_year, current_rainfall])
    change = []

    for m, y, r in month_with_year:
        current_predict = commodity.getPredictedValue([float(m), y, r])
        wpis.append(current_predict)
        change.append(((current_predict - current_wpi) * 100) / current_wpi)

    crop_price = []
    for i in range(0, len(wpis)):
        m, y, r = month_with_year[i]
        x = datetime(y, m, 1)
        x = x.strftime("%b %y")
        crop_price.append([x, round((wpis[i] * base[name_lower.capitalize()]) / 100, 2), round(change[i], 2)])

    return crop_price


def CurrentMonth(name):
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_rainfall = annual_rainfall[current_month - 1]
    
    commodity = get_commodity_by_name(name.lower())
    current_wpi = commodity.getPredictedValue([float(current_month), current_year, current_rainfall])
    current_price = (base[name.capitalize()] * current_wpi) / 100
    
    return current_price


def TwelveMonthsForecast(name):
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    commodity = get_commodity_by_name(name.lower())
    
    month_with_year = []
    for i in range(1, 13):
        if current_month + i <= 12:
            month_with_year.append((current_month + i, current_year, annual_rainfall[current_month + i - 1]))
        else:
            month_with_year.append((current_month + i - 12, current_year + 1, annual_rainfall[current_month + i - 13]))
    
    max_index = 0
    min_index = 0
    max_value = 0
    min_value = 9999
    wpis = []
    current_wpi = commodity.getPredictedValue([float(current_month), current_year, annual_rainfall[current_month - 1]])
    change = []

    for m, y, r in month_with_year:
        current_predict = commodity.getPredictedValue([float(m), y, r])
        if current_predict > max_value:
            max_value = current_predict
            max_index = month_with_year.index((m, y, r))
        if current_predict < min_value:
            min_value = current_predict
            min_index = month_with_year.index((m, y, r))
        wpis.append(current_predict)
        change.append(((current_predict - current_wpi) * 100) / current_wpi)

    max_month, max_year, r1 = month_with_year[max_index]
    min_month, min_year, r2 = month_with_year[min_index]
    min_value = min_value * base[name.capitalize()] / 100
    max_value = max_value * base[name.capitalize()] / 100
    
    crop_price = []
    for i in range(0, len(wpis)):
        m, y, r = month_with_year[i]
        x = datetime(y, m, 1)
        x = x.strftime("%b %y")
        crop_price.append([x, round((wpis[i] * base[name.capitalize()]) / 100, 2), round(change[i], 2)])
    
    x = datetime(max_year, max_month, 1)
    x = x.strftime("%b %y")
    max_crop = [x, round(max_value, 2)]
    
    x = datetime(min_year, min_month, 1)
    x = x.strftime("%b %y")
    min_crop = [x, round(min_value, 2)]

    return max_crop, min_crop, crop_price


def TwelveMonthPrevious(name):
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    commodity = get_commodity_by_name(name.lower())
    
    wpis = []
    crop_price = []
    
    month_with_year = []
    for i in range(1, 13):
        if current_month - i >= 1:
            month_with_year.append((current_month - i, current_year, annual_rainfall[current_month - i - 1]))
        else:
            month_with_year.append((current_month - i + 12, current_year - 1, annual_rainfall[current_month - i + 11]))

    for m, y, r in month_with_year:
        current_predict = commodity.getPredictedValue([float(m), 2013, r])
        wpis.append(current_predict)

    for i in range(0, len(wpis)):
        m, y, r = month_with_year[i]
        x = datetime(y, m, 1)
        x = x.strftime("%b %y")
        crop_price.append([x, round((wpis[i] * base[name.capitalize()]) / 100, 2)])
    
    new_crop_price = []
    for i in range(len(crop_price) - 1, -1, -1):
        new_crop_price.append(crop_price[i])
    
    return new_crop_price


# API Endpoints
@app.get("/new_work")
async def root():
    return {
        "message": "Apna Anaaj API",
        "version": "1.0.0",
        "endpoints": {
            "dashboard": "/api/dashboard",
            "commodity_profile": "/api/commodity/{name}",
            "ticker": "/api/ticker/{item}/{number}",
            "commodities_list": "/api/commodities"
        }
    }


@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard():
    """Get dashboard data with top gainers, losers, and 6-month forecast"""
    return {
        "top5": TopFiveWinners(),
        "bottom5": TopFiveLosers(),
        "sixmonths": SixMonthsForecast()
    }


@app.get("/api/commodity/{name}")
async def get_commodity_profile(name: str):
    """Get detailed profile for a specific commodity"""
    try:
        max_crop, min_crop, forecast_crop_values = TwelveMonthsForecast(name)
        prev_crop_values = TwelveMonthPrevious(name)
        current_price = CurrentMonth(name)
        
        forecast_x = [i[0] for i in forecast_crop_values]
        forecast_y = [i[1] for i in forecast_crop_values]
        previous_x = [i[0] for i in prev_crop_values]
        previous_y = [i[1] for i in prev_crop_values]
        
        # Get crop metadata or use defaults
        metadata = crop_metadata.get(name.lower(), {
            "image_url": "https://img.icons8.com/color/96/000000/potato.png",
            "prime_loc": "Various States",
            "type_c": "Seasonal",
            "export": "Various Products"
        })
        
        return {
            "name": name,
            "max_crop": max_crop,
            "min_crop": min_crop,
            "forecast_values": forecast_crop_values,
            "forecast_x": forecast_x,
            "forecast_y": forecast_y,
            "previous_values": prev_crop_values,
            "previous_x": previous_x,
            "previous_y": previous_y,
            "current_price": round(current_price, 2),
            **metadata
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/ticker/{item}/{number}")
async def get_ticker(item: int, number: int):
    """Get specific ticker data for live updates"""
    try:
        data = SixMonthsForecast()
        context = str(data[number][item])
        
        if item == 2 or item == 5:
            context = '₹' + context
        elif item == 3 or item == 6:
            context = context + '%'
        
        return {"value": context}
    except (IndexError, Exception) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/commodities")
async def get_commodities_list():
    """Get list of all available commodities"""
    commodities = []
    for commodity in commodity_list:
        name = commodity.getCropName().split('/')[-1]
        commodities.append({
            "name": name,
            "key": name.lower()
        })
    return {"commodities": commodities}


@app.on_event("startup")
async def startup_event():
    """Initialize commodities on startup"""
    global commodity_list
    
    for key, csv_path in commodity_dict.items():
        try:
            commodity = Commodity(csv_path)
            commodity_list.append(commodity)
        except Exception as e:
            print(f"Error loading {key}: {e}")
    
    print(f"Loaded {len(commodity_list)} commodities")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
