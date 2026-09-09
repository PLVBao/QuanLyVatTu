USE QuanLyVatTuXayDung;
GO

-- 1. Xóa sạch dữ liệu giao dịch phát sinh khi test demo
DELETE FROM CT_PHIEU_NHAP;
DELETE FROM PHIEU_NHAP;
DELETE FROM CT_PHIEU_XUAT;
DELETE FROM PHIEU_XUAT;
DELETE FROM CT_CHUYEN_KHO;
DELETE FROM PHIEU_CHUYEN_KHO;
DELETE FROM CT_DIEU_CHINH;
DELETE FROM PHIEU_DIEU_CHINH;
DELETE FROM TON_KHO;

-- 2. Nạp lại các phiếu mẫu chuẩn ban đầu
-- Phiếu nhập 1
INSERT INTO PHIEU_NHAP (MaPN, MaNCC, MaKho, NgayNhap, NguoiLap, GhiChu, TrangThai)
VALUES ('PN01', 'NCC01', 'KHO01', '2026-07-01', 'TK02', N'Nhập thép đợt 1', 'HOAN_THANH');
INSERT INTO CT_PHIEU_NHAP (MaPN, MaVT, SoLuong, DonGia) VALUES ('PN01', 'VT01', 500, 150000);

-- Phiếu nhập 2
INSERT INTO PHIEU_NHAP (MaPN, MaNCC, MaKho, NgayNhap, NguoiLap, GhiChu, TrangThai)
VALUES ('PN02', 'NCC02', 'KHO01', '2026-07-02', 'TK02', N'Nhập xi măng đợt 1', 'HOAN_THANH');
INSERT INTO CT_PHIEU_NHAP (MaPN, MaVT, SoLuong, DonGia) VALUES ('PN02', 'VT02', 200, 90000);

-- Phiếu nhập 3
INSERT INTO PHIEU_NHAP (MaPN, MaNCC, MaKho, NgayNhap, NguoiLap, GhiChu, TrangThai)
VALUES ('PN03', 'NCC02', 'KHO02', '2026-07-03', 'TK02', N'Nhập cát và đá', 'HOAN_THANH');
INSERT INTO CT_PHIEU_NHAP (MaPN, MaVT, SoLuong, DonGia) 
VALUES ('PN03', 'VT03', 1000, 350000), ('PN03', 'VT04', 800, 450000);

-- Phiếu xuất 1
INSERT INTO PHIEU_XUAT (MaPX, MaKho, MaCT, NgayXuat, NguoiLap, GhiChu, TrangThai)
VALUES ('PX01', 'KHO01', 'CT01', '2026-07-05', 'TK02', N'Xuất thép cho công trình An Phú', 'HOAN_THANH');
INSERT INTO CT_PHIEU_XUAT (MaPX, MaVT, SoLuong) VALUES ('PX01', 'VT01', 20);

-- Phiếu chuyển kho 1
INSERT INTO PHIEU_CHUYEN_KHO (MaPCK, MaKhoNguon, MaKhoDich, NgayChuyen, NguoiLap, GhiChu, TrangThai)
VALUES ('PCK01', 'KHO01', 'KHO02', '2026-07-08', 'TK02', N'Chuyển thép sang kho phụ', 'HOAN_THANH');
INSERT INTO CT_CHUYEN_KHO (MaPCK, MaVT, SoLuong) VALUES ('PCK01', 'VT01', 10);

-- Phiếu điều chỉnh 1
INSERT INTO PHIEU_DIEU_CHINH (MaPDC, MaKho, NgayDieuChinh, NguoiLap, LyDo, TrangThai)
VALUES ('PDC01', 'KHO01', '2026-07-10', 'TK01', N'Kiểm kê thực tế thiếu 5 cây thép', 'HOAN_THANH');
INSERT INTO CT_DIEU_CHINH (MaPDC, MaVT, SoLuongTruoc, SoLuongSau) VALUES ('PDC01', 'VT01', 470, 465);

-- 3. Khôi phục số dư chuẩn xác vào bảng TON_KHO
INSERT INTO TON_KHO (MaKho, MaVT, SoLuongTon)
VALUES
    ('KHO01', 'VT01', 465),
    ('KHO01', 'VT02', 200),
    ('KHO02', 'VT01', 10),
    ('KHO02', 'VT03', 1000),
    ('KHO02', 'VT04', 800);

PRINT N'Đã Reset toàn diện Database về dữ liệu gốc chuẩn xác!';
GO
