import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import Base, get_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.models.menu_order import Order, OrderStatus, Payment, PaymentMethod, PaymentStatus, AuditLog, AuditAction
# Verifying management test execution - touch 8

from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Check if users already exist to prevent UNIQUE constraint failures
    mgr = db.query(User).filter(User.username == "manager1").first()
    if not mgr:
        mgr = User(username="manager1", hashed_password=get_password_hash("password123"), full_name="Manager One", role=UserRole.MANAGER, is_active=True)
        db.add(mgr)
    
    csh = db.query(User).filter(User.username == "cashier1").first()
    if not csh:
        csh = User(username="cashier1", hashed_password=get_password_hash("password123"), full_name="Cashier One", role=UserRole.CASHIER, is_active=True)
        db.add(csh)
    
    db.commit()

    # Refresh user instances to get IDs
    mgr = db.query(User).filter(User.username == "manager1").first()
    csh = db.query(User).filter(User.username == "cashier1").first()

    # Add sample order and payment if not exists
    order = db.query(Order).filter(Order.order_number == "ORD-20261020-001").first()
    if not order:
        order = Order(order_number="ORD-20261020-001", user_id=csh.id, status=OrderStatus.COMPLETED, total_amount=50000)
        db.add(order)
        db.commit()
        payment = Payment(order_id=order.id, user_id=csh.id, amount=50000, payment_method=PaymentMethod.CASH, status=PaymentStatus.SUCCESS, transaction_code="TXN-123")
        db.add(payment)

    # Add audit log
    audit_count = db.query(AuditLog).count()
    if audit_count == 0:
        audit = AuditLog(user_id=mgr.id, action=AuditAction.LOGIN, target_entity="User", target_id=str(mgr.id), details="User login")
        db.add(audit)
    db.commit()
    db.close()

    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def get_token(username, password):
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return response.json()["access_token"]

def test_dashboard_metrics_manager():
    token = get_token("manager1", "password123")
    response = client.get("/api/v1/management/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue" in data
    assert data["total_revenue"] == 50000
    assert data["total_orders"] == 1

def test_dashboard_metrics_cashier_forbidden():
    token = get_token("cashier1", "password123")
    response = client.get("/api/v1/management/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

def test_sales_report_manager():
    token = get_token("manager1", "password123")
    response = client.get("/api/v1/management/reports/sales?group_by=day", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "summary" in data
    assert data["summary"]["total_revenue"] == 50000

def test_audit_logs_manager():
    token = get_token("manager1", "password123")
    response = client.get("/api/v1/management/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

def test_audit_logs_cashier_forbidden():
    token = get_token("cashier1", "password123")
    response = client.get("/api/v1/management/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
