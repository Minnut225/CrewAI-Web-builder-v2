from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, delete
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal

from app.models.menu_order import (
    Category,
    Product,
    Ingredient,
    Recipe,
    StockMovement,
    MovementType,
    Order,
    OrderItem,
    OrderStatus,
    OrderType,
    Payment,
    PaymentMethod,
    PaymentStatus,
    AuditLog,
    AuditAction,
)
from app.models.user import User


class InventoryService:
    """
    Inventory Management Service (alias / wrapper for stock / ingredient methods in OrderService).
    """
    @staticmethod
    def import_stock(db: Session, data: Dict[str, Any], user_id: Optional[int] = None) -> StockMovement:
        return OrderService.import_stock(db, data, user_id)

    @staticmethod
    def get_low_stock_alerts(db: Session) -> List[Ingredient]:
        return OrderService.get_low_stock_alerts(db)

    @staticmethod
    def stock_take(db: Session, data: Dict[str, Any], user_id: Optional[int] = None) -> List[StockMovement]:
        return OrderService.stock_take(db, data, user_id)


class OrderService:
    """
    Complete Service layer handling Menu Management, POS Order Creation,
    ACID Multi-Step Order Confirmation & Stock Deduction with SELECT FOR UPDATE.
    """

    # =========================================================================
    # CATEGORIES
    # =========================================================================
    @staticmethod
    def create_category(db: Session, data: Dict[str, Any]) -> Category:
        existing = db.execute(select(Category).where(Category.name == data["name"])).scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{data['name']}' already exists."
            )
        category = Category(
            name=data["name"],
            display_order=data.get("display_order", 0),
            is_active=data.get("is_active", True)
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def list_categories(db: Session) -> List[Category]:
        return db.execute(select(Category).order_by(Category.display_order, Category.id)).scalars().all()

    @staticmethod
    def update_category(db: Session, category_id: int, data: Dict[str, Any]) -> Category:
        category = db.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
        for k, v in data.items():
            setattr(category, k, v)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def delete_category(db: Session, category_id: int) -> None:
        category = db.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
        db.delete(category)
        db.commit()

    # =========================================================================
    # INGREDIENTS
    # =========================================================================
    @staticmethod
    def create_ingredient(db: Session, data: Dict[str, Any]) -> Ingredient:
        existing = db.execute(
            select(Ingredient).where((Ingredient.name == data["name"]) | (Ingredient.sku == data["sku"]))
        ).scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ingredient with name '{data['name']}' or sku '{data['sku']}' already exists."
            )
        ingredient = Ingredient(
            name=data["name"],
            sku=data["sku"],
            unit=data["unit"],
            stock_quantity=Decimal(str(data.get("stock_quantity", 0))),
            min_stock_level=Decimal(str(data.get("min_stock_level", 0))),
            cost_per_unit=int(data.get("cost_per_unit", 0))
        )
        db.add(ingredient)
        db.commit()
        db.refresh(ingredient)
        return ingredient

    @staticmethod
    def list_ingredients(db: Session) -> List[Ingredient]:
        return db.execute(select(Ingredient).order_by(Ingredient.id)).scalars().all()

    @staticmethod
    def update_ingredient(db: Session, ingredient_id: int, data: Dict[str, Any]) -> Ingredient:
        ingredient = db.get(Ingredient, ingredient_id)
        if not ingredient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found.")
        for k, v in data.items():
            if k in ("stock_quantity", "min_stock_level"):
                setattr(ingredient, k, Decimal(str(v)))
            elif k == "cost_per_unit":
                setattr(ingredient, k, int(v))
            else:
                setattr(ingredient, k, v)
        db.commit()
        db.refresh(ingredient)
        return ingredient

    @staticmethod
    def import_stock(db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        ingredient_id = data["ingredient_id"]
        quantity = Decimal(str(data["quantity"]))
        user_id = data.get("user_id", 1)
        user = db.get(User, user_id) or db.execute(select(User)).scalars().first()
        note = data.get("note", "Manual restock")

        ingredient = OrderService.import_inventory(
            db=db,
            ingredient_id=ingredient_id,
            quantity=float(quantity),
            user=user,
            note=note
        )
        return {"status": "SUCCESS", "ingredient_id": ingredient.id, "new_stock": float(ingredient.stock_quantity)}

    @staticmethod
    def import_inventory(
        db: Session,
        ingredient_id: int,
        quantity: float,
        user: User,
        note: Optional[str] = None
    ) -> Ingredient:
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Import quantity must be greater than zero."
            )

        ingredient = db.execute(
            select(Ingredient).where(Ingredient.id == ingredient_id).with_for_update()
        ).scalars().first()

        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient with id {ingredient_id} not found."
            )

        ingredient.stock_quantity += Decimal(str(quantity))

        movement = StockMovement(
            ingredient_id=ingredient.id,
            user_id=user.id if user else 1,
            change_amount=Decimal(str(quantity)),
            movement_type=MovementType.IMPORT,
            note=note or "Restocked"
        )
        db.add(movement)

        if user:
            audit_log = AuditLog(
                user_id=user.id,
                action=AuditAction.IMPORT_STOCK,
                target_entity="Ingredient",
                target_id=str(ingredient.id),
                details=f"Imported {quantity} {ingredient.unit} of ingredient {ingredient.name}"
            )
            db.add(audit_log)

        db.commit()
        db.refresh(ingredient)
        return ingredient

    # =========================================================================
    # PRODUCTS & RECIPES
    # =========================================================================
    @staticmethod
    def create_product(db: Session, data: Dict[str, Any]) -> Product:
        existing = db.execute(select(Product).where(Product.sku == data["sku"])).scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with sku '{data['sku']}' already exists."
            )

        recipes_data = data.pop("recipes", [])
        product = Product(
            category_id=data["category_id"],
            name=data["name"],
            sku=data["sku"],
            price=int(data["price"]),
            cost_price=int(data.get("cost_price", 0)),
            image_url=data.get("image_url"),
            is_available=data.get("is_available", True),
            description=data.get("description")
        )
        db.add(product)
        db.flush()

        for r in recipes_data:
            recipe = Recipe(
                product_id=product.id,
                ingredient_id=r["ingredient_id"],
                quantity_required=Decimal(str(r["quantity_required"]))
            )
            db.add(recipe)

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def list_products(
        db: Session,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> List[Product]:
        query = select(Product)
        if category_id is not None:
            query = query.where(Product.category_id == category_id)
        if is_active is not None:
            query = query.where(Product.is_available == is_active)
        return db.execute(query.order_by(Product.id)).scalars().all()

    @staticmethod
    def update_product(db: Session, product_id: int, data: Dict[str, Any]) -> Product:
        product = db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        recipes_data = data.pop("recipes", None)
        for k, v in data.items():
            if k in ("price", "cost_price"):
                setattr(product, k, int(v))
            else:
                setattr(product, k, v)

        if recipes_data is not None:
            db.execute(delete(Recipe).where(Recipe.product_id == product.id))
            for r in recipes_data:
                recipe = Recipe(
                    product_id=product.id,
                    ingredient_id=r["ingredient_id"],
                    quantity_required=Decimal(str(r["quantity_required"]))
                )
                db.add(recipe)

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def delete_product(db: Session, product_id: int) -> None:
        product = db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        db.delete(product)
        db.commit()

    # =========================================================================
    # ORDERS & STOCK DEDUCTION
    # =========================================================================
    _IDEMPOTENCY_STORE: Dict[str, Any] = {}

    @classmethod
    def create_order(
        cls,
        db: Session,
        order_data: Dict[str, Any],
        cashier_id: Optional[int] = None,
        user: Optional[User] = None,
        idempotency_key: Optional[str] = None
    ) -> Order:
        if idempotency_key and idempotency_key in cls._IDEMPOTENCY_STORE:
            cached_order_id = cls._IDEMPOTENCY_STORE[idempotency_key]
            existing_order = db.execute(
                select(Order).where(Order.id == cached_order_id)
            ).scalars().first()
            if existing_order:
                return existing_order

        if not user and cashier_id:
            user = db.execute(select(User).where(User.id == cashier_id)).scalars().first()
        if not user:
            user = db.execute(select(User)).scalars().first()
        order = cls.create_and_confirm_order(db, user, order_data, idempotency_key=idempotency_key)
        if idempotency_key:
            cls._IDEMPOTENCY_STORE[idempotency_key] = order.id
        return order

    @classmethod
    def create_and_confirm_order(
        cls,
        db: Session,
        user: User,
        order_data: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Order:
        """
        Creates an order AND automatically deducts stock according to product recipes.
        All in an ACID single atomic transaction.
        """
        if idempotency_key and idempotency_key in cls._IDEMPOTENCY_STORE:
            cached_order_id = cls._IDEMPOTENCY_STORE[idempotency_key]
            existing_order = db.execute(
                select(Order).where(Order.id == cached_order_id)
            ).scalars().first()
            if existing_order:
                return existing_order

        items_data = order_data.get("items", [])
        if not items_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must contain at least one item."
            )

        order_type = order_data.get("order_type", OrderType.DINE_IN)
        table_number = order_data.get("table_number")

        subtotal = 0
        order_items_to_create = []

        # Validate products & prices
        for item in items_data:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 1)
            if quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Item quantity must be greater than zero."
                )

            product = db.execute(
                select(Product).where(Product.id == product_id)
            ).scalars().first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with id {product_id} not found."
                )

            if not product.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name}' is currently unavailable."
                )

            unit_price = int(product.price)
            item_subtotal = unit_price * quantity
            subtotal += item_subtotal

            order_items_to_create.append({
                "product_id": product.id,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": item_subtotal,
                "note": item.get("note"),
                "product": product
            })

        discount_amount = int(order_data.get("discount_amount", 0))
        tax_amount = int(order_data.get("tax_amount", 0))
        total_amount = max(0, subtotal - discount_amount + tax_amount)

        # Generate unique order number
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        count_today = db.execute(
            select(func.count(Order.id))
        ).scalar() or 0
        order_number = f"ORD-{today_str}-{count_today + 1:04d}"

        new_order = Order(
            order_number=order_number,
            user_id=user.id,
            customer_name=order_data.get("customer_name"),
            table_number=table_number,
            order_type=order_type,
            status=OrderStatus.PENDING,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            note=order_data.get("note")
        )

        db.add(new_order)
        db.flush()

        for item_dict in order_items_to_create:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item_dict["product_id"],
                quantity=item_dict["quantity"],
                unit_price=item_dict["unit_price"],
                subtotal=item_dict["subtotal"],
                note=item_dict["note"]
            )
            db.add(order_item)

        # Calculate required ingredients and atomically deduct with SELECT FOR UPDATE
        required_ingredients: Dict[int, Decimal] = {}
        for item_dict in order_items_to_create:
            recipes = db.execute(
                select(Recipe).where(Recipe.product_id == item_dict["product_id"])
            ).scalars().all()
            for rec in recipes:
                needed = rec.quantity_required * Decimal(str(item_dict["quantity"]))
                required_ingredients[rec.ingredient_id] = required_ingredients.get(rec.ingredient_id, Decimal("0")) + needed

        for ing_id, needed_qty in required_ingredients.items():
            ingredient = db.execute(
                select(Ingredient).where(Ingredient.id == ing_id).with_for_update()
            ).scalars().first()

            if not ingredient:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ingredient with id {ing_id} not found."
                )

            if ingredient.stock_quantity < needed_qty:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for '{ingredient.name}'. Required: {needed_qty}, Available: {ingredient.stock_quantity}"
                )

            ingredient.stock_quantity -= needed_qty

            movement = StockMovement(
                ingredient_id=ingredient.id,
                user_id=user.id,
                change_amount=-needed_qty,
                movement_type=MovementType.SALE,
                reference_id=str(new_order.id),
                note=f"Sale deduction for Order {order_number}"
            )
            db.add(movement)

        # Audit Log
        audit_log = AuditLog(
            user_id=user.id,
            action=AuditAction.CREATE,
            target_entity="Order",
            target_id=str(new_order.id),
            details=f"Created order {order_number} totaling {total_amount} VND"
        )
        db.add(audit_log)

        db.commit()
        db.refresh(new_order)
        if idempotency_key:
            cls._IDEMPOTENCY_STORE[idempotency_key] = new_order.id
        return new_order

    @classmethod
    def checkout_order(
        cls,
        db: Session,
        order_id: int,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Completes payment for an order and updates status to PAID.
        """
        order = db.execute(
            select(Order).where(Order.id == order_id).with_for_update()
        ).scalars().first()

        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found.")

        if order.status == OrderStatus.PAID:
            # Idempotent return
            change_due = max(0, payload.get("amount_paid", order.total_amount) - order.total_amount)
            payment = order.payments[0] if order.payments else None
            return {
                "order_id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "total_amount": order.total_amount,
                "amount_paid": payload.get("amount_paid", order.total_amount),
                "change_due": change_due,
                "payment": payment,
                "message": "Order was already paid."
            }

        amount_paid = int(payload.get("amount_paid", order.total_amount))
        if amount_paid < order.total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Amount paid ({amount_paid}) is less than total ({order.total_amount})."
            )

        change_due = amount_paid - order.total_amount
        payment_method = payload.get("payment_method", PaymentMethod.CASH)
        transaction_code = payload.get("transaction_code")

        payment = Payment(
            order_id=order.id,
            user_id=order.user_id,
            amount=amount_paid,
            payment_method=payment_method,
            status=PaymentStatus.SUCCESS,
            transaction_code=transaction_code
        )
        db.add(payment)
        order.status = OrderStatus.PAID

        db.commit()
        db.refresh(order)
        db.refresh(payment)

        return {
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": order.total_amount,
            "amount_paid": amount_paid,
            "change_due": change_due,
            "payment": payment,
            "message": "Order paid successfully."
        }

    @staticmethod
    def list_orders(
        db: Session,
        status: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Order]:
        target_status = status or status_filter
        query = select(Order)
        if target_status:
            query = query.where(Order.status == target_status)
        return db.execute(query.order_by(Order.id.desc()).offset(offset).limit(limit)).scalars().all()

    @staticmethod
    def get_order(db: Session, order_id: int) -> Order:
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        return order
