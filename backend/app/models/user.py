import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class UserRole(str, enum.Enum):
    MANAGER = "MANAGER"
    CASHIER = "CASHIER"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.CASHIER)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    orders = relationship("Order", back_populates="cashier")
    payments = relationship("Payment", back_populates="cashier")
    stock_movements = relationship("StockMovement", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
