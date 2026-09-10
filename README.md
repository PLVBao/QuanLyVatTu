# Hệ thống quản lý vật tư xây dựng

Đồ án môn **Hệ quản trị cơ sở dữ liệu**.

## 1. Giới thiệu

Hệ thống quản lý vật tư xây dựng được xây dựng nhằm hỗ trợ doanh nghiệp quản lý toàn bộ quá trình nhập, xuất và theo dõi tồn kho vật tư nội bộ.

Hệ thống tập trung vào các nghiệp vụ:

- Quản lý danh mục vật tư.
- Quản lý kho.
- Nhập vật tư từ nhà cung cấp.
- Xuất vật tư cho công trình.
- Chuyển vật tư giữa các kho.
- Điều chỉnh tồn kho sau kiểm kê.
- Tra cứu và thống kê dữ liệu.
- Kiểm thử các vấn đề tương tranh trong cơ sở dữ liệu.

Luồng nghiệp vụ chính:

```
Nhà cung cấp
      ↓
Nhập kho
      ↓
Theo dõi tồn kho
      ↓
Xuất vật tư cho công trình
      ↓
Chuyển kho / Điều chỉnh tồn
      ↓
Báo cáo và thống kê
```

---

# 2. Công nghệ sử dụng

## Backend

- Python
- Streamlit
- pyodbc

## Database

- Microsoft SQL Server
- T-SQL

## Công cụ phát triển

- Visual Studio Code
- SQL Server Management Studio
- Git/GitHub

---

# 3. Kiến trúc hệ thống

Cấu trúc thư mục:

```
QuanLyVatTu/

│── app.py
│── database.py
│── requirements.txt
│── .env.example

│── assets/
│   └── style.css

│── database/
│   ├── quan_ly_vat_tu.sql
│   ├── Nhap_kho.sql
│   ├── Xuat_kho.sql
│   ├── Chuyen_kho.sql
│   └── trigger.sql


│── src/

    ├── auth.py
    ├── inventory_ops.py
    ├── master_data.py
    ├── queries_reports.py
    ├── concurrency_runner.py
    └── utils.py
```

---

# 4. Vai trò các module

## app.py

File khởi động hệ thống Streamlit.

Chịu trách nhiệm:

- Hiển thị giao diện.
- Điều hướng các chức năng.
- Kiểm tra quyền người dùng.

---

## database.py

Quản lý kết nối SQL Server.

Chức năng:

- Đọc thông tin kết nối từ file `.env`.
- Tạo kết nối database.
- Xử lý lỗi kết nối.

---

## src/auth.py

Xử lý:

- Đăng nhập.
- Xác thực tài khoản.
- Kiểm tra quyền truy cập.

---

## src/inventory_ops.py

Xử lý nghiệp vụ kho:

- Nhập kho.
- Xuất kho.
- Chuyển kho.
- Điều chỉnh tồn.

Các nghiệp vụ thay đổi dữ liệu sử dụng transaction để đảm bảo tính toàn vẹn.

---

## src/master_data.py

Quản lý dữ liệu danh mục:

- Vật tư.
- Kho.
- Nhà cung cấp.
- Công trình.

---

## src/queries_reports.py

Xử lý:

- Tra cứu tồn kho.
- Báo cáo nhập xuất tồn.
- Thống kê dữ liệu.

---

## src/concurrency_runner.py

Module phục vụ kiểm thử tương tranh.

Mô phỏng các lỗi:

- Lost Update.
- Dirty Read.
- Non-repeatable Read.
- Phantom Read.

---

# 5. Chức năng hệ thống

## Quản trị

- Quản lý tài khoản.
- Quản lý danh mục.
- Quản lý dữ liệu hệ thống.

## Nghiệp vụ kho

- Nhập kho vật tư.
- Xuất kho vật tư.
- Chuyển vật tư giữa các kho.
- Điều chỉnh số lượng tồn.

## Báo cáo

- Theo dõi tồn kho.
- Cảnh báo vật tư dưới mức tối thiểu.
- Báo cáo nhập - xuất - tồn.

---

# 6. Cài đặt môi trường

## Bước 1: Clone project

```bash
git clone <repository-url>
```

Di chuyển vào thư mục:

```bash
cd QuanLyVatTu
```

---

## Bước 2: Tạo môi trường Python

Cài đặt thư viện:

```bash
pip install -r requirements.txt
```

---

# 7. Cấu hình Database

## Tạo database

Mở SQL Server Management Studio.

Chạy file:

```
database/quan_ly_vat_tu.sql
```

Sau đó chạy các file nghiệp vụ:

```
Nhap_kho.sql
Xuat_kho.sql
Chuyen_kho.sql
trigger.sql
```

---

# 8. Cấu hình file .env

Tạo file:

```
.env
```

từ:

```
.env.example
```

Ví dụ:

```env
DB_SERVER=localhost\SQLEXPRESS
DB_NAME=QuanLyVatTuXayDung
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_TRUSTED_CONNECTION=yes
```

Lưu ý:

File `.env` không được commit lên GitHub.

---

# 9. Chạy hệ thống

Khởi động ứng dụng:

```bash
streamlit run app.py
```

Sau khi chạy thành công, truy cập:

```
http://localhost:8501
```

---

# 10. Kiểm thử tương tranh

Chạy module:

```
src/concurrency_runner.py
```

Mục đích:

- Mô phỏng các giao tác đồng thời.
- Quan sát lỗi xảy ra.
- Đánh giá mức độ ảnh hưởng.
- Kiểm tra phương pháp xử lý.

---

# 11. Quy trình làm việc nhóm

Trước khi chỉnh sửa:

```bash
git pull origin main
```

Sau khi hoàn thành:

```bash
git add .
git commit -m "Mô tả thay đổi"
git push origin main
```

Không sử dụng:

```bash
git push --force
```

trừ khi được người leader xác nhận.

---

# 12. Thành viên phát triển

Danh sách thành viên:

| Thành viên | Phụ trách |
|---|---|
| ... | ...|
| ... | ...|
| ... | ...|
| ... | ...|
| ... | ...|
