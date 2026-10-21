import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.models.user import User, UserRole
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

def test_login_manager(client, db_session):
    manager = User(
        username="manager1",
        hashed_password=get_password_hash("securepass123"),
        full_name="Store Manager",
        role=UserRole.MANAGER,
        is_active=True
    )
    db_session.add(manager)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "manager1", "password": "securepass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "MANAGER"
    assert data["full_name"] == "Store Manager"

def test_login_cashier(client, db_session):
    cashier = User(
        username="cashier1",
        hashed_password=get_password_hash("cashierpass123"),
        full_name="Front Cashier",
        role=UserRole.CASHIER,
        is_active=True
    )
    db_session.add(cashier)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "cashier1", "password": "cashierpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "CASHIER"

def test_login_inactive_user(client, db_session):
    inactive = User(
        username="inactive1",
        hashed_password=get_password_hash("password123"),
        full_name="Inactive User",
        role=UserRole.CASHIER,
        is_active=False
    )
    db_session.add(inactive)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "inactive1", "password": "password123"}
    )
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()

def test_login_invalid_credentials(client, db_session):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "wrongpassword"}
    )
    assert response.status_code == 401
