from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Annotated, Optional, List
from datetime import datetime
import json

app = FastAPI()

# -------------------------------------------------------
# CORS SETTINGS
# -------------------------------------------------------
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

# -------------------------------------------------------
# MODELS
# -------------------------------------------------------

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


# FIXED — ID ADDED
class Stock(BaseModel):
    id: Annotated[str, Field(..., description="Stock entry ID")]
    item: Annotated[str, Field(..., description="Item name")]
    quantity: Annotated[int, Field(..., gt=0, description="Quantity purchased")]
    price: Annotated[float, Field(..., gt=0, description="Total price")]
    date: Annotated[str, Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))]


class StockUpdate(BaseModel):
    item: Optional[str] = None
    quantity: Optional[int] = Field(None, gt=0)
    price: Optional[float] = Field(None, gt=0)


# -------------------------------------------------------
# JSON LOAD/SAVE HELPERS
# -------------------------------------------------------

def load_data():
    try:
        with open('customers.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        save_data({})
        return {}

def save_data(data):
    with open('customers.json', 'w') as f:
        json.dump(data, f, indent=4)


def load_stock_data():
    try:
        with open('stock.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        save_stock_data({})
        return {}

def save_stock_data(data):
    with open('stock.json', 'w') as f:
        json.dump(data, f, indent=4)


# -------------------------------------------------------
# ROUTES
# -------------------------------------------------------

@app.get("/")
def hello():
    return {"message": "outfithuv"}

@app.get("/about")
def about():
    return {"message": "A fully functional API to manage customer records & stock"}


# -------- CUSTOMERS --------

@app.get('/view')
def view_customers():
    return load_data()


@app.get('/customer/{customer_id}')
def view_customer(customer_id: str = Path(..., example='c001')):
    data = load_data()
    if customer_id not in data:
        raise HTTPException(status_code=404, detail="Customer Not Found")
    return data[customer_id]


@app.get('/sort')
def sort_customer(
    sort_by: str = Query(...),
    order: str = Query('asc')
):
    if sort_by != "price":
        raise HTTPException(status_code=400, detail="Invalid field: only 'price' allowed")

    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Order must be 'asc' or 'desc'")

    data = load_data()
    return sorted(
        data.values(),
        key=lambda x: x.get("price", 0),
        reverse=True if order == "desc" else False
    )


@app.post("/create")
def create_customer(customer: Customer):
    data = load_data()

    if customer.id in data:
        raise HTTPException(status_code=400, detail="Customer already exists")

    customer_info = customer.model_dump(exclude=['id'])
    customer_info["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data[customer.id] = customer_info
    save_data(data)

    return JSONResponse(status_code=201, content={"message": "Customer created successfully"})


@app.put("/edit/{customer_id}")
def update_customer(customer_id: str, customer_update: CustomerUpdate):
    data = load_data()

    if customer_id not in data:
        raise HTTPException(status_code=404, detail="Customer Not Found")

    updated_fields = customer_update.model_dump(exclude_unset=True)
    data[customer_id].update(updated_fields)

    save_data(data)
    return {"message": "Customer updated successfully"}


@app.delete("/delete/{customer_id}")
def delete_customer(customer_id: str):
    data = load_data()

    if customer_id not in data:
        raise HTTPException(status_code=404, detail="Customer not found")

    del data[customer_id]
    save_data(data)

    return {"message": "Customer deleted successfully"}


# -------- STOCK --------

@app.get('/stock/view')
def view_stock():
    return load_stock_data()


@app.get('/stock/{stock_id}')
def view_stock_entry(stock_id: str):
    data = load_stock_data()
    if stock_id not in data:
        raise HTTPException(status_code=404, detail="Stock entry not found")
    return data[stock_id]


# FIXED — now works 100%
@app.post("/stock/create")
def create_stock(stock: Stock):
    data = load_stock_data()

    if stock.id in data:
        raise HTTPException(status_code=400, detail='Stock entry already exists')

    data[stock.id] = stock.model_dump(exclude=['id'])
    save_stock_data(data)

    return JSONResponse(status_code=201, content={'message': 'Stock entry created successfully!'})


@app.put('/stock/edit/{stock_id}')
def update_stock(stock_id: str, stock_update: StockUpdate):
    data = load_stock_data()

    if stock_id not in data:
        raise HTTPException(status_code=404, detail="Stock entry not found")

    updated = stock_update.model_dump(exclude_unset=True)
    data[stock_id].update(updated)

    save_stock_data(data)
    return {"message": "Stock entry updated successfully"}


@app.delete('/stock/delete/{stock_id}')
def delete_stock(stock_id: str):
    data = load_stock_data()

    if stock_id not in data:
        raise HTTPException(status_code=404, detail="Stock entry not found")

    del data[stock_id]
    save_stock_data(data)

    return {"message": "Stock entry deleted successfully"}
