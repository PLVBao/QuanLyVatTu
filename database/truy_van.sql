use QuanLyVatTuXayDung;
go

-- 1. Cảnh báo vật tư dưới mức tồn tối thiểu
select 
    k.MaKho,
    k.TenKho,
    vt.MaVT,
    vt.TenVT,
    vt.DonViTinh,
    tk.SoLuongTon,
    vt.TonToiThieu,
    (vt.TonToiThieu - tk.SoLuongTon) as SoLuongCanNhapThem
from TON_KHO tk
join VAT_TU vt on tk.MaVT = vt.MaVT
join KHO k on tk.MaKho = k.MaKho
where tk.SoLuongTon < vt.TonToiThieu;
go

-- 2. Tra cứu tồn kho chi tiết theo từng kho và loại vật tư
select 
    k.MaKho,
    k.TenKho,
    lvt.TenLoai,
    vt.MaVT,
    vt.TenVT,
    vt.DonViTinh,
    tk.SoLuongTon
from TON_KHO tk
join VAT_TU vt on tk.MaVT = vt.MaVT
join LOAI_VAT_TU lvt on vt.MaLoai = lvt.MaLoai
join KHO k on tk.MaKho = k.MaKho
order by k.MaKho, lvt.TenLoai;
go

-- 3. Lịch sử xuất cấp vật tư cho các công trình
select 
    ct.MaCT,
    ct.TenCT,
    px.MaPX,
    px.NgayXuat,
    k.TenKho as KhoXuat,
    vt.TenVT,
    ctx.SoLuong,
    vt.DonViTinh,
    tk.HoTen as NguoiLapPhieu
from PHIEU_XUAT px
join CT_PHIEU_XUAT ctx on px.MaPX = ctx.MaPX
join CONG_TRINH ct on px.MaCT = ct.MaCT
join KHO k on px.MaKho = k.MaKho
join VAT_TU vt on ctx.MaVT = vt.MaVT
join TAI_KHOAN tk on px.NguoiLap = tk.MaTK
order by px.NgayXuat desc;
go

-- 4. View tổng hợp Nhập - Xuất - Tồn
create or alter view vw_TongHopNhapXuatTon
as
select 
    vt.MaVT,
    vt.TenVT,
    vt.DonViTinh,
    coalesce(sum(tk.SoLuongTon), 0) as TongTonHienTai,
    coalesce((select sum(ctn.SoLuong) 
              from CT_PHIEU_NHAP ctn 
              join PHIEU_NHAP pn on ctn.MaPN = pn.MaPN 
              where ctn.MaVT = vt.MaVT and pn.TrangThai = 'HOAN_THANH'), 0) as TongDaNhap,
    coalesce((select sum(ctx.SoLuong) 
              from CT_PHIEU_XUAT ctx 
              join PHIEU_XUAT px on ctx.MaPX = px.MaPX 
              where ctx.MaVT = vt.MaVT and px.TrangThai = 'HOAN_THANH'), 0) as TongDaXuat
from VAT_TU vt
left join TON_KHO tk on vt.MaVT = tk.MaVT
group by vt.MaVT, vt.TenVT, vt.DonViTinh;
go

-- 5. Báo cáo đối chiếu Tồn kho thực tế và Lịch sử Nhập/Xuất
SELECT 
    MaVT,
    TenVT,
    DonViTinh,
    TongDaNhap,
    TongDaXuat,
    (TongDaNhap - TongDaXuat) AS TonLyThuyet,
    TongTonHienTai AS TonThucTe,
    (TongTonHienTai - (TongDaNhap - TongDaXuat)) AS DoChenhLechDieuChinh
FROM 
    vw_TongHopNhapXuatTon
WHERE 
    TongTonHienTai <> (TongDaNhap - TongDaXuat);
GO
    
-- 6. Báo cáo Tổng giá trị tồn kho ước tính theo giá nhập gần nhất
SELECT 
    v.MaVT,
    v.TenVT,
    v.TongTonHienTai,
    (SELECT TOP 1 DonGia FROM CT_PHIEU_NHAP ctn JOIN PHIEU_NHAP pn ON ctn.MaPN = pn.MaPN WHERE ctn.MaVT = v.MaVT ORDER BY pn.NgayNhap DESC) AS GiaNhapGanNhat,
    (v.TongTonHienTai * (SELECT TOP 1 DonGia FROM CT_PHIEU_NHAP ctn JOIN PHIEU_NHAP pn ON ctn.MaPN = pn.MaPN WHERE ctn.MaVT = v.MaVT ORDER BY pn.NgayNhap DESC)) AS TongGiaTriUocTinh
FROM 
    vw_TongHopNhapXuatTon v
WHERE 
    v.TongTonHienTai > 0;
GO
