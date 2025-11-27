from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Annotated, Optional, List
from datetime import datetime
import json

app = FastAPI()

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://outfithuv-frontend.onrender.com",
        "http://localhost:5500",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Customer(BaseModel):
    id: Annotated[str, Field(..., description="ID of the customer")]
    name: Annotated[Optional[str], Field(None, description="Name of the customer")]
    clothe: Annotated[List[str], Field(..., description="List of clothes")]
    size: Annotated[str, Field(..., description="Size")]
    price: Annotated[float, Field(..., gt=0)]
    phone: Annotated[Optional[int], Field(None, description="Phone number")]
    date: Annotated[Optional[str], Field(None, description="Date created")]

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    clothe: Optional[List[str]] = None
    size: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    phone: Optional[int] = None

class Stock(BaseModel):
    item: Annotated[str, Field(..., description="Item name")]
    quantity: Annotated[int, Field(..., gt=0, description="Quantity purchased")]
    price: Annotated[float, Field(..., gt=0, description="Total price")]
    date: Annotated[Optional[str], Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))]

class StockUpdate(BaseModel):
    item: Optional[str] = None
    quantity: Optional[int] = Field(None, gt=0)
    price: Optional[float] = Field(None, gt=0)

# Helper function to open and load the JSON file
def load_data():
    try:
        with open('customers.json', 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        # If file doesn't exist, create it with empty dict
        save_data({})
        return {}

def save_data(data):
    with open('customers.json', 'w') as f:
        json.dump(data, f, indent=4)

def load_stock_data():
    try:
        with open('stock.json', 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        save_stock_data({})
        return {}

def save_stock_data(data):
    with open('stock.json', 'w') as f:
        json.dump(data, f, indent=4)

# Home route
@app.get("/")
def hello():
    return {'message': 'outfithuv'}

# About route
@app.get("/about")
def about():
    return {'message': 'a fully functional API to manage customers Record'}

# View all customers
@app.get('/view')
def view():
    data = load_data()
    return data

# View a single customer by ID
@app.get('/customer/{customer_id}')
def view_customer(customer_id: str = Path(..., description='id of the customer', example='c001')):
    data = load_data()
    if customer_id in data:
        return data[customer_id]
    raise HTTPException(status_code=404, detail="Customer Not Found, check again")

# Sort customers by price
@app.get('/sort')
def sort_customer(
    sort_by: str = Query(..., description="Sort on the basis of Price"),
    order: str = Query('asc', description="Sort in ascending or descending order")
):
    valid_fields = ['price']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f'Invalid field, select from {valid_fields}')
    
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Invalid order, use 'asc' or 'desc'")
    
    data = load_data()
    sort_order = True if order == 'desc' else False
    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by, 0), reverse=sort_order)
    return sorted_data

# Create new customer
@app.post("/create")
def create_customer(customer: Customer):
    # Load existing data
    data = load_data()
    
    # Check if the customer already exists
    if customer.id in data:
        raise HTTPException(status_code=400, detail='Customer already exists')
    
    # Add new customer to the database with current date
    customer_data = customer.model_dump(exclude=['id'])
    customer_data['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data[customer.id] = customer_data
    
    # Save into the json file
    save_data(data)
    
    return JSONResponse(status_code=201, content={'message': 'CUSTOMER CREATED SUCCESSFULLY!!'})

# Update existing customer
@app.put('/edit/{customer_id}')
def update_customer(
    customer_id: str = Path(..., description="ID of the customer to update"),
    customer_update: CustomerUpdate = None
):
    data = load_data()
    
    if customer_id not in data:
        raise HTTPException(status_code=404, detail="Customer Not Found")
    
    existing_customer_info = data[customer_id]
    updated_customer_info = customer_update.model_dump(exclude_unset=True)
    
    for key, value in updated_customer_info.items():
        existing_customer_info[key] = value
    
    data[customer_id] = existing_customer_info
    save_data(data)
    
    return JSONResponse(status_code=200, content={'message': 'Customer updated successfully'})

# Delete customer
@app.delete('/delete/{customer_id}')
def delete_customer(customer_id: str = Path(..., description="ID of the customer to delete")):
    # Load the data
    data = load_data()
    
    if customer_id not in data:
        raise HTTPException(status_code=404, detail='Customer not found')
    
    del data[customer_id]
    save_data(data)
    
    return JSONResponse(status_code=200, content={'message': 'Customer deleted successfully'})

# ============= STOCK MANAGEMENT ENDPOINTS =============

# View all stock
@app.get('/stock/view')
def view_stock():
    data = load_stock_data()
    return data

# View single stock entry
@app.get('/stock/{stock_id}')
def view_stock_entry(stock_id: str = Path(..., description='ID of the stock entry')):
    data = load_stock_data()
    if stock_id in data:
        return data[stock_id]
    raise HTTPException(status_code=404, detail="Stock entry not found")

# Create stock entry
@app.post("/stock/create")
def create_stock(stock: Stock):
    data = load_stock_data()
    
    if stock.id in data:
        raise HTTPException(status_code=400, detail='Stock entry already exists')
    
    data[stock.id] = stock.model_dump(exclude=['id'])
    save_stock_data(data)
    
    return JSONResponse(status_code=201, content={'message': 'Stock entry created successfully!'})

# Update stock entry
@app.put('/stock/edit/{stock_id}')
def update_stock(
    stock_id: str = Path(..., description="ID of the stock entry to update"),
    stock_update: StockUpdate = None
):
    data = load_stock_data()
    
    if stock_id not in data:
        raise HTTPException(status_code=404, detail="Stock entry not found")
    
    existing_stock = data[stock_id]
    updated_stock = stock_update.model_dump(exclude_unset=True)
    
    for key, value in updated_stock.items():
        existing_stock[key] = value
    
    data[stock_id] = existing_stock
    save_stock_data(data)
    
    return JSONResponse(status_code=200, content={'message': 'Stock entry updated successfully'})

# Delete stock entry
@app.delete('/stock/delete/{stock_id}')
def delete_stock(stock_id: str = Path(..., description="ID of the stock entry to delete")):
    data = load_stock_data()
    
    if stock_id not in data:
        raise HTTPException(status_code=404, detail='Stock entry not found')
    
    del data[stock_id]
    save_stock_data(data)
    
    return JSONResponse(status_code=200, content={'message': 'Stock entry deleted successfully'})