# 🧠 Web Builder Flow (CrewAI Multi-Agent Engine)

Module lõi của hệ thống **Autonomous Software Engineering Team**, quản lý việc phối hợp các tác nhân AI (BA, Backend, Frontend, QA) theo kiến trúc **Hierarchical Decomposition & Atomic Execution Pipeline**. Hoàn toàn trung lập với đề án (Project-Agnostic), tự động thích ứng với mọi dự án phần mềm theo tài liệu trong `plans/` và `design/`.

---

## 🚀 Tính Năng Chính

1. **BA Zero-Touch Task Decomposition**: Đọc tài liệu từ `plans/` (PRD, Architecture), khảo sát mã nguồn và thư mục `design/`, tự động phân rã phase thành các task nhỏ có cấu trúc (WBS) và lưu log vào `output/plans/wbs_*.json`.
2. **Tiered Execution**:
   - **Backend**: Chia thành `BE-1` (Contracts & Repositories) -> `BE-2` (Services ACID, Zero-Float) -> `BE-3` (Controllers & Tests). Chạy cổng kiểm tra `mvn test` ngay sau khi xong.
   - **Frontend**: Chia thành `FE-1` (Types & API synced 1:1 với DTO Backend) -> `FE-2` (UI Pages & Components theo chuẩn Stitch tokens). Chạy cổng kiểm tra `npm run build` ngay sau khi xong.
3. **Fail-Fast Gates & Auto-Repair Loop**: Tự động phát hiện lỗi và kích hoạt Agent sửa chữa trực tiếp trên đĩa (tối đa `MAX_REPAIR_ATTEMPTS`).
4. **QA Verification**: Nghiệm thu dựa trên danh sách `acceptance_criteria` cụ thể do BA đề ra.

---

## 💻 Cách Khởi Chạy

### 1. Khởi chạy bằng CrewAI Flow CLI:
```bash
crewai run
```

### 2. Khởi chạy từ Python trực tiếp:
```bash
python src/web_builder/main.py
```

### 3. Khởi chạy thông qua Runner chính ở thư mục gốc:
```bash
# Từ thư mục gốc của dự án:
python main.py --phase 6
```

---

## 📁 Cấu Trúc Module

- `src/web_builder/main.py`: Trình điều phối luồng Flow (`CodingFlow`) với các giai đoạn:
  - `plan_and_decompose`: BA phân rã tự động, xuất JSON WBS và Markdown log.
  - `execute_backend_tier`: Thực thi cụm Backend và kiểm tra `mvn test`.
  - `execute_frontend_tier`: Thực thi cụm Frontend và kiểm tra `npm run build`.
  - `verify_qa_and_signoff`: QA kiểm thử nghiệm thu.
  - `final_build_gate`: Xác nhận toàn bộ build xanh.
  - `save_report`: Lưu và lưu trữ báo cáo nghiệm thu.
- `src/web_builder/crews/content_crew/`:
  - `config/agents.yaml`: Định nghĩa vai trò của 4 Agent.
  - `config/tasks.yaml`: Định nghĩa các nhiệm vụ nguyên tử (Approach A).
  - `content_crew.py`: Định nghĩa các crew chuyên trách (`ba_crew`, `backend_crew`, `frontend_crew`, `qa_crew`).
- `src/web_builder/tools/`:
  - `code_tools.py`: Các công cụ thao tác tệp và thực thi lệnh an toàn.
  - `plan_loader.py`: Tự động nạp và bóc tách tài liệu từ `plans/`.
  - `progress_tracker.py`: Báo cáo tiến độ thời gian thực.
