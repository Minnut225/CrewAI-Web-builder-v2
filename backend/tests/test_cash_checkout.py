import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.models.user import User, UserRole
from app.models.menu_order import Category, Product, Ingredient, Recipe
from app.core.security import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        manager = User(
            username="manager1",
            hashed_password=get_password_hash("password123"),
            full_name="Manager User",
            role=UserRole.MANAGER,
            is_active=True
        )
        cashier = User(
            username="cashier1",
            hashed_password=get_password_hash("password123"),
            full_name="Cashier User",
            role=UserRole.CASHIER,
            is_active=True
        )
        db.add_all([manager, cashier])
        db.commit()

        cat = Category(name="Beverages", display_order=1, is_active=True)
        db.add(cat)
        db.commit()

        ing = Ingredient(name="Coffee Beans", sku="ING-CF", unit="g", stock_quantity=1000.0, min_stock_level=100.0, cost_per_unit=200)
        db.add(ing)
        db.commit()

        prod = Product(category_id=cat.id, name="Espresso", sku="PROD-ESP", price=30000, cost_price=10000, is_available=True)
        db.add(prod)
        db.commit()

        recipe = Recipe(product_id=prod.id, ingredient_id=ing.id, quantity_required=15.0)
        db.add(recipe)
        db.commit()

        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def get_auth_token(client: TestClient, username: str, password: str = "password123") -> str:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return response.json()["access_token"]

def test_cashier_forbidden_management(client):
    cashier_token = get_auth_token(client, "cashier1")
    headers = {"Authorization": f"Bearer {cashier_token}"}
    
    # Try creating a category (manager only)
    res = client.post("/api/v1/categories", json={"name": "New Cat", "display_order": 2}, headers=headers)
    assert res.status_code == 403

def test_order_creation_and_checkout_idempotency(client):
    cashier_token = get_auth_token(client, "cashier1")
    headers = {"Authorization": f"Bearer {cashier_token}"}

    # 1. Create order
    order_payload = {
        "order_type": "DINE_IN",
        "table_number": 4,
        "items": [
            {"product_id": 1, "quantity": 2, "notes": "Extra hot"}
        ]
    }
    res = client.post("/api/v1/orders", json=order_payload, headers={**headers, "X-Idempotency-Key": "order-key-1"})
    assert res.status_code == 201
    order_data = res.json()
    assert order_data["status"] in ("PENDING", "CONFIRMED")
    assert order_data["total_amount"] == 60000
    order_id = order_data["id"]

    # 2. Test duplicate order creation with same idempotency key
    res_dup = client.post("/api/v1/orders", json=order_payload, headers={**headers, "X-Idempotency-Key": "order-key-1"})
    assert res_dup.status_code == 201
    assert res_dup.json()["id"] == order_id

    # 3. Checkout order with cash payment
    checkout_payload = {
        "payment_method": "CASH",
        "amount_paid": 100000
    }
    checkout_res = client.post(
        f"/api/v1/orders/{order_id}/checkout",
        json=checkout_payload,
        headers={**headers, "X-Idempotency-Key": "pay-key-1"}
    )
    assert checkout_res.status_code == 200
    checkout_data = checkout_res.json()
    assert checkout_data["status"] == "PAID"
    assert checkout_data["change_due"] == 40000
    assert checkout_data["amount_paid"] == 100000

    # 4. Test idempotency checkout with same key
    checkout_dup = client.post(
        f"/api/v1/orders/{order_id}/checkout",
        json=checkout_payload,
        headers={**headers, "X-Idempotency-Key": "pay-key-1"}
    )
    assert checkout_dup.status_code == 200
    assert checkout_dup.json()["status"] == "PAID"
    assert checkout_dup.json()["change_due"] == 40000

    # 5. Test insufficient payment
    # Create another order
    res2 = client.post("/api/v1/orders", json=order_payload, headers=headers)
    order_id_2 = res2.json()["id"]

    bad_checkout = client.post(
        f"/api/v1/orders/{order_id_2}/checkout",
        json={"payment_method": "CASH", "amount_paid": 10000},
        headers=headers
    )
    assert bad_checkout.status_code == 400
