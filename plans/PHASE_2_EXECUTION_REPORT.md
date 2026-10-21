# Phase 2: Menu Management & POS Order Creation - Architectural & WBS Execution Report

- **Timestamp**: 2026-10-13 15:45:00
- **Phase**: Phase 2: Menu Management & POS Order Creation
- **Status**: AUTHORIZED & DECOMPOSED (WBS Ready for Implementation)
- **Quality Gate Target**: 100% Zero-Float Currency Precision, ACID Order Creation with Pricing Snapshot, RBAC Menu Protection.

---

## 1. Executive Summary & Architectural Analysis

Phase 2 implements the core revenue engine of **CoffeeFlow**: **Menu Management & POS Order Creation**.
Following `docs/DATA_MODEL.md`, `docs/API_CONTRACTS.md`, `docs/BUSINESS_RULES.md`, and `design/DESIGN_SYSTEM.md`, this phase bridges administrative catalog control with high-throughput POS cashier workflows.

### Key Technical Pillars:
1. **Zero-Float Currency Precision (`DECIMAL(12,2)`)**: All monetary attributes (`price`, `base_price`, `subtotal`, `total_amount`, `option_price`) are stored as fixed-precision decimals and transmitted as strings/decimals in JSON payloads to prevent floating-point rounding errors.
2. **ACID Transaction Orchestration**: POS order creation wraps `Order` insertion, `OrderItem` creation, `OrderItemOption` mapping, and inventory deduction in an atomic database transaction.
3. **Immutable Pricing Snapshot**: `Order` and `OrderItem` capture `base_price` and `option_price` at the exact moment of order placement. Subsequent menu price modifications never alter historical financial reports or existing active orders.
4. **Role-Based Access Control (RBAC)**:
   - `MANAGER`: Full CRUD access to Categories, Products, and Product Options.
   - `CASHIER`: Read-only access to menu catalogs, full write access to Orders, Order Items, and POS checkout workflows.
5. **Faithful Google Stitch Integration**: The POS interface (`/pos`) and Menu/Product management screens strictly adhere to the warm artisan palette (`#FFF8F5`, `#220F05`, `#88512A`), Plus Jakarta Sans typography, and Material Symbols Outlined icons extracted from `design/screen_pos_cashier/code.html` and `design/screen_products_menu/code.html`.

---

## 2. Work Breakdown Structure (WBS)

### Backend Tasks

#### Task BE-1: Models, Schemas & Data Contracts
- **Target Files**:
  - `backend/app/models/menu.py` (New or updated: `Category`, `Product`, `ProductOptionGroup`, `ProductOption`)
  - `backend/app/models/order.py` (New or updated: `Order`, `OrderItem`, `OrderItemOption`)
  - `backend/app/schemas/menu.py` (Pydantic schemas with Decimal validation)
  - `backend/app/schemas/order.py` (Pydantic schemas for order creation, snapshot validation, and response DTOs)
  - `backend/app/db/base.py` or alembic migration scripts
- **Details**:
  - Define SQLAlchemy models with explicit foreign keys, indexes, and `Numeric(12, 2)` types for currency.
  - Implement Pydantic validators ensuring `total_amount = base_price + sum(options)` matches server-side calculation.
  - Create Alembic migration script for tables: `categories`, `products`, `product_option_groups`, `product_options`, `orders`, `order_items`, `order_item_options`.

#### Task BE-2: Business Logic & Services (ACID & Precision)
- **Target Files**:
  - `backend/app/services/menu_service.py`
  - `backend/app/services/order_service.py`
- **Details**:
  - `MenuService`: Handle category/product CRUD with uniqueness validations and soft delete / active status toggling.
  - `OrderService`: Implement atomic order creation transaction. Validate stock availability, calculate totals using Python `Decimal`, and freeze pricing snapshots (`unit_price`, `base_price`, `total_amount`).

#### Task BE-3: API Routers, Security & Tests
- **Target Files**:
  - `backend/app/api/v1/endpoints/menu.py`
  - `backend/app/api/v1/endpoints/orders.py`
  - `backend/tests/test_menu_order.py`
- **Details**:
  - REST endpoints: `GET /api/v1/categories`, `POST /api/v1/categories`, `GET /api/v1/products`, `POST /api/v1/products`, `GET /api/v1/orders`, `POST /api/v1/orders`.
  - Enforce RBAC dependencies: `@role_required(["MANAGER"])` for menu modifications; `@role_required(["CASHIER", "MANAGER"])` for order creation and viewing.
  - Comprehensive pytest suite verifying snapshot pricing immutability and decimal precision.

---

### Frontend Tasks

#### Task FE-1: TypeScript Types & API Services
- **Target Files**:
  - `frontend/src/types/menu.ts`
  - `frontend/src/types/order.ts`
  - `frontend/src/services/menuService.ts`
  - `frontend/src/services/orderService.ts`
- **Details**:
  - TypeScript interfaces matching backend Pydantic models 1:1.
  - API client methods using Axios with JWT bearer tokens for catalog fetching, product filtering, and POS order submission.

#### Task FE-2: UI Pages, Components & POS Layout
- **Target Files**:
  - `frontend/src/pages/POSPage.tsx`
  - `frontend/src/pages/ProductsMenuPage.tsx`
  - `frontend/src/components/pos/ProductGrid.tsx`
  - `frontend/src/components/pos/CartSidebar.tsx`
  - `frontend/src/components/pos/ProductCustomizerModal.tsx`
- **Details**:
  - Faithful implementation of `design/screen_pos_cashier/code.html` and `design/screen_products_menu/code.html`.
  - POS two-pane layout: Catalog & Category filter (70%) + Cart & Checkout sidebar (30%).
  - Size and topping selection modal for customized drinks.

---

## 3. Acceptance Criteria & Verification Evidence

1. **Backend Tests**: `pytest` runs successfully with 0 failures and 0 errors, validating zero-float precision and snapshot pricing.
2. **Frontend Build**: `npm run build` completes with 0 TypeScript errors and 0 Vite bundling warnings.
3. **RBAC Enforcement**: Cashier attempts to create/edit product category return HTTP 403 Forbidden; Manager successfully executes CRUD.
4. **Snapshot Pricing Test**: Modifying a product's base price after an order is placed leaves historical order items unchanged.

---
