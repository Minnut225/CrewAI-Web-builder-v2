import enum
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Enum, ForeignKey, Text, CheckConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    price = Column(Integer, nullable=False)  # Zero-float VND stored as integer
    cost_price = Column(Integer, nullable=False, default=0)
    image_url = Column(Text, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    category = relationship("Category", back_populates="products")
    recipes = relationship("Recipe", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False, unique=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    unit = Column(String(20), nullable=False)  # e.g., 'g', 'ml', 'pcs'
    stock_quantity = Column(Numeric(12, 3), nullable=False, default=0)  # Decimal precision for inventory
    min_stock_level = Column(Numeric(12, 3), nullable=False, default=0)
    cost_per_unit = Column(Integer, nullable=False, default=0)  # VND integer
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    recipes = relationship("Recipe", back_populates="ingredient", cascade="all, delete-orphan")
    stock_movements = relationship("StockMovement", back_populates="ingredient")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity_required = Column(Numeric(10, 3), nullable=False)  # Quantity per 1 unit of product

    product = relationship("Product", back_populates="recipes")
    ingredient = relationship("Ingredient", back_populates="recipes")


class MovementType(str, enum.Enum):
    IMPORT = "IMPORT"
    SALE = "SALE"
    ADJUSTMENT = "ADJUSTMENT"
    WASTE = "WASTE"


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    change_amount = Column(Numeric(12, 3), nullable=False)  # positive for import, negative for sale/waste
    movement_type = Column(Enum(MovementType, name="movement_type_enum"), nullable=False, index=True)
    reference_id = Column(String(100), nullable=True)  # e.g. order_id or batch ref
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ingredient = relationship("Ingredient", back_populates="stock_movements")
    user = relationship("User", back_populates="stock_movements")


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class OrderType(str, enum.Enum):
    DINE_IN = "DINE_IN"
    TAKEAWAY = "TAKEAWAY"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)  # cashier/manager
    customer_name = Column(String(100), nullable=True)
    table_number = Column(String(20), nullable=True)
    order_type = Column(Enum(OrderType, name="order_type_enum"), default=OrderType.DINE_IN, nullable=False)
    status = Column(Enum(OrderStatus, name="order_status_enum"), default=OrderStatus.PENDING, nullable=False, index=True)
    subtotal = Column(Integer, nullable=False, default=0)  # Zero-float VND
    discount_amount = Column(Integer, nullable=False, default=0)
    tax_amount = Column(Integer, nullable=False, default=0)
    total_amount = Column(Integer, nullable=False, default=0)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    cashier = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Integer, nullable=False)  # Price snapshot at order time
    subtotal = Column(Integer, nullable=False)  # quantity * unit_price
    note = Column(String(255), nullable=True)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    QR_PAY = "QR_PAY"
    CARD = "CARD"


class PaymentStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # VND integer
    payment_method = Column(Enum(PaymentMethod, name="payment_method_enum"), nullable=False)
    status = Column(Enum(PaymentStatus, name="payment_status_enum"), default=PaymentStatus.SUCCESS, nullable=False)
    transaction_code = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order = relationship("Order", back_populates="payments")
    cashier = relationship("User", back_populates="payments")


class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    CONFIRM_ORDER = "CONFIRM_ORDER"
    IMPORT_STOCK = "IMPORT_STOCK"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    action = Column(Enum(AuditAction, name="audit_action_enum"), nullable=False, index=True)
    target_entity = Column(String(100), nullable=False)
    target_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="audit_logs")
