import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.models import *
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
    mgr = User(username="mgr", hashed_password=get_password_hash("123456"), full_name="Manager", role=UserRole.MANAGER, is_active=True)
    csh = User(username="csh", hashed_password=get_password_hash("123456"), full_name="Cashier", role=UserRole.CASHIER, is_active=True)
    db.add(mgr)
    db.add(csh)
    db.commit()
    try:
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

def get_token(client, username: str, password: str = "123456"):
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return response.json()["access_token"]

def test_menu_and_pos_flow(client, db_session):
    mgr_token = get_token(client, "mgr")
    csh_token = get_token(client, "csh")
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}
    csh_headers = {"Authorization": f"Bearer {csh_token}"}

    # 1. Create Category (Manager)
    cat_res = client.post("/api/v1/categories", json={"name": "Cà phê máy", "display_order": 1}, headers=mgr_headers)
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["id"]

    # 2. Create Ingredients (Manager)
    ing1_res = client.post("/api/v1/ingredients", json={
        "name": "Hạt Arabica",
        "sku": "ING-ARA",
        "unit": "g",
        "stock_quantity": 1000.0,
        "min_stock_level": 100.0,
        "cost_per_unit": 200
    }, headers=mgr_headers)
    assert ing1_res.status_code == 201
    ing1_id = ing1_res.json()["id"]

    ing2_res = client.post("/api/v1/ingredients", json={
        "name": "Sữa tươi",
        "sku": "ING-MILK",
        "unit": "ml",
        "stock_quantity": 500.0,
        "min_stock_level": 50.0,
        "cost_per_unit": 50
    }, headers=mgr_headers)
    assert ing2_res.status_code == 201
    ing2_id = ing2_res.json()["id"]

    # 3. Create Product with Recipe (Manager)
    prod_res = client.post("/api/v1/products", json={
        "category_id": cat_id,
        "name": "Cà phê sữa đá",
        "sku": "PROD-CPS",
        "price": 35000,
        "cost_price": 10000,
        "recipes": [
            {"ingredient_id": ing1_id, "quantity_required": 20.0},
            {"ingredient_id": ing2_id, "quantity_required": 50.0}
        ]
    }, headers=mgr_headers)
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    # 4. Create Order & Test Stock Deduction (Cashier)
    order_res = client.post("/api/v1/orders", json={
        "customer_name": "Nguyễn Văn A",
        "table_number": "T1",
        "order_type": "DINE_IN",
        "items": [
            {"product_id": prod_id, "quantity": 2, "note": "Ít đá"}
        ]
    }, headers=csh_headers)
    assert order_res.status_code == 201
    order_data = order_res.json()
    assert order_data["total_amount"] == 70000
    order_id = order_data["id"]

    # Verify ingredient stock deducted: Arabica 1000 - 40 = 960, Milk 500 - 100 = 400
    ing_list_res = client.get("/api/v1/ingredients", headers=mgr_headers)
    ingredients = ing_list_res.json()
    for ing in ingredients:
        if ing["id"] == ing1_id:
            assert ing["stock_quantity"] == 960.0
        elif ing["id"] == ing2_id:
            assert ing["stock_quantity"] == 400.0

    # 5. Checkout Order
    checkout_res = client.post(f"/api/v1/orders/{order_id}/checkout", json={
        "payment_method": "CASH",
        "amount_paid": 100000
    }, headers=csh_headers)
    assert checkout_res.status_code == 200
    checkout_data = checkout_res.json()
    assert checkout_data["status"] == "PAID"
    assert checkout_data["change_due"] == 30000
