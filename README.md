# ☕ CoffeeFlow — Hệ Thống Quản Lý Quán Cà Phê & Autonomous CrewAI Flow

> **CoffeeFlow** là hệ thống quản lý chuỗi/quán cà phê chuyên nghiệp kết hợp phân hệ bán hàng tại quầy (**Cashier POS**) và phân hệ điều hành quản lý (**Manager Dashboard**). Dự án áp dụng kiến trúc Monorepo Full-Stack hiện đại (**FastAPI + React 19 Vite**) và được vận hành, phát triển tự động bởi luồng đa tác tử **CrewAI Flow (BA ➔ Backend ➔ Frontend ➔ QA)** với cơ chế **Fail-Fast Quality Gates** và **Auto-Repair**.

---

## 📌 Mục Lục
1. [Kiến Trúc Kỹ Thuật (Tech Stack & Architecture)](#-kiến-trúc-kỹ-thuật-tech-stack--architecture)
2. [Cấu Trúc Thư Mục Monorepo](#-cấu-trúc-thư-mục-monorepo)
3. [Quy Chuẩn Kỹ Thuật Cốt Lõi (Zero-Tolerance Rules)](#-quy-chuẩn-kỹ-thuật-cốt-lõi-zero-tolerance-rules)
4. [Cài Đặt & Cấu Hình Môi Trường](#-cài-đặt--cấu-hình-môi-trường)
5. [Hướng Dẫn Vận Hành CrewAI Multi-Agent Flow](#-hướng-dẫn-vận-hành-crewai-multi-agent-flow)
6. [Lộ Trình Triển Khai 6 Phase (Roadmap)](#-lộ-trình-triển-khai-6-phase-roadmap)
7. [Khởi Chạy Ứng Dụng (Deployment)](#-khởi-chạy-ứng-dụng-deployment)
8. [Kiểm Thử & Đảm Bảo Chất Lượng (Quality Assurance)](#-kiểm-thử--đảm-bảo-chất-lượng-quality-assurance)
9. [Tài Liệu Đặc Tả & Nhật Ký Phát Triển](#-tài-liệu-đặc-tả--nhật-ký-phát-triển)

---

## ⚙️ Kiến Trúc Kỹ Thuật (Tech Stack & Architecture)

### 1. Phân Hệ Backend (REST API)
- **Ngôn ngữ & Framework**: Python 3.12+, [FastAPI](https://fastapi.tiangolo.com/), Pydantic v2.
- **Cơ Sở Dữ Liệu & ORM**: PostgreSQL 16, [SQLAlchemy 2.x](https://docs.sqlalchemy.org/) (Mapped declarative, eager/lazy joins tối ưu), Alembic Migrations.
- **Bảo Mật & Xác Thực**: JWT (JSON Web Tokens), băm mật khẩu Bcrypt, kiểm soát truy cập dựa trên vai trò (Role-Based Access Control - RBAC).
- **Kiểm Thử**: `pytest` kết hợp SQLite in-memory / PostgreSQL test fixture.

### 2. Phân Hệ Frontend (Single Page Application - SPA)
- **Công Nghệ**: React 19, TypeScript, [Vite](https://vitejs.dev/), Tailwind CSS, Lucide React Icons.
- **Thiết Kế Giao Diện**: Dựa trên Design Tokens và mockup Touch-Friendly POS tại `design/DESIGN_SYSTEM.md`.
- **Bố Cục Đa Phân Hệ**:
  - Giao diện POS bán hàng (`/pos`): Tối ưu thao tác chạm nhanh, chọn kích cỡ, topping, thanh toán tiền mặt tức thì.
  - Khung giao diện quản lý dùng chung (`Layout`, `Sidebar`, `Header`): Thống nhất cho `/dashboard`, `/orders`, `/products`, `/inventory`, `/reports`.

### 3. Động Cơ Tự Động Hóa CrewAI (web_builder)
Hệ thống tích hợp quy trình phát triển phần mềm đa tác tử tự động hóa (Autonomous Flow Pipeline):

```mermaid
flowchart TD
    Start(["🚀 Bắt đầu Phase"]) --> Stage1["📋 STAGE 1: BA Requirement Analysis<br/>(Đọc PRD, Data Model, phân rã WBS tự động)"]
    
    Stage1 --> LogPlan["💾 Ghi log WBS Plan ra đĩa<br/>(output/plans/wbs_*.json & .md)"]
    
    LogPlan --> Stage2["⚙️ STAGE 2: Backend Tier Execution<br/>(Models, Schemas, Repositories, Services, APIs)"]
    
    subgraph Backend_Gate ["🛡️ Backend Fail-Fast Gate"]
        Stage2 --> BE_Test{"🧪 pytest --disable-warnings"}
        BE_Test -- "Thất bại" --> BE_Repair["🔧 Auto-Repair Backend Agent"]
        BE_Repair --> BE_Test
    end
    
    BE_Test -- "Vượt qua (100% tests pass)" --> Stage3["🎨 STAGE 3: Frontend Contract Execution<br/>(Types, API Client, Pages & Components)"]
    
    subgraph Frontend_Gate ["🛡️ Frontend Fail-Fast Gate"]
        Stage3 --> FE_Build{"🧪 npm run build (tsc + vite)"}
        FE_Build -- "Thất bại" --> FE_Repair["🔧 Auto-Repair Frontend Agent"]
        FE_Repair --> FE_Build
    end
    
    FE_Build -- "Vượt qua (0 lỗi TS)" --> Stage4["🛡️ STAGE 4: QA Acceptance Verification<br/>(Kiểm tra toàn bộ Acceptance Criteria & AT-01 đến AT-07)"]
    Stage4 --> Stage5["📊 STAGE 5: Lưu Báo Cáo Nghiệm Thu & Cập Nhật Trạng Thái"]
    Stage5 --> End(["✅ Hoàn thành Phase"])
```

---

## 📁 Cấu Trúc Thư Mục Monorepo

```text
CrewAIv2/
├── backend/                              # ☕ Phân hệ Backend (FastAPI, SQLAlchemy, Pytest)
│   ├── app/
│   │   ├── api/v1/                       # REST API Endpoints (auth, menu, pos, orders, management)
│   │   ├── core/                         # Config, Security (JWT/Bcrypt), Database Session
│   │   ├── models/                       # SQLAlchemy ORM Models (User, Category, Product, Order, v.v.)
│   │   ├── repositories/                 # Data Access Layer & DB Queries
│   │   ├── schemas/                      # Pydantic v2 Request/Response Schemas
│   │   └── services/                     # Business Logic (ACID, Concurrency Locks, Zero-Float)
│   ├── tests/                            # Bộ kiểm thử Pytest tự động (12+ tests P0)
│   ├── Dockerfile                        # Dockerfile container Backend
│   └── pyproject.toml                    # Cấu hình dependency Python
├── frontend/                             # ⚛️ Phân hệ Frontend (React 19 + TypeScript + Vite)
│   ├── src/
│   │   ├── api/                          # Axios Client với JWT Interceptors
│   │   ├── components/                   # Shared UI: Layout, Sidebar, Header, Modals, Receipt
│   │   ├── pages/                        # CashierPOS, Dashboard, ProductsMenu, Inventory, Reports, Login
│   │   ├── types/                        # TypeScript Interfaces đồng bộ 1:1 với Pydantic Schemas
│   │   └── App.tsx                       # React Router & Role-Based Guards
│   ├── Dockerfile                        # Dockerfile container Frontend (Nginx multi-stage)
│   └── package.json                      # Cấu hình NPM Scripts & Dependencies
├── design/                               # 🎨 Design System Tokens & Mockup HTML/CSS Stitch
│   └── DESIGN_SYSTEM.md                  # Hướng dẫn bảng màu, spacing, typography
├── docs/                                 # 📚 Tài liệu đặc tả sản phẩm & kỹ thuật
│   ├── PRD.md                            # Product Requirements Document chi tiết
│   ├── ARCHITECTURE.md                   # Kiến trúc hệ thống & giải pháp kỹ thuật
│   ├── DATA_MODEL.md                     # Mô hình dữ liệu & quan hệ thực thể (ERD)
│   ├── API_CONTRACTS.md                  # Hợp đồng REST API chuẩn
│   └── BUSINESS_RULES.md                 # Quy tắc nghiệp vụ bắt buộc (BR-01 đến BR-08)
├── plans/                                # 📋 Kế hoạch triển khai & phân rã công việc
│   ├── IMPLEMENT_PLAN.md                 # Lộ trình 6 Phase chi tiết
│   └── TASKS.md                          # Work Breakdown Structure (WBS) & Task Tracking
├── state/                                # 🔄 Trạng thái thực thi runtime & Agent Handoff
│   ├── PROJECT_STATE.md                  # Trạng thái hiện tại của codebase
│   └── HANDOFF.md                        # Biên bản bàn giao giữa các tác tử
├── web_builder/                          # 🧠 Nhân CrewAI Multi-Agent Pipeline
│   ├── src/web_builder/
│   │   ├── main.py                       # CodingFlow Pipeline (BA -> BE -> FE -> QA -> Gate)
│   │   ├── crews/content_crew/           # Cấu hình Agents & Tasks (YAML & Python)
│   │   └── tools/                        # Công cụ đọc kế hoạch, đo lường tiến độ, patch file
│   └── pyproject.toml                    # Cấu hình CrewAI
├── output/                               # 📊 Nhật ký thực thi, WBS logs & báo cáo QA
├── docker-compose.yml                    # 🐳 Orchestration: Postgres 16 + FastAPI + React Nginx
├── main.py                               # 🚀 CLI Runner chính (tham số --phase, --task, --mode)
├── test_crew.py                          # 🛠️ Script chẩn đoán môi trường trước khi chạy
├── AGENTS.md                             # 📜 Bộ quy tắc kỹ thuật tối cao cho AI Coding Agents
└── .env                                  # Biến môi trường & cấu hình API Keys
```

---

## 🛑 Quy Chuẩn Kỹ Thuật Cốt Lõi (Zero-Tolerance Rules)

Tất cả các thay đổi mã nguồn và tác tử AI đều phải tuân thủ nghiêm ngặt các nguyên tắc được định nghĩa tại `AGENTS.md`:

1. **Zero-Float Rule (Tiền tệ chính xác tuyệt đối)**:
   - Toàn bộ giá trị tiền tệ (`base_price`, `unit_price`, `subtotal`, `total_amount`, `amount_tendered`, `change_amount`) bắt buộc dùng kiểu số nguyên VND (`int` / `BIGINT`) hoặc `Decimal`. **Tuyệt đối không dùng `float`**.
2. **ACID Transactions**:
   - Mọi thao tác ghi nhiều bước (Tạo đơn + Snapshot giá, Xác nhận đơn + Trừ tồn kho nguyên liệu, Thanh toán tiền mặt + Chuyển trạng thái `COMPLETED`) phải nằm trong một transaction duy nhất với cơ chế rollback tự động khi có lỗi.
3. **Chống Race Condition & Idempotency**:
   - Trừ kho nguyên liệu sử dụng khóa bi quan `SELECT ... FOR UPDATE` để tránh lost-update khi nhiều cashier cùng chốt đơn.
   - Endpoint thanh toán hỗ trợ `Idempotency-Key` ngăn chặn thanh toán trùng lặp.
4. **Bảo Toàn Lịch Sử (Price Snapshots)**:
   - Thông tin giá và tên sản phẩm trong `order_items` phải được snapshot tại thời điểm mua hàng. Việc cập nhật giá sản phẩm trong thực đơn không bao giờ làm thay đổi dữ liệu đơn hàng trong quá khứ.
5. **Phân Quyền RBAC Nghiêm Ngặt**:
   - Chỉ có đúng 2 vai trò: `CASHIER` (chỉ thao tác POS và xem đơn) và `MANAGER` (toàn quyền quản trị, xem Dashboard, Kho, Báo cáo và Quản lý nhân viên). Cashier truy cập trang quản lý phải nhận mã lỗi `403 Forbidden`.

---

## 💻 Cài Đặt & Cấu Hình Môi Trường

### 1. Yêu Cầu Tiên Quyết
* **Python**: Phiên bản `>= 3.10` (Khuyên dùng Python 3.12).
* **Node.js**: Phiên bản `>= 18` (kèm `npm`).
* **Docker & Docker Compose** (để chạy database PostgreSQL và kiểm thử production).

### 2. Thiết Lập Môi Trường Ảo Python
```powershell
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Cài đặt thư viện phụ thuộc
pip install -r requirements.txt
# hoặc cài trực tiếp backend requirements:
pip install -r backend/requirements.txt
```

### 3. Thiết Lập Frontend
```powershell
cd frontend
npm install
cd ..
```

### 4. Cấu Hình Biến Môi Trường (`.env`)
Tạo file `.env` ở thư mục gốc:

```env
# Database Settings
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/coffeeflow
SECRET_KEY=supersecretkey0123456789abcdefghijklmnopqrstuvwxyz
ACCESS_TOKEN_EXPIRE_MINUTES=480

# LLM Engine cho CrewAI (Chọn 1 trong các provider)
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key-here
MODEL=openrouter/google/gemini-2.5-flash

# Hoặc dùng OpenAI:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-proj-your-key-here
# MODEL=gpt-4o-mini

# Tùy chọn Auto-Repair khi build/test thất bại (Mặc định: 3)
MAX_REPAIR_ATTEMPTS=3
```

---

## 🤖 Hướng Dẫn Vận Hành CrewAI Multi-Agent Flow

### 1. Kiểm Tra Sức Khỏe Môi Trường (System Diagnostics)
Chạy script chẩn đoán để xác thực Python, các CLI tools (`pytest`, `node`, `npm`), API key và thư mục kế hoạch:
```powershell
python test_crew.py
```
> Khi màn hình xuất hiện `✅ ALL CHECKS PASSED`, hệ thống đã sẵn sàng 100%.

### 2. Khởi Chạy Tự Động Theo Phase Với `main.py`
Pipeline tích hợp sẵn khả năng tự động đọc tài liệu trong `plans/` và `design/`, gọi tác tử BA phân rã WBS và điều phối Backend/Frontend thực thi:

```powershell
# Chạy một Phase cụ thể (Ví dụ: Phase 2 - Menu & POS Orders)
python main.py --phase 2

# Chạy một Task con cụ thể (Ví dụ: Task BE-102)
python main.py --task TASK-BE-102

# Chạy toàn bộ các Phase liên tục theo lộ trình
python main.py --phase all
```

### 3. Tùy Biến LLM Trực Tiếp Từ CLI
```powershell
# Sử dụng Gemini qua OpenRouter
python main.py --phase 2 --provider openrouter --model openrouter/google/gemini-2.5-flash

# Sử dụng OpenAI GPT-4o-mini
python main.py --phase 2 --provider openai --model gpt-4o-mini

# Sử dụng mô hình cục bộ hoặc OpenAI-compatible (Ollama / vLLM / DeepSeek)
python main.py --phase 2 --provider openai --base-url http://localhost:11434/v1 --model llama3
```

---

## 🗺️ Lộ Trình Triển Khai 6 Phase (Roadmap)

Dự án CoffeeFlow được thiết kế theo 6 Phase tăng trưởng dựa trên [docs/PRD.md](docs/PRD.md) và [plans/IMPLEMENT_PLAN.md](plans/IMPLEMENT_PLAN.md):

| Phase | Trọng Tâm Nghiệp Vụ | Tiêu Chí Hoàn Thành Chính | Lệnh Thực Thi |
| :---: | :--- | :--- | :--- |
| **Phase 1** | **Foundation & Authentication** | PostgreSQL Schema, JWT Auth, Phân quyền RBAC (`CASHIER` & `MANAGER`), Màn hình Đăng nhập `/login`. | `python main.py --phase 1` |
| **Phase 2** | **Menu Management & POS Orders** | Danh mục & Món (`categories`, `products`), Tùy chọn Size/Topping, Giao diện POS bán hàng `/pos`, Lưu Price Snapshots. | `python main.py --phase 2` |
| **Phase 3** | **Cash Payment & Idempotency** | Thanh toán tiền mặt (`CASH`), Tính tiền thối, Khóa thanh toán trùng (`Idempotency-Key`), Xem lịch sử đơn `/orders`. | `python main.py --phase 3` |
| **Phase 4** | **Inventory & Auto Stock Deduction** | Quản lý kho nguyên liệu (`ingredients`), Định lượng công thức (`recipes`), Trừ kho nguyên tử với khóa `SELECT FOR UPDATE`. | `python main.py --phase 4` |
| **Phase 5** | **Dashboard & Sales Reports** | Dashboard phân tích doanh thu `/dashboard`, Báo cáo theo ngày/tuần, Hoàn tiền (`Refund`) & Ghi nhận `audit_logs`. | `python main.py --phase 5` |
| **Phase 6** | **QA, Security & Release** | Bộ test tích hợp toàn diện (AT-01 đến AT-07), Tối ưu query, Hoàn thiện giao diện thống nhất, Đóng gói Docker Compose. | `python main.py --phase 6` |

---

## 🚀 Khởi Chạy Ứng Dụng (Deployment)

### Cách 1: Khởi Chạy Bằng Docker Compose (Khuyên Dùng Cho Production/Demo)

Hệ thống được đóng gói hoàn chỉnh gồm cơ sở dữ liệu PostgreSQL, Backend FastAPI và Frontend React:

```powershell
# Xây dựng và khởi chạy tất cả các dịch vụ chạy ngầm
docker compose up --build -d

# Xem log các dịch vụ theo thời gian thực
docker compose logs -f

# Dừng toàn bộ hệ thống
docker compose down
```

#### Các Cổng Truy Cập Dịch Vụ:
* **Frontend Web App**: [http://localhost:3000](http://localhost:3000)
* **Backend REST API**: [http://localhost:8000](http://localhost:8000) (Tài liệu OpenAPI Swagger: [http://localhost:8000/docs](http://localhost:8000/docs))
* **PostgreSQL Database**: `localhost:5432` (Database: `coffeeflow`, User: `postgres`, Pass: `postgres`)

---

### Cách 2: Khởi Chạy Thủ Công (Chế Độ Development)

#### 1. Chạy Backend:
```powershell
# Đảm bảo đã kích hoạt .venv
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Chạy Frontend:
```powershell
cd frontend
npm run dev
```
Truy cập [http://localhost:5173](http://localhost:5173) hoặc [http://localhost:3000](http://localhost:3000).

#### 3. Tài Khoản Kiểm Thử Mặc Định:
| Vai Trò | Tên Đăng Nhập | Mật Khẩu | Quyền Hạn |
| :--- | :--- | :--- | :--- |
| **Manager** | `manager1` | `securepass123` | Toàn quyền Dashboard, Menu, Kho, Báo cáo, Nhân viên, POS |
| **Cashier** | `cashier1` | `securepass123` | Bán hàng POS (`/pos`), Tạo đơn & Thanh toán tiền mặt |

---

## 🧪 Kiểm Thử & Đảm Bảo Chất Lượng (Quality Assurance)

Codebase CoffeeFlow áp dụng cổng kiểm định kép (Dual-Quality Gates). Bạn có thể tự kích hoạt kiểm thử bất kỳ lúc nào:

### 1. Kiểm Thử Backend (Pytest Suite)
Bộ kiểm thử tự động kiểm tra xác thực, RBAC, tạo đơn, snapshot giá, thanh toán trùng và khóa kho:
```powershell
# Chạy toàn bộ 12 test cases kiểm thử tự động
.\.venv\Scripts\python.exe -m pytest backend/tests -v
```
> Kết quả tiêu chuẩn: **12 passed, 0 failures, 0 errors**.

### 2. Kiểm Thử Frontend (TypeScript Type-Check & Production Build)
Xác thực tính toàn vẹn của mã nguồn TypeScript và đóng gói Vite:
```powershell
cd frontend
npm run build
cd ..
```
> Kết quả tiêu chuẩn: **0 TypeScript errors, build thành công bundle production**.

---

## 📚 Tài Liệu Đặc Tả & Nhật Ký Phát Triển

Để hiểu sâu hơn về kiến trúc và các quy định kỹ thuật của dự án, vui lòng tham khảo các tài liệu chi tiết:
- [docs/PRD.md](docs/PRD.md): Bản đặc tả yêu cầu sản phẩm đầy đủ (User Stories, Acceptance Tests AT-01 -> AT-07).
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Kiến trúc phân tầng, giải pháp kỹ thuật, cơ chế caching và logging.
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md): Chi tiết cấu trúc các bảng dữ liệu, khóa ngoại và chỉ mục.
- [docs/API_CONTRACTS.md](docs/API_CONTRACTS.md): Danh sách toàn bộ Endpoint, Request Payload và Response Codes.
- [docs/BUSINESS_RULES.md](docs/BUSINESS_RULES.md): 8 nguyên tắc nghiệp vụ cốt lõi không được vi phạm.
- [plans/IMPLEMENT_PLAN.md](plans/IMPLEMENT_PLAN.md): Chi tiết lộ trình thực hiện từng giai đoạn.
- [state/PROJECT_STATE.md](state/PROJECT_STATE.md): Nhật ký trạng thái hoàn thành và biên bản xác thực thực tế.
- [AGENTS.md](AGENTS.md): Bản hợp đồng làm việc và các quy tắc tối cao cho AI Coding Assistants.
