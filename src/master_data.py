import streamlit as st
import pandas as pd
from datetime import date
from database import execute_query, execute_non_query
from src.utils import format_quantity, apply_quantity_format

def get_next_id(table_name: str, id_col: str, prefix: str) -> str:
    """Tự động sinh mã danh mục kế tiếp có sắp xếp độ dài và giá trị chuẩn xác."""
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

def render_master_data_ui():
    """Giao diện Quản lý Danh mục Hệ thống chuẩn Enterprise ERP (Chỉ dành cho QUAN_LY)."""
    from src.auth import is_manager, render_access_denied
    if not is_manager():
        render_access_denied("Quản lý danh mục hệ thống")
        return

    st.title("Quản lý danh mục hệ thống")
    st.caption("Quản trị thông tin danh mục Vật tư, Phân loại, Nhà cung cấp, Kho bãi và Công trình xây dựng")

    tab_vt, tab_lvt, tab_ncc, tab_kho, tab_ct = st.tabs([
        "Vật tư",
        "Loại vật tư",
        "Nhà cung cấp",
        "Kho lưu trữ",
        "Công trình"
    ])

    # ==============================================================
    # 1. QUẢN LÝ VẬT TƯ
    # ==============================================================
    with tab_vt:
        subtab1, subtab2 = st.tabs(["Danh sách vật tư", "Thêm vật tư mới"])
        
        with subtab1:
            df_vt = execute_query("""
                SELECT vt.MaVT, vt.TenVT, lvt.TenLoai, vt.DonViTinh, 
                       vt.TonToiThieu, vt.MoTa,
                       CASE WHEN vt.TrangThai = 1 THEN N'Đang sử dụng' ELSE N'Ngừng sử dụng' END AS TrangThaiHienThi,
                       vt.TrangThai,
                       COALESCE((SELECT SUM(tk.SoLuongTon) FROM TON_KHO tk WHERE tk.MaVT = vt.MaVT), 0) AS TongTonKho
                FROM VAT_TU vt
                JOIN LOAI_VAT_TU lvt ON vt.MaLoai = lvt.MaLoai
                ORDER BY vt.MaVT
            """)
            
            df_vt_display = apply_quantity_format(df_vt, ["TonToiThieu", "TongTonKho"])
            st.dataframe(
                df_vt_display[["MaVT", "TenVT", "TenLoai", "DonViTinh", "TonToiThieu", "TongTonKho", "TrangThaiHienThi"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "MaVT": "Mã vật tư",
                    "TenVT": "Tên vật tư",
                    "TenLoai": "Phân loại",
                    "DonViTinh": "Đơn vị tính",
                    "TonToiThieu": "Tồn tối thiểu",
                    "TongTonKho": "Tổng tồn thực tế",
                    "TrangThaiHienThi": "Trạng thái"
                }
            )
            
            st.write("---")
            st.markdown("##### Cập nhật trạng thái sử dụng (Kiểm tra Trigger ràng buộc tồn kho)")
            st.caption("Thực thi lệnh DELETE để kiểm tra trigger trg_VatTu_NgauXoa. Nếu tồn kho > 0, hệ thống từ chối thao tác nhằm bảo toàn dữ liệu.")
            
            col_sel, col_act = st.columns([3, 1.2])
            with col_sel:
                vt_options = {f"{r['MaVT']} - {r['TenVT']} (Tồn: {format_quantity(r['TongTonKho'], r['DonViTinh'])} - {r['TrangThaiHienThi']})": r for _, r in df_vt.iterrows()}
                selected_label = st.selectbox("Chọn vật tư thao tác", list(vt_options.keys()), key="sb_vt_act")
                selected_vt = vt_options[selected_label]
            with col_act:
                st.write("")
                st.write("")
                if selected_vt["TrangThai"] == 1:
                    if st.button("Ngừng sử dụng / Xóa", use_container_width=True):
                        # Lệnh DELETE này kích hoạt trigger trg_VatTu_NgauXoa
                        ok, msg = execute_non_query("DELETE FROM VAT_TU WHERE MaVT = ?", (selected_vt["MaVT"],))
                        if ok:
                            st.success(f"Thông báo: {msg}")
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    if st.button("Khôi phục sử dụng", type="primary", use_container_width=True):
                        ok, msg = execute_non_query("UPDATE VAT_TU SET TrangThai = 1 WHERE MaVT = ?", (selected_vt["MaVT"],))
                        if ok:
                            st.success(f"Đã kích hoạt lại vật tư {selected_vt['MaVT']}.")
                            st.rerun()
                        else:
                            st.error(f"Lỗi: {msg}")

        with subtab2:
            st.markdown("##### Khởi tạo mặt hàng vật tư mới")
            df_loai = execute_query("SELECT MaLoai, TenLoai FROM LOAI_VAT_TU")
            if df_loai.empty:
                st.warning("Cần tạo ít nhất một Loại vật tư trước khi tạo Vật tư.")
            else:
                with st.form("form_add_vt", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        next_mavt = get_next_id("VAT_TU", "MaVT", "VT")
                        ma_vt = st.text_input("Mã vật tư", value=next_mavt).strip()
                        ten_vt = st.text_input("Tên vật tư quy chuẩn").strip()
                        loai_opts = {f"{r['MaLoai']} - {r['TenLoai']}": r['MaLoai'] for _, r in df_loai.iterrows()}
                        sel_loai = st.selectbox("Nhóm loại vật tư", list(loai_opts.keys()))
                    with col2:
                        dvt = st.text_input("Đơn vị tính (Cây, Bao, Mét khối, Tấn...)").strip()
                        ton_min = st.number_input("Mức tồn tối thiểu cảnh báo", min_value=0.0, value=20.0, step=1.0)
                        mo_ta = st.text_input("Mô tả quy cách kỹ thuật")
                    
                    btn_save_vt = st.form_submit_button("Lưu vật tư", type="primary", use_container_width=True)
                    if btn_save_vt:
                        if not ma_vt or not ten_vt or not dvt:
                            st.error("Vui lòng điền đủ Mã, Tên vật tư và Đơn vị tính.")
                        else:
                            chk = execute_query("SELECT 1 FROM VAT_TU WHERE MaVT = ?", (ma_vt,))
                            if not chk.empty:
                                st.error(f"Mã vật tư '{ma_vt}' đã tồn tại trong hệ thống.")
                            else:
                                sql_ins = """
                                INSERT INTO VAT_TU (MaVT, TenVT, MaLoai, DonViTinh, TonToiThieu, MoTa, TrangThai)
                                VALUES (?, ?, ?, ?, ?, ?, 1)
                                """
                                ok, msg = execute_non_query(sql_ins, (ma_vt, ten_vt, loai_opts[sel_loai], dvt, ton_min, mo_ta))
                                if ok:
                                    st.success(f"Thêm vật tư '{ten_vt}' ({ma_vt}) thành công.")
                                    st.rerun()
                                else:
                                    st.error(f"Lỗi: {msg}")

    # ==============================================================
    # 2. QUẢN LÝ LOẠI VẬT TƯ
    # ==============================================================
    with tab_lvt:
        col_l1, col_l2 = st.columns([1.5, 1])
        with col_l1:
            st.markdown("##### Danh mục phân loại vật tư")
            df_lvt = execute_query("SELECT MaLoai, TenLoai, MoTa FROM LOAI_VAT_TU ORDER BY MaLoai")
            st.dataframe(df_lvt, use_container_width=True, hide_index=True, column_config={
                "MaLoai": "Mã loại",
                "TenLoai": "Tên nhóm loại vật tư",
                "MoTa": "Mô tả chi tiết"
            })
        with col_l2:
            st.markdown("##### Thêm loại vật tư mới")
            with st.form("form_add_lvt", clear_on_submit=True):
                ma_loai = st.text_input("Mã loại (VD: LOAI04)").strip()
                ten_loai = st.text_input("Tên nhóm loại").strip()
                mo_ta_loai = st.text_area("Mô tả nhóm", height=80)
                btn_lvt = st.form_submit_button("Lưu loại vật tư", type="primary", use_container_width=True)
                if btn_lvt:
                    if not ma_loai or not ten_loai:
                        st.error("Vui lòng điền đủ Mã loại và Tên loại.")
                    else:
                        chk = execute_query("SELECT 1 FROM LOAI_VAT_TU WHERE MaLoai = ?", (ma_loai,))
                        if not chk.empty:
                            st.error(f"Mã loại '{ma_loai}' đã tồn tại trong hệ thống.")
                        else:
                            ok, msg = execute_non_query("INSERT INTO LOAI_VAT_TU (MaLoai, TenLoai, MoTa) VALUES (?, ?, ?)", (ma_loai, ten_loai, mo_ta_loai))
                            if ok:
                                st.success("Thêm loại vật tư thành công.")
                                st.rerun()
                            else:
                                st.error(f"Lỗi: {msg}")

    # ==============================================================
    # 3. QUẢN LÝ NHÀ CUNG CẤP
    # ==============================================================
    with tab_ncc:
        subtab_ncc1, subtab_ncc2 = st.tabs(["Danh sách nhà cung cấp", "Thêm nhà cung cấp"])
        
        with subtab_ncc1:
            df_ncc = execute_query("""
                SELECT MaNCC, TenNCC, DiaChi, SoDienThoai, Email,
                       CASE WHEN TrangThai = 1 THEN N'Đang hợp tác' ELSE N'Ngừng hợp tác' END AS TrangThaiHienThi,
                       TrangThai
                FROM NHA_CUNG_CAP
                ORDER BY MaNCC
            """)
            st.dataframe(df_ncc[["MaNCC", "TenNCC", "DiaChi", "SoDienThoai", "Email", "TrangThaiHienThi"]], use_container_width=True, hide_index=True, column_config={
                "MaNCC": "Mã NCC",
                "TenNCC": "Tên nhà cung cấp",
                "DiaChi": "Địa chỉ",
                "SoDienThoai": "Số điện thoại",
                "Email": "Email liên hệ",
                "TrangThaiHienThi": "Trạng thái hợp tác"
            })
            
            st.write("---")
            st.markdown("##### Thay đổi trạng thái hợp tác")
            col_ncc_s, col_ncc_b = st.columns([3, 1.2])
            with col_ncc_s:
                ncc_opts = {f"{r['MaNCC']} - {r['TenNCC']} ({r['TrangThaiHienThi']})": r for _, r in df_ncc.iterrows()}
                sel_ncc_lbl = st.selectbox("Chọn nhà cung cấp", list(ncc_opts.keys()))
                sel_ncc = ncc_opts[sel_ncc_lbl]
            with col_ncc_b:
                st.write("")
                st.write("")
                next_tt = 0 if sel_ncc["TrangThai"] == 1 else 1
                txt = "Ngừng hợp tác" if sel_ncc["TrangThai"] == 1 else "Tái hợp tác"
                if st.button(txt, key="btn_ncc_toggle", use_container_width=True):
                    ok, msg = execute_non_query("UPDATE NHA_CUNG_CAP SET TrangThai = ? WHERE MaNCC = ?", (next_tt, sel_ncc["MaNCC"]))
                    if ok:
                        st.success(f"Đã cập nhật trạng thái NCC {sel_ncc['MaNCC']}.")
                        st.rerun()
                    else:
                        st.error(f"Lỗi: {msg}")

        with subtab_ncc2:
            st.markdown("##### Khởi tạo thông tin nhà cung cấp")
            with st.form("form_add_ncc", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    next_mancc = get_next_id("NHA_CUNG_CAP", "MaNCC", "NCC")
                    ma_ncc = st.text_input("Mã nhà cung cấp", value=next_mancc).strip()
                    ten_ncc = st.text_input("Tên đơn vị cung ứng").strip()
                    dia_chi = st.text_input("Địa chỉ trụ sở / chi nhánh").strip()
                with col2:
                    sdt = st.text_input("Số điện thoại liên hệ").strip()
                    email = st.text_input("Hộp thư điện tử (Email)").strip()
                
                btn_ncc = st.form_submit_button("Lưu nhà cung cấp", type="primary", use_container_width=True)
                if btn_ncc:
                    if not ma_ncc or not ten_ncc:
                        st.error("Vui lòng điền đủ Mã và Tên nhà cung cấp.")
                    else:
                        chk = execute_query("SELECT 1 FROM NHA_CUNG_CAP WHERE MaNCC = ?", (ma_ncc,))
                        if not chk.empty:
                            st.error(f"Mã NCC '{ma_ncc}' đã tồn tại trong hệ thống.")
                        else:
                            sql_ins = "INSERT INTO NHA_CUNG_CAP (MaNCC, TenNCC, DiaChi, SoDienThoai, Email, TrangThai) VALUES (?, ?, ?, ?, ?, 1)"
                            ok, msg = execute_non_query(sql_ins, (ma_ncc, ten_ncc, dia_chi, sdt, email))
                            if ok:
                                st.success(f"Thêm nhà cung cấp '{ten_ncc}' thành công.")
                                st.rerun()
                            else:
                                st.error(f"Lỗi: {msg}")

    # ==============================================================
    # 4. QUẢN LÝ KHO LƯU TRỮ
    # ==============================================================
    with tab_kho:
        subtab_k1, subtab_k2 = st.tabs(["Danh sách kho", "Thêm kho mới"])
        with subtab_k1:
            df_kho = execute_query("""
                SELECT MaKho, TenKho, DiaChi, MoTa,
                       CASE WHEN TrangThai = 1 THEN N'Đang hoạt động' ELSE N'Ngừng hoạt động' END AS TrangThaiHienThi,
                       TrangThai
                FROM KHO
                ORDER BY MaKho
            """)
            st.dataframe(df_kho[["MaKho", "TenKho", "DiaChi", "MoTa", "TrangThaiHienThi"]], use_container_width=True, hide_index=True, column_config={
                "MaKho": "Mã kho",
                "TenKho": "Tên kho lưu trữ",
                "DiaChi": "Địa điểm kho bãi",
                "MoTa": "Ghi chú thủ kho",
                "TrangThaiHienThi": "Trạng thái vận hành"
            })
            
            st.write("---")
            st.markdown("##### Thay đổi trạng thái vận hành kho")
            col_ks, col_kb = st.columns([3, 1.2])
            with col_ks:
                kho_opts = {f"{r['MaKho']} - {r['TenKho']} ({r['TrangThaiHienThi']})": r for _, r in df_kho.iterrows()}
                sel_k_lbl = st.selectbox("Chọn kho lưu trữ", list(kho_opts.keys()))
                sel_k = kho_opts[sel_k_lbl]
            with col_kb:
                st.write("")
                st.write("")
                next_tt = 0 if sel_k["TrangThai"] == 1 else 1
                txt = "Ngừng hoạt động" if sel_k["TrangThai"] == 1 else "Kích hoạt lại"
                if st.button(txt, key="btn_kho_toggle", use_container_width=True):
                    ok, msg = execute_non_query("UPDATE KHO SET TrangThai = ? WHERE MaKho = ?", (next_tt, sel_k["MaKho"]))
                    if ok:
                        st.success(f"Cập nhật trạng thái Kho {sel_k['MaKho']} thành công.")
                        st.rerun()
                    else:
                        st.error(f"Lỗi: {msg}")

        with subtab_k2:
            st.markdown("##### Khởi tạo kho lưu trữ mới")
            with st.form("form_add_kho", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    next_makho = get_next_id("KHO", "MaKho", "KHO")
                    ma_kho = st.text_input("Mã kho", value=next_makho).strip()
                    ten_kho = st.text_input("Tên kho lưu trữ").strip()
                with col2:
                    dia_chi_kho = st.text_input("Địa chỉ kho bãi").strip()
                    mo_ta_kho = st.text_input("Mô tả quản lý / Thủ kho").strip()
                
                btn_kho = st.form_submit_button("Lưu kho", type="primary", use_container_width=True)
                if btn_kho:
                    if not ma_kho or not ten_kho:
                        st.error("Vui lòng điền đủ Mã kho và Tên kho.")
                    else:
                        chk = execute_query("SELECT 1 FROM KHO WHERE MaKho = ?", (ma_kho,))
                        if not chk.empty:
                            st.error(f"Mã kho '{ma_kho}' đã tồn tại trong hệ thống.")
                        else:
                            ok, msg = execute_non_query("INSERT INTO KHO (MaKho, TenKho, DiaChi, MoTa, TrangThai) VALUES (?, ?, ?, ?, 1)", (ma_kho, ten_kho, dia_chi_kho, mo_ta_kho))
                            if ok:
                                st.success(f"Thêm kho '{ten_kho}' thành công.")
                                st.rerun()
                            else:
                                st.error(f"Lỗi: {msg}")

    # ==============================================================
    # 5. QUẢN LÝ CÔNG TRÌNH
    # ==============================================================
    with tab_ct:
        subtab_ct1, subtab_ct2 = st.tabs(["Danh sách công trình", "Thêm công trình"])
        
        status_map = {
            "CHUA_BAT_DAU": "Chưa bắt đầu",
            "DANG_THI_CONG": "Đang thi công",
            "TAM_DUNG": "Tạm dừng",
            "HOAN_THANH": "Đã hoàn thành"
        }
        
        with subtab_ct1:
            df_ct = execute_query("SELECT MaCT, TenCT, DiaDiem, NgayBatDau, NgayKetThucDuKien, TrangThai FROM CONG_TRINH ORDER BY MaCT")
            df_ct["TrangThaiHienThi"] = df_ct["TrangThai"].map(lambda x: status_map.get(x, x))
            st.dataframe(df_ct[["MaCT", "TenCT", "DiaDiem", "NgayBatDau", "NgayKetThucDuKien", "TrangThaiHienThi"]], use_container_width=True, hide_index=True, column_config={
                "MaCT": "Mã công trình",
                "TenCT": "Tên dự án / Công trình",
                "DiaDiem": "Địa điểm thi công",
                "NgayBatDau": st.column_config.DateColumn("Ngày bắt đầu"),
                "NgayKetThucDuKien": st.column_config.DateColumn("Ngày dự kiến hoàn thành"),
                "TrangThaiHienThi": "Tiến độ thi công"
            })
            
            st.write("---")
            st.markdown("##### Cập nhật tiến độ dự án")
            col_cts, col_stt, col_btn = st.columns([2, 1.5, 1])
            with col_cts:
                ct_opts = {f"{r['MaCT']} - {r['TenCT']} ({r['TrangThaiHienThi']})": r for _, r in df_ct.iterrows()}
                sel_ct_lbl = st.selectbox("Chọn công trình", list(ct_opts.keys()))
                sel_ct = ct_opts[sel_ct_lbl]
            with col_stt:
                rev_map = {v: k for k, v in status_map.items()}
                curr_vn = status_map.get(sel_ct["TrangThai"], "Đang thi công")
                new_stt_vn = st.selectbox("Tiến độ mới", list(status_map.values()), index=list(status_map.values()).index(curr_vn))
            with col_btn:
                st.write("")
                st.write("")
                if st.button("Cập nhật tiến độ", type="primary", use_container_width=True):
                    new_code = rev_map[new_stt_vn]
                    ok, msg = execute_non_query("UPDATE CONG_TRINH SET TrangThai = ? WHERE MaCT = ?", (new_code, sel_ct["MaCT"]))
                    if ok:
                        st.success(f"Cập nhật tiến độ công trình {sel_ct['MaCT']} thành công.")
                        st.rerun()
                    else:
                        st.error(f"Lỗi: {msg}")

        with subtab_ct2:
            st.markdown("##### Khởi tạo công trình mới")
            with st.form("form_add_ct", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    next_mact = get_next_id("CONG_TRINH", "MaCT", "CT")
                    ma_ct = st.text_input("Mã công trình", value=next_mact).strip()
                    ten_ct = st.text_input("Tên công trình").strip()
                    dia_diem = st.text_input("Địa điểm thi công").strip()
                with col2:
                    ngay_bd = st.date_input("Ngày bắt đầu", value=date.today())
                    ngay_kt = st.date_input("Ngày dự kiến kết thúc", value=date.today())
                    stt_val = st.selectbox("Tiến độ ban đầu", list(status_map.keys()), format_func=lambda x: status_map[x])
                
                btn_ct = st.form_submit_button("Lưu công trình", type="primary", use_container_width=True)
                if btn_ct:
                    if not ma_ct or not ten_ct or not dia_diem:
                        st.error("Vui lòng nhập đầy đủ Mã, Tên và Địa điểm công trình.")
                    elif ngay_kt < ngay_bd:
                        st.error("Ngày kết thúc dự kiến không thể nhỏ hơn Ngày bắt đầu.")
                    else:
                        chk = execute_query("SELECT 1 FROM CONG_TRINH WHERE MaCT = ?", (ma_ct,))
                        if not chk.empty:
                            st.error(f"Mã công trình '{ma_ct}' đã tồn tại trong hệ thống.")
                        else:
                            sql_ins = "INSERT INTO CONG_TRINH (MaCT, TenCT, DiaDiem, NgayBatDau, NgayKetThucDuKien, TrangThai) VALUES (?, ?, ?, ?, ?, ?)"
                            ok, msg = execute_non_query(sql_ins, (ma_ct, ten_ct, dia_diem, ngay_bd, ngay_kt, stt_val))
                            if ok:
                                st.success(f"Thêm công trình '{ten_ct}' thành công.")
                                st.rerun()
                            else:
                                st.error(f"Lỗi: {msg}")
