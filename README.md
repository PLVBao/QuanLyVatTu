# Hệ thống quản lý vật tư xây dựng

Đồ án môn **Hệ quản trị cơ sở dữ liệu**.

## 1. Giới thiệu

Hệ thống hỗ trợ doanh nghiệp xây dựng quản lý vật tư nội bộ trong quá trình nhập vật tư từ nhà cung cấp, lưu kho, xuất/cấp vật tư cho công trình, chuyển vật tư giữa các kho, điều chỉnh tồn sau kiểm kê và tra cứu, thống kê dữ liệu.

Luồng hoạt động chính:

```text
Nhà cung cấp → Nhập kho → Theo dõi tồn kho
→ Xuất cho công trình → Chuyển kho
→ Điều chỉnh tồn → Tra cứu và thống kê
```

Hệ thống không phục vụ hoạt động bán vật tư cho doanh nghiệp khác.

## 2. Loại ứng dụng

Hệ thống được xây dựng dưới dạng ứng dụng desktop.

Giao diện chương trình sử dụng PyQt6. Chương trình Python kết nối với SQL Server thông qua `pyodbc`. Các nghiệp vụ cơ sở dữ liệu được xử lý bằng T-SQL.

## 3. Công nghệ dự kiến

- Python
- PyQt6
- SQL Server
- SQL Server Management Studio
- T-SQL
- pyodbc
- Git và GitHub

## 4. Chức năng dự kiến

1. Đăng nhập và đăng xuất.
2. Quản lý tài khoản người dùng.
3. Quản lý loại vật tư.
4. Quản lý vật tư.
5. Quản lý nhà cung cấp.
6. Quản lý kho.
7. Quản lý công trình.
8. Nhập vật tư từ nhà cung cấp vào kho.
9. Xuất/cấp vật tư từ kho cho công trình.
10. Chuyển vật tư giữa các kho.
11. Điều chỉnh tồn kho sau kiểm kê.
12. Tra cứu tồn kho theo vật tư hoặc kho.
13. Xem lịch sử nhập, xuất, chuyển và điều chỉnh.
14. Cảnh báo vật tư dưới mức tồn tối thiểu.
15. Thống kê nhập – xuất – tồn theo thời gian, kho, vật tư hoặc công trình.
16. Phân quyền cơ bản theo tài khoản nếu nhóm triển khai.

## 5. Nghiệp vụ trọng tâm

- Nhập vật tư vào kho.
- Xuất vật tư cho công trình.
- Chuyển vật tư giữa các kho.
- Điều chỉnh tồn kho.
- Theo dõi số lượng tồn.

Các nghiệp vụ làm thay đổi tồn kho phải sử dụng transaction để bảo đảm dữ liệu được xử lý đồng bộ. Nếu xảy ra lỗi giữa chừng, hệ thống phải rollback để tránh sai lệch dữ liệu.

## 6. Cấu trúc source

```text
QuanLyVatTu/
├── README.md
├── requirements.txt
├── .gitignore
│
├── src/
│   ├── main.py
│   ├── frontend/
│   │   ├── login_ui.py
│   │   ├── main_ui.py
│   │   ├── accounts_ui.py
│   │   ├── master_data_ui.py
│   │   ├── inventory_ui.py
│   │   └── reports_ui.py
│   │
│   └── backend/
│       ├── database_connection.py
│       ├── auth.py
│       ├── accounts.py
│       ├── master_data.py
│       ├── inventory.py
│       └── reports.py
│
└── database/
    └── quan_ly_vat_tu.sql
```

## 7. Vai trò các thành phần

- `src/main.py`: khởi động chương trình.
- `src/frontend`: chứa giao diện PyQt6.
- `src/backend`: xử lý chức năng và kết nối SQL Server.
- `database/quan_ly_vat_tu.sql`: chứa toàn bộ mã T-SQL của hệ thống.
- `requirements.txt`: danh sách thư viện Python cần sử dụng.

## 8. Trạng thái

Đồ án đang trong giai đoạn phân tích bài toán, thiết kế cơ sở dữ liệu và xây dựng khung source.
