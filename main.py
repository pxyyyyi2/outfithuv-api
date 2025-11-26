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
    allow_origins=["*"],  # In production, replace with your frontend domain
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
    date: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    clothe: Optional[List[str]] = None
    size: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    phone: Optional[int] = None

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
    
    # Add new customer to the database
    data[customer.id] = customer.model_dump(exclude=['id'])
    
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