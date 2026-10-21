# DESIGN_SYSTEM.md — CoffeeFlow UI Design System & Stitch Screen Directory

> **Design Source of Truth**: Bộ thiết kế **Artisan Operational Craft** xuất từ Google Stitch.  
> Toàn bộ giao diện frontend (React + Tailwind CSS) phải tuân thủ nghiêm ngặt bảng token và cấu trúc HTML mẫu trong thư mục `design/`.

---

## 1. Danh mục màn hình Stitch (Mockup Catalog)

Hệ thống gồm 7 màn hình hoàn chỉnh kèm mã HTML/CSS và thiết kế gốc tại thư mục `design/`:

| STT | Tên màn hình | Thư mục Mockup | Đường dẫn mã nguồn | Đường dẫn Route ứng dụng | Mô tả & Chức năng chính |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | **Đăng nhập hệ thống** | `screen_login/` | [code.html](file:///C:/Users/Minnut/Desktop/VSCode/CrewAI%20-%20Copy/design/screen_login/code.html) | `/login` | Form đăng nhập nhân viên/quản lý, ca làm việc, chọn chi nhánh, ghi nhớ phiên. |
| **02** | **Bán hàng POS** | `screen_pos_cashier/` | [code.html](file:///C:/Users/Minnut/Desktop/VSCode/CrewAI%20-%20Copy/design/screen_pos_cashier/code.html) | `/pos` | Giao diện thu ngân 2 cột (70% danh mục món / 30% giỏ hàng), phím tắt F1-F9, chọn Size/Đá/Đường/Topping, thanh toán tiền mặt/QR. |
| **03** | **Tổng quan quản lý** | `screen_dashboard_overview/` | [code.html](file:///C:/Users/Minnut/Desktop/VSCode/CrewAI%20-%20Copy/design/screen_dashboard_overview/code.html) | `/dashboard` | Dashboard điều hành quán: Doanh thu theo ca, số đơn, món bán chạy, biểu đồ giờ cao điểm, cảnh báo tồn kho. |
| **04** | **Quản lý đơn hàng** | `screen_orders_management/` | [code.html](file:///C:/Users/Minnut/Desktop/VSCode/CrewAI%20-%20Copy/design/screen_orders_management/code.html) | `/orders` | Danh sách đơn hàng thời gian thực, lọc trạng thái (`PENDING`, `COMPLETED`, `CANCELLED`), xem chi tiết đơn, hủy đơn và hoàn tiền. |
| **05** | **Quản lý sản phẩm** | `screen_products_menu/` | [code.html](file:///C:/Users/Minnut/Desktop/VSCode/CrewAI%20-%20Copy/design/screen_products_menu/code.html) | `/menu` | CRUD sản phẩm, phân loại danh mục, cấu hình nhóm tùy chọn (Size, Topping), bật/tắt trạng thái món hết hàng (`is_available`). |
| **06** | **Kho nguyên liệu** | `screen_inventory_stock/` | [code.html](file:///C:/Users/Minnut/Desktop/VSCode/CrewAI%20-%20Copy/design/screen_inventory_stock/code.html) | `/inventory` | Danh mục nguyên liệu (hạt cafe, sữa tươi, siro...), định lượng tồn kho, cảnh báo sắp hết (Low-stock threshold), nhập kho. |
| **07** | **Báo cáo doanh thu** | `screen_reports_revenue/` | [code.html](file:///C:/Users/Minnut/Desktop/VSCode/CrewAI%20-%20Copy/design/screen_reports_revenue/code.html) | `/reports` | Báo cáo chi tiết theo ngày/tuần/tháng, phương thức thanh toán (Tiền mặt vs Chuyển khoản), tỷ suất bán mang về vs tại chỗ. |

---

## 2. Token thiết kế chuẩn (Design Tokens)

Trích xuất trực tiếp từ [design/artisan_operational_craft/DESIGN.md](file:///C:/Users/Minnut/Desktop/VSCode/CrewAI%20-%20Copy/design/artisan_operational_craft/DESIGN.md):

### 2.1. Bảng màu (Color Palette)
```javascript
// tailwind.config.js extend colors:
colors: {
  // Brand & Espresso Surface
  "primary": "#220f05",              // Màu nâu đậm thương hiệu (Espresso Roaster)
  "primary-container": "#3a2317",    // Nền nút / container chính
  "on-primary": "#ffffff",
  "on-primary-container": "#ab8878",
  
  // Secondary (Caramel / Honey Accent)
  "secondary": "#88512a",            // Nâu caramel ấm
  "secondary-container": "#fdb385",  // Điểm nhấn badge, tag, highlight
  "on-secondary-container": "#78431e",
  
  // Neutral Surfaces & Containers
  "background": "#fff8f5",           // Nền chung ứng dụng (Warm cream)
  "surface": "#fff8f5",
  "surface-container-lowest": "#ffffff", // Nền thẻ card trắng
  "surface-container-low": "#fff1e9",    // Nền thanh Sidebar / Sub-bar
  "surface-container": "#fdeadf",
  "surface-container-high": "#f7e5d9",
  "surface-container-highest": "#f1dfd4",
  
  // Text & Border Colors
  "on-surface": "#231a13",           // Văn bản chính (gần đen ấm)
  "on-surface-variant": "#50443f",   // Văn bản phụ / Label
  "outline": "#82746f",              // Border phụ / placeholder
  "outline-variant": "#d4c3bc",      // Đường chia phân cách mờ
  
  // Semantic & Alerts
  "error": "#ba1a1a",                // Báo đỏ / Cảnh báo hết kho / Đơn hủy
  "error-container": "#ffdad6",
  "on-error-container": "#93000a",
  "tertiary": "#001907",             // Điểm nhấn thành công / Hoàn thành
  "tertiary-container": "#003013"
}
```

### 2.2. Kiểu chữ & Typography (Plus Jakarta Sans)
- **Display Large**: `32px / 40px`, bold (`700`), letter-spacing `-0.02em`
- **Headline Large / Medium**: `24px` / `20px`, semi-bold (`600`)
- **Headline Small**: `16px`, semi-bold (`600`)
- **Body Large / Medium / Small**: `16px` / `14px` / `12px`, normal (`400`)
- **Hotkey Badge**: `11px`, bold (`700`), letter-spacing `0.02em` (F1, F2, F4, F9)
- **Currency Cell & Display**: `14px` (table cell) / `22px` (POS total summary), bold (`700`)

### 2.3. Quy chuẩn phím tắt POS (Hotkeys)
Theo thiết kế chuẩn tại [screen_pos_cashier/code.html](file:///C:/Users/Minnut/Desktop/VSCode/CrewAI%20-%20Copy/design/screen_pos_cashier/code.html#L11-L18):
- **`F1`**: Trở về màn hình Bán hàng (Mặc định).
- **`F2`**: Focus vào ô Tìm kiếm món nhanh (`#posSearchInput`).
- **`F4`**: Chuyển đổi trạng thái Đơn: Tại bàn / Mang đi.
- **`F9`**: Mở hộp thoại Thanh toán hóa đơn (Checkout Modal).

---

## 3. Quy tắc tích hợp cho Frontend Agent

1. **Tái sử dụng HTML/CSS từ Stitch**: Khi triển khai các component React trong `frontend/src/pages/` hoặc `components/`, agent PHẢI tham chiếu trực tiếp markup trong file `code.html` của thư mục `screen_*` tương ứng.
2. **Iconography**: Sử dụng thư viện **Google Material Symbols Outlined** (ví dụ `<span className="material-symbols-outlined">local_cafe</span>`).
3. **Responsive & Cảm ứng**:
   - Màn hình POS tối ưu cho màn hình Tablet (1024px+) và Desktop (1280px+).
   - Chiều cao các nút cảm ứng tối thiểu `44px` để bấm dễ dàng bằng ngón tay.
4. **Định dạng tiền tệ**: Luôn format VND theo chuẩn Việt Nam (ví dụ: `45.000 ₫`). Không bao giờ hiển thị phần thập phân.
