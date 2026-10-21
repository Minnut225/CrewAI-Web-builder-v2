from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth
from app.api.menu_order import router as menu_order_router
from app.api.management import router as management_router
from app.db.session import engine, Base, SessionLocal
from app.models import *
from app.core.security import get_password_hash


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables & seed default credentials and menu on startup
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            from app.db.seed import seed_database
            seed_database(db)
        finally:
            db.close()
    except Exception as e:
        print(f"Database auto-init notice: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(menu_order_router, prefix=settings.API_V1_STR)
app.include_router(management_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"message": "Welcome to CoffeeFlow API"}


@app.get("/health")
def health():
    return {"status": "ok"}
