import streamlit as st
import pandas as pd
from datetime import datetime
from database import execute_query, execute_sp
from src.auth import get_current_user
from src.utils import format_quantity

def get_next_id(table_name: str, id_col: str, prefix: str) -> str:
    """Tự động sinh mã chứng từ kế tiếp dạng PN04, PX02, PCK02, PDC02."""
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

def render_inventory_ops_ui():
    """Giao diện Nghiệp vụ Quản lý Kho vật tư chuẩn Enterprise ERP."""
    st.title("Nghiệp vụ kho vật tư")
    st.caption("Thực thi các nghiệp vụ biến động kho thông qua Stored Procedure đảm bảo an toàn giao tác và tính toàn vẹn dữ liệu")

    tab_nhap, tab_xuat, tab_chuyen, tab_dieuchinh = st.tabs([
        "Nhập kho",
        "Xuất kho công trình",
        "Chuyển kho",
        "Điều chỉnh kiểm kê"
    ])

    current_user = get_current_user()
    user_id = current_user.get("MaTK", "TK01")
    user_name = current_user.get("HoTen", "Quản trị viên")

    # ==============================================================
    # 1. NHẬP KHO (sp_NhapKho)
    # ==============================================================
    with tab_nhap:
        st.markdown("##### Lập phiếu nhập kho vật tư")
        st.caption("Thủ tục thực thi: sp_NhapKho")

        df_ncc = execute_query("SELECT MaNCC, TenNCC FROM NHA_CUNG_CAP WHERE TrangThai = 1 ORDER BY MaNCC")
        df_kho = execute_query("SELECT MaKho, TenKho FROM KHO WHERE TrangThai = 1 ORDER BY MaKho")
        df_vt = execute_query("SELECT MaVT, TenVT, DonViTinh FROM VAT_TU WHERE TrangThai = 1 ORDER BY MaVT")

        if df_ncc.empty or df_kho.empty or df_vt.empty:
            st.error("Cần có ít nhất một Nhà cung cấp, một Kho và một Vật tư đang hoạt động trong hệ thống.")
        else:
            with st.form("form_nhap_kho", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    ma_pn = st.text_input("Mã phiếu nhập", value=get_next_id("PHIEU_NHAP", "MaPN", "PN")).strip()
                    
                    ncc_opts = {f"{r['MaNCC']} - {r['TenNCC']}": r['MaNCC'] for _, r in df_ncc.iterrows()}
                    sel_ncc = st.selectbox("Nhà cung cấp", list(ncc_opts.keys()))
                    
                    kho_opts = {f"{r['MaKho']} - {r['TenKho']}": r['MaKho'] for _, r in df_kho.iterrows()}
                    sel_kho = st.selectbox("Kho lưu trữ nhận hàng", list(kho_opts.keys()))
                    
                    ngay_nhap = st.date_input("Ngày nhập hàng", value=datetime.today())
                
                with col2:
                    vt_opts = {f"{r['MaVT']} - {r['TenVT']} ({r['DonViTinh']})": (r['MaVT'], r['DonViTinh']) for _, r in df_vt.iterrows()}
                    sel_vt = st.selectbox("Vật tư nhập kho", list(vt_opts.keys()))
                    ma_vt, dvt = vt_opts[sel_vt]
                    
                    so_luong = st.number_input("Số lượng nhập", min_value=0.01, value=50.0, step=1.0)
                    don_gia = st.number_input("Đơn giá nhập (VNĐ)", min_value=1.0, value=100000.0, step=5000.0, format="%.0f")
                    
                    ghi_chu = st.text_input("Ghi chú chứng từ", value="Nhập vật tư mới")

                st.caption(f"Người lập phiếu: {user_name} ({user_id})")
                btn_nhap = st.form_submit_button("Xác nhận nhập kho", type="primary", use_container_width=True)
                
                if btn_nhap:
                    if not ma_pn:
                        st.error("Vui lòng điền mã phiếu nhập.")
                    else:
                        dt_nhap = datetime.combine(ngay_nhap, datetime.now().time())
                        ok, msg = execute_sp("sp_NhapKho", (
                            ma_pn,
                            ncc_opts[sel_ncc],
                            kho_opts[sel_kho],
                            dt_nhap,
                            user_id,
                            ghi_chu,
                            "HOAN_THANH",
                            ma_vt,
                            float(so_luong),
                            float(don_gia)
                        ))
                        if ok:
                            st.success(f"Ghi nhận nhập kho thành công: Chứng từ {ma_pn}. Dữ liệu tồn kho đã được cập nhật đồng bộ.")
                        else:
                            st.error(f"Lỗi thực thi: {msg}")

    # ==============================================================
    # 2. XUẤT KHO CÔNG TRÌNH (sp_XuatKho)
    # ==============================================================
    with tab_xuat:
        st.markdown("##### Lập phiếu xuất cấp vật tư cho công trình")
        st.caption("Thủ tục thực thi: sp_XuatKho (Tự động áp dụng khóa UPDLOCK để bảo đảm an toàn số dư tồn)")

        df_kho = execute_query("SELECT MaKho, TenKho FROM KHO WHERE TrangThai = 1 ORDER BY MaKho")
        df_ct = execute_query("SELECT MaCT, TenCT FROM CONG_TRINH ORDER BY MaCT")
        df_vt = execute_query("SELECT MaVT, TenVT, DonViTinh FROM VAT_TU WHERE TrangThai = 1 ORDER BY MaVT")

        if df_kho.empty or df_ct.empty or df_vt.empty:
            st.error("Cần có ít nhất một Kho, một Công trình và một Vật tư trong hệ thống.")
        else:
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                kho_opts_x = {f"{r['MaKho']} - {r['TenKho']}": r['MaKho'] for _, r in df_kho.iterrows()}
                sel_kho_x = st.selectbox("Kho xuất", list(kho_opts_x.keys()), key="sb_xk_kho")
                ma_kho_x = kho_opts_x[sel_kho_x]
            with col_sel2:
                vt_opts_x = {f"{r['MaVT']} - {r['TenVT']} ({r['DonViTinh']})": (r['MaVT'], r['DonViTinh']) for _, r in df_vt.iterrows()}
                sel_vt_x = st.selectbox("Vật tư xuất cấp", list(vt_opts_x.keys()), key="sb_xk_vt")
                ma_vt_x, dvt_x = vt_opts_x[sel_vt_x]

            df_curr_ton = execute_query(
                "SELECT SoLuongTon FROM TON_KHO WHERE MaKho = ? AND MaVT = ?",
                (ma_kho_x, ma_vt_x)
            )
            curr_ton = float(df_curr_ton.iloc[0]["SoLuongTon"]) if not df_curr_ton.empty else 0.0

            if curr_ton > 0:
                st.info(f"Tồn kho khả dụng của {sel_vt_x} tại {sel_kho_x}: {format_quantity(curr_ton, dvt_x)}")
            else:
                st.warning(f"Vật tư này hiện không còn số lượng tồn ({format_quantity(0, dvt_x)}) tại kho đã chọn.")

            with st.form("form_xuat_kho", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    ma_px = st.text_input("Mã phiếu xuất", value=get_next_id("PHIEU_XUAT", "MaPX", "PX")).strip()
                    ct_opts = {f"{r['MaCT']} - {r['TenCT']}": r['MaCT'] for _, r in df_ct.iterrows()}
                    sel_ct = st.selectbox("Công trình tiếp nhận", list(ct_opts.keys()))
                    ngay_xuat = st.date_input("Ngày xuất cấp", value=datetime.today())
                with col2:
                    so_luong_x = st.number_input("Số lượng xuất", min_value=0.01, value=min(10.0, curr_ton if curr_ton > 0 else 1.0), step=1.0)
                    ghi_chu_x = st.text_input("Mục đích sử dụng / Ghi chú", value="Xuất cấp thi công theo tiến độ")

                st.caption(f"Người lập phiếu: {user_name} ({user_id})")
                btn_xuat = st.form_submit_button("Xác nhận xuất kho", type="primary", use_container_width=True)
                
                if btn_xuat:
                    if not ma_px:
                        st.error("Vui lòng điền mã phiếu xuất.")
                    else:
                        dt_xuat = datetime.combine(ngay_xuat, datetime.now().time())
                        ok, msg = execute_sp("sp_XuatKho", (
                            ma_px,
                            ma_kho_x,
                            ct_opts[sel_ct],
                            dt_xuat,
                            user_id,
                            ghi_chu_x,
                            "HOAN_THANH",
                            ma_vt_x,
                            float(so_luong_x)
                        ))
                        if ok:
                            st.success(f"Ghi nhận xuất kho thành công: Chứng từ {ma_px}. Đã trừ tồn kho theo số lượng thực xuất.")
                        else:
                            st.error(f"Lỗi thực thi: {msg}")

    # ==============================================================
    # 3. CHUYỂN KHO (sp_ChuyenKho)
    # ==============================================================
    with tab_chuyen:
        st.markdown("##### Lập phiếu điều chuyển vật tư giữa các kho")
        st.caption("Thủ tục thực thi: sp_ChuyenKho (Trừ kho nguồn và cộng kho đích trong cùng một giao tác)")

        df_kho = execute_query("SELECT MaKho, TenKho FROM KHO WHERE TrangThai = 1 ORDER BY MaKho")
        df_vt = execute_query("SELECT MaVT, TenVT, DonViTinh FROM VAT_TU WHERE TrangThai = 1 ORDER BY MaVT")

        if len(df_kho) < 2:
            st.error("Hệ thống yêu cầu tối thiểu 2 kho lưu trữ đang hoạt động để thực hiện điều chuyển.")
        else:
            col_k1, col_k2 = st.columns(2)
            kho_opts_all = {f"{r['MaKho']} - {r['TenKho']}": r['MaKho'] for _, r in df_kho.iterrows()}
            kho_keys = list(kho_opts_all.keys())

            with col_k1:
                sel_kho_nguon = st.selectbox("Kho nguồn (Xuất)", kho_keys, index=0, key="sb_ck_nguon")
                ma_kho_nguon = kho_opts_all[sel_kho_nguon]
            with col_k2:
                sel_kho_dich = st.selectbox("Kho đích (Nhận)", kho_keys, index=1 if len(kho_keys) > 1 else 0, key="sb_ck_dich")
                ma_kho_dich = kho_opts_all[sel_kho_dich]

            vt_opts_ck = {f"{r['MaVT']} - {r['TenVT']} ({r['DonViTinh']})": (r['MaVT'], r['DonViTinh']) for _, r in df_vt.iterrows()}
            sel_vt_ck = st.selectbox("Vật tư điều chuyển", list(vt_opts_ck.keys()), key="sb_ck_vt")
            ma_vt_ck, dvt_ck = vt_opts_ck[sel_vt_ck]

            df_curr_nguon = execute_query(
                "SELECT SoLuongTon FROM TON_KHO WHERE MaKho = ? AND MaVT = ?",
                (ma_kho_nguon, ma_vt_ck)
            )
            curr_ton_nguon = float(df_curr_nguon.iloc[0]["SoLuongTon"]) if not df_curr_nguon.empty else 0.0
            
            st.info(f"Tồn kho hiện tại tại Kho nguồn ({sel_kho_nguon}): {format_quantity(curr_ton_nguon, dvt_ck)}")

            with st.form("form_chuyen_kho", clear_on_submit=True):
                ma_pck = st.text_input("Mã phiếu chuyển kho", value=get_next_id("PHIEU_CHUYEN_KHO", "MaPCK", "PCK")).strip()
                sl_chuyen = st.number_input("Số lượng điều chuyển", min_value=0.01, value=min(5.0, curr_ton_nguon if curr_ton_nguon > 0 else 1.0), step=1.0)
                
                st.caption(f"Người lập phiếu: {user_name} ({user_id})")
                btn_chuyen = st.form_submit_button("Xác nhận điều chuyển", type="primary", use_container_width=True)

                if btn_chuyen:
                    if ma_kho_nguon == ma_kho_dich:
                        st.error("Kho nguồn và Kho đích không được trùng nhau.")
                    elif not ma_pck:
                        st.error("Vui lòng điền mã phiếu chuyển kho.")
                    else:
                        ok, msg = execute_sp("sp_ChuyenKho", (
                            ma_pck,
                            ma_kho_nguon,
                            ma_kho_dich,
                            ma_vt_ck,
                            float(sl_chuyen),
                            user_id
                        ))
                        if ok:
                            st.success(f"Ghi nhận chuyển kho thành công: Chứng từ {ma_pck}. Đã đồng bộ số dư giữa 2 kho.")
                        else:
                            st.error(f"Lỗi thực thi: {msg}")

    # ==============================================================
    # 4. ĐIỀU CHỈNH KIỂM KÊ (sp_DieuChinhKho)
    # ==============================================================
    with tab_dieuchinh:
        st.markdown("##### Lập phiếu điều chỉnh số dư sau kiểm kê")
        st.caption("Thủ tục thực thi: sp_DieuChinhKho (Cân đối số liệu thực tế tại hiện trường với số sách phần mềm)")

        df_kho = execute_query("SELECT MaKho, TenKho FROM KHO WHERE TrangThai = 1 ORDER BY MaKho")
        df_vt = execute_query("SELECT MaVT, TenVT, DonViTinh FROM VAT_TU WHERE TrangThai = 1 ORDER BY MaVT")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            kho_opts_dc = {f"{r['MaKho']} - {r['TenKho']}": r['MaKho'] for _, r in df_kho.iterrows()}
            sel_kho_dc = st.selectbox("Kho kiểm kê", list(kho_opts_dc.keys()), key="sb_dc_kho")
            ma_kho_dc = kho_opts_dc[sel_kho_dc]
        with col_d2:
            vt_opts_dc = {f"{r['MaVT']} - {r['TenVT']} ({r['DonViTinh']})": (r['MaVT'], r['DonViTinh']) for _, r in df_vt.iterrows()}
            sel_vt_dc = st.selectbox("Vật tư kiểm kê", list(vt_opts_dc.keys()), key="sb_dc_vt")
            ma_vt_dc, dvt_dc = vt_opts_dc[sel_vt_dc]

        df_ton_dc = execute_query("SELECT SoLuongTon FROM TON_KHO WHERE MaKho = ? AND MaVT = ?", (ma_kho_dc, ma_vt_dc))
        ton_truoc = float(df_ton_dc.iloc[0]["SoLuongTon"]) if not df_ton_dc.empty else 0.0

        st.metric(
            label=f"Số lượng tồn trên hệ thống trước kiểm kê ({dvt_dc})",
            value=format_quantity(ton_truoc)
        )

        with st.form("form_dieu_chinh", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                ma_pdc = st.text_input("Mã phiếu điều chỉnh", value=get_next_id("PHIEU_DIEU_CHINH", "MaPDC", "PDC")).strip()
                sl_sau = st.number_input("Số lượng thực tế sau kiểm đếm", min_value=0.0, value=ton_truoc, step=1.0)
            with col_b:
                ly_do = st.text_area("Lý do điều chỉnh (Bắt buộc)", placeholder="Ví dụ: Kiểm kê định kỳ phát hiện hao hụt tự nhiên trong quá trình vận chuyển...")

            st.caption(f"Người lập phiếu: {user_name} ({user_id})")
            btn_dc = st.form_submit_button("Xác nhận điều chỉnh", type="primary", use_container_width=True)

            if btn_dc:
                if not ma_pdc:
                    st.error("Vui lòng nhập mã phiếu điều chỉnh.")
                elif not ly_do or not ly_do.strip():
                    st.error("Lý do điều chỉnh không được để trống.")
                elif sl_sau == ton_truoc:
                    st.warning("Số lượng thực tế sau kiểm đếm trùng khớp với tồn kho hiện tại, không có chênh lệch.")
                else:
                    ok, msg = execute_sp("sp_DieuChinhKho", (
                        ma_pdc,
                        ma_kho_dc,
                        ma_vt_dc,
                        float(sl_sau),
                        user_id,
                        ly_do.strip()
                    ))
                    if ok:
                        diff = sl_sau - ton_truoc
                        diff_text = format_quantity(diff, show_plus=True)
                        st.success(f"Ghi nhận điều chỉnh thành công: Chứng từ {ma_pdc}. Chênh lệch ghi nhận: {diff_text} {dvt_dc}.")
                    else:
                        st.error(f"Lỗi thực thi: {msg}")
