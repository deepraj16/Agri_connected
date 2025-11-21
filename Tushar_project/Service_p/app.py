from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import pymysql
import pymysql.cursors
from datetime import datetime
import uvicorn

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection using PyMySQL
def get_db():
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="1234",  # change as needed
        database="agri",  # change as needed
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        yield conn
    finally:
        conn.close()

# Pydantic models
class ServiceProvider(BaseModel):
    name: str
    username: str
    phone: str
    email: str
    password: str
    location: str

class ServiceProviderLogin(BaseModel):
    username: str
    password: str

class Customer(BaseModel):
    name: str
    username: str
    phone: str
    email: str
    password: str

class Transaction(BaseModel):
    service_provider_id: int
    customer_id: int
    service_type: str
    amount: float
    description: Optional[str] = None
    status: str = "pending"

class Service(BaseModel):
    service_provider_id: int
    service_name: str
    service_type: str
    price_per_hour: float
    available: bool = True
    description: Optional[str] = None

# -------------------- SERVICE PROVIDER ENDPOINTS --------------------

@app.post("/api/service-provider/register")
def register_service_provider(provider: ServiceProvider, conn=Depends(get_db)):
    cursor = conn.cursor()

    try:
        query = """
        INSERT INTO service_providers (name, username, phone, email, password, location)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            provider.name, provider.username, provider.phone,
            provider.email, provider.password, provider.location
        ))
        conn.commit()

        return {"message": "Registration successful", "id": cursor.lastrowid}

    except pymysql.err.IntegrityError:
        raise HTTPException(status_code=400, detail="Username, phone or email already exists")

    finally:
        cursor.close()


@app.post("/api/service-provider/login")
def login_service_provider(login: ServiceProviderLogin, conn=Depends(get_db)):
    cursor = conn.cursor()

    query = "SELECT * FROM service_providers WHERE username = %s AND password = %s"
    cursor.execute(query, (login.username, login.password))
    user = cursor.fetchone()
    cursor.close()

    if user:
        return {"message": "Login successful", "user": user}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/api/service-provider/{provider_id}")
def get_service_provider(provider_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM service_providers WHERE id = %s", (provider_id,))
    provider = cursor.fetchone()
    cursor.close()

    if provider:
        return provider
    else:
        raise HTTPException(status_code=404, detail="Provider not found")




@app.get("/api/services/provider/{provider_id}")
def get_provider_services(provider_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    query = """
    SELECT * FROM services 
    WHERE service_provider_id = %s 
    ORDER BY created_at DESC
    """
    
    cursor.execute(query, (provider_id,))
    services = cursor.fetchall()
    cursor.close()
    
    return services


@app.get("/api/services/{service_id}")
def get_service(service_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services WHERE id = %s", (service_id,))
    service = cursor.fetchone()
    cursor.close()
    
    if service:
        return service
    else:
        raise HTTPException(status_code=404, detail="Service not found")


@app.put("/api/services/{service_id}")
def update_service(service_id: int, service: Service, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        query = """
        UPDATE services
        SET service_name=%s, service_type=%s, price_per_hour=%s, 
            available=%s, description=%s
        WHERE id=%s
        """
        cursor.execute(query, (
            service.service_name,
            service.service_type,
            service.price_per_hour,
            service.available,
            service.description,
            service_id
        ))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Service not found")
        
        return {"message": "Service updated"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    finally:
        cursor.close()


@app.patch("/api/services/{service_id}/toggle")
def toggle_service_availability(service_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        # Get current availability
        cursor.execute("SELECT available FROM services WHERE id = %s", (service_id,))
        service = cursor.fetchone()
        
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # Toggle availability
        new_availability = not service['available']
        cursor.execute(
            "UPDATE services SET available = %s WHERE id = %s",
            (new_availability, service_id)
        )
        conn.commit()
        
        return {"message": "Availability toggled", "available": new_availability}
    
    finally:
        cursor.close()


@app.delete("/api/services/{service_id}")
def delete_service(service_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM services WHERE id = %s", (service_id,))
    conn.commit()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    
    cursor.close()
    return {"message": "Service deleted successfully"}


@app.get("/api/services")
def get_all_services(conn=Depends(get_db)):
    cursor = conn.cursor()
    
    query = """
    SELECT s.*, sp.name as provider_name, sp.location as provider_location
    FROM services s
    JOIN service_providers sp ON s.service_provider_id = sp.id
    WHERE s.available = 1
    ORDER BY s.created_at DESC
    """
    
    cursor.execute(query)
    services = cursor.fetchall()
    cursor.close()
    
    return services

# -------------------- TRANSACTION ENDPOINTS --------------------

@app.post("/api/transactions")
def create_transaction(transaction: Transaction, conn=Depends(get_db)):
    cursor = conn.cursor()

    query = """
    INSERT INTO transactions
    (service_provider_id, customer_id, service_type, amount, description, status)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (
        transaction.service_provider_id,
        transaction.customer_id,
        transaction.service_type,
        transaction.amount,
        transaction.description,
        transaction.status
    ))
    conn.commit()
    transaction_id = cursor.lastrowid
    cursor.close()

    return {"message": "Transaction created", "id": transaction_id}


@app.get("/api/transactions/provider/{provider_id}")
def get_provider_transactions(provider_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()

    query = """
    SELECT t.*, c.name AS customer_name, c.phone AS customer_phone
    FROM transactions t
    LEFT JOIN customers c ON t.customer_id = c.id
    WHERE t.service_provider_id = %s
    ORDER BY t.created_at DESC
    """

    cursor.execute(query, (provider_id,))
    transactions = cursor.fetchall()
    cursor.close()

    return transactions


@app.put("/api/transactions/{transaction_id}")
def update_transaction(transaction_id: int, transaction: Transaction, conn=Depends(get_db)):
    cursor = conn.cursor()

    query = """
    UPDATE transactions
    SET service_type=%s, amount=%s, description=%s, status=%s
    WHERE id=%s
    """

    cursor.execute(query, (
        transaction.service_type,
        transaction.amount,
        transaction.description,
        transaction.status,
        transaction_id
    ))
    conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")

    cursor.close()
    return {"message": "Transaction updated"}


@app.delete("/api/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()

    cursor.execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
    conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")

    cursor.close()
    return {"message": "Transaction deleted"}


# -------------------- RUN APP --------------------
if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
