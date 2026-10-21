# PRD — CoffeeFlow
## Coffee Shop Management System

**Version:** 1.1  
**Status:** Ready for architecture and implementation planning  
**Product type:** Internal coffee shop management web application  
**Primary language:** Vietnamese  
**Currency:** VND  
**Timezone:** Asia/Ho_Chi_Minh  
**Deployment scope:** One coffee shop  
**Primary roles:** `CASHIER`, `MANAGER`

---

## 1. Product Overview

### 1.1. Product Description

CoffeeFlow là web application quản lý hoạt động kinh doanh của một quán cafe. Hệ thống số hóa quy trình bán hàng, thanh toán, quản lý menu, quản lý nguyên liệu và theo dõi doanh thu.

Cashier sử dụng POS để tạo đơn và thanh toán tại quầy. Manager quản lý menu, kho, nhân viên và báo cáo kinh doanh.

### 1.2. Problem Statement

Các quán cafe nhỏ và vừa có thể gặp những vấn đề sau:

- Đơn hàng được ghi nhận thủ công, dễ xảy ra sai sót.
- Giá bán và trạng thái món thiếu nhất quán.
- Khó theo dõi số lượng nguyên liệu còn lại.
- Thiếu báo cáo tổng hợp doanh thu và sản phẩm bán chạy.
- Không có lịch sử rõ ràng cho thao tác hủy đơn, hoàn tiền hoặc điều chỉnh tồn kho.
- Nhân viên có thể truy cập những chức năng không thuộc trách nhiệm của mình.

CoffeeFlow giải quyết các vấn đề này bằng cách tập trung dữ liệu, phân quyền theo vai trò và chuẩn hóa quy trình nghiệp vụ.

### 1.3. Product Goals

- Quản lý tập trung đơn hàng và giao dịch thanh toán.
- Giảm thao tác tạo đơn tại quầy.
- Quản lý menu và giá bán nhất quán.
- Theo dõi nguyên liệu và phát hiện tồn kho thấp.
- Cung cấp báo cáo kinh doanh đáng tin cậy.
- Bảo đảm khả năng truy vết các thao tác quan trọng.

### 1.4. Success Metrics

Các mục tiêu dưới đây là tiêu chí đề xuất để đánh giá MVP, không phải kết quả thực tế đã được đo lường.

| Metric | Target |
|---|---|
| Tạo đơn hàng thông thường | Hoàn tất trong tối đa 5 thao tác chính sau khi bắt đầu chọn món |
| Thời gian phản hồi API thông thường | p95 dưới 500 ms trong môi trường kiểm thử mục tiêu |
| Tính nhất quán dữ liệu thanh toán | Không ghi nhận trùng do retry cùng yêu cầu |
| Phân quyền | 100% API được bảo vệ theo chính sách truy cập |
| Báo cáo doanh thu | Khớp các giao dịch hợp lệ theo quy tắc báo cáo |
| Kiểm thử | Tất cả test case P0 pass trước khi phát hành |

---

## 2. User Roles and Permissions

CoffeeFlow có hai role nghiệp vụ.

### 2.1. Cashier — Nhân viên thu ngân

**Trách nhiệm chính:** Tạo đơn hàng và xử lý thanh toán.

Quyền hạn:

- Đăng nhập và đăng xuất.
- Xem menu và giá bán hiện hành.
- Tạo đơn tại quán hoặc mang đi.
- Thêm, sửa, xóa món trong đơn chưa xác nhận.
- Chọn size, topping và số lượng nếu sản phẩm hỗ trợ.
- Thêm ghi chú cho món.
- Xem tổng tiền và áp dụng khuyến mại được hệ thống cho phép.
- Xác nhận đơn và thực hiện thanh toán.
- Xem hóa đơn và tra cứu đơn hàng theo quyền được cấp.
- Hủy đơn chưa thanh toán theo điều kiện nghiệp vụ.
- Xem lịch sử giao dịch do mình thực hiện.

Không được phép:

- Tạo, sửa hoặc ngừng bán sản phẩm.
- Thay đổi giá menu.
- Quản lý nguyên liệu hoặc điều chỉnh tồn kho.
- Xem báo cáo doanh thu tổng hợp của toàn quán.
- Tự hoàn tiền hoặc hủy giao dịch đã thanh toán.
- Quản lý tài khoản Manager.
- Thay đổi cấu hình hệ thống.

### 2.2. Manager — Quản lý quán

**Trách nhiệm chính:** Quản lý hoạt động kinh doanh, menu, kho và nhân viên.

Quyền hạn:

- Truy cập dashboard và báo cáo kinh doanh.
- Xem toàn bộ đơn hàng và giao dịch.
- Tạo đơn và thực hiện thanh toán như Cashier.
- Quản lý danh mục, sản phẩm, giá bán, size và topping.
- Bật hoặc tắt trạng thái bán của sản phẩm.
- Quản lý nguyên liệu, công thức pha chế và mức tồn tối thiểu.
- Nhập kho, xuất kho và điều chỉnh tồn kho.
- Xem lịch sử biến động kho.
- Xử lý các trường hợp hủy đơn và hoàn tiền theo chính sách.
- Tạo, vô hiệu hóa và quản lý tài khoản Cashier.
- Xem lịch sử thao tác quan trọng.
- Cấu hình các thông số vận hành được hỗ trợ.

### 2.3. Permission Matrix

| Feature | Cashier | Manager |
|---|---|---|
| Đăng nhập, đăng xuất | Yes | Yes |
| Xem menu | Yes | Yes |
| Tạo đơn hàng | Yes | Yes |
| Thanh toán | Yes | Yes |
| Tra cứu đơn hàng | Đơn liên quan theo quyền | Tất cả đơn |
| Hủy đơn chưa thanh toán | Có điều kiện | Yes |
| Hoàn tiền | No | Yes, theo chính sách |
| Quản lý menu | No | Yes |
| Quản lý giá bán | No | Yes |
| Quản lý kho | No | Yes |
| Xem báo cáo doanh thu | No | Yes |
| Quản lý tài khoản Cashier | No | Yes |
| Xem audit log | No | Yes |
| Thay đổi cấu hình | No | Yes |

Tất cả quyền phải được kiểm tra tại backend. Việc ẩn menu hoặc nút trên frontend không thay thế authorization.

---

## 3. Scope and Priorities

### 3.1. P0 — MVP Core Features

1. Authentication và role-based access control.
2. Dashboard kinh doanh cơ bản.
3. Quản lý danh mục và sản phẩm.
4. Quản lý size, topping và giá bán.
5. POS và quản lý đơn hàng.
6. Thanh toán tiền mặt.
7. Tra cứu đơn và xem hóa đơn.
8. Quản lý nguyên liệu cơ bản.
9. Nhập kho và điều chỉnh tồn kho.
10. Quản lý công thức pha chế và trừ kho theo đơn.
11. Báo cáo doanh thu cơ bản.
12. Quản lý tài khoản Cashier.
13. Audit log cho các thao tác nhạy cảm.

### 3.2. P1 — Post-MVP

- Thanh toán QR và tích hợp cổng thanh toán.
- In hóa đơn qua máy in POS.
- Quản lý ca làm và đối soát tiền mặt cuối ca.
- Quản lý nhà cung cấp và đơn nhập hàng.
- Xuất báo cáo CSV.
- Voucher và chương trình khuyến mại nâng cao.
- Đồng bộ dữ liệu đơn hàng theo thời gian thực bằng WebSocket.
- Quản lý bàn và sơ đồ bàn nâng cao.

### 3.3. Out of Scope

- Ứng dụng mobile native.
- Hệ thống kế toán đầy đủ.
- Tích hợp ngân hàng trực tiếp trong MVP.
- Quản lý lương và chấm công chuyên sâu.
- Quản lý nhiều chi nhánh trong MVP.
- Website đặt món dành cho khách hàng trong MVP.
- Dự báo AI trong MVP.

---

## 4. Functional Requirements

### FR-01 — Authentication and Account Management

**Description:** Hệ thống xác thực người dùng và giới hạn truy cập theo role.

Requirements:

- FR-01.1: Người dùng đăng nhập bằng email và mật khẩu.
- FR-01.2: Hệ thống xác minh tài khoản đang hoạt động trước khi cấp quyền truy cập.
- FR-01.3: Người dùng có thể đăng xuất.
- FR-01.4: Manager có thể tạo tài khoản Cashier.
- FR-01.5: Manager có thể vô hiệu hóa tài khoản Cashier.
- FR-01.6: Hệ thống từ chối đăng nhập bằng tài khoản đã vô hiệu hóa.
- FR-01.7: Hệ thống kiểm tra quyền tại mỗi API được bảo vệ.
- FR-01.8: Mật khẩu phải được hash bằng thuật toán phù hợp, không lưu plaintext.
- FR-01.9: Frontend chỉ hiển thị chức năng mà role hiện tại được phép sử dụng.

Acceptance criteria:

- Đăng nhập đúng thông tin và tài khoản hợp lệ sẽ thành công.
- Đăng nhập sai mật khẩu bị từ chối.
- Cashier gọi API quản lý menu hoặc kho phải nhận lỗi 403.
- Người chưa xác thực truy cập API bảo vệ phải nhận lỗi 401.
- Tài khoản bị vô hiệu hóa không thể tạo phiên đăng nhập mới.
- Không thể tạo tài khoản Manager thông qua chức năng quản lý Cashier.

### FR-02 — Dashboard

**Description:** Manager theo dõi tình hình kinh doanh qua các chỉ số tổng hợp.

Dashboard hiển thị:

- Tổng doanh thu.
- Số đơn đã thanh toán.
- Giá trị đơn hàng trung bình.
- Biểu đồ doanh thu theo ngày.
- Top sản phẩm theo số lượng bán.
- Sản phẩm sắp hết nguyên liệu hoặc tạm ngừng bán.
- Tổng giá trị hoàn tiền trong kỳ.
- Bộ lọc theo ngày, tuần, tháng hoặc khoảng thời gian tùy chỉnh.

Business rules:

- Chỉ Manager được truy cập dashboard kinh doanh.
- Doanh thu được tính từ giao dịch thanh toán hợp lệ, trừ các khoản hoàn tiền đã được ghi nhận theo quy tắc báo cáo.
- Đơn bị hủy trước thanh toán không được tính doanh thu.
- Đơn chưa thanh toán không được tính doanh thu.
- Khoảng thời gian báo cáo được hiểu theo múi giờ `Asia/Ho_Chi_Minh`.
- Các chỉ số dashboard phải thống nhất với trang báo cáo.
- Không sử dụng số liệu giả lập trong môi trường production.

Acceptance criteria:

- Manager chọn một khoảng ngày và nhận dữ liệu tương ứng.
- Khoảng ngày không hợp lệ phải được từ chối.
- Dashboard không có dữ liệu phải hiển thị trạng thái empty.
- Khi có giao dịch hoàn tiền, báo cáo cập nhật theo quy tắc đã quy định.

### FR-03 — Category Management

**Description:** Manager quản lý danh mục sản phẩm.

Category fields:

- `id`
- `name`
- `description`
- `is_active`
- `created_at`
- `updated_at`

Requirements:

- Tạo danh mục.
- Xem danh sách danh mục.
- Sửa tên và mô tả.
- Kích hoạt hoặc ngừng sử dụng danh mục.
- Tìm kiếm danh mục.
- Không cho phép tên danh mục trùng theo quy tắc chuẩn hóa đã xác định.
- Không xóa cứng danh mục đang được sản phẩm tham chiếu.
- Sản phẩm thuộc danh mục ngừng hoạt động không được xuất hiện trong luồng tạo đơn mới nếu chính sách menu quy định ngừng bán theo danh mục.

### FR-04 — Product and Menu Management

**Description:** Manager quản lý menu được Cashier sử dụng để tạo đơn.

Product fields:

- `id`
- `category_id`
- `name`
- `description`
- `image_url`
- `base_price`
- `is_available`
- `created_at`
- `updated_at`

Requirements:

- FR-04.1: Tạo sản phẩm.
- FR-04.2: Xem và tìm kiếm sản phẩm.
- FR-04.3: Sửa thông tin sản phẩm.
- FR-04.4: Thay đổi giá bán.
- FR-04.5: Kích hoạt hoặc tạm ngừng bán sản phẩm.
- FR-04.6: Lọc sản phẩm theo danh mục và trạng thái.
- FR-04.7: Phân trang danh sách sản phẩm.
- FR-04.8: Cấu hình các size và topping được phép chọn.
- FR-04.9: Lưu snapshot tên và giá sản phẩm trong từng order item.
- FR-04.10: Chỉ Manager được thay đổi dữ liệu menu.

Business rules:

- Giá sản phẩm phải lớn hơn hoặc bằng 0; sản phẩm được bán phải có giá hợp lệ theo chính sách cấu hình.
- Giá và số lượng sử dụng kiểu dữ liệu chính xác, không dùng floating point cho tiền.
- Sản phẩm đã được sử dụng trong đơn không được xóa cứng làm mất lịch sử.
- Sản phẩm ngừng bán không thể được thêm vào đơn mới.
- Thay đổi giá menu không làm thay đổi đơn hàng đã tạo.
- Nếu sản phẩm có size hoặc topping bắt buộc, backend phải kiểm tra lựa chọn hợp lệ.

Acceptance criteria:

- Cashier nhìn thấy giá bán hiện hành.
- Cashier không thể sửa giá bằng cách gửi request trực tiếp.
- Manager cập nhật giá thành công; đơn cũ giữ nguyên giá snapshot.
- Sản phẩm không hoạt động bị từ chối khi thêm vào đơn mới.

### FR-05 — Size and Topping Management

**Description:** Hỗ trợ các biến thể đồ uống.

Ví dụ:

- Size: S, M, L.
- Topping: trân châu, thạch, kem cheese.
- Tùy chọn đường và đá nếu được cấu hình.

Requirements:

- Manager tạo và sửa các lựa chọn của sản phẩm.
- Mỗi tùy chọn có tên, giá cộng thêm và trạng thái hoạt động.
- Cashier chọn các tùy chọn được hỗ trợ khi tạo đơn.
- Giá cuối cùng được tính từ giá cơ bản, giá size và giá topping.
- Lưu snapshot tên và giá của từng lựa chọn trong order item.

Business rule:

`unit_price = base_price + size_price_delta + sum(topping_price_delta)`

Nếu sản phẩm sử dụng bảng giá theo size thay vì giá cộng thêm, hệ thống phải áp dụng đúng chiến lược giá đã cấu hình, không áp dụng đồng thời hai phương pháp.

### FR-06 — Order Management and POS

**Description:** Cashier tạo và quản lý đơn hàng tại quầy.

Order types:

- `DINE_IN`: Tại quán.
- `TAKEAWAY`: Mang đi.

Order status:

- `DRAFT`: Đang tạo, chưa xác nhận.
- `PENDING`: Đã xác nhận, chờ xử lý.
- `COMPLETED`: Đã thanh toán và kết thúc.
- `CANCELLED`: Đã hủy.

Trạng thái thanh toán được quản lý riêng:

- `UNPAID`
- `PAID`
- `PARTIALLY_REFUNDED`
- `REFUNDED`

Order fields:

- `id`
- `order_code`
- `order_type`
- `created_by`
- `status`
- `subtotal`
- `discount_amount`
- `total_amount`
- `note`
- `created_at`
- `updated_at`

Order item fields:

- `id`
- `order_id`
- `product_id`
- `product_name_snapshot`
- `unit_price`
- `quantity`
- `subtotal`
- `selected_options_snapshot`
- `note`

Requirements:

- FR-06.1: Cashier tạo đơn mới.
- FR-06.2: Cashier chọn loại đơn.
- FR-06.3: Cashier thêm sản phẩm vào giỏ.
- FR-06.4: Cashier chọn size và topping.
- FR-06.5: Cashier thay đổi số lượng và ghi chú món.
- FR-06.6: Cashier xóa món khỏi đơn chưa xác nhận.
- FR-06.7: Hệ thống tính lại tổng tiền.
- FR-06.8: Cashier xác nhận đơn.
- FR-06.9: Cashier tra cứu đơn hàng theo quyền.
- FR-06.10: Manager xem toàn bộ đơn.
- FR-06.11: Hệ thống lưu người tạo và thời gian tạo đơn.
- FR-06.12: Hệ thống lưu snapshot giá và tên sản phẩm.
- FR-06.13: Hệ thống ngăn tạo trùng đơn do gửi lại cùng yêu cầu có cùng idempotency key.

Business rules:

- Mỗi đơn có mã duy nhất.
- Số lượng phải là số nguyên dương.
- Giá và tổng tiền do backend tính toán.
- Không tin tổng tiền do frontend gửi lên.
- Đơn `DRAFT` có thể chỉnh sửa.
- Đơn `PENDING` không được sửa tùy ý; mọi thay đổi phải thông qua thao tác nghiệp vụ riêng.
- Đơn `COMPLETED` không thể quay lại `PENDING`.
- Đơn `CANCELLED` không thể thanh toán.
- Đơn đã thanh toán không thể bị hủy theo luồng hủy đơn thông thường; phải xử lý bằng luồng hoàn tiền hoặc điều chỉnh phù hợp.
- Mọi thao tác hủy phải lưu lý do và người thực hiện.
- Thao tác xác nhận đơn phải được xử lý trong database transaction.
- Nếu nguyên liệu được quản lý theo công thức, việc trừ kho phải tuân theo chính sách trừ kho thống nhất và không được trừ lặp khi retry.

Acceptance criteria:

- Tạo đơn với một hoặc nhiều sản phẩm hợp lệ thành công.
- Thêm số lượng âm hoặc sản phẩm không hoạt động bị từ chối.
- Giá tổng từ backend khớp với các order item.
- Giá sản phẩm đã lưu không thay đổi khi Manager chỉnh sửa menu.
- Hai request trùng idempotency key không tạo hai đơn.
- Đơn đã thanh toán không thể bị thanh toán thêm lần nữa.

### FR-07 — Payment Management

**Description:** Cashier nhận và ghi nhận thanh toán tại quầy.

MVP payment method:

- `CASH`

Payment fields:

- `id`
- `transaction_code`
- `order_id`
- `processed_by`
- `payment_method`
- `amount`
- `status`
- `created_at`

Payment status:

- `SUCCESS`
- `FAILED`
- `REFUNDED`
- `PARTIALLY_REFUNDED`

Requirements:

- FR-07.1: Cashier chọn đơn cần thanh toán.
- FR-07.2: Hệ thống hiển thị số tiền cần thu.
- FR-07.3: Cashier nhập số tiền khách đưa.
- FR-07.4: Hệ thống tính tiền thối lại.
- FR-07.5: Hệ thống ghi nhận giao dịch thành công.
- FR-07.6: Hệ thống cập nhật trạng thái thanh toán và trạng thái đơn nhất quán.
- FR-07.7: Cashier xem hóa đơn sau thanh toán.
- FR-07.8: Manager tra cứu toàn bộ giao dịch.
- FR-07.9: Manager xử lý hoàn tiền theo chính sách.
- FR-07.10: Hệ thống ghi audit log cho thao tác hoàn tiền.

Business rules:

- Số tiền khách đưa phải lớn hơn hoặc bằng số tiền cần thu.
- Tiền thối lại bằng số tiền nhận trừ số tiền phải thu.
- Backend tự tính số tiền cần thanh toán.
- Đơn đã thanh toán không thể nhận thêm một giao dịch thu tiền trùng.
- Ghi nhận payment và cập nhật trạng thái order phải được thực hiện nguyên tử đối với thanh toán tiền mặt.
- Nếu request bị gửi lại do timeout, hệ thống phải dùng idempotency key hoặc cơ chế tương đương để ngăn ghi nhận trùng.
- Hoàn tiền không được xóa giao dịch gốc.
- Tổng tiền hoàn không được vượt quá số tiền đã thanh toán hợp lệ trừ số tiền đã hoàn trước đó.
- Mọi giao dịch phải lưu người thực hiện và thời gian.

Acceptance criteria:

- Thanh toán tiền mặt hợp lệ ghi nhận thành công và hoàn tất đơn.
- Thanh toán số tiền thiếu bị từ chối.
- Thanh toán đơn đã hủy bị từ chối.
- Request thanh toán lặp không tạo giao dịch thu tiền thứ hai.
- Hoàn tiền vượt số tiền còn có thể hoàn bị từ chối.
- Lịch sử giao dịch vẫn tồn tại sau khi hoàn tiền.

### FR-08 — Inventory Management

**Description:** Manager quản lý nguyên liệu và lượng tồn kho.

Ingredient fields:

- `id`
- `name`
- `unit`
- `current_stock`
- `minimum_stock`
- `is_active`
- `created_at`
- `updated_at`

Các đơn vị hỗ trợ có thể gồm `g`, `kg`, `ml`, `l`, `piece`. Hệ thống phải quy đổi về đơn vị chuẩn cho từng nguyên liệu khi tính toán.

Requirements:

- FR-08.1: Manager tạo nguyên liệu.
- FR-08.2: Manager cập nhật tên, đơn vị và mức tồn tối thiểu.
- FR-08.3: Manager nhập kho.
- FR-08.4: Manager điều chỉnh tồn kho có lý do.
- FR-08.5: Manager xem lịch sử biến động kho.
- FR-08.6: Hệ thống hiển thị cảnh báo khi tồn kho thấp hơn hoặc bằng mức tối thiểu.
- FR-08.7: Hệ thống từ chối số lượng nhập kho không hợp lệ.
- FR-08.8: Hệ thống không cho phép tồn kho âm theo chính sách mặc định.
- FR-08.9: Chỉ Manager được thực hiện thao tác điều chỉnh kho.
- FR-08.10: Hệ thống ghi người thao tác và thời gian cho mỗi biến động.

Stock movement types:

- `IN`: Nhập kho.
- `OUT`: Xuất kho.
- `ADJUSTMENT`: Điều chỉnh tồn.
- `SALE_CONSUMPTION`: Tiêu hao theo đơn bán hàng.
- `REVERSAL`: Bút toán đảo khi cần sửa một giao dịch đã ghi nhận.

Mỗi stock movement phải lưu nguyên liệu, số lượng, loại biến động, lý do, người thực hiện, thời gian và tham chiếu nghiệp vụ nếu có.

Business rules:

- Không xóa cứng lịch sử biến động kho.
- Tồn kho phải được cập nhật nguyên tử.
- Khi nhiều giao dịch cùng thay đổi một nguyên liệu, hệ thống phải ngăn lost update.
- Không được âm kho trừ khi chính sách được thay đổi rõ ràng.
- Sửa sai giao dịch kho phải có audit trail.
- Hủy đơn hoặc hoàn tiền không tự động cộng lại nguyên liệu nếu quy trình thực tế không bảo đảm nguyên liệu đã được thu hồi.

### FR-09 — Recipe and Automatic Stock Deduction

**Description:** Manager cấu hình công thức để theo dõi tiêu hao nguyên liệu theo số món bán.

Recipe fields:

- `id`
- `product_id`
- `ingredient_id`
- `quantity_required`
- `unit`

Requirements:

- Manager tạo và chỉnh sửa công thức.
- Một sản phẩm có thể sử dụng nhiều nguyên liệu.
- Một nguyên liệu có thể được sử dụng bởi nhiều sản phẩm.
- Công thức phải có định mức hợp lệ.
- Hệ thống tính tiêu hao theo số lượng sản phẩm và các lựa chọn đã cấu hình.
- Hệ thống tạo stock movement tham chiếu đến đơn hàng.
- Hệ thống ngăn tiêu hao kho lặp cho cùng một nghiệp vụ.
- Nếu tồn kho không đủ, hệ thống áp dụng chính sách được cấu hình và thông báo rõ cho Cashier.

MVP default policy:

- Chỉ cho phép xác nhận đơn nếu nguyên liệu cần thiết còn đủ tồn kho khi kiểm soát tồn kho được bật.
- Khi xác nhận đơn, tạo bản ghi tiêu hao kho và cập nhật tồn kho trong transaction.
- Nếu cập nhật tồn kho thất bại, việc xác nhận đơn phải thất bại hoàn toàn.
- Khi hủy đơn sau khi đã trừ kho, hệ thống không tự cộng lại kho nếu chưa có quy trình xác nhận nguyên liệu thực sự được hoàn lại.
- Các lựa chọn như topping phải được liên kết với công thức hoặc định mức tiêu hao tương ứng nếu cần theo dõi nguyên liệu.

Acceptance criteria:

- Bán một sản phẩm có công thức làm giảm đúng lượng tồn tương ứng.
- Bán nhiều sản phẩm tính tiêu hao theo tổng số lượng.
- Không trừ kho hai lần khi gửi lại cùng yêu cầu.
- Nếu nguyên liệu không đủ theo chính sách mặc định, hệ thống từ chối xác nhận đơn và trả về lỗi nghiệp vụ rõ ràng.
- Điều chỉnh công thức không thay đổi stock movement đã ghi nhận.

### FR-10 — Sales Reports

**Description:** Manager xem báo cáo kinh doanh.

Reports:

- Doanh thu theo ngày.
- Doanh thu theo tuần.
- Doanh thu theo tháng.
- Số đơn đã thanh toán.
- Giá trị đơn hàng trung bình.
- Top sản phẩm theo số lượng bán.
- Doanh thu theo phương thức thanh toán.
- Tổng số tiền hoàn.
- Báo cáo biến động kho cơ bản.

Business rules:

- Chỉ Manager truy cập báo cáo tổng hợp.
- Báo cáo dùng chung định nghĩa doanh thu với Dashboard.
- Đơn chưa thanh toán và đơn bị hủy trước thanh toán không được tính vào doanh thu.
- Khoản hoàn tiền được thể hiện riêng và được tính vào doanh thu thuần theo quy tắc thống nhất.
- Báo cáo top sản phẩm sử dụng snapshot sản phẩm trên đơn hàng.
- Các bộ lọc thời gian phải có ngày bắt đầu không lớn hơn ngày kết thúc.
- Việc chỉnh sửa menu không làm thay đổi báo cáo lịch sử.

Definitions:

- `Gross Sales`: Tổng giá trị bán hợp lệ sau chiết khấu, trước hoàn tiền.
- `Net Sales`: `Gross Sales - Refunds`.

Doanh thu không đồng nghĩa lợi nhuận. Tính lợi nhuận cần thêm dữ liệu giá vốn và chi phí vận hành.

### FR-11 — Audit Log

**Description:** Hệ thống lưu vết thao tác quan trọng để hỗ trợ kiểm tra và xử lý sự cố.

Các sự kiện cần ghi nhận:

- Tạo hoặc vô hiệu hóa tài khoản.
- Thay đổi giá bán.
- Ngừng bán sản phẩm.
- Hủy đơn.
- Hoàn tiền.
- Nhập kho và điều chỉnh tồn.
- Thay đổi công thức pha chế.
- Thay đổi cấu hình hệ thống.

Audit log fields:

- `id`
- `actor_user_id`
- `action`
- `entity_type`
- `entity_id`
- `before_value`
- `after_value`
- `reason`
- `created_at`

Requirements:

- Người dùng thông thường không thể chỉnh sửa hoặc xóa audit log.
- Manager có quyền xem audit log.
- Không ghi mật khẩu, token hoặc dữ liệu bí mật vào log.
- Các thao tác nhạy cảm phải có người thực hiện và thời gian.
- Lý do hủy đơn, hoàn tiền hoặc điều chỉnh kho là bắt buộc.

### FR-12 — Notifications and System Feedback

Requirements:

- Hiển thị thông báo khi thao tác thành công hoặc thất bại.
- Hiển thị lỗi validation tại trường dữ liệu liên quan.
- Hiển thị cảnh báo khi sản phẩm ngừng bán hoặc nguyên liệu không đủ.
- Cảnh báo khi tồn kho dưới định mức.
- Hiển thị loading state trong lúc gửi request.
- Ngăn thao tác lặp ngoài ý muốn khi request đang xử lý.
- Khi lỗi mạng xảy ra, không hiển thị thông báo thành công nếu backend chưa xác nhận.

---

## 5. Core Business Workflows

### 5.1. Order and Payment Workflow

1. Cashier đăng nhập.
2. Cashier mở màn hình POS.
3. Chọn loại đơn: tại quán hoặc mang đi.
4. Chọn sản phẩm, size, topping và số lượng.
5. Backend xác thực sản phẩm, giá và các lựa chọn.
6. Hệ thống tính tổng tiền.
7. Cashier xác nhận đơn.
8. Backend tạo đơn và kiểm tra tồn kho nếu chính sách kho được bật.
9. Hệ thống ghi nhận tiêu hao nguyên liệu theo công thức.
10. Cashier nhận thanh toán.
11. Backend xác thực số tiền và ghi nhận payment.
12. Đơn chuyển sang trạng thái `COMPLETED`.
13. Hệ thống hiển thị hóa đơn và lưu lịch sử giao dịch.
14. Dashboard và báo cáo được cập nhật từ dữ liệu đã ghi nhận.

Nếu một bước thuộc cùng transaction thất bại, hệ thống phải rollback các thay đổi liên quan trong transaction đó.

### 5.2. Menu Management Workflow

1. Manager mở trang Menu.
2. Chọn danh mục hoặc sản phẩm.
3. Tạo mới hoặc chỉnh sửa.
4. Backend validate giá, danh mục, size và topping.
5. Lưu dữ liệu.
6. Menu mới được sử dụng trong các đơn hàng tiếp theo.
7. Đơn cũ tiếp tục giữ snapshot giá và tên sản phẩm.

### 5.3. Inventory Workflow

1. Manager mở trang Kho.
2. Chọn nguyên liệu.
3. Nhập kho hoặc điều chỉnh số lượng.
4. Nhập lý do.
5. Backend xác thực quyền và số lượng.
6. Tạo stock movement và cập nhật tồn kho nguyên tử.
7. Hệ thống cập nhật cảnh báo tồn kho.
8. Audit log được lưu cho thao tác phù hợp.

### 5.4. Refund Workflow

1. Manager tìm giao dịch đã thanh toán.
2. Chọn chức năng hoàn tiền.
3. Nhập số tiền và lý do.
4. Backend xác thực quyền và số tiền còn có thể hoàn.
5. Ghi nhận giao dịch hoàn tiền.
6. Cập nhật trạng thái thanh toán và báo cáo.
7. Lưu audit log.

MVP chỉ hỗ trợ ghi nhận hoàn tiền đối với thanh toán tiền mặt. Việc hoàn tiền thực tế được thực hiện tại quầy và xác nhận bởi Manager; tích hợp hoàn tiền tự động với ngân hàng hoặc cổng thanh toán không thuộc MVP.

---

## 6. UI/UX Requirements

### 6.1. Design Source of Truth

**Thiết kế giao diện được lấy từ Stitch.** Stitch là nguồn tham chiếu chính cho layout, màu sắc, typography, spacing, component styles và responsive behavior.

Trước khi triển khai frontend:

1. Kiểm tra và đọc các file thiết kế được export từ Stitch.
2. Xác định màn hình, component, design tokens và trạng thái UI đã có.
3. Lập danh sách các màn hình theo từng role.
4. Đối chiếu UI với functional requirements trong PRD.
5. Ghi nhận màn hình hoặc trạng thái còn thiếu trong `docs/UI_SPEC.md`.
6. Không tự ý thay thế design đã được duyệt bằng một phong cách mới.
7. Nếu design và PRD mâu thuẫn, ghi nhận vấn đề và yêu cầu xác nhận trước khi tự quyết định.

Nếu thiết kế Stitch chưa có một màn hình hoặc trạng thái bắt buộc, frontend agent phải mở rộng theo design system hiện có, giữ tính nhất quán về visual style và ghi rõ phần bổ sung.

### 6.2. Design Requirements

- Giao diện tiếng Việt.
- Tiền tệ hiển thị theo VND.
- Responsive cho desktop và tablet; các trang quản lý cơ bản sử dụng được trên mobile.
- Ưu tiên tốc độ thao tác, đặc biệt với màn hình POS.
- Có trạng thái loading, empty, success và error.
- Xác nhận trước thao tác không thể hoàn tác.
- Không phụ thuộc hoàn toàn vào màu sắc để biểu thị trạng thái.
- Form có validation và thông báo lỗi dễ hiểu.
- Reuse React components thay vì tạo các component trùng lặp.
- Dùng design tokens từ Stitch nếu có; tránh hard-code nhiều giá trị style riêng lẻ.

### 6.3. Required Screens

| Route | Screen | Access |
|---|---|---|
| `/login` | Đăng nhập | Public |
| `/pos` | Bán hàng | Cashier, Manager |
| `/orders` | Danh sách đơn | Cashier giới hạn; Manager toàn bộ |
| `/orders/:id` | Chi tiết đơn | Theo quyền |
| `/payments/:id` | Chi tiết giao dịch | Theo quyền |
| `/dashboard` | Dashboard | Manager |
| `/menu` | Quản lý menu | Manager |
| `/menu/categories` | Danh mục | Manager |
| `/inventory` | Tổng quan kho | Manager |
| `/inventory/ingredients` | Danh sách nguyên liệu | Manager |
| `/inventory/movements` | Lịch sử kho | Manager |
| `/inventory/recipes` | Công thức pha chế | Manager |
| `/reports/sales` | Báo cáo doanh thu | Manager |
| `/employees` | Quản lý Cashier | Manager |
| `/audit-logs` | Lịch sử thao tác | Manager |
| `/settings` | Cấu hình | Manager |

Frontend phải kiểm tra quyền truy cập route. Backend vẫn là lớp quyết định cuối cùng.

---

## 7. Data Model Requirements

### 7.1. Core Entities

#### Users

- `id`
- `full_name`
- `email`
- `password_hash`
- `role`
- `is_active`
- `created_at`
- `updated_at`

Role enum: `CASHIER`, `MANAGER`.

#### Categories

- `id`
- `name`
- `description`
- `is_active`
- `created_at`
- `updated_at`

#### Products

- `id`
- `category_id`
- `name`
- `description`
- `base_price`
- `image_url`
- `is_available`
- `created_at`
- `updated_at`

#### Product Options

Quản lý size, topping và các tùy chọn bổ sung:

- `id`
- `product_id`
- `name`
- `option_type`
- `price_delta`
- `is_active`

Nếu topping được dùng chung giữa nhiều sản phẩm, có thể tách option groups, options và bảng liên kết sản phẩm.

#### Orders

- `id`
- `order_code`
- `order_type`
- `created_by`
- `status`
- `subtotal`
- `discount_amount`
- `total_amount`
- `note`
- `created_at`
- `updated_at`

#### Order Items

- `id`
- `order_id`
- `product_id`
- `product_name_snapshot`
- `unit_price`
- `quantity`
- `subtotal`
- `selected_options_snapshot`
- `note`

#### Payments

- `id`
- `transaction_code`
- `order_id`
- `processed_by`
- `payment_method`
- `amount`
- `status`
- `created_at`

#### Refunds

- `id`
- `payment_id`
- `processed_by`
- `amount`
- `reason`
- `status`
- `created_at`

#### Ingredients

- `id`
- `name`
- `unit`
- `current_stock`
- `minimum_stock`
- `is_active`
- `created_at`
- `updated_at`

#### Recipes

- `id`
- `product_id`
- `ingredient_id`
- `quantity_required`
- `unit`

#### Stock Movements

- `id`
- `ingredient_id`
- `movement_type`
- `quantity_delta`
- `reason`
- `reference_type`
- `reference_id`
- `created_by`
- `created_at`

#### Audit Logs

- `id`
- `actor_user_id`
- `action`
- `entity_type`
- `entity_id`
- `before_value`
- `after_value`
- `reason`
- `created_at`

### 7.2. Data Integrity Rules

- Sử dụng `BIGINT` hoặc UUID nhất quán cho primary key.
- Tiền tệ sử dụng `DECIMAL`, không sử dụng floating point.
- Email, order code và transaction code phải có unique constraint phù hợp.
- Sử dụng foreign key để bảo đảm quan hệ.
- Không xóa cứng dữ liệu có liên quan đến lịch sử giao dịch.
- Các thao tác thanh toán phải có cơ chế chống ghi nhận trùng.
- Tồn kho phải được cập nhật nguyên tử và tránh lost update.
- Thêm index cho các cột lọc thường xuyên như trạng thái đơn, thời gian tạo, order ID và ingredient ID.
- Sử dụng database migration để quản lý thay đổi schema.
- Giá snapshot và dữ liệu lịch sử không được cập nhật theo thay đổi menu hiện tại.

---

## 8. API Requirements

API sử dụng REST, JSON và prefix `/api/v1`.

### 8.1. Authentication

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Đăng nhập |
| `POST` | `/api/v1/auth/logout` | Đăng xuất |
| `GET` | `/api/v1/auth/me` | Thông tin người dùng hiện tại |

### 8.2. Users

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/users` | Danh sách Cashier |
| `POST` | `/api/v1/users` | Tạo Cashier |
| `PATCH` | `/api/v1/users/{id}` | Cập nhật thông tin |
| `PATCH` | `/api/v1/users/{id}/status` | Vô hiệu hóa/kích hoạt |

Chỉ Manager được sử dụng các endpoint này, với giới hạn không cho thay đổi role vượt quyền.

### 8.3. Menu

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/categories` | Danh sách danh mục |
| `POST` | `/api/v1/categories` | Tạo danh mục |
| `PATCH` | `/api/v1/categories/{id}` | Sửa danh mục |
| `GET` | `/api/v1/products` | Danh sách sản phẩm |
| `POST` | `/api/v1/products` | Tạo sản phẩm |
| `GET` | `/api/v1/products/{id}` | Chi tiết sản phẩm |
| `PATCH` | `/api/v1/products/{id}` | Sửa sản phẩm |
| `PATCH` | `/api/v1/products/{id}/availability` | Bật/tắt bán |

Cashier được phép đọc menu nhưng không được gọi các API ghi dữ liệu menu.

### 8.4. Orders

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/orders` | Tạo đơn |
| `GET` | `/api/v1/orders` | Danh sách đơn |
| `GET` | `/api/v1/orders/{id}` | Chi tiết đơn |
| `PATCH` | `/api/v1/orders/{id}` | Chỉnh sửa đơn ở trạng thái cho phép |
| `POST` | `/api/v1/orders/{id}/confirm` | Xác nhận đơn |
| `POST` | `/api/v1/orders/{id}/cancel` | Hủy đơn theo điều kiện |

### 8.5. Payments and Refunds

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/orders/{id}/payments` | Thanh toán |
| `GET` | `/api/v1/orders/{id}/payments` | Lịch sử thanh toán |
| `GET` | `/api/v1/payments/{id}` | Chi tiết giao dịch |
| `POST` | `/api/v1/payments/{id}/refunds` | Hoàn tiền |
| `GET` | `/api/v1/refunds` | Tra cứu hoàn tiền |

### 8.6. Inventory

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/inventory/ingredients` | Danh sách nguyên liệu |
| `POST` | `/api/v1/inventory/ingredients` | Tạo nguyên liệu |
| `PATCH` | `/api/v1/inventory/ingredients/{id}` | Cập nhật nguyên liệu |
| `POST` | `/api/v1/inventory/movements` | Nhập/xuất/điều chỉnh kho |
| `GET` | `/api/v1/inventory/movements` | Lịch sử kho |
| `GET` | `/api/v1/inventory/alerts` | Cảnh báo tồn thấp |
| `GET` | `/api/v1/inventory/recipes` | Danh sách công thức |
| `POST` | `/api/v1/inventory/recipes` | Tạo công thức |
| `PATCH` | `/api/v1/inventory/recipes/{id}` | Sửa công thức |

### 8.7. Dashboard and Reports

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/dashboard/summary` | KPI tổng quan |
| `GET` | `/api/v1/reports/sales` | Báo cáo doanh thu |
| `GET` | `/api/v1/reports/products` | Báo cáo sản phẩm |
| `GET` | `/api/v1/reports/inventory` | Báo cáo tồn kho |
| `GET` | `/api/v1/audit-logs` | Audit log |

### 8.8. API Standards

- Dùng HTTP status code đúng ngữ nghĩa.
- `401` cho request chưa xác thực.
- `403` cho người dùng không đủ quyền.
- `404` cho tài nguyên không tồn tại hoặc không được phép tiết lộ.
- `409` cho xung đột trạng thái hoặc giao dịch trùng.
- `400` hoặc `422` cho dữ liệu đầu vào không hợp lệ, theo quy ước thống nhất.
- Response lỗi phải có mã lỗi và thông báo rõ ràng.
- Dùng pagination cho danh sách lớn.
- Có validation ở backend.
- Các endpoint ghi dữ liệu phải xác thực quyền và điều kiện nghiệp vụ.
- Dùng idempotency key cho thao tác có nguy cơ gửi lặp, đặc biệt là thanh toán.
- API contract phải được ghi bằng OpenAPI/Swagger trước khi frontend tích hợp.

---

## 9. Non-functional Requirements

### NFR-01 — Performance

- API thông thường có mục tiêu p95 dưới 500 ms trong môi trường kiểm thử được xác định.
- Danh sách lớn phải hỗ trợ phân trang.
- Dashboard không nên thực hiện truy vấn toàn bảng không giới hạn.
- Tải ảnh sản phẩm không được làm chậm các thao tác POS quan trọng.

### NFR-02 — Security

- Hash mật khẩu bằng thuật toán chuyên dụng.
- Dùng cơ chế xác thực phù hợp với kiến trúc backend Python.
- Kiểm tra role tại backend.
- Validate và sanitize dữ liệu đầu vào phù hợp.
- Bảo vệ secrets bằng biến môi trường hoặc secret manager.
- Không trả stack trace hoặc thông tin nhạy cảm cho client.
- Không ghi token hoặc mật khẩu vào log.
- Có chính sách timeout và vô hiệu hóa phiên đăng nhập phù hợp.

### NFR-03 — Data Consistency

- Thanh toán phải ghi nhận giao dịch và cập nhật trạng thái đơn nhất quán.
- Xác nhận đơn và tiêu hao kho phải nhất quán nếu hai thao tác thuộc cùng quy trình nghiệp vụ.
- Không để request retry tạo dữ liệu nghiệp vụ trùng.
- Tồn kho phải được cập nhật theo cơ chế concurrency-safe.
- Sử dụng database transaction cho các thao tác gồm nhiều bước liên quan.

### NFR-04 — Reliability

- Có xử lý lỗi tập trung.
- Có log phục vụ debugging.
- Có transaction rollback khi nghiệp vụ thất bại.
- Không hiển thị thành công khi backend chưa xác nhận.
- Có cơ chế backup và phục hồi dữ liệu.

### NFR-05 — Usability

- POS dễ sử dụng khi quán đông khách.
- Các nút hành động chính dễ nhận biết.
- Form có validation rõ ràng.
- Hạn chế thao tác lặp và chuyển trang không cần thiết.
- Hiển thị trạng thái đơn và thanh toán riêng biệt.

### NFR-06 — Maintainability

- Tách API routes/controllers, services, repositories/data access và schemas.
- Frontend tổ chức theo feature/module.
- Không để business logic quan trọng trong UI.
- Có migration và tài liệu cấu hình.
- API contract được version hóa.
- Quy tắc coding được thống nhất trước khi các agent triển khai song song.

### NFR-07 — Testing

- Unit test cho business logic.
- Integration test cho database và transaction.
- Test authorization cho từng nhóm API.
- Test chống thanh toán trùng.
- Test tồn kho và concurrent update.
- End-to-end test cho luồng tạo đơn và thanh toán.

### NFR-08 — Auditability

- Ghi nhận các thao tác nhạy cảm.
- Lịch sử giao dịch và biến động kho không bị xóa tùy tiện.
- Dữ liệu audit không được chứa secrets.
- Các thao tác có ảnh hưởng đến tiền phải truy được người thực hiện.

---

## 10. Error Handling and Edge Cases

Hệ thống phải xử lý tối thiểu các trường hợp sau:

1. Đăng nhập bằng tài khoản bị vô hiệu hóa.
2. Cashier gọi trực tiếp API quản lý menu.
3. Cashier sửa giá bằng cách thay đổi request payload.
4. Thêm sản phẩm đã ngừng bán vào đơn.
5. Thêm sản phẩm không tồn tại.
6. Gửi số lượng bằng 0 hoặc âm.
7. Thay đổi giá menu khi Cashier đang mở POS.
8. Hai request đồng thời cập nhật cùng một đơn.
9. Hai request thanh toán cho cùng một đơn.
10. Thanh toán đơn đã hủy.
11. Hoàn tiền vượt số tiền đã thanh toán.
12. Gửi lại yêu cầu hoàn tiền sau timeout.
13. Nhập số lượng nguyên liệu âm.
14. Điều chỉnh kho làm tồn kho âm.
15. Hai đơn đồng thời tiêu hao cùng một nguyên liệu.
16. Lỗi database giữa quá trình xác nhận đơn và trừ kho.
17. Hủy đơn sau khi đã tiêu hao nguyên liệu.
18. Không có dữ liệu cho khoảng thời gian báo cáo.
19. Khoảng thời gian báo cáo không hợp lệ.
20. Mất kết nối mạng trong lúc thanh toán.
21. Người dùng nhấn nút thanh toán nhiều lần.
22. Tài khoản Cashier bị vô hiệu hóa khi phiên đăng nhập vẫn còn hiệu lực.

Mỗi trường hợp phải có kết quả mong đợi, HTTP status phù hợp và bảo đảm không để dữ liệu ở trạng thái nửa chừng.

---

## 11. Acceptance Test Plan

### AT-01 — Authentication

- Đăng nhập hợp lệ thành công.
- Sai mật khẩu bị từ chối.
- Tài khoản bị vô hiệu hóa không thể đăng nhập.
- Cashier không truy cập được dashboard Manager.
- API bảo vệ không thể được truy cập khi chưa xác thực.

### AT-02 — Menu

- Manager tạo sản phẩm thành công.
- Manager cập nhật giá thành công.
- Cashier không sửa được giá.
- Sản phẩm ngừng bán không thể thêm vào đơn mới.
- Giá snapshot của đơn cũ không thay đổi khi giá menu cập nhật.

### AT-03 — Order

- Cashier tạo đơn với các món hợp lệ.
- Backend tính đúng tổng tiền.
- Sản phẩm không hợp lệ bị từ chối.
- Không thể thanh toán đơn đã hủy.
- Không thể chỉnh sửa đơn đã hoàn thành.
- Request lặp không tạo đơn trùng khi sử dụng cùng idempotency key.

### AT-04 — Payment

- Thanh toán tiền mặt hợp lệ thành công.
- Số tiền nhận thấp hơn số tiền phải thu bị từ chối.
- Giao dịch thành công làm đơn chuyển sang `COMPLETED`.
- Thanh toán lặp không tạo giao dịch thu tiền thứ hai.
- Hoàn tiền vượt giới hạn bị từ chối.
- Hoàn tiền có lý do, người thực hiện và lịch sử đầy đủ.

### AT-05 — Inventory

- Manager nhập kho thành công.
- Cashier không thể điều chỉnh kho.
- Tồn kho cập nhật đúng sau giao dịch.
- Không thể tạo tồn kho âm theo chính sách mặc định.
- Hai thao tác đồng thời không làm sai số lượng tồn.
- Cùng một đơn không trừ nguyên liệu hai lần.

### AT-06 — Reports

- Dashboard chỉ hiển thị cho Manager.
- Báo cáo khớp với dữ liệu thanh toán.
- Khoản hoàn tiền được thể hiện đúng.
- Thay đổi menu không ảnh hưởng doanh thu lịch sử.
- Bộ lọc thời gian trả dữ liệu đúng khoảng đã chọn.

### AT-07 — Reliability

- Lỗi giữa transaction không để lại dữ liệu cập nhật một phần.
- Lỗi mạng không tạo giao dịch trùng khi retry.
- Mọi lỗi nghiệp vụ hiển thị thông báo có thể hiểu được.
- Log không chứa mật khẩu hoặc token.

---

## 12. Definition of Done

Một tính năng chỉ được xem là hoàn thành khi đáp ứng đầy đủ các điều kiện:

1. Đáp ứng functional requirements.
2. Có acceptance criteria và test cases tương ứng.
3. API contract được cập nhật.
4. Quyền truy cập được kiểm tra ở backend.
5. Validation được triển khai.
6. Có unit test cho business logic.
7. Có integration test cho các thao tác dữ liệu quan trọng.
8. Database migration được bổ sung nếu schema thay đổi.
9. Frontend có loading, empty, success và error states.
10. Không có lỗi build liên quan đến thay đổi.
11. Test bắt buộc pass.
12. Không có secrets trong source code.
13. README và tài liệu chạy dự án được cập nhật.
14. Không sử dụng dữ liệu hard-code thay cho backend trong các chức năng production.
15. Các hành động nhạy cảm có audit log.

---

## 13. Technology Stack

### 13.1. Backend — Python

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Pytest
- HTTPX cho API testing
- OpenAPI/Swagger được FastAPI sinh tự động

Backend architecture:

- API/router layer: HTTP endpoints và dependency injection.
- Schema layer: Pydantic request/response schemas.
- Service layer: business logic và transaction orchestration.
- Repository/data access layer: truy vấn và thao tác database.
- Model layer: SQLAlchemy entities.
- Core layer: settings, authentication, authorization, logging và error handling.

### 13.2. Frontend — React

- React
- TypeScript
- Vite
- React Router
- Tailwind CSS, nếu phù hợp với thiết kế Stitch
- TanStack Query cho server state
- React Hook Form và Zod cho form validation
- Recharts cho biểu đồ, nếu phù hợp với thiết kế

Frontend requirements:

- Reuse React components theo design system.
- Dùng TypeScript types khớp API contract.
- Tách page, feature components, shared components, hooks và API client.
- Không chứa business rules quan trọng chỉ ở frontend.
- Không hard-code dữ liệu nghiệp vụ trong các trang production.
- Giao diện phải tuân thủ thiết kế Stitch đã được cung cấp.
- Nếu Stitch export có component hoặc CSS tương thích, ưu tiên tái sử dụng sau khi kiểm tra chất lượng và khả năng maintainability.

### 13.3. Database and Infrastructure

- PostgreSQL.
- Alembic migrations.
- Docker và Docker Compose.
- Environment variables cho cấu hình.
- Git và CI pipeline chạy lint, tests và build.

---

## 14. Stitch Design Integration Requirements

Stitch là nguồn thiết kế giao diện chuẩn của CoffeeFlow.

Trước khi triển khai:

1. Đọc toàn bộ thiết kế Stitch được cung cấp trong workspace.
2. Kiểm tra các màn hình, component, assets và design tokens đã export.
3. Tạo danh sách mapping giữa Stitch screens và routes trong PRD.
4. Ghi lại các component có thể tái sử dụng.
5. Xác định các trạng thái loading, empty, error, disabled và confirmation còn thiếu.
6. Bổ sung UI spec nếu có yêu cầu nghiệp vụ chưa được thể hiện trong thiết kế.
7. Không tự thay đổi màu sắc, typography, layout hoặc spacing đã được duyệt nếu không có lý do và xác nhận.
8. Khi cần bổ sung màn hình, phải dùng lại design system hiện có.

Deliverable trước khi coding frontend:

- `docs/UI_SPEC.md`
- Danh sách routes và role access.
- Danh sách shared React components.
- Mapping giữa Stitch screens và functional requirements.
- Danh sách design gaps cần xử lý.

Nếu file Stitch chưa có trong workspace, frontend agent phải ghi nhận dependency còn thiếu thay vì tự tuyên bố đã đọc hoặc tái tạo chính xác thiết kế.

---

## 15. Implementation Constraints for AI Agents

1. PRD là nguồn yêu cầu nghiệp vụ gốc.
2. Không tự ý thêm role thứ ba.
3. Không tự ý thay đổi business rules về thanh toán, tồn kho hoặc phân quyền.
4. Không triển khai frontend trước khi API contract của chức năng liên quan được xác định.
5. Không để Backend và Frontend tự định nghĩa hai schema khác nhau.
6. Không sử dụng floating point để xử lý tiền tệ.
7. Không tin giá, tổng tiền hoặc role do frontend gửi lên.
8. Không xóa cứng dữ liệu giao dịch lịch sử.
9. Không bỏ qua test để làm cho pipeline pass.
10. Không đánh dấu task hoàn thành nếu chưa có bằng chứng build/test tương ứng.
11. Mọi thay đổi phạm vi phải được cập nhật vào tài liệu và WBS.
12. Mọi task phải có acceptance criteria rõ ràng.
13. Khi yêu cầu mơ hồ, agent phải ghi nhận giả định hoặc tạo câu hỏi cần xác nhận thay vì âm thầm tự quyết định.
14. Các agent chỉ được chỉnh sửa file nằm trong phạm vi task được giao, trừ khi có phê duyệt rõ ràng.
15. Frontend agent phải tuân thủ thiết kế Stitch và React component conventions.
16. Backend agent phải sử dụng Python stack được xác định trong PRD.
17. QA agent phải kiểm thử cả quyền truy cập, nghiệp vụ, lỗi và tính nhất quán dữ liệu.
18. Các agent phải báo cáo file đã tạo/sửa và kết quả kiểm thử thực tế.

---

## 16. Recommended Project Documentation

| File | Responsibility |
|---|---|
| `docs/PRD.md` | Yêu cầu sản phẩm và nghiệp vụ |
| `docs/ARCHITECTURE.md` | Kiến trúc hệ thống và công nghệ |
| `docs/DATA_MODEL.md` | Entity, quan hệ, constraints và migrations |
| `docs/API_CONTRACT.md` | Endpoint, schemas, responses, errors và authorization |
| `docs/UI_SPEC.md` | Mapping thiết kế Stitch, routes, components và UI states |
| `docs/BUSINESS_RULES.md` | State transitions, thanh toán, tồn kho và báo cáo |
| `docs/TEST_PLAN.md` | Test scenarios, test data và expected results |
| `docs/IMPLEMENTATION_PLAN.md` | Milestones, dependencies và thứ tự triển khai |
| `AGENTS.md` | Quy tắc chung dành cho các agent |

### Suggested Implementation Phases

**Phase 1 — Foundation**
- Project setup.
- Database schema.
- Authentication.
- Role-based access control.
- API error handling.

**Phase 2 — Menu and POS**
- Categories.
- Products.
- Product options.
- Order creation.
- Price snapshots.

**Phase 3 — Payments**
- Cash payment.
- Transaction consistency.
- Idempotency.
- Receipt and order history.

**Phase 4 — Inventory**
- Ingredients.
- Stock movements.
- Recipes.
- Automatic stock deduction.
- Inventory alerts.

**Phase 5 — Management**
- Dashboard.
- Sales reports.
- Employee management.
- Audit logs.

**Phase 6 — Quality Assurance**
- Integration tests.
- End-to-end tests.
- Security tests.
- Performance validation.
- Documentation and release verification.

---

## 17. Final MVP Acceptance Criteria

CoffeeFlow MVP được xem là đủ điều kiện phát hành khi:

- Cashier có thể đăng nhập, tạo đơn và thanh toán thành công.
- Manager có thể quản lý menu, nguyên liệu, nhân viên và báo cáo.
- Backend áp dụng đúng role permissions.
- Giá bán trong lịch sử đơn không bị thay đổi khi menu cập nhật.
- Thanh toán không bị ghi nhận trùng do request lặp.
- Tồn kho được cập nhật nhất quán theo công thức.
- Dashboard và báo cáo sử dụng cùng quy tắc tính doanh thu.
- Các thao tác nhạy cảm có thể truy vết.
- Các test case P0 pass.
- Hệ thống có thể khởi chạy từ tài liệu hướng dẫn.
- Database được khởi tạo bằng migration có kiểm soát.
- Không còn lỗi build hoặc lỗi nghiêm trọng đã biết ảnh hưởng đến luồng bán hàng chính.

**End of PRD — CoffeeFlow v1.1**
