# TASKS.md — Work Breakdown Structure & Task Tracking (CoffeeFlow)

Tài liệu này quản lý danh sách công việc nguyên tử theo Task ID, người phụ trách (Owner), trạng thái thực hiện và tiêu chí hoàn thành.

---

## 1. Task Summary Dashboard
- **Tổng số tasks**: 8 (Phase 1 & Phase 2 baseline)
- **Đã hoàn thành (`DONE`)**: 8
- **Đang thực hiện (`IN_PROGRESS`)**: 0
- **Sẵn sàng (`TODO`)**: 0
- **Bị chặn (`BLOCKED`)**: 0

---

## 2. Phase 1 Tasks: Foundation & Authentication

| Task ID | Tiêu đề công việc | Owner | Trạng thái | Dependencies |
| :--- | :--- | :--- | :--- | :--- |
| `TASK-BE-101` | Khởi tạo Backend FastAPI, cấu hình Docker Compose Postgres và Alembic | Backend | `TODO` | - |
| `TASK-BE-102` | Triển khai User model, Password Hashing, JWT Auth và RBAC Dependency | Backend | `TODO` | `TASK-BE-101` |
| `TASK-BE-103` | Viết Auth Endpoints (`/login`, `/me`) và Pytest Auth Test Suite | Backend | `TODO` | `TASK-BE-102` |
| `TASK-FE-101` | Khởi tạo Frontend React + Vite + Tailwind, Auth API client và TypeScript types | Frontend | `TODO` | `TASK-BE-103` |
| `TASK-FE-102` | Xây dựng màn hình Đăng nhập `/login` và Router ProtectedRoute theo Role | Frontend | `TODO` | `TASK-FE-101` |

---

## 3. Phase 2 Tasks: Menu Management & POS Order Creation

| Task ID | Tiêu đề công việc | Owner | Trạng thái | Dependencies |
| :--- | :--- | :--- | :--- | :--- |
| `TASK-BE-201` | Triển khai Models & CRUD APIs cho Danh mục (`categories`) và Món (`products`) | Backend | `TODO` | `TASK-BE-103` |
| `TASK-BE-202` | Triển khai Order & OrderItem Models, API tạo đơn kèm Price Snapshots | Backend | `TODO` | `TASK-BE-201` |
| `TASK-FE-201` | Xây dựng giao diện POS `/pos`: Lưới món, Bộ chọn Size/Topping và Giỏ hàng | Frontend | `TODO` | `TASK-BE-202` |

---

## 4. Chi Tiết Tiêu Chí Nghiệm Thu (Acceptance Criteria)

### `TASK-BE-101` & `TASK-BE-102`: Core Auth & RBAC
- Model `User` có `email` (unique), `password_hash`, `role` (`CASHIER` hoặc `MANAGER`), `is_active` (boolean).
- Mật khẩu được băm bằng Bcrypt (không lưu plaintext).
- Middleware dependency `require_role(["MANAGER"])` trả về 403 khi Cashier truy cập.
- Pytest kiểm thử đăng nhập đúng thành công, đăng nhập sai trả về 401, tài khoản vô hiệu hóa không đăng nhập được.

### `TASK-FE-101` & `TASK-FE-102`: Frontend Login
- Form đăng nhập có validation email và mật khẩu.
- Lưu JWT access token vào `localStorage` hoặc secure cookie.
- Tự động điều hướng: `MANAGER` vào `/dashboard` hoặc `/pos`, `CASHIER` vào `/pos`.
- Chặn Cashier truy cập route quản lý của Manager.

### `TASK-BE-201` & `TASK-BE-202`: Menu & Orders
- `products.base_price` lưu kiểu integer VND.
- Khi tạo đơn, backend tính toán `unit_price = base_price + sum(options)` và lưu snapshot vào `order_items`.
- Backend tự sinh `order_code` duy nhất.
- Kiểm tra tính bất biến: Thay đổi giá ở bảng `products` không làm sai lệch số tiền của các đơn hàng đã tạo trước đó.
