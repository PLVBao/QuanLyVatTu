CREATE DATABASE QuanLyVatTuXayDung;
USE QuanLyVatTuXayDung;

-- 1. Bảng tài khoản
CREATE TABLE TAI_KHOAN
(
    MaTK VARCHAR(10) NOT NULL,
    TenDangNhap VARCHAR(50) NOT NULL,
    MatKhau VARCHAR(255) NOT NULL,
    HoTen NVARCHAR(100) NOT NULL,
    VaiTro NVARCHAR(30) NOT NULL,
    TrangThai BIT NOT NULL CONSTRAINT DF_TAIKHOAN_TT DEFAULT 1,

    CONSTRAINT PK_TAI_KHOAN PRIMARY KEY (MaTK),
    CONSTRAINT UQ_TAI_KHOAN_TENDANGNHAP UNIQUE (TenDangNhap)
);

-- 2. Bảng loại vật tư
CREATE TABLE LOAI_VAT_TU
(
    MaLoai VARCHAR(10) NOT NULL,
    TenLoai NVARCHAR(100) NOT NULL,
    MoTa NVARCHAR(255),

    CONSTRAINT PK_LOAI_VAT_TU PRIMARY KEY (MaLoai)
);

-- 3. Bảng vật tư
CREATE TABLE VAT_TU
(
    MaVT VARCHAR(10) NOT NULL,
    TenVT NVARCHAR(150) NOT NULL,
    MaLoai VARCHAR(10) NOT NULL,
    DonViTinh NVARCHAR(30) NOT NULL,
    TonToiThieu DECIMAL(18,2) NOT NULL,
    MoTa NVARCHAR(255),
    TrangThai BIT NOT NULL CONSTRAINT DF_VATTU_TT DEFAULT 1,

    CONSTRAINT PK_VAT_TU PRIMARY KEY (MaVT),

    CONSTRAINT FK_VAT_TU_LOAI
        FOREIGN KEY (MaLoai) REFERENCES LOAI_VAT_TU(MaLoai),

    CONSTRAINT CK_VAT_TU_TONTOITHIEU
            CHECK (TonToiThieu >= 0)
);

-- 4. Bảng nhà cung cấp
CREATE TABLE NHA_CUNG_CAP
(
    MaNCC VARCHAR(10) NOT NULL,
    TenNCC NVARCHAR(150) NOT NULL,
    DiaChi NVARCHAR(255),
    SoDienThoai VARCHAR(20),
    Email VARCHAR(100),
    TrangThai BIT NOT NULL CONSTRAINT DF_NCC_TT DEFAULT 1,

    CONSTRAINT PK_NHA_CUNG_CAP PRIMARY KEY (MaNCC),
);

-- 5. Bảng kho
CREATE TABLE KHO
(
    MaKho VARCHAR(10) NOT NULL,
    TenKho NVARCHAR(100) NOT NULL,
    DiaChi NVARCHAR(255),
    MoTa NVARCHAR(255),
    TrangThai BIT NOT NULL CONSTRAINT DF_KHO_TT DEFAULT 1,

    CONSTRAINT PK_KHO PRIMARY KEY (MaKho),
);

-- 6. Bảng công trình
CREATE TABLE CONG_TRINH
(
    MaCT VARCHAR(10) NOT NULL,
    TenCT NVARCHAR(150) NOT NULL,
    DiaDiem NVARCHAR(255) NOT NULL,
    NgayBatDau DATE,
    NgayKetThucDuKien DATE,
    TrangThai VARCHAR(30) NOT NULL CONSTRAINT DF_CT_TT  DEFAULT N'Dang thi cong',

    CONSTRAINT PK_CONG_TRINH PRIMARY KEY (MaCT),
);

-- 7. Bảng tồn kho
CREATE TABLE TON_KHO
(
    MaKho VARCHAR(10) NOT NULL,
    MaVT VARCHAR(10) NOT NULL,
    SoLuongTon DECIMAL(18,2) NOT NULL,

    CONSTRAINT PK_TON_KHO PRIMARY KEY (MaKho, MaVT),

    CONSTRAINT FK_TON_KHO_KHO
        FOREIGN KEY (MaKho) REFERENCES KHO(MaKho),

    CONSTRAINT FK_TON_KHO_VAT_TU
        FOREIGN KEY (MaVT) REFERENCES VAT_TU(MaVT),

    CONSTRAINT CK_TON_KHO_SOLUONG
        CHECK (SoLuongTon >= 0)
);

-- 8. Bảng phiếu nhập
CREATE TABLE PHIEU_NHAP
(
    MaPN VARCHAR(10) NOT NULL,
    MaNCC VARCHAR(10) NOT NULL,
    MaKho VARCHAR(10) NOT NULL,
    NgayNhap DATETIME NOT NULL CONSTRAINT DF_PN_NGAY  DEFAULT GETDATE(),
    NguoiLap VARCHAR(10) NOT NULL,
    GhiChu NVARCHAR(500),
    TrangThai VARCHAR(20) NOT NULL CONSTRAINT DF_PN_TT  DEFAULT N'Cho duyet',

    CONSTRAINT PK_PHIEU_NHAP PRIMARY KEY (MaPN),

    CONSTRAINT FK_PHIEU_NHAP_NCC
        FOREIGN KEY (MaNCC) REFERENCES NHA_CUNG_CAP(MaNCC),

    CONSTRAINT FK_PHIEU_NHAP_KHO
        FOREIGN KEY (MaKho) REFERENCES KHO(MaKho),

    CONSTRAINT FK_PHIEU_NHAP_TAI_KHOAN
        FOREIGN KEY (NguoiLap) REFERENCES TAI_KHOAN(MaTK)
);

-- 9. Bảng chi tiết phiếu nhập
CREATE TABLE CT_PHIEU_NHAP
(
    MaPN VARCHAR(10) NOT NULL,
    MaVT VARCHAR(10) NOT NULL,
    SoLuong DECIMAL(18,2) NOT NULL,
    DonGia DECIMAL(18,2) NOT NULL,

    CONSTRAINT PK_CT_PHIEU_NHAP PRIMARY KEY (MaPN, MaVT),

    CONSTRAINT FK_CT_NHAP_PHIEU_NHAP
        FOREIGN KEY (MaPN) REFERENCES PHIEU_NHAP(MaPN),

    CONSTRAINT FK_CT_NHAP_VAT_TU
        FOREIGN KEY (MaVT) REFERENCES VAT_TU(MaVT),

    CONSTRAINT CK_CT_NHAP_SOLUONG
        CHECK (SoLuong > 0),

    CONSTRAINT CK_CT_NHAP_DONGIA
        CHECK (DonGia > 0)
);

-- 10. Bảng phiếu xuất
CREATE TABLE PHIEU_XUAT
(
    MaPX VARCHAR(10) NOT NULL,
    MaKho VARCHAR(10) NOT NULL,
    MaCT VARCHAR(10) NOT NULL,
    NgayXuat DATETIME NOT NULL  CONSTRAINT DF_PX_NGAY  DEFAULT GETDATE(),
    NguoiLap VARCHAR(10) NOT NULL,
    GhiChu NVARCHAR(500),
    TrangThai VARCHAR(20) NOT NULL CONSTRAINT DF_PX_TT  DEFAULT N'Cho duyet',

    CONSTRAINT PK_PHIEU_XUAT PRIMARY KEY (MaPX),

    CONSTRAINT FK_PHIEU_XUAT_KHO
        FOREIGN KEY (MaKho) REFERENCES KHO(MaKho),

    CONSTRAINT FK_PHIEU_XUAT_CONG_TRINH
        FOREIGN KEY (MaCT) REFERENCES CONG_TRINH(MaCT),

    CONSTRAINT FK_PHIEU_XUAT_TAI_KHOAN
        FOREIGN KEY (NguoiLap) REFERENCES TAI_KHOAN(MaTK)
);

-- 11. Bảng chi tiết phiếu xuất
CREATE TABLE CT_PHIEU_XUAT
(
    MaPX VARCHAR(10) NOT NULL,
    MaVT VARCHAR(10) NOT NULL,
    SoLuong DECIMAL(18,2) NOT NULL,

    CONSTRAINT PK_CT_PHIEU_XUAT PRIMARY KEY (MaPX, MaVT),

    CONSTRAINT FK_CT_XUAT_PHIEU_XUAT
        FOREIGN KEY (MaPX) REFERENCES PHIEU_XUAT(MaPX),

    CONSTRAINT FK_CT_XUAT_VAT_TU
        FOREIGN KEY (MaVT) REFERENCES VAT_TU(MaVT),

    CONSTRAINT CK_CT_XUAT_SOLUONG
        CHECK (SoLuong > 0)
);

-- 12. Bảng phiếu chuyển kho
CREATE TABLE PHIEU_CHUYEN_KHO
(
    MaPCK VARCHAR(10) NOT NULL,
    MaKhoNguon VARCHAR(10) NOT NULL,
    MaKhoDich VARCHAR(10) NOT NULL,
    NgayChuyen DATETIME NOT NULL CONSTRAINT DF_PCK_NGAY DEFAULT GETDATE(),
    NguoiLap VARCHAR(10) NOT NULL,
    GhiChu NVARCHAR(500),
    TrangThai VARCHAR(20) NOT NULL CONSTRAINT DF_PCK_TT DEFAULT N'Cho duyet',

    CONSTRAINT PK_PHIEU_CHUYEN_KHO PRIMARY KEY (MaPCK),

    CONSTRAINT FK_CHUYEN_KHO_NGUON
        FOREIGN KEY (MaKhoNguon) REFERENCES KHO(MaKho),

    CONSTRAINT FK_CHUYEN_KHO_DICH
        FOREIGN KEY (MaKhoDich) REFERENCES KHO(MaKho),

    CONSTRAINT FK_CHUYEN_KHO_TAI_KHOAN
        FOREIGN KEY (NguoiLap) REFERENCES TAI_KHOAN(MaTK),

    CONSTRAINT CK_CHUYEN_KHO_KHAC_KHO
        CHECK (MaKhoNguon <> MaKhoDich)
);

-- 13. Bảng chi tiết chuyển kho
CREATE TABLE CT_CHUYEN_KHO
(
    MaPCK VARCHAR(10) NOT NULL,
    MaVT VARCHAR(10) NOT NULL,
    SoLuong DECIMAL(18,2) NOT NULL,

    CONSTRAINT PK_CT_CHUYEN_KHO PRIMARY KEY (MaPCK, MaVT),

    CONSTRAINT FK_CT_CHUYEN_PHIEU_CHUYEN
        FOREIGN KEY (MaPCK) REFERENCES PHIEU_CHUYEN_KHO(MaPCK),

    CONSTRAINT FK_CT_CHUYEN_VAT_TU
        FOREIGN KEY (MaVT) REFERENCES VAT_TU(MaVT),

    CONSTRAINT CK_CT_CHUYEN_SOLUONG
        CHECK (SoLuong > 0)
);

-- 14. Bảng phiếu điều chỉnh
CREATE TABLE PHIEU_DIEU_CHINH
(
    MaPDC VARCHAR(10) NOT NULL,
    MaKho VARCHAR(10) NOT NULL,
    NgayDieuChinh DATETIME NOT NULL CONSTRAINT DF_PDC_NGAY DEFAULT GETDATE(),
    NguoiLap VARCHAR(10) NOT NULL,
    LyDo NVARCHAR(500) NOT NULL,
    TrangThai VARCHAR(20) NOT NULL CONSTRAINT DF_PDC_TT DEFAULT N'Cho duyet',

    CONSTRAINT PK_PHIEU_DIEU_CHINH PRIMARY KEY (MaPDC),

    CONSTRAINT FK_DIEU_CHINH_KHO
        FOREIGN KEY (MaKho) REFERENCES KHO(MaKho),

    CONSTRAINT FK_DIEU_CHINH_TAI_KHOAN
        FOREIGN KEY (NguoiLap) REFERENCES TAI_KHOAN(MaTK)
);

-- 15. Bảng chi tiết điều chỉnh
CREATE TABLE CT_DIEU_CHINH
(
    MaPDC VARCHAR(10) NOT NULL,
    MaVT VARCHAR(10) NOT NULL,
    SoLuongTruoc DECIMAL(18,2) NOT NULL,
    SoLuongSau DECIMAL(18,2) NOT NULL,

    CONSTRAINT PK_CT_DIEU_CHINH PRIMARY KEY (MaPDC, MaVT),

    CONSTRAINT FK_CT_DIEU_CHINH_PHIEU
        FOREIGN KEY (MaPDC) REFERENCES PHIEU_DIEU_CHINH(MaPDC),

    CONSTRAINT FK_CT_DIEU_CHINH_VAT_TU
        FOREIGN KEY (MaVT) REFERENCES VAT_TU(MaVT),

    CONSTRAINT CK_DIEU_CHINH_TRUOC
        CHECK (SoLuongTruoc >= 0),

    CONSTRAINT CK_DIEU_CHINH_SAU
        CHECK (SoLuongSau >= 0)
);

/* =====================================================================
   THEM DU LIEU MAU
   ===================================================================== */
-- TAI_KHOAN
INSERT INTO TAI_KHOAN (MaTK, TenDangNhap, MatKhau, HoTen, VaiTro, TrangThai)
VALUES
    ('TK01', 'admin',    'HASHED_PW_1', N'Nguyen Van An',   N'Quan tri vien', 1),
    ('TK02', 'nhanvien1', 'HASHED_PW_2', N'Tran Thi Binh',  N'Thu kho',       1),
    ('TK03', 'nhanvien2', 'HASHED_PW_3', N'Le Van Cuong',   N'Ke toan kho',   1);

-- LOAI_VAT_TU
INSERT INTO LOAI_VAT_TU (MaLoai, TenLoai, MoTa) VALUES
    ('LOAI01', N'Sat thep',   N'Sat, thep xay dung'),
    ('LOAI02', N'Xi mang',    N'Cac loai xi mang'),
    ('LOAI03', N'Cat da',     N'Cat, da xay dung');

-- VAT_TU
INSERT INTO VAT_TU (MaVT, TenVT, MaLoai, DonViTinh, TonToiThieu, MoTa, TrangThai)
VALUES
    ('VT01', N'Thep phi 10',       'LOAI01', N'Cay', 50,  N'Thep xay dung phi 10', 1),
    ('VT02', N'Xi mang Ha Tien',   'LOAI02', N'Bao', 100, N'Xi mang PCB40',        1),
    ('VT03', N'Cat vang',          'LOAI03', N'M3',  20,  N'Cat vang xay tho',     1),
    ('VT04', N'Da 1x2',            'LOAI03', N'M3',  20,  N'Da xay dung 1x2',      1);

-- NHA_CUNG_CAP
INSERT INTO NHA_CUNG_CAP (MaNCC, TenNCC, DiaChi, SoDienThoai, Email, TrangThai)
VALUES
    ('NCC01', N'Cong ty Thep Viet',  N'12 Le Loi, Q1, TP.HCM', '0901111111', 'contact@thepviet.vn', 1),
    ('NCC02', N'Cong ty VLXD Minh Phat', N'45 Cach Mang Thang 8, TP.HCM', '0902222222', 'sales@minhphat.vn', 1);

-- KHO
INSERT INTO KHO (MaKho, TenKho, DiaChi, MoTa, TrangThai)
VALUES
    ('KHO01', N'Kho A - Quan 9',   N'Khu cong nghiep Q9, TP.HCM', N'Kho chinh', 1),
    ('KHO02', N'Kho B - Thu Duc',  N'Duong so 5, Thu Duc, TP.HCM', N'Kho phu',  1);

-- 2.6. CONG_TRINH
INSERT INTO CONG_TRINH (MaCT, TenCT, DiaDiem, NgayBatDau, NgayKetThucDuKien, TrangThai)
VALUES
    ('CT01', N'Chung cu An Phu',  N'Q2, TP.HCM', '2026-01-10', '2026-12-31', N'Dang thi cong'),
    ('CT02', N'Nha xuong Binh Duong', N'Binh Duong', '2026-03-01', '2026-09-30', N'Dang thi cong');

-- TON_KHO
INSERT INTO TON_KHO (MaKho, MaVT, SoLuongTon)
VALUES
    ('KHO01', 'VT01', 500),
    ('KHO01', 'VT02', 200),
    ('KHO02', 'VT03', 1000),
    ('KHO02', 'VT04', 800);

-- PHIEU_NHAP
INSERT INTO PHIEU_NHAP (MaPN, MaNCC, MaKho, NgayNhap, NguoiLap, GhiChu, TrangThai)
VALUES
    ('PN01', 'NCC01', 'KHO01', '2026-07-01', 'TK01', N'Nhap thep dot 1', N'Da duyet');

-- CT_PHIEU_NHAP
INSERT INTO CT_PHIEU_NHAP (MaPN, MaVT, SoLuong, DonGia)
VALUES
    ('PN01', 'VT01', 100, 15000),
    ('PN01', 'VT02', 50,  90000);

-- PHIEU_XUAT
INSERT INTO PHIEU_XUAT (MaPX, MaKho, MaCT, NgayXuat, NguoiLap, GhiChu, TrangThai)
VALUES
    ('PX01', 'KHO01', 'CT01', '2026-07-05', 'TK02', N'Xuat thep cho cong trinh An Phu', N'Da duyet');

-- CT_PHIEU_XUAT
INSERT INTO CT_PHIEU_XUAT (MaPX, MaVT, SoLuong)
VALUES
    ('PX01', 'VT01', 20);

-- PHIEU_CHUYEN_KHO
INSERT INTO PHIEU_CHUYEN_KHO (MaPCK, MaKhoNguon, MaKhoDich, NgayChuyen, NguoiLap, GhiChu, TrangThai)
VALUES
    ('PCK01', 'KHO01', 'KHO02', '2026-07-08', 'TK01', N'Chuyen thep sang kho B', N'Da duyet');

-- CT_CHUYEN_KHO
INSERT INTO CT_CHUYEN_KHO (MaPCK, MaVT, SoLuong)
VALUES
    ('PCK01', 'VT01', 10);

-- PHIEU_DIEU_CHINH
INSERT INTO PHIEU_DIEU_CHINH (MaPDC, MaKho, NgayDieuChinh, NguoiLap, LyDo, TrangThai)
VALUES
    ('PDC01', 'KHO01', '2026-07-10', 'TK03', N'Kiem ke dinh ky, lech so luong thuc te', N'Da duyet');

-- CT_DIEU_CHINH
INSERT INTO CT_DIEU_CHINH (MaPDC, MaVT, SoLuongTruoc, SoLuongSau)
VALUES
    ('PDC01', 'VT01', 500, 490);

/* =====================================================================
   PHAN 3. THU THEM DU LIEU SAI DE KIEM TRA RANG BUOC
   ===================================================================== */
-- Ten dang nhap bi trung -> vi pham UNIQUE (UQ_TAI_KHOAN_TENDANGNHAP)
INSERT INTO TAI_KHOAN (MaTK, TenDangNhap, MatKhau, HoTen, VaiTro, TrangThai)
VALUES
    ('TK04', 'admin', 'HASHED_PW_4', N'Pham Thi Test', N'Thu kho', 1);

-- So luong ton am -> vi pham CHECK CK_TON_KHO_SOLUONG
INSERT INTO TON_KHO (MaKho, MaVT, SoLuongTon)
VALUES
    ('KHO01', 'VT03', -5);

-- So luong nhap bang 0 -> vi pham CHECK CK_CT_NHAP_SOLUONG
INSERT INTO CT_PHIEU_NHAP (MaPN, MaVT, SoLuong, DonGia)
VALUES
    ('PN01', 'VT03', 0, 10000);

-- So luong xuat am -> vi pham CHECK CK_CT_XUAT_SOLUONG
INSERT INTO CT_PHIEU_XUAT (MaPX, MaVT, SoLuong)
VALUES
    ('PX01', 'VT02', -10);

-- Ma loai vat tu khong ton tai -> vi pham FK FK_VAT_TU_LOAI
INSERT INTO VAT_TU (MaVT, TenVT, MaLoai, DonViTinh, TonToiThieu, MoTa, TrangThai)
VALUES
    ('VT05', N'Gach ong', 'LOAI99', N'Vien', 100, N'Test FK sai', 1);

-- Kho nguon bang kho dich -> vi pham CHECK CK_CHUYEN_KHO_KHAC_KHO
INSERT INTO PHIEU_CHUYEN_KHO (MaPCK, MaKhoNguon, MaKhoDich, NgayChuyen, NguoiLap, GhiChu, TrangThai)
VALUES
    ('PCK02', 'KHO01', 'KHO01', '2026-07-11', 'TK01', N'Test kho nguon = kho dich', N'Cho duyet');

-- Chi tiet tham chieu den phieu khong ton tai -> vi pham FK FK_CT_NHAP_PHIEU_NHAP
INSERT INTO CT_PHIEU_NHAP (MaPN, MaVT, SoLuong, DonGia)
VALUES
    ('PN99', 'VT01', 10, 15000);