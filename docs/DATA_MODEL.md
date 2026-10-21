# DATA_MODEL.md — Database Schema, Entities & Constraints (CoffeeFlow)

## 1. Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    USERS ||--o{ ORDERS : "creates"
    USERS ||--o{ PAYMENTS : "processes"
    USERS ||--o{ STOCK_MOVEMENTS : "records"
    USERS ||--o{ AUDIT_LOGS : "acts"

    CATEGORIES ||--o{ PRODUCTS : "contains"
    PRODUCTS ||--o{ PRODUCT_OPTION_GROUPS : "configured with"
    OPTION_GROUPS ||--o{ PRODUCT_OPTION_GROUPS : "linked to"
    OPTION_GROUPS ||--o{ OPTIONS : "contains"

    PRODUCTS ||--o{ RECIPES : "composed of"
    PRODUCTS ||--o{ ORDER_ITEMS : "ordered as"

    INGREDIENTS ||--o{ RECIPES : "used in"
    INGREDIENTS ||--o{ STOCK_MOVEMENTS : "tracked by"

    ORDERS ||--o{ ORDER_ITEMS : "contains"
    ORDERS ||--o{ PAYMENTS : "paid via"

    PAYMENTS ||--o{ REFUNDS : "refunded by"

    USERS {
        bigint id PK
        varchar full_name
        varchar email UK
        varchar password_hash
        varchar role "CASHIER | MANAGER"
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    CATEGORIES {
        bigint id PK
        varchar name UK
        text description
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    PRODUCTS {
        bigint id PK
        bigint category_id FK
        varchar name UK
        text description
        varchar image_url
        bigint base_price "Zero-Float VND"
        boolean is_available
        timestamp created_at
        timestamp updated_at
    }

    OPTION_GROUPS {
        bigint id PK
        varchar name "Kích cỡ / Topping / Độ ngọt / Đá"
        varchar selection_type "SINGLE | MULTIPLE"
        boolean is_required "True for Size, False for Topping"
        boolean is_active
        timestamp created_at
    }

    OPTIONS {
        bigint id PK
        bigint group_id FK
        varchar name "Size S, Size M, Size L, Trân châu..."
        bigint price_delta "Zero-Float VND"
        boolean is_active
    }

    PRODUCT_OPTION_GROUPS {
        bigint id PK
        bigint product_id FK
        bigint group_id FK
    }

    ORDERS {
        bigint id PK
        varchar order_code UK
        varchar order_type "DINE_IN | TAKEAWAY"
        bigint created_by FK
        varchar status "DRAFT | PENDING | COMPLETED | CANCELLED"
        varchar payment_status "UNPAID | PAID | PARTIALLY_REFUNDED | REFUNDED"
        bigint subtotal
        bigint discount_amount
        bigint total_amount
        text note
        timestamp created_at
        timestamp updated_at
    }

    ORDER_ITEMS {
        bigint id PK
        bigint order_id FK
        bigint product_id FK
        varchar product_name_snapshot
        bigint unit_price
        integer quantity
        bigint subtotal
        jsonb selected_options_snapshot
        text note
    }

    PAYMENTS {
        bigint id PK
        varchar transaction_code UK
        bigint order_id FK
        bigint processed_by FK
        varchar payment_method "CASH"
        bigint amount
        bigint amount_tendered
        bigint change_amount
        varchar status "SUCCESS | FAILED | REFUNDED | PARTIALLY_REFUNDED"
        varchar idempotency_key UK
        timestamp created_at
    }

    REFUNDS {
        bigint id PK
        bigint payment_id FK
        bigint processed_by FK
        bigint amount
        varchar reason
        varchar status "SUCCESS | FAILED"
        timestamp created_at
    }

    INGREDIENTS {
        bigint id PK
        varchar name UK
        varchar unit "g | kg | ml | l | piece"
        numeric current_stock
        numeric minimum_stock
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    RECIPES {
        bigint id PK
        bigint product_id FK
        bigint ingredient_id FK
        numeric quantity_required
        varchar unit
    }

    STOCK_MOVEMENTS {
        bigint id PK
        bigint ingredient_id FK
        varchar movement_type "IN | OUT | ADJUSTMENT | SALE_CONSUMPTION | REVERSAL"
        numeric quantity_delta
        varchar reason
        varchar reference_type "ORDER | MANUAL | AUDIT"
        bigint reference_id
        bigint created_by FK
        timestamp created_at
    }

    AUDIT_LOGS {
        bigint id PK
        bigint actor_user_id FK
        varchar action
        varchar entity_type
        bigint entity_id
        jsonb before_value
        jsonb after_value
        varchar reason
        timestamp created_at
    }
```

---

## 2. Table Specifications & Constraints

### 2.1. `users`
- `role`: Restricted to enum `'CASHIER'`, `'MANAGER'`.
- `email`: Case-insensitive unique constraint.
- `password_hash`: Bcrypt hash (cost >= 10).

### 2.2. `products`, `option_groups`, `options` & `product_option_groups` (Phương án B)
- `products.base_price`: `BIGINT NOT NULL CHECK (base_price >= 0)` (VND integer).
- `option_groups`:
  - `selection_type`: `'SINGLE'` (radio: chọn 1 duy nhất, ví dụ Size, Mức đá, Lượng đường) hoặc `'MULTIPLE'` (checkbox: chọn nhiều, ví dụ Topping).
  - `is_required`: `TRUE` (bắt buộc chọn, ví dụ Size) hoặc `FALSE` (tùy chọn, ví dụ Topping).
- `options`:
  - `price_delta`: `BIGINT NOT NULL DEFAULT 0 CHECK (price_delta >= 0)` (Khoản tiền cộng thêm VND).
- Soft delete / availability: `is_available = FALSE` thay vì xóa cứng.

### 2.3. `orders` & `order_items`
- `order_code`: Unique e.g. `ORD-YYYYMMDD-XXXX`.
- `total_amount = subtotal - discount_amount`.
- `order_items.unit_price = base_price + sum(option_price_deltas)`.
- `selected_options_snapshot`: Lưu cấu trúc JSON array ghi lại chính xác tên nhóm, tên option và giá cộng thêm tại thời điểm đặt đơn:
  ```json
  [
    {"group_name": "Kích cỡ", "option_name": "Size L", "price_delta": 6000},
    {"group_name": "Topping", "option_name": "Kem Phô Mai", "price_delta": 10000}
  ]
  ```

### 2.4. `payments` & `refunds`
- `payment_method`: Defaults to `'CASH'` for MVP.
- `idempotency_key`: Unique string provided by client to prevent duplicate submissions.
- Total refunded amount on any payment cannot exceed `payment.amount`.

### 2.5. `ingredients`, `recipes` & `stock_movements`
- `unit`: Normalized unit strings (`g`, `ml`, `piece`).
- `current_stock`: Updated inside the same transaction as order confirmation.
- Concurrency protection: `SELECT ... FOR UPDATE` on `ingredients` during consumption to prevent lost updates.

### 2.6. `audit_logs`
- Append-only table. Read-only for `MANAGER`, completely forbidden for `CASHIER`.
- Stores sensitive actions: account disablement, price updates, order cancellation, refunds, stock adjustments.

---

## 3. Migration Strategy (Alembic)
- Alembic manages schema versioning in `backend/alembic/versions/`.
- Seed data migration: Default Admin Manager account, initial categories, default option groups (Size, Topping, Ice, Sugar) and starter ingredients.
