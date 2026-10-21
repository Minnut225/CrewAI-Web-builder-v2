from typing import Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.menu_order import OrderType, OrderStatus, PaymentMethod, PaymentStatus, MovementType

# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_order: int = Field(0, ge=0)
    is_active: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Recipe Item for Product ---
class RecipeItemCreate(BaseModel):
    ingredient_id: int
    quantity_required: float = Field(..., gt=0)

class RecipeItemResponse(BaseModel):
    id: int
    ingredient_id: int
    quantity_required: float

    class Config:
        from_attributes = True


# --- Product Schemas ---
class ProductBase(BaseModel):
    category_id: int
    name: str = Field(..., min_length=1, max_length=150)
    sku: str = Field(..., min_length=1, max_length=50)
    price: int = Field(..., ge=0)  # VND integer
    cost_price: int = Field(0, ge=0)
    image_url: Optional[str] = None
    is_available: bool = True
    description: Optional[str] = None

class ProductCreate(ProductBase):
    recipes: List[RecipeItemCreate] = []

class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    price: Optional[int] = Field(None, ge=0)
    cost_price: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    description: Optional[str] = None
    recipes: Optional[List[RecipeItemCreate]] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    recipes: List[RecipeItemResponse] = []

    class Config:
        from_attributes = True


# --- Ingredient Schemas ---
class IngredientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    sku: str = Field(..., min_length=1, max_length=50)
    unit: str = Field(..., min_length=1, max_length=20)
    stock_quantity: float = Field(0, ge=0)
    min_stock_level: float = Field(0, ge=0)
    cost_per_unit: int = Field(0, ge=0)

class IngredientCreate(IngredientBase):
    pass

class IngredientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    min_stock_level: Optional[float] = Field(None, ge=0)
    cost_per_unit: Optional[int] = Field(None, ge=0)

class IngredientResponse(IngredientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Stock Import Schema ---
class StockImportItem(BaseModel):
    ingredient_id: int
    quantity: float = Field(..., gt=0)
    cost_per_unit: Optional[int] = Field(None, ge=0)
    note: Optional[str] = None

class StockImportRequest(BaseModel):
    items: List[StockImportItem]
    note: Optional[str] = None


# --- POS Order Creation Schemas ---
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    note: Optional[str] = None
    notes: Optional[str] = None

class OrderCreate(BaseModel):
    customer_name: Optional[str] = Field(None, max_length=100)
    table_number: Optional[Union[str, int]] = Field(None)
    order_type: OrderType = OrderType.DINE_IN
    discount_amount: int = Field(0, ge=0)
    tax_amount: int = Field(0, ge=0)
    note: Optional[str] = None
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: int
    subtotal: int
    note: Optional[str] = None
    product_name: Optional[str] = None

    class Config:
        from_attributes = True


class OrderPaymentResponse(BaseModel):
    id: int
    amount: int
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_code: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    customer_name: Optional[str] = None
    table_number: Optional[Union[str, int]] = None
    order_type: OrderType
    status: OrderStatus
    subtotal: int
    discount_amount: int
    tax_amount: int
    total_amount: int
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    payments: List[OrderPaymentResponse] = []

    class Config:
        from_attributes = True


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus

# --- Checkout / Payment Schemas ---
class CheckoutRequest(BaseModel):
    payment_method: PaymentMethod = PaymentMethod.CASH
    amount_paid: int = Field(..., gt=0)
    transaction_code: Optional[str] = None

class CheckoutResponse(BaseModel):
    order_id: int
    order_number: str
    status: OrderStatus
    total_amount: int
    amount_paid: int
    change_due: int
    payment: OrderPaymentResponse
    message: str
