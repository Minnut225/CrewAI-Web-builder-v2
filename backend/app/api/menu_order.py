import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_manager
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.menu_order import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CheckoutRequest,
    CheckoutResponse,
    IngredientCreate,
    IngredientResponse,
    IngredientUpdate,
    OrderCreate,
    OrderResponse,
    OrderStatusUpdateRequest,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    StockImportRequest,
)
from app.services.pos_service import InventoryService, OrderService

router = APIRouter(prefix="", tags=["menu_order"])


# --- Categories ---
@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    return OrderService.create_category(db, payload.model_dump())


@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return OrderService.list_categories(db)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    return OrderService.update_category(
        db, category_id, payload.model_dump(exclude_unset=True)
    )


# --- Products ---
@router.post(
    "/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED
)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    return OrderService.create_product(db, payload.model_dump())


@router.get("/products", response_model=List[ProductResponse])
def list_products(
    category_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return OrderService.list_products(
        db, category_id=category_id, is_active=is_active
    )


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    return OrderService.update_product(
        db, product_id, payload.model_dump(exclude_unset=True)
    )


# --- Ingredients & Inventory ---
@router.post(
    "/ingredients",
    response_model=IngredientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ingredient(
    payload: IngredientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    return OrderService.create_ingredient(db, payload.model_dump())


@router.get("/ingredients", response_model=List[IngredientResponse])
def list_ingredients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return OrderService.list_ingredients(db)


@router.put("/ingredients/{ingredient_id}", response_model=IngredientResponse)
def update_ingredient(
    ingredient_id: int,
    payload: IngredientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    return OrderService.update_ingredient(
        db, ingredient_id, payload.model_dump(exclude_unset=True)
    )


@router.post("/ingredients/import", status_code=status.HTTP_200_OK)
def import_stock(
    payload: StockImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    InventoryService.import_stock(
        db,
        ingredient_id=payload.ingredient_id,
        quantity=payload.quantity,
        user_id=current_user.id,
        note=payload.note,
    )
    return {"message": "Import stock successful"}


# --- Orders & POS ---
@router.post(
    "/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED
)
def create_order(
    payload: OrderCreate,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return OrderService.create_order(
        db, payload.model_dump(), cashier_id=current_user.id, idempotency_key=x_idempotency_key
    )


@router.get("/orders", response_model=List[OrderResponse])
def list_orders(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return OrderService.list_orders(db, status=status, limit=limit, offset=offset)


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return OrderService.get_order(db, order_id)


@router.post("/orders/{order_id}/checkout", response_model=CheckoutResponse)
def checkout_order(
    order_id: int,
    payload: CheckoutRequest,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return OrderService.checkout_order(
        db, order_id, payload.model_dump(), idempotency_key=x_idempotency_key
    )


@router.post("/orders/{order_id}/confirm", response_model=OrderResponse)
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from app.models.menu_order import Order, OrderStatus
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status == OrderStatus.PENDING:
        order.status = OrderStatus.PAID
        db.commit()
        db.refresh(order)
    return order


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from app.models.menu_order import Order, OrderStatus, Payment, PaymentMethod, PaymentStatus
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order.status = payload.status
    if payload.status == OrderStatus.PAID and not order.payments:
        payment = Payment(
            order_id=order.id,
            user_id=current_user.id,
            amount=order.total_amount,
            payment_method=PaymentMethod.CASH,
            status=PaymentStatus.SUCCESS,
            transaction_code=f"TXN-{order.order_number}"
        )
        db.add(payment)

    db.commit()
    db.refresh(order)
    return order
