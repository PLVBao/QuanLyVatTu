import streamlit as st
import pandas as pd
from database import execute_query, reset_database_data
from src.auth import (
    init_session,
    is_authenticated,
    is_manager,
    is_staff,
    get_current_user,
    logout_user,
    can_access_module,
    render_access_denied,
    render_login_ui,
    render_accounts_management_ui
)
from src.master_data import render_master_data_ui
from src.inventory_ops import render_inventory_ops_ui
from src.queries_reports import render_queries_reports_ui
from src.concurrency_runner import render_concurrency_demo_ui
from src.utils import format_quantity, apply_quantity_format
from streamlit_option_menu import option_menu

import pathlib

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Hệ thống Quản lý Vật tư Doanh nghiệp",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Nạp bộ CSS Enterprise ERP từ assets/style.css
css_file = pathlib.Path(__file__).parent / "assets" / "style.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Khởi tạo phiên
init_session()

def render_dashboard_overview():
    """Trang chủ: Bảng điều khiển Tổng quan hệ thống."""
    st.title("Tổng quan hệ thống")
    st.caption("Doanh nghiệp Xây dựng - Phân hệ Quản trị Kho & Cung ứng Vật tư")

    df_vt_count = execute_query("SELECT COUNT(*) AS Cnt FROM VAT_TU WHERE TrangThai = 1")
    df_ton_sum = execute_query("SELECT COALESCE(SUM(SoLuongTon), 0) AS TotalStock FROM TON_KHO")
    df_alert_count = execute_query("""
        SELECT COUNT(*) AS Cnt 
        FROM TON_KHO tk 
        JOIN VAT_TU vt ON tk.MaVT = vt.MaVT 
        WHERE tk.SoLuongTon <= vt.TonToiThieu
    """)
    df_ct_active = execute_query("SELECT COUNT(*) AS Cnt FROM CONG_TRINH WHERE TrangThai = 'DANG_THI_CONG'")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        cnt_vt = int(df_vt_count.iloc[0]["Cnt"]) if not df_vt_count.empty else 0
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Vật tư đang quản lý</span>
                <div class="kpi-icon-wrap kpi-icon-blue">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                </div>
            </div>
            <div class="kpi-body">
                <div class="kpi-value">{cnt_vt:,}</div>
                <span class="kpi-badge-normal">Danh mục</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        total_ton = float(df_ton_sum.iloc[0]["TotalStock"]) if not df_ton_sum.empty else 0.0
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Tổng lượng tồn kho</span>
                <div class="kpi-icon-wrap kpi-icon-emerald">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>
                </div>
            </div>
            <div class="kpi-body">
                <div class="kpi-value">{format_quantity(total_ton)}</div>
                <span class="kpi-badge-success">Toàn hệ thống</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        alert_cnt = int(df_alert_count.iloc[0]["Cnt"]) if not df_alert_count.empty else 0
        badge_html = f'<span class="kpi-badge-alert">Cảnh báo ({alert_cnt})</span>' if alert_cnt > 0 else '<span class="kpi-badge-success">Đạt định mức</span>'
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Mặt hàng chạm ngưỡng cảnh báo</span>
                <div class="kpi-icon-wrap kpi-icon-red">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                </div>
            </div>
            <div class="kpi-body">
                <div class="kpi-value">{alert_cnt:,}</div>
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Xem chi tiết →", key="btn_view_alert_details", use_container_width=True):
            st.session_state["nav_selection"] = "Báo cáo & Cảnh báo tồn"
            st.session_state["force_nav"] = True
            st.session_state["report_focus_alert"] = True
            st.rerun()

    with c4:
        cnt_ct = int(df_ct_active.iloc[0]["Cnt"]) if not df_ct_active.empty else 0
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Công trình đang thi công</span>
                <div class="kpi-icon-wrap kpi-icon-indigo">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><path d="M9 22v-4h6v4"></path><path d="M8 6h.01"></path><path d="M16 6h.01"></path><path d="M12 6h.01"></path><path d="M12 10h.01"></path><path d="M12 14h.01"></path><path d="M16 10h.01"></path><path d="M16 14h.01"></path><path d="M8 10h.01"></path><path d="M8 14h.01"></path></svg>
                </div>
            </div>
            <div class="kpi-body">
                <div class="kpi-value">{cnt_ct:,}</div>
                <span class="kpi-badge-normal">Đang cấp VT</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")

    col_left, col_right = st.columns([1.8, 1.2])

    with col_left:
        st.markdown("##### Số dư tồn kho theo mặt hàng và kho bãi")
        df_ton_kho = execute_query("""
            SELECT 
                k.TenKho,
                vt.TenVT,
                vt.DonViTinh,
                tk.SoLuongTon,
                vt.TonToiThieu
            FROM TON_KHO tk
            JOIN VAT_TU vt ON tk.MaVT = vt.MaVT
            JOIN KHO k ON tk.MaKho = k.MaKho
            ORDER BY k.TenKho, vt.TenVT
        """)
        df_ton_kho = apply_quantity_format(df_ton_kho, ["SoLuongTon", "TonToiThieu"])
        st.dataframe(
            df_ton_kho,
            use_container_width=True,
            hide_index=True,
            column_config={
                "TenKho": "Kho lưu trữ",
                "TenVT": "Tên vật tư",
                "DonViTinh": "ĐVT",
                "SoLuongTon": "Số lượng tồn",
                "TonToiThieu": "Tồn tối thiểu"
            }
        )

    with col_right:
        st.markdown("""
        <div class="process-card">
            <div class="process-card-title">Quy trình nghiệp vụ kho trọng tâm</div>
            <div class="process-step-item">
                <span class="process-step-num">1</span>
                <div><strong>Nhập kho:</strong> Tiếp nhận vật tư từ NCC vào kho lưu trữ.</div>
            </div>
            <div class="process-step-item">
                <span class="process-step-num">2</span>
                <div><strong>Xuất kho:</strong> Xuất cấp vật tư phục vụ thi công công trình.</div>
            </div>
            <div class="process-step-item">
                <span class="process-step-num">3</span>
                <div><strong>Chuyển kho:</strong> Điều chuyển cân bằng vật tư giữa các kho nội bộ.</div>
            </div>
            <div class="process-step-item">
                <span class="process-step-num">4</span>
                <div><strong>Kiểm kê:</strong> Cân bằng số liệu sau kiểm đếm hiện trường.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if alert_cnt > 0:
            st.markdown(f"""
            <div class="alert-card-warning">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2" style="flex-shrink:0; margin-top:2px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                <div>Phát hiện <strong>{alert_cnt}</strong> mặt hàng có lượng tồn thấp hơn mức tối thiểu. Vui lòng kiểm tra phân hệ <em>Báo cáo & Cảnh báo tồn</em>.</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Đi tới Báo cáo & Cảnh báo tồn →", key="btn_goto_alert_banner", use_container_width=True):
                st.session_state["nav_selection"] = "Báo cáo & Cảnh báo tồn"
                st.session_state["force_nav"] = True
                st.session_state["report_focus_alert"] = True
                st.rerun()

    st.write("---")
    st.markdown("##### Giao dịch chứng từ phát sinh gần đây")
    # Sửa triệt để lỗi encoding: dùng N'Nhập kho' để SQL Server không bị mã hóa dấu ?
    df_recent = execute_query("""
        SELECT TOP 5 
            N'Nhập kho' AS LoaiGiaoDich,
            pn.MaPN AS MaPhieu,
            pn.NgayNhap AS NgayGiaoDich,
            vt.TenVT,
            ctn.SoLuong,
            k.TenKho,
            tk.HoTen AS NguoiLap
        FROM PHIEU_NHAP pn
        JOIN CT_PHIEU_NHAP ctn ON pn.MaPN = ctn.MaPN
        JOIN KHO k ON pn.MaKho = k.MaKho
        JOIN VAT_TU vt ON ctn.MaVT = vt.MaVT
        JOIN TAI_KHOAN tk ON pn.NguoiLap = tk.MaTK
        ORDER BY pn.NgayNhap DESC
    """)
    df_recent = apply_quantity_format(df_recent, ["SoLuong"])
    st.dataframe(
        df_recent,
        use_container_width=True,
        hide_index=True,
        column_config={
            "LoaiGiaoDich": "Loại chứng từ",
            "MaPhieu": "Mã phiếu",
            "NgayGiaoDich": st.column_config.DatetimeColumn("Thời gian ghi nhận", format="DD/MM/YYYY HH:mm"),
            "TenVT": "Mặt hàng",
            "SoLuong": "Số lượng",
            "TenKho": "Kho tiếp nhận",
            "NguoiLap": "Người lập"
        }
    )

def main():
    if not is_authenticated():
        render_login_ui()
        return

    user = get_current_user()
    role_vn = "Quản lý hệ thống (Toàn quyền)" if is_manager() else "Nhân viên kho (Nghiệp vụ)"

    with st.sidebar:
        st.markdown(f"""
        <div class="user-profile-card">
            <div class="user-profile-name">{user.get('HoTen', 'NGƯỜI DÙNG')}</div>
            <div class="user-profile-meta">Tài khoản: {user.get('TenDangNhap', '')} | Mã: {user.get('MaTK', '')}</div>
            <div class="user-profile-badge">{role_vn}</div>
        </div>
        """, unsafe_allow_html=True)

        if is_manager():
            menu_options = [
                "Tổng quan hệ thống",
                "Quản lý danh mục",
                "Nghiệp vụ kho vật tư",
                "Báo cáo & Cảnh báo tồn",
                "Kiểm thử tương tranh SQL",
                "Phân quyền tài khoản"
            ]
            menu_icons = ["grid-1x2", "archive", "arrow-left-right", "graph-up", "shield-lock", "person-gear"]
        else:
            # Tài khoản Nhân viên kho: Menu giới hạn chỉ gồm các chức năng nghiệp vụ kho và tra cứu
            menu_options = [
                "Tổng quan hệ thống",
                "Nghiệp vụ kho vật tư",
                "Báo cáo & Cảnh báo tồn"
            ]
            menu_icons = ["grid-1x2", "arrow-left-right", "graph-up"]

        # Quản lý trạng thái điều hướng menu
        if "nav_selection" not in st.session_state or st.session_state["nav_selection"] not in menu_options:
            st.session_state["nav_selection"] = "Tổng quan hệ thống"

        target_idx = menu_options.index(st.session_state["nav_selection"])
        manual_idx = None
        if st.session_state.get("force_nav"):
            manual_idx = target_idx
            st.session_state["force_nav"] = False

        selected_page = option_menu(
            menu_title="DANH MỤC HỆ THỐNG",
            options=menu_options,
            icons=menu_icons,
            menu_icon="layers-half",
            default_index=target_idx,
            manual_select=manual_idx,
            key="main_menu_nav",
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#64748B", "font-size": "15px"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "3px 0",
                    "border-radius": "8px",
                    "color": "#334155",
                    "padding": "10px 14px"
                },
                "nav-link-selected": {
                    "background-color": "#EFF6FF",
                    "color": "#1D4ED8",
                    "font-weight": "600",
                    "border-left": "4px solid #2563EB"
                }
            }
        )

        st.session_state["nav_selection"] = selected_page

        st.write("---")
        st.markdown("""
        <div style="padding: 2px 0 6px 0; font-size: 12px; color: #64748B; line-height: 1.5;">
            <div style="font-weight: 600; color: #334155;">Quản lý vật tư xây dựng</div>
            <div style="display: flex; align-items: center; gap: 6px; margin-top: 3px;">
                <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background-color: #10B981;"></span>
                <span>Trạng thái: Đang hoạt động</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Nút Đăng xuất ở chân Sidebar: Full width, Outlined mỏng thanh lịch
        if st.button("Đăng xuất", use_container_width=True, key="btn_logout"):
            logout_user()

    # Kiểm tra quyền truy cập phân hệ khi gọi module (Module Access Guard)
    if not can_access_module(selected_page):
        render_access_denied(selected_page)
        return

    # Điều hướng trang khi đã thỏa mãn phân quyền
    if selected_page == "Tổng quan hệ thống":
        render_dashboard_overview()
    elif selected_page == "Quản lý danh mục":
        render_master_data_ui()
    elif selected_page == "Nghiệp vụ kho vật tư":
        render_inventory_ops_ui()
    elif selected_page == "Báo cáo & Cảnh báo tồn":
        render_queries_reports_ui()
    elif selected_page in ("Kiểm thử tương tranh SQL", "Kiểm thử giao tác & Tương tranh"):
        render_concurrency_demo_ui()
    elif selected_page == "Phân quyền tài khoản":
        render_accounts_management_ui()

if __name__ == "__main__":
    main()
