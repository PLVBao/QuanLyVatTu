import streamlit as st
import pandas as pd
from database import execute_query, execute_non_query

def get_next_id(table_name: str, id_col: str, prefix: str) -> str:
    """Tự động sinh mã tài khoản kế tiếp có sắp xếp độ dài và giá trị chuẩn xác."""
    df = execute_query(
        f"SELECT TOP 1 {id_col} FROM {table_name} WHERE {id_col} LIKE ? ORDER BY LEN({id_col}) DESC, {id_col} DESC",
        (f"{prefix}%",)
    )
    if not df.empty:
        val = str(df.iloc[0][id_col]).strip()
        if val.startswith(prefix):
            try:
                num = int(val[len(prefix):]) + 1
                return f"{prefix}{num:02d}"
            except Exception:
                pass
    return f"{prefix}01"

def authenticate(username: str, password: str):
    """
    Xác thực người dùng từ bảng TAI_KHOAN.
    Chỉ cho phép đăng nhập nếu thông tin chính xác và TrangThai = 1.
    """
    sql = """
    SELECT MaTK, TenDangNhap, HoTen, VaiTro, TrangThai 
    FROM TAI_KHOAN 
    WHERE TenDangNhap = ? AND MatKhau = ?
    """
    df = execute_query(sql, (username, password))
    if df.empty:
        return False, "Tên đăng nhập hoặc mật khẩu không chính xác."
    
    user = df.iloc[0].to_dict()
    if not user.get("TrangThai", False):
        return False, "Tài khoản này hiện đang bị tạm khóa hoặc đã ngưng hoạt động."
        
    return True, user

def init_session():
    """Khởi tạo trạng thái phiên làm việc trong st.session_state."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None

def login_user(user_dict: dict):
    st.session_state.logged_in = True
    st.session_state.user = user_dict

def logout_user():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

def is_authenticated() -> bool:
    return st.session_state.get("logged_in", False) and st.session_state.get("user") is not None

def is_manager() -> bool:
    if not is_authenticated():
        return False
    return st.session_state.user.get("VaiTro") == "QUAN_LY"

def is_staff() -> bool:
    if not is_authenticated():
        return False
    return st.session_state.user.get("VaiTro") == "NHAN_VIEN"

def get_current_user() -> dict:
    return st.session_state.get("user", {})

# Ma trận phân quyền theo vai trò (Role-Based Access Control)
MODULE_PERMISSIONS = {
    "Tổng quan hệ thống": ["QUAN_LY", "NHAN_VIEN"],
    "Quản lý danh mục": ["QUAN_LY"],
    "Nghiệp vụ kho vật tư": ["QUAN_LY", "NHAN_VIEN"],
    "Báo cáo & Cảnh báo tồn": ["QUAN_LY", "NHAN_VIEN"],
    "Kiểm thử tương tranh SQL": ["QUAN_LY"],
    "Kiểm thử giao tác & Tương tranh": ["QUAN_LY"],
    "Phân quyền tài khoản": ["QUAN_LY"]
}

def can_access_module(module_name: str) -> bool:
    """Kiểm tra quyền truy cập vào module cụ thể dựa trên vai trò người dùng hiện tại."""
    if not is_authenticated():
        return False
    user_role = st.session_state.user.get("VaiTro", "")
    allowed_roles = MODULE_PERMISSIONS.get(module_name)
    if allowed_roles is None:
        # Mặc định an toàn: nếu module không xác định, chỉ QUAN_LY được truy cập
        return user_role == "QUAN_LY"
    return user_role in allowed_roles

def render_access_denied(module_name: str = ""):
    """Hiển thị giao diện Từ chối truy cập chuẩn Enterprise ERP khi người dùng không đủ quyền."""
    st.markdown("<div style='height: 2vh;'></div>", unsafe_allow_html=True)
    module_label = f" <strong>{module_name}</strong>" if module_name else ""
    st.markdown(f"""
    <div style="background-color: #FEF2F2; border: 1px solid #FECACA; border-left: 5px solid #DC2626; border-radius: 8px; padding: 22px 26px; margin-bottom: 20px;">
        <div style="display: flex; align-items: flex-start; gap: 16px;">
            <div style="background-color: #FEE2E2; padding: 10px; border-radius: 50%; color: #DC2626; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
            </div>
            <div>
                <div style="font-size: 17px; font-weight: 700; color: #991B1B; margin-bottom: 6px;">
                    Từ chối truy cập (Access Denied)
                </div>
                <div style="font-size: 13.5px; color: #7F1D1D; line-height: 1.6;">
                    Tài khoản của bạn không có đặc quyền truy cập vào phân hệ{module_label}.
                    <br>
                    Phân hệ này yêu cầu vai trò <strong>QUẢN LÝ (QUAN_LY)</strong>. Tài khoản nhân viên chỉ được phép thao tác các chức năng nghiệp vụ kho và tra cứu số dư tồn.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 1. GIAO DIỆN ĐĂNG NHẬP (ENTERPRISE STYLE)
# ==========================================
def render_login_ui():
    """Hiển thị màn hình đăng nhập hệ thống chuẩn Enterprise ERP."""
    st.markdown("<div style='height: 4vh;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; margin-bottom: 24px;'>
            <div style='font-size: 12.5px; font-weight: 700; color: #1D4ED8; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 6px;'>
                DOANH NGHIỆP XÂY DỰNG
            </div>
            <div style='font-size: 24px; font-weight: 700; color: #0F172A; letter-spacing: -0.3px;'>
                HỆ THỐNG QUẢN LÝ VẬT TƯ DOANH NGHIỆP
            </div>
            <div style='font-size: 13.5px; color: #64748B; margin-top: 6px;'>
                Phân hệ Quản trị Kho, Cung ứng & Kiểm kê Vật tư Xây dựng
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("<div style='font-size: 16px; font-weight: 600; color: #1E293B; margin-bottom: 16px;'>Đăng nhập hệ thống</div>", unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Tên đăng nhập", placeholder="Nhập tên đăng nhập...").strip()
                password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu...")
                submitted = st.form_submit_button("Đăng nhập hệ thống", use_container_width=True, type="primary")
                
                if submitted:
                    if not username or not password:
                        st.error("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
                    else:
                        success, res = authenticate(username, password)
                        if success:
                            login_user(res)
                            st.rerun()
                        else:
                            st.error(res)

        st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<div style='font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 10px;'>Thông tin tài khoản kiểm thử hệ thống</div>", unsafe_allow_html=True)
            df_demo = pd.DataFrame([
                {"Tài khoản": "admin", "Mật khẩu": "123456", "Vai trò": "QUAN_LY", "Phân quyền": "Toàn quyền quản trị & phân quyền"},
                {"Tài khoản": "nhanvien1", "Mật khẩu": "123456", "Vai trò": "NHAN_VIEN", "Phân quyền": "Thực hiện nghiệp vụ kho & tra cứu"},
                {"Tài khoản": "nhanvien2", "Mật khẩu": "123456", "Vai trò": "NHAN_VIEN", "Phân quyền": "Thực hiện nghiệp vụ kho & tra cứu"}
            ])
            st.dataframe(df_demo, use_container_width=True, hide_index=True)

# ==========================================
# 2. PHÂN QUYỀN VÀ QUẢN LÝ TÀI KHOẢN
# ==========================================
def render_accounts_management_ui():
    """Giao diện Quản lý Tài khoản (chỉ dành cho QUAN_LY)."""
    st.title("Phân quyền và quản lý tài khoản người dùng")
    st.caption("Quản trị danh sách người dùng, phân cấp quyền truy cập và kiểm soát trạng thái hoạt động")
    
    if not is_manager():
        st.error("Từ chối truy cập: Chức năng này chỉ dành cho tài khoản có vai trò QUẢN LÝ.")
        return

    tab1, tab2 = st.tabs(["Danh sách tài khoản", "Thêm tài khoản mới"])

    with tab1:
        df_accounts = execute_query("""
            SELECT MaTK, TenDangNhap, HoTen, VaiTro, 
                   CASE WHEN TrangThai = 1 THEN N'Đang hoạt động' ELSE N'Đã khóa' END AS TrangThaiHienThi,
                   TrangThai
            FROM TAI_KHOAN
            ORDER BY MaTK
        """)
        
        st.dataframe(
            df_accounts[["MaTK", "TenDangNhap", "HoTen", "VaiTro", "TrangThaiHienThi"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "MaTK": "Mã tài khoản",
                "TenDangNhap": "Tên đăng nhập",
                "HoTen": "Họ và tên",
                "VaiTro": "Vai trò hệ thống",
                "TrangThaiHienThi": "Trạng thái"
            }
        )
        
        st.write("---")
        st.markdown("##### Cập nhật trạng thái tài khoản")
        col_acc, col_btn = st.columns([3, 1])
        with col_acc:
            account_options = {f"{row['MaTK']} - {row['HoTen']} ({row['TenDangNhap']})": row for _, row in df_accounts.iterrows()}
            selected_label = st.selectbox("Chọn tài khoản cần cập nhật trạng thái", list(account_options.keys()))
            selected_row = account_options[selected_label]
            
        with col_btn:
            st.write("")
            st.write("")
            current_status = selected_row["TrangThai"]
            target_status = 0 if current_status == 1 else 1
            action_text = "Khóa tài khoản" if current_status == 1 else "Mở khóa tài khoản"
            
            if st.button(action_text, use_container_width=True):
                # Không cho phép tự khóa tài khoản của chính mình
                if selected_row["MaTK"] == get_current_user().get("MaTK"):
                    st.error("Không thể tự khóa tài khoản quản trị đang đăng nhập hiện tại.")
                else:
                    ok, msg = execute_non_query(
                        "UPDATE TAI_KHOAN SET TrangThai = ? WHERE MaTK = ?",
                        (target_status, selected_row["MaTK"])
                    )
                    if ok:
                        st.success(f"Cập nhật trạng thái tài khoản {selected_row['MaTK']} thành công.")
                        st.rerun()
                    else:
                        st.error(f"Lỗi: {msg}")

    with tab2:
        st.markdown("##### Khởi tạo tài khoản người dùng mới")
        with st.form("add_account_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                # Gợi ý mã TK tiếp theo
                next_matk = get_next_id("TAI_KHOAN", "MaTK", "TK")
                ma_tk = st.text_input("Mã tài khoản", value=next_matk).strip()
                username = st.text_input("Tên đăng nhập").strip()
                password = st.text_input("Mật khẩu ban đầu", type="password")
            with col_b:
                full_name = st.text_input("Họ và tên nhân sự").strip()
                role = st.selectbox("Vai trò phân quyền", ["NHAN_VIEN", "QUAN_LY"])
                
            submitted = st.form_submit_button("Lưu tài khoản", type="primary", use_container_width=True)
            if submitted:
                if not ma_tk or not username or not password or not full_name:
                    st.error("Vui lòng điền đầy đủ tất cả các trường thông tin bắt buộc.")
                else:
                    chk = execute_query("SELECT 1 FROM TAI_KHOAN WHERE MaTK = ? OR TenDangNhap = ?", (ma_tk, username))
                    if not chk.empty:
                        st.error("Mã tài khoản hoặc Tên đăng nhập đã tồn tại trong hệ thống.")
                    else:
                        sql_ins = """
                        INSERT INTO TAI_KHOAN (MaTK, TenDangNhap, MatKhau, HoTen, VaiTro, TrangThai)
                        VALUES (?, ?, ?, ?, ?, 1)
                        """
                        ok, msg = execute_non_query(sql_ins, (ma_tk, username, password, full_name, role))
                        if ok:
                            st.success(f"Tạo tài khoản {username} thành công.")
                            st.rerun()
                        else:
                            st.error(f"Lỗi: {msg}")
