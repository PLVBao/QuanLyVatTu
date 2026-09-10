import os
import re
from pathlib import Path
import pyodbc
import pandas as pd
from dotenv import load_dotenv

# Xác định đường dẫn gốc của dự án và nạp file .env tuyệt đối
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)


# Cấu hình mặc định
DEFAULT_DB_NAME = os.getenv("DB_NAME", "QuanLyVatTuXayDung")
DEFAULT_SERVER = os.getenv("DB_SERVER", r"localhost\SQLEXPRESS")
DEFAULT_TRUSTED = os.getenv("DB_TRUSTED_CONNECTION", "yes")

def get_installed_driver() -> str:
    """Tự động tìm kiếm ODBC Driver phù hợp trên máy tính người dùng."""
    drivers = pyodbc.drivers()
    preferred = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server Native Client RDA 11.0",
        "SQL Server"
    ]
    for p in preferred:
        if p in drivers:
            return p
    return "SQL Server"

def get_connection(server: str = None, database: str = None):
    """Tạo kết nối đến SQL Server với cơ chế thử nghiệm và cấu hình linh hoạt."""
    driver = os.getenv("DB_DRIVER") or get_installed_driver()
    db = database or DEFAULT_DB_NAME
    
    server_candidates = [
        server or DEFAULT_SERVER,
        r".\SQLEXPRESS",
        r"localhost\SQLEXPRESS",
        r"(local)\SQLEXPRESS",
        "localhost",
        "."
    ]
    
    # Loại bỏ trùng lặp giữ nguyên thứ tự
    seen = set()
    server_list = []
    for s in server_candidates:
        if s and s not in seen:
            seen.add(s)
            server_list.append(s)

    last_error = None
    for srv in server_list:
        conn_str = f"DRIVER={{{driver}}};SERVER={srv};DATABASE={db};Trusted_Connection={DEFAULT_TRUSTED};"
        if "ODBC Driver 18" in driver:
            conn_str += "TrustServerCertificate=yes;"
            
        try:
            conn = pyodbc.connect(conn_str, autocommit=False, timeout=3)
            # Thiết lập mã hóa UTF-8 cho dữ liệu ký tự
            try:
                conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
                if os.name != 'nt':
                    conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
                    conn.setencoding(encoding='utf-8')
            except Exception:
                pass
            return conn
        except Exception as e:
            last_error = e
            continue


    raise ConnectionError(f"Không thể kết nối đến SQL Server Database '{db}'. Vui lòng kiểm tra dịch vụ SQL Server và cấu hình .env (Lỗi: {clean_sql_error(last_error) if last_error else 'Timeout'})")

def clean_sql_error(ex: Exception) -> str:
    """Trích xuất và làm sạch thông báo lỗi nghiệp vụ từ SQL Server / RAISERROR."""
    if ex is None:
        return ""
    msg = str(ex)
    if hasattr(ex, "args") and len(ex.args) > 1 and isinstance(ex.args[1], str):
        msg = ex.args[1]
    # Bỏ tiền tố lỗi ODBC/SQL Server dạng [42000] [Microsoft][ODBC Driver...]
    clean_msg = re.sub(r"\[.*?\]", "", msg).strip()
    # Bỏ hậu tố mã lỗi ODBC dạng (50000) (SQLExecDirectW) hoặc tương tự
    clean_msg = re.sub(r"\(\d+\)\s*\(SQL.*?\)", "", clean_msg).strip()
    return clean_msg if clean_msg else msg


def execute_sp(sp_name: str, params: tuple | list = ()) -> tuple[bool, str]:
    """
    Thực thi Stored Procedure có xử lý commit transaction và bắt lỗi từ
    khối TRY...CATCH / RAISERROR của SQL Server.
    
    Trả về:
        (success: bool, message: str)
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        placeholders = ", ".join(["?"] * len(params))
        sql = f"EXEC {sp_name} {placeholders}" if placeholders else f"EXEC {sp_name}"
        
        cursor.execute(sql, params)
        
        # Duyệt qua toàn bộ recordsets để nhận thông báo từ PRINT / RAISERROR
        while cursor.nextset():
            pass
            
        conn.commit()
        cursor.close()
        return True, "Thực thi giao tác thành công!"
    except pyodbc.Error as ex:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return False, clean_sql_error(ex)
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return False, str(e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

def execute_query(sql_query: str, params=None) -> pd.DataFrame:
    """
    Đọc kết quả truy vấn SELECT ra DataFrame của Pandas sạch sẽ, không warning.
    Có xử lý bắt lỗi pyodbc / kết nối an toàn và hiển thị thông báo thân thiện.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(sql_query, params)
        else:
            cursor.execute(sql_query)
        if cursor.description:
            cols = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            df = pd.DataFrame.from_records([tuple(r) for r in rows], columns=cols)
        else:
            df = pd.DataFrame()
        cursor.close()
        return df
    except (pyodbc.Error, ConnectionError) as ex:
        err_msg = clean_sql_error(ex)
        try:
            import streamlit as st
            st.error(f"Lỗi truy vấn CSDL: {err_msg}")
        except Exception:
            pass
        return pd.DataFrame()
    except Exception as e:
        err_msg = str(e)
        try:
            import streamlit as st
            st.error(f"Lỗi hệ thống CSDL: {err_msg}")
        except Exception:
            pass
        return pd.DataFrame()
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def execute_non_query(sql_query: str, params=None) -> tuple[bool, str]:
    """
    Thực thi câu lệnh T-SQL (như cập nhật danh mục, kích hoạt trigger, soft delete)
    có xử lý commit và bắt lỗi trigger.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(sql_query, params)
        else:
            cursor.execute(sql_query)
        while cursor.nextset():
            pass
        conn.commit()
        cursor.close()
        return True, "Thao tác thành công!"
    except pyodbc.Error as ex:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return False, clean_sql_error(ex)
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return False, str(e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

def reset_database_data() -> tuple[bool, str]:
    """
    Khôi phục toàn diện dữ liệu giao dịch và số dư tồn kho chuẩn mực ban đầu
    theo đúng kịch bản database/reset_data.sql (VT01 KHO01 = 465.00).
    """
    sql_script = """
    DELETE FROM CT_PHIEU_NHAP;
    DELETE FROM PHIEU_NHAP;
    DELETE FROM CT_PHIEU_XUAT;
    DELETE FROM PHIEU_XUAT;
    DELETE FROM CT_CHUYEN_KHO;
    DELETE FROM PHIEU_CHUYEN_KHO;
    DELETE FROM CT_DIEU_CHINH;
    DELETE FROM PHIEU_DIEU_CHINH;
    DELETE FROM TON_KHO;

    INSERT INTO PHIEU_NHAP (MaPN, MaNCC, MaKho, NgayNhap, NguoiLap, GhiChu, TrangThai)
    VALUES ('PN01', 'NCC01', 'KHO01', '2026-07-01', 'TK02', N'Nhập thép đợt 1', 'HOAN_THANH');
    INSERT INTO CT_PHIEU_NHAP (MaPN, MaVT, SoLuong, DonGia) VALUES ('PN01', 'VT01', 500, 150000);

    INSERT INTO PHIEU_NHAP (MaPN, MaNCC, MaKho, NgayNhap, NguoiLap, GhiChu, TrangThai)
    VALUES ('PN02', 'NCC02', 'KHO01', '2026-07-02', 'TK02', N'Nhập xi măng đợt 1', 'HOAN_THANH');
    INSERT INTO CT_PHIEU_NHAP (MaPN, MaVT, SoLuong, DonGia) VALUES ('PN02', 'VT02', 200, 90000);

    INSERT INTO PHIEU_NHAP (MaPN, MaNCC, MaKho, NgayNhap, NguoiLap, GhiChu, TrangThai)
    VALUES ('PN03', 'NCC02', 'KHO02', '2026-07-03', 'TK02', N'Nhập cát và đá', 'HOAN_THANH');
    INSERT INTO CT_PHIEU_NHAP (MaPN, MaVT, SoLuong, DonGia) 
    VALUES ('PN03', 'VT03', 1000, 350000), ('PN03', 'VT04', 800, 450000);

    INSERT INTO PHIEU_XUAT (MaPX, MaKho, MaCT, NgayXuat, NguoiLap, GhiChu, TrangThai)
    VALUES ('PX01', 'KHO01', 'CT01', '2026-07-05', 'TK02', N'Xuất thép cho công trình An Phú', 'HOAN_THANH');
    INSERT INTO CT_PHIEU_XUAT (MaPX, MaVT, SoLuong) VALUES ('PX01', 'VT01', 20);

    INSERT INTO PHIEU_CHUYEN_KHO (MaPCK, MaKhoNguon, MaKhoDich, NgayChuyen, NguoiLap, GhiChu, TrangThai)
    VALUES ('PCK01', 'KHO01', 'KHO02', '2026-07-08', 'TK02', N'Chuyển thép sang kho phụ', 'HOAN_THANH');
    INSERT INTO CT_CHUYEN_KHO (MaPCK, MaVT, SoLuong) VALUES ('PCK01', 'VT01', 10);

    INSERT INTO PHIEU_DIEU_CHINH (MaPDC, MaKho, NgayDieuChinh, NguoiLap, LyDo, TrangThai)
    VALUES ('PDC01', 'KHO01', '2026-07-10', 'TK01', N'Kiểm kê thực tế thiếu 5 cây thép', 'HOAN_THANH');
    INSERT INTO CT_DIEU_CHINH (MaPDC, MaVT, SoLuongTruoc, SoLuongSau) VALUES ('PDC01', 'VT01', 470, 465);

    INSERT INTO TON_KHO (MaKho, MaVT, SoLuongTon)
    VALUES
        ('KHO01', 'VT01', 465),
        ('KHO01', 'VT02', 200),
        ('KHO02', 'VT01', 10),
        ('KHO02', 'VT03', 1000),
        ('KHO02', 'VT04', 800);
    """
    return execute_non_query(sql_script)
