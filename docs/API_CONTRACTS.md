# API_CONTRACTS.md — REST Endpoints, Pydantic Schemas & Error Specifications (CoffeeFlow)

Tất cả các API tuân thủ chuẩn REST JSON, prefix `/api/v1` và kiểm tra quyền RBAC tại backend.

---

## 1. Global Response & Error Conventions

### 1.1. Standard Error Envelope
Mọi response lỗi (4xx, 5xx) tuân thủ cấu trúc đồng nhất:
```json
{
  "error_code": "INSUFFICIENT_STOCK",
  "message": "Nguyên liệu không đủ tồn kho để thực hiện đơn hàng.",
  "details": {
    "ingredient_name": "Sữa tươi thanh trùng",
    "required": 250,
    "available": 100,
    "unit": "ml"
  }
}
```

### 1.2. HTTP Status Code Conventions
- `200 OK`: Truy vấn hoặc cập nhật thành công.
- `201 Created`: Tạo mới thành công (Đơn hàng, Sản phẩm, Payment).
- `400 Bad Request`: Payload không hợp lệ hoặc vi phạm logic nghiệp vụ.
- `401 Unauthorized`: Chưa gửi kèm hoặc JWT token hết hạn/không hợp lệ.
- `403 Forbidden`: Người dùng không có quyền truy cập endpoint này (Ví dụ: Cashier gọi API Menu/Kho).
- `404 Not Found`: Không tìm thấy tài nguyên.
- `409 Conflict`: Xung đột trạng thái (ví dụ: Thanh toán lại đơn đã hoàn tất, trùng idempotency key).

---

## 2. Authentication Endpoints (`/api/v1/auth`)

### 2.1. Đăng nhập
- **POST** `/api/v1/auth/login` (Public)
- **Request Body**:
```json
{
  "email": "manager@coffeeflow.vn",
  "password": "SecurePassword123!"
}
```
- **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "full_name": "Nguyen Van Quan Ly",
    "email": "manager@coffeeflow.vn",
    "role": "MANAGER",
    "is_active": true
  }
}
```

### 2.2. Lấy thông tin phiên hiện tại
- **GET** `/api/v1/auth/me` (Authenticated)

---

## 3. Quản lý Nhân Viên Cashier (`/api/v1/users`) — Manager Only

### 3.1. Danh sách Cashier
- **GET** `/api/v1/users` (Query param: `?role=CASHIER&is_active=true`)

### 3.2. Tạo tài khoản Cashier
- **POST** `/api/v1/users` (Manager Only)
- **Request Body**:
```json
{
  "full_name": "Tran Thu Ngan",
  "email": "cashier1@coffeeflow.vn",
  "password": "CashierPass123!"
}
```

---

## 4. Menu & Sản Phẩm (`/api/v1/categories`, `/api/v1/products`)

### 4.1. Lấy danh sách sản phẩm hiển thị trên POS
- **GET** `/api/v1/products?is_available=true&category_id=1` (Cashier & Manager)
- **Response (200 OK)**:
```json
[
  {
    "id": 10,
    "category_id": 1,
    "name": "Cà Phê Muối",
    "description": "Cà phê pha phin truyền thống kết hợp lớp kem mặn béo ngậy",
    "image_url": "/assets/menu/cafe-muoi.png",
    "base_price": 35000,
    "is_available": true,
    "option_groups": [
      {
        "id": 1,
        "name": "Kích cỡ",
        "selection_type": "SINGLE",
        "is_required": true,
        "options": [
          {"id": 1, "name": "Size M", "price_delta": 0},
          {"id": 2, "name": "Size L", "price_delta": 6000}
        ]
      },
      {
        "id": 2,
        "name": "Topping thêm",
        "selection_type": "MULTIPLE",
        "is_required": false,
        "options": [
          {"id": 3, "name": "Thêm Kem Muối", "price_delta": 8000},
          {"id": 4, "name": "Thêm Trân Châu Trắng", "price_delta": 7000}
        ]
      }
    ]
  }
]
```

### 4.2. Quản lý Sản Phẩm (Manager Only)
- **POST** `/api/v1/products`
- **PATCH** `/api/v1/products/{id}`
- **PATCH** `/api/v1/products/{id}/availability` (`{"is_available": false}`)

---

## 5. POS & Quản Lý Đơn Hàng (`/api/v1/orders`)

### 5.1. Tạo Đơn Hàng
- **POST** `/api/v1/orders` (Cashier & Manager)
- **Header**: `Idempotency-Key: <UUID>`
- **Request Body**:
```json
{
  "order_type": "DINE_IN",
  "note": "Khách ngồi bàn 4",
  "items": [
    {
      "product_id": 10,
      "quantity": 2,
      "selected_option_ids": [2, 3],
      "note": "Ít đá"
    }
  ]
}
```
- **Response (201 Created)**:
```json
{
  "id": 101,
  "order_code": "ORD-20261013-0001",
  "order_type": "DINE_IN",
  "status": "DRAFT",
  "payment_status": "UNPAID",
  "subtotal": 98000,
  "discount_amount": 0,
  "total_amount": 98000,
  "items": [
    {
      "id": 501,
      "product_name_snapshot": "Cà Phê Muối",
      "unit_price": 49000,
      "quantity": 2,
      "subtotal": 98000,
      "selected_options_snapshot": [
        {"name": "Size L", "price_delta": 6000},
        {"name": "Thêm Kem Muối", "price_delta": 8000}
      ],
      "note": "Ít đá"
    }
  ]
}
```

### 5.2. Xác Nhận Đơn Hàng (Trừ tồn kho)
- **POST** `/api/v1/orders/{id}/confirm` (Cashier & Manager)
- Chuyển `status: "PENDING"`, tự động trừ nguyên liệu theo công thức pha chế trong database transaction.

### 5.3. Hủy Đơn Hàng
- **POST** `/api/v1/orders/{id}/cancel`
- **Request Body**: `{"reason": "Khách đổi ý hủy món"}`

---

## 6. Thanh Toán & Hoàn Tiền (`/api/v1/orders/{id}/payments`, `/api/v1/payments/{id}/refunds`)

### 6.1. Thanh toán Tiền Mặt tại quầy
- **POST** `/api/v1/orders/{id}/payments` (Cashier & Manager)
- **Header**: `Idempotency-Key: <UUID>`
- **Request Body**:
```json
{
  "payment_method": "CASH",
  "amount_tendered": 100000
}
```
- **Response (201 Created)**:
```json
{
  "id": 301,
  "transaction_code": "TXN-20261013-0001",
  "order_id": 101,
  "payment_method": "CASH",
  "amount": 98000,
  "amount_tendered": 100000,
  "change_amount": 2000,
  "status": "SUCCESS",
  "created_at": "2026-10-13T10:15:30Z"
}
```

### 6.2. Hoàn Tiền (Manager Only)
- **POST** `/api/v1/payments/{id}/refunds`
- **Request Body**:
```json
{
  "amount": 98000,
  "reason": "Làm nhầm món khách yêu cầu hoàn tiền"
}
```

---

## 7. Quản Lý Kho & Công Thức (`/api/v1/inventory/*`) — Manager Only

### 7.1. Danh sách Nguyên Liệu & Cảnh Báo Tồn Thấp
- **GET** `/api/v1/inventory/ingredients`
- **GET** `/api/v1/inventory/alerts`

### 7.2. Nhập Kho / Xuất Kho / Điều Chỉnh
- **POST** `/api/v1/inventory/movements`
- **Request Body**:
```json
{
  "ingredient_id": 5,
  "movement_type": "IN",
  "quantity_delta": 5000,
  "reason": "Nhập hạt cà phê Arabica Đà Lạt từ NCC"
}
```

### 7.3. Cấu hình Công Thức Pha Chế (Recipe)
- **POST** `/api/v1/inventory/recipes`
- **Request Body**:
```json
{
  "product_id": 10,
  "ingredient_id": 5,
  "quantity_required": 25,
  "unit": "g"
}
```

---

## 8. Dashboard & Báo Cáo Doanh Thu (`/api/v1/dashboard/summary`, `/api/v1/reports/*`) — Manager Only

### 8.1. KPI Tổng quan
- **GET** `/api/v1/dashboard/summary?start_date=2026-10-01&end_date=2026-10-13`
- **Response (200 OK)**:
```json
{
  "gross_sales": 15450000,
  "total_refunds": 98000,
  "net_sales": 15352000,
  "completed_orders_count": 312,
  "average_order_value": 49205,
  "top_products": [
    {"product_name": "Cà Phê Muối", "quantity_sold": 142, "revenue": 6958000},
    {"product_name": "Trà Đào Cam Sả", "quantity_sold": 95, "revenue": 4275000}
  ],
  "low_stock_ingredients_count": 2
}
```
