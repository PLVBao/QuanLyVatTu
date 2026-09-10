import streamlit as st
import pandas as pd
from database import execute_query
from src.utils import format_quantity, apply_quantity_format

def render_queries_reports_ui():
    """Giao diện Tra cứu, Báo cáo & Cảnh báo tồn kho chuẩn Enterprise ERP."""
    st.title("Báo cáo & Cảnh báo tồn")
    st.caption("Tổng hợp thông tin tồn kho thời gian thực, phân tích lịch sử giao dịch và đối chiếu Nhập - Xuất - Tồn")

    focus_alert = st.session_state.pop("report_focus_alert", False)
    if focus_alert:
        tab_canhbao, tab_tontuc, tab_history, tab_baocao = st.tabs([
            "Cảnh báo tồn tối thiểu",
            "Tra cứu tồn kho",
            "Lịch sử giao dịch",
            "Báo cáo Nhập - Xuất - Tồn"
        ])
    else:
        tab_tontuc, tab_canhbao, tab_history, tab_baocao = st.tabs([
            "Tra cứu tồn kho",
            "Cảnh báo tồn tối thiểu",
            "Lịch sử giao dịch",
            "Báo cáo Nhập - Xuất - Tồn"
        ])

    # ==============================================================
    # 1. TRA CỨU TỒN KHO THỜI GIAN THỰC
    # ==============================================================
    with tab_tontuc:
        st.markdown("##### Tra cứu số dư tồn kho theo kho lưu trữ và phân loại")
        
        col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 2])
        df_kho_filter = execute_query("SELECT MaKho, TenKho FROM KHO")
        df_loai_filter = execute_query("SELECT MaLoai, TenLoai FROM LOAI_VAT_TU")

        with col_f1:
            kho_list = ["Tất cả kho"] + [f"{r['MaKho']} - {r['TenKho']}" for _, r in df_kho_filter.iterrows()]
            sel_kho_filter = st.selectbox("Lọc theo Kho lưu trữ", kho_list)
        with col_f2:
            loai_list = ["Tất cả loại"] + [f"{r['MaLoai']} - {r['TenLoai']}" for _, r in df_loai_filter.iterrows()]
            sel_loai_filter = st.selectbox("Lọc theo Phân loại vật tư", loai_list)
        with col_f3:
            kw = st.text_input("Tìm kiếm theo Mã hoặc Tên vật tư", placeholder="Nhập từ khóa tìm kiếm...").strip()

        sql = """
        SELECT 
            k.MaKho,
            k.TenKho,
            lvt.TenLoai,
            vt.MaVT,
            vt.TenVT,
            vt.DonViTinh,
            tk.SoLuongTon,
            vt.TonToiThieu,
            CASE 
                WHEN tk.SoLuongTon <= 0 THEN N'Hết hàng'
                WHEN tk.SoLuongTon <= vt.TonToiThieu THEN N'Dưới mức tối thiểu'
                ELSE N'Đủ tồn kho'
            END AS TinhTrang
        FROM TON_KHO tk
        JOIN VAT_TU vt ON tk.MaVT = vt.MaVT
        JOIN LOAI_VAT_TU lvt ON vt.MaLoai = lvt.MaLoai
        JOIN KHO k ON tk.MaKho = k.MaKho
        WHERE 1=1
        """
        params = []
        if sel_kho_filter != "Tất cả kho":
            makho = sel_kho_filter.split(" - ")[0]
            sql += " AND k.MaKho = ?"
            params.append(makho)
        if sel_loai_filter != "Tất cả loại":
            maloai = sel_loai_filter.split(" - ")[0]
            sql += " AND lvt.MaLoai = ?"
            params.append(maloai)
        if kw:
            sql += " AND (vt.MaVT LIKE ? OR vt.TenVT LIKE ?)"
            params.extend([f"%{kw}%", f"%{kw}%"])

        sql += " ORDER BY k.MaKho, lvt.TenLoai, vt.MaVT"
        df_ton = execute_query(sql, tuple(params) if params else None)

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Tổng số dòng tồn kho", f"{len(df_ton):,}")
        with col_m2:
            alert_sub = len(df_ton[df_ton["TinhTrang"] != "Đủ tồn kho"])
            st.metric("Mặt hàng cần lưu ý", f"{alert_sub:,}")
        with col_m3:
            st.metric("Kho kiểm tra", sel_kho_filter if sel_kho_filter != "Tất cả kho" else "Toàn bộ hệ thống")

        df_ton_disp = apply_quantity_format(df_ton, ["SoLuongTon", "TonToiThieu"])
        st.dataframe(
            df_ton_disp,
            use_container_width=True,
            hide_index=True,
            column_config={
                "MaKho": "Mã kho",
                "TenKho": "Tên kho",
                "TenLoai": "Phân loại",
                "MaVT": "Mã vật tư",
                "TenVT": "Tên vật tư",
                "DonViTinh": "ĐVT",
                "SoLuongTon": "Số lượng tồn",
                "TonToiThieu": "Tồn tối thiểu",
                "TinhTrang": "Tình trạng định mức"
            }
        )

    # ==============================================================
    # 2. CẢNH BÁO TỒN TỐI THIỂU
    # ==============================================================
    with tab_canhbao:
        st.markdown("##### Cảnh báo mặt hàng dưới mức tồn kho tối thiểu")
        st.caption("Truy vấn các mặt hàng có SoLuongTon <= TonToiThieu phục vụ lập kế hoạch mua sắm và cung ứng")

        sql_cb = """
        SELECT 
            k.MaKho,
            k.TenKho,
            vt.MaVT,
            vt.TenVT,
            vt.DonViTinh,
            tk.SoLuongTon,
            vt.TonToiThieu,
            (vt.TonToiThieu - tk.SoLuongTon) AS SoLuongCanNhapThem
        FROM TON_KHO tk
        JOIN VAT_TU vt ON tk.MaVT = vt.MaVT
        JOIN KHO k ON tk.MaKho = k.MaKho
        WHERE tk.SoLuongTon <= vt.TonToiThieu
        ORDER BY SoLuongCanNhapThem DESC
        """
        df_cb = execute_query(sql_cb)

        if df_cb.empty:
            st.success("Tất cả các mặt hàng tại các kho hiện đều đạt mức tồn an toàn (lớn hơn định mức tối thiểu).")
        else:
            st.error(f"Cảnh báo: Phát hiện {len(df_cb)} mặt hàng đang dưới mức tồn kho tối thiểu. Cần lập kế hoạch bổ sung hàng.")
            
            df_cb_disp = apply_quantity_format(df_cb, ["SoLuongTon", "TonToiThieu", "SoLuongCanNhapThem"])
            st.dataframe(
                df_cb_disp,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "MaKho": "Mã kho",
                    "TenKho": "Tên kho",
                    "MaVT": "Mã vật tư",
                    "TenVT": "Tên vật tư",
                    "DonViTinh": "Đơn vị tính",
                    "SoLuongTon": "Tồn thực tế hiện có",
                    "TonToiThieu": "Định mức tối thiểu",
                    "SoLuongCanNhapThem": "Lượng cần bổ sung"
                }
            )

    # ==============================================================
    # 3. XEM LỊCH SỬ GIAO DỊCH
    # ==============================================================
    with tab_history:
        st.markdown("##### Nhật ký giao dịch chứng từ kho")
        
        htab_nhap, htab_xuat, htab_chuyen, htab_dc = st.tabs([
            "Phiếu nhập kho",
            "Phiếu xuất kho",
            "Phiếu chuyển kho",
            "Phiếu điều chỉnh"
        ])

        with htab_nhap:
            sql_pn = """
            SELECT 
                pn.MaPN,
                pn.NgayNhap,
                ncc.TenNCC,
                k.TenKho AS KhoNhap,
                vt.TenVT,
                ctn.SoLuong,
                vt.DonViTinh,
                ctn.DonGia,
                (ctn.SoLuong * ctn.DonGia) AS ThanhTien,
                tk.HoTen AS NguoiLapPhieu,
                pn.GhiChu,
                pn.TrangThai
            FROM PHIEU_NHAP pn
            JOIN CT_PHIEU_NHAP ctn ON pn.MaPN = ctn.MaPN
            JOIN NHA_CUNG_CAP ncc ON pn.MaNCC = ncc.MaNCC
            JOIN KHO k ON pn.MaKho = k.MaKho
            JOIN VAT_TU vt ON ctn.MaVT = vt.MaVT
            JOIN TAI_KHOAN tk ON pn.NguoiLap = tk.MaTK
            ORDER BY pn.NgayNhap DESC
            """
            df_pn = execute_query(sql_pn)
            df_pn_disp = apply_quantity_format(df_pn, ["SoLuong"])
            st.dataframe(df_pn_disp, use_container_width=True, hide_index=True, column_config={
                "MaPN": "Mã phiếu",
                "NgayNhap": st.column_config.DatetimeColumn("Thời gian", format="DD/MM/YYYY HH:mm"),
                "TenNCC": "Nhà cung cấp",
                "KhoNhap": "Kho nhập",
                "TenVT": "Vật tư",
                "SoLuong": "Số lượng",
                "DonGia": st.column_config.NumberColumn("Đơn giá (VNĐ)", format="%,.0f"),
                "ThanhTien": st.column_config.NumberColumn("Thành tiền (VNĐ)", format="%,.0f"),
                "NguoiLapPhieu": "Người lập",
                "TrangThai": "Trạng thái"
            })

        with htab_xuat:
            sql_px = """
            SELECT 
                px.MaPX,
                px.NgayXuat,
                k.TenKho AS KhoXuat,
                ct.TenCT AS CongTrinhNhan,
                vt.TenVT,
                ctx.SoLuong,
                vt.DonViTinh,
                tk.HoTen AS NguoiLapPhieu,
                px.GhiChu,
                px.TrangThai
            FROM PHIEU_XUAT px
            JOIN CT_PHIEU_XUAT ctx ON px.MaPX = ctx.MaPX
            JOIN CONG_TRINH ct ON px.MaCT = ct.MaCT
            JOIN KHO k ON px.MaKho = k.MaKho
            JOIN VAT_TU vt ON ctx.MaVT = vt.MaVT
            JOIN TAI_KHOAN tk ON px.NguoiLap = tk.MaTK
            ORDER BY px.NgayXuat DESC
            """
            df_px = execute_query(sql_px)
            df_px_disp = apply_quantity_format(df_px, ["SoLuong"])
            st.dataframe(df_px_disp, use_container_width=True, hide_index=True, column_config={
                "MaPX": "Mã phiếu",
                "NgayXuat": st.column_config.DatetimeColumn("Thời gian", format="DD/MM/YYYY HH:mm"),
                "KhoXuat": "Kho xuất",
                "CongTrinhNhan": "Công trình nhận",
                "TenVT": "Vật tư",
                "SoLuong": "Số lượng",
                "NguoiLapPhieu": "Người lập",
                "TrangThai": "Trạng thái"
            })

        with htab_chuyen:
            sql_pck = """
            SELECT 
                pck.MaPCK,
                pck.NgayChuyen,
                kn.TenKho AS KhoNguon,
                kd.TenKho AS KhoDich,
                vt.TenVT,
                ctc.SoLuong,
                vt.DonViTinh,
                tk.HoTen AS NguoiLapPhieu,
                pck.TrangThai
            FROM PHIEU_CHUYEN_KHO pck
            JOIN CT_CHUYEN_KHO ctc ON pck.MaPCK = ctc.MaPCK
            JOIN KHO kn ON pck.MaKhoNguon = kn.MaKho
            JOIN KHO kd ON pck.MaKhoDich = kd.MaKho
            JOIN VAT_TU vt ON ctc.MaVT = vt.MaVT
            JOIN TAI_KHOAN tk ON pck.NguoiLap = tk.MaTK
            ORDER BY pck.NgayChuyen DESC
            """
            df_pck = execute_query(sql_pck)
            df_pck_disp = apply_quantity_format(df_pck, ["SoLuong"])
            st.dataframe(df_pck_disp, use_container_width=True, hide_index=True, column_config={
                "MaPCK": "Mã phiếu",
                "NgayChuyen": st.column_config.DatetimeColumn("Thời gian", format="DD/MM/YYYY HH:mm"),
                "KhoNguon": "Kho nguồn",
                "KhoDich": "Kho đích",
                "TenVT": "Vật tư",
                "SoLuong": "Số lượng",
                "NguoiLapPhieu": "Người lập",
                "TrangThai": "Trạng thái"
            })

        with htab_dc:
            sql_pdc = """
            SELECT 
                pdc.MaPDC,
                pdc.NgayDieuChinh,
                k.TenKho,
                vt.TenVT,
                vt.DonViTinh,
                ctd.SoLuongTruoc,
                ctd.SoLuongSau,
                (ctd.SoLuongSau - ctd.SoLuongTruoc) AS ChenhLech,
                pdc.LyDo,
                tk.HoTen AS NguoiLapPhieu,
                pdc.TrangThai
            FROM PHIEU_DIEU_CHINH pdc
            JOIN CT_DIEU_CHINH ctd ON pdc.MaPDC = ctd.MaPDC
            JOIN KHO k ON pdc.MaKho = k.MaKho
            JOIN VAT_TU vt ON ctd.MaVT = vt.MaVT
            JOIN TAI_KHOAN tk ON pdc.NguoiLap = tk.MaTK
            ORDER BY pdc.NgayDieuChinh DESC
            """
            df_pdc = execute_query(sql_pdc)
            df_pdc_disp = apply_quantity_format(df_pdc, ["SoLuongTruoc", "SoLuongSau"])
            df_pdc_disp["ChenhLech"] = df_pdc["ChenhLech"].apply(lambda x: format_quantity(x, show_plus=True))
            st.dataframe(df_pdc_disp, use_container_width=True, hide_index=True, column_config={
                "MaPDC": "Mã phiếu",
                "NgayDieuChinh": st.column_config.DatetimeColumn("Thời gian", format="DD/MM/YYYY HH:mm"),
                "TenKho": "Kho kiểm kê",
                "TenVT": "Vật tư",
                "SoLuongTruoc": "Số lượng trước",
                "SoLuongSau": "Số lượng sau",
                "ChenhLech": "Chênh lệch",
                "LyDo": "Lý do điều chỉnh",
                "NguoiLapPhieu": "Người lập"
            })

    # ==============================================================
    # 4. BÁO CÁO NHẬP - XUẤT - TỒN
    # ==============================================================
    with tab_baocao:
        st.markdown("##### Tổng hợp số liệu Nhập - Xuất - Tồn toàn hệ thống")
        st.caption("Dữ liệu trích xuất từ khung nhìn vw_TongHopNhapXuatTon")

        df_nxt = execute_query("SELECT MaVT, TenVT, DonViTinh, TongTonHienTai, TongDaNhap, TongDaXuat FROM vw_TongHopNhapXuatTon")
        
        col_c1, col_c2 = st.columns([1.5, 1])
        with col_c1:
            df_nxt_disp = apply_quantity_format(df_nxt, ["TongDaNhap", "TongDaXuat", "TongTonHienTai"])
            st.dataframe(
                df_nxt_disp,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "MaVT": "Mã vật tư",
                    "TenVT": "Tên vật tư",
                    "DonViTinh": "ĐVT",
                    "TongDaNhap": "Tổng nhập",
                    "TongDaXuat": "Tổng xuất",
                    "TongTonHienTai": "Tồn hiện tại"
                }
            )
        with col_c2:
            st.markdown("<div style='font-size: 14px; font-weight: 600; margin-bottom: 8px;'>Biểu đồ tồn kho thực tế theo mặt hàng</div>", unsafe_allow_html=True)
            if not df_nxt.empty:
                chart_df = df_nxt.set_index("TenVT")[["TongTonHienTai"]]
                st.bar_chart(chart_df, color="#1E3A8A")

        st.write("---")
        st.markdown("##### Đối chiếu Tồn kho Thực tế & Lý thuyết")
        sql_chenhlech = """
        SELECT 
            MaVT,
            TenVT,
            DonViTinh,
            TongDaNhap,
            TongDaXuat,
            (TongDaNhap - TongDaXuat) AS TonLyThuyet,
            TongTonHienTai AS TonThucTe,
            (TongTonHienTai - (TongDaNhap - TongDaXuat)) AS DoChenhLechDieuChinh
        FROM vw_TongHopNhapXuatTon
        WHERE TongTonHienTai <> (TongDaNhap - TongDaXuat)
        """
        df_chenhlech = execute_query(sql_chenhlech)
        if df_chenhlech.empty:
            st.info("Không có sai lệch giữa Tồn lý thuyết (Nhập trừ Xuất) và Tồn thực tế tại kho.")
        else:
            df_chenhlech_disp = apply_quantity_format(df_chenhlech, ["TonLyThuyet", "TonThucTe"])
            df_chenhlech_disp["DoChenhLechDieuChinh"] = df_chenhlech["DoChenhLechDieuChinh"].apply(lambda x: format_quantity(x, show_plus=True))
            st.dataframe(
                df_chenhlech_disp,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "MaVT": "Mã vật tư",
                    "TenVT": "Tên vật tư",
                    "DonViTinh": "ĐVT",
                    "TonLyThuyet": "Tồn lý thuyết",
                    "TonThucTe": "Tồn thực tế",
                    "DoChenhLechDieuChinh": "Chênh lệch kiểm kê"
                }
            )

        st.write("---")
        st.markdown("##### Định giá tổng tài sản tồn kho (Theo đơn giá nhập gần nhất)")
        sql_giatri = """
        SELECT 
            v.MaVT,
            v.TenVT,
            v.DonViTinh,
            v.TongTonHienTai,
            (SELECT TOP 1 DonGia FROM CT_PHIEU_NHAP ctn JOIN PHIEU_NHAP pn ON ctn.MaPN = pn.MaPN WHERE ctn.MaVT = v.MaVT ORDER BY pn.NgayNhap DESC) AS GiaNhapGanNhat,
            (v.TongTonHienTai * (SELECT TOP 1 DonGia FROM CT_PHIEU_NHAP ctn JOIN PHIEU_NHAP pn ON ctn.MaPN = pn.MaPN WHERE ctn.MaVT = v.MaVT ORDER BY pn.NgayNhap DESC)) AS TongGiaTriUocTinh
        FROM 
            vw_TongHopNhapXuatTon v
        WHERE 
            v.TongTonHienTai > 0
        """
        df_giatri = execute_query(sql_giatri)
        if not df_giatri.empty:
            tong_tien = df_giatri["TongGiaTriUocTinh"].sum()
            st.metric("Tổng giá trị tài sản vật tư lưu kho", f"{tong_tien:,.0f} VNĐ")
            df_giatri_disp = apply_quantity_format(df_giatri, ["TongTonHienTai"])
            st.dataframe(
                df_giatri_disp,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "MaVT": "Mã vật tư",
                    "TenVT": "Tên vật tư",
                    "TongTonHienTai": "Số lượng tồn",
                    "GiaNhapGanNhat": st.column_config.NumberColumn("Giá nhập gần nhất (VNĐ)", format="%,.0f"),
                    "TongGiaTriUocTinh": st.column_config.NumberColumn("Tổng giá trị ước tính (VNĐ)", format="%,.0f")
                }
            )
