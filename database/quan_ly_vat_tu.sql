USE master;
GO

IF DB_ID(N'QuanLyVatTuXayDung') IS NULL
BEGIN
    CREATE DATABASE QuanLyVatTuXayDung;
END;
GO

USE QuanLyVatTuXayDung;
GO

-- 1. Bảng tài khoản
CREATE TABLE TAI_KHOAN
(
    MaTK VARCHAR(10) NOT NULL,
    TenDangNhap VARCHAR(50) NOT NULL,
    MatKhau VARCHAR(255) NOT NULL,
    HoTen NVARCHAR(100) NOT NULL,
    VaiTro VARCHAR(30) NOT NULL,
    TrangThai BIT NOT NULL
        CONSTRAINT DF_TAIKHOAN_TT DEFAULT 1,

    CONSTRAINT PK_TAI_KHOAN PRIMARY KEY (MaTK),

    CONSTRAINT UQ_TAI_KHOAN_TENDANGNHAP
        UNIQUE (TenDangNhap),

    CONSTRAINT CK_TAIKHOAN_VAITRO
        CHECK (VaiTro IN ('QUAN_LY', 'NHAN_VIEN'))
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
    TrangThai BIT NOT NULL
        CONSTRAINT DF_VATTU_TT DEFAULT 1,

    CONSTRAINT PK_VAT_TU PRIMARY KEY (MaVT),

    CONSTRAINT FK_VAT_TU_LOAI
        FOREIGN KEY (MaLoai)
        REFERENCES LOAI_VAT_TU(MaLoai),

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
    TrangThai BIT NOT NULL
        CONSTRAINT DF_NCC_TT DEFAULT 1,

    CONSTRAINT PK_NHA_CUNG_CAP PRIMARY KEY (MaNCC)
);

-- 5. Bảng kho
CREATE TABLE KHO
(
    MaKho VARCHAR(10) NOT NULL,
    TenKho NVARCHAR(100) NOT NULL,
    DiaChi NVARCHAR(255),
    MoTa NVARCHAR(255),
    TrangThai BIT NOT NULL
        CONSTRAINT DF_KHO_TT DEFAULT 1,

    CONSTRAINT PK_KHO PRIMARY KEY (MaKho)
);

-- 6. Bảng công trình
CREATE TABLE CONG_TRINH
(
    MaCT VARCHAR(10) NOT NULL,
    TenCT NVARCHAR(150) NOT NULL,
    DiaDiem NVARCHAR(255) NOT NULL,
    NgayBatDau DATE,
    NgayKetThucDuKien DATE,
    TrangThai VARCHAR(30) NOT NULL
        CONSTRAINT DF_CT_TT DEFAULT 'CHUA_BAT_DAU',

    CONSTRAINT PK_CONG_TRINH PRIMARY KEY (MaCT),

    CONSTRAINT CK_CONG_TRINH_TRANGTHAI
        CHECK
        (
            TrangThai IN
            (
                'CHUA_BAT_DAU',
                'DANG_THI_CONG',
                'TAM_DUNG',
                'HOAN_THANH'
            )
        ),

    CONSTRAINT CK_CONG_TRINH_NGAY
        CHECK
        (
            NgayBatDau IS NULL
            OR NgayKetThucDuKien IS NULL
            OR NgayKetThucDuKien >= NgayBatDau
        )
);

-- 7. Bảng tồn kho
CREATE TABLE TON_KHO
(
    MaKho VARCHAR(10) NOT NULL,
    MaVT VARCHAR(10) NOT NULL,
    SoLuongTon DECIMAL(18,2) NOT NULL
        CONSTRAINT DF_TONKHO_SOLUONG DEFAULT 0,

    CONSTRAINT PK_TON_KHO
        PRIMARY KEY (MaKho, MaVT),

    CONSTRAINT FK_TON_KHO_KHO
        FOREIGN KEY (MaKho)
        REFERENCES KHO(MaKho),

    CONSTRAINT FK_TON_KHO_VAT_TU
        FOREIGN KEY (MaVT)
        REFERENCES VAT_TU(MaVT),

    CONSTRAINT CK_TON_KHO_SOLUONG
        CHECK (SoLuongTon >= 0)
);

-- 8. Bảng phiếu nhập
CREATE TABLE PHIEU_NHAP
(
    MaPN VARCHAR(10) NOT NULL,
    MaNCC VARCHAR(10) NOT NULL,
    MaKho VARCHAR(10) NOT NULL,
    NgayNhap DATETIME NOT NULL
        CONSTRAINT DF_PN_NGAY DEFAULT GETDATE(),
    NguoiLap VARCHAR(10) NOT NULL,
    GhiChu NVARCHAR(500),
    TrangThai VARCHAR(20) NOT NULL
        CONSTRAINT DF_PN_TT DEFAULT 'NHAP',

    CONSTRAINT PK_PHIEU_NHAP PRIMARY KEY (MaPN),

    CONSTRAINT FK_PHIEU_NHAP_NCC
        FOREIGN KEY (MaNCC)
        REFERENCES NHA_CUNG_CAP(MaNCC),

    CONSTRAINT FK_PHIEU_NHAP_KHO
        FOREIGN KEY (MaKho)
        REFERENCES KHO(MaKho),

    CONSTRAINT FK_PHIEU_NHAP_TAI_KHOAN
        FOREIGN KEY (NguoiLap)
        REFERENCES TAI_KHOAN(MaTK),

    CONSTRAINT CK_PHIEU_NHAP_TRANGTHAI
        CHECK (TrangThai IN ('NHAP', 'HOAN_THANH', 'DA_HUY'))
);

-- 9. Bảng chi tiết phiếu nhập
CREATE TABLE CT_PHIEU_NHAP
(
    MaPN VARCHAR(10) NOT NULL,
    MaVT VARCHAR(10) NOT NULL,
    SoLuong DECIMAL(18,2) NOT NULL,
    DonGia DECIMAL(18,2) NOT NULL,

    CONSTRAINT PK_CT_PHIEU_NHAP
        PRIMARY KEY (MaPN, MaVT),

    CONSTRAINT FK_CT_NHAP_PHIEU_NHAP
        FOREIGN KEY (MaPN)
        REFERENCES PHIEU_NHAP(MaPN),

    CONSTRAINT FK_CT_NHAP_VAT_TU
        FOREIGN KEY (MaVT)
        REFERENCES VAT_TU(MaVT),

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
    NgayXuat DATETIME NOT NULL
        CONSTRAINT DF_PX_NGAY DEFAULT GETDATE(),
    NguoiLap VARCHAR(10) NOT NULL,
    GhiChu NVARCHAR(500),
    TrangThai VARCHAR(20) NOT NULL
        CONSTRAINT DF_PX_TT DEFAULT 'NHAP',

    CONSTRAINT PK_PHIEU_XUAT PRIMARY KEY (MaPX),

    CONSTRAINT FK_PHIEU_XUAT_KHO
        FOREIGN KEY (MaKho)
        REFERENCES KHO(MaKho),

    CONSTRAINT FK_PHIEU_XUAT_CONG_TRINH
        FOREIGN KEY (MaCT)
        REFERENCES CONG_TRINH(MaCT),

    CONSTRAINT FK_PHIEU_XUAT_TAI_KHOAN
        FOREIGN KEY (NguoiLap)
        REFERENCES TAI_KHOAN(MaTK),

    CONSTRAINT CK_PHIEU_XUAT_TRANGTHAI
        CHECK (TrangThai IN ('NHAP', 'HOAN_THANH', 'DA_HUY'))
);

-- 11. Bảng chi tiết phiếu xuất
CREATE TABLE CT_PHIEU_XUAT
(
    MaPX VARCHAR(10) NOT NULL,
    MaVT VARCHAR(10) NOT NULL,
    SoLuong DECIMAL(18,2) NOT NULL,

    CONSTRAINT PK_CT_PHIEU_XUAT
        PRIMARY KEY (MaPX, MaVT),

    CONSTRAINT FK_CT_XUAT_PHIEU_XUAT
        FOREIGN KEY (MaPX)
        REFERENCES PHIEU_XUAT(MaPX),

    CONSTRAINT FK_CT_XUAT_VAT_TU
        FOREIGN KEY (MaVT)
        REFERENCES VAT_TU(MaVT),

    CONSTRAINT CK_CT_XUAT_SOLUONG
        CHECK (SoLuong > 0)
);

-- 12. Bảng phiếu chuyển kho
CREATE TABLE PHIEU_CHUYEN_KHO
(
    MaPCK VARCHAR(10) NOT NULL,
    MaKhoNguon VARCHAR(10) NOT NULL,
    MaKhoDich VARCHAR(10) NOT NULL,
    NgayChuyen DATETIME NOT NULL
        CONSTRAINT DF_PCK_NGAY DEFAULT GETDATE(),
    NguoiLap VARCHAR(10) NOT NULL,
    GhiChu NVARCHAR(500),
    TrangThai VARCHAR(20) NOT NULL
        CONSTRAINT DF_PCK_TT DEFAULT 'NHAP',

    CONSTRAINT PK_PHIEU_CHUYEN_KHO PRIMARY KEY (MaPCK),

    CONSTRAINT FK_CHUYEN_KHO_NGUON
        FOREIGN KEY (MaKhoNguon)
        REFERENCES KHO(MaKho),

    CONSTRAINT FK_CHUYEN_KHO_DICH
        FOREIGN KEY (MaKhoDich)
        REFERENCES KHO(MaKho),

    CONSTRAINT FK_CHUYEN_KHO_TAI_KHOAN
        FOREIGN KEY (NguoiLap)
        REFERENCES TAI_KHOAN(MaTK),

    CONSTRAINT CK_CHUYEN_KHO_KHAC_KHO
        CHECK (MaKhoNguon <> MaKhoDich),

    CONSTRAINT CK_CHUYEN_KHO_TRANGTHAI
        CHECK (TrangThai IN ('NHAP', 'HOAN_THANH', 'DA_HUY'))
);

-- 13. Bảng chi tiết chuyển kho
CREATE TABLE CT_CHUYEN_KHO
(
    MaPCK VARCHAR(10) NOT NULL,
    MaVT VARCHAR(10) NOT NULL,
    SoLuong DECIMAL(18,2) NOT NULL,

    CONSTRAINT PK_CT_CHUYEN_KHO
        PRIMARY KEY (MaPCK, MaVT),

    CONSTRAINT FK_CT_CHUYEN_PHIEU_CHUYEN
        FOREIGN KEY (MaPCK)
        REFERENCES PHIEU_CHUYEN_KHO(MaPCK),

    CONSTRAINT FK_CT_CHUYEN_VAT_TU
        FOREIGN KEY (MaVT)
        REFERENCES VAT_TU(MaVT),

    CONSTRAINT CK_CT_CHUYEN_SOLUONG
        CHECK (SoLuong > 0)
);

-- 14. Bảng phiếu điều chỉnh
CREATE TABLE PHIEU_DIEU_CHINH
(
    MaPDC VARCHAR(10) NOT NULL,
    MaKho VARCHAR(10) NOT NULL,
    NgayDieuChinh DATETIME NOT NULL
        CONSTRAINT DF_PDC_NGAY DEFAULT GETDATE(),
    NguoiLap VARCHAR(10) NOT NULL,
    LyDo NVARCHAR(500) NOT NULL,
    TrangThai VARCHAR(20) NOT NULL
        CONSTRAINT DF_PDC_TT DEFAULT 'NHAP',

    CONSTRAINT PK_PHIEU_DIEU_CHINH PRIMARY KEY (MaPDC),

    CONSTRAINT FK_DIEU_CHINH_KHO
        FOREIGN KEY (MaKho)
        REFERENCES KHO(MaKho),

    CONSTRAINT FK_DIEU_CHINH_TAI_KHOAN
        FOREIGN KEY (NguoiLap)
        REFERENCES TAI_KHOAN(MaTK),

    CONSTRAINT CK_DIEU_CHINH_LYDO
        CHECK (LEN(LTRIM(RTRIM(LyDo))) > 0),

    CONSTRAINT CK_DIEU_CHINH_TRANGTHAI
        CHECK (TrangThai IN ('NHAP', 'HOAN_THANH', 'DA_HUY'))
);

-- 15. Bảng chi tiết điều chỉnh
CREATE TABLE CT_DIEU_CHINH
(
    MaPDC VARCHAR(10) NOT NULL,
    MaVT VARCHAR(10) NOT NULL,
    SoLuongTruoc DECIMAL(18,2) NOT NULL,
    SoLuongSau DECIMAL(18,2) NOT NULL,

    CONSTRAINT PK_CT_DIEU_CHINH
        PRIMARY KEY (MaPDC, MaVT),

    CONSTRAINT FK_CT_DIEU_CHINH_PHIEU
        FOREIGN KEY (MaPDC)
        REFERENCES PHIEU_DIEU_CHINH(MaPDC),

    CONSTRAINT FK_CT_DIEU_CHINH_VAT_TU
        FOREIGN KEY (MaVT)
        REFERENCES VAT_TU(MaVT),

    CONSTRAINT CK_DIEU_CHINH_TRUOC
        CHECK (SoLuongTruoc >= 0),

    CONSTRAINT CK_DIEU_CHINH_SAU
        CHECK (SoLuongSau >= 0),

    CONSTRAINT CK_DIEU_CHINH_CHENH_LECH
        CHECK (SoLuongTruoc <> SoLuongSau)
);

/*====================================================
  DỮ LIỆU MẪU
====================================================*/

-- Tài khoản
INSERT INTO TAI_KHOAN
    (MaTK, TenDangNhap, MatKhau, HoTen, VaiTro, TrangThai)
VALUES
    ('TK01', 'admin', '123456',
     N'Nguyễn Văn An', 'QUAN_LY', 1),

    ('TK02', 'nhanvien1', '123456',
     N'Trần Thị Bình', 'NHAN_VIEN', 1),

    ('TK03', 'nhanvien2', '123456',
     N'Lê Văn Cường', 'NHAN_VIEN', 1);

-- Loại vật tư
INSERT INTO LOAI_VAT_TU
    (MaLoai, TenLoai, MoTa)
VALUES
    ('LOAI01', N'Sắt thép', N'Sắt, thép phục vụ xây dựng'),
    ('LOAI02', N'Xi măng', N'Các loại xi măng xây dựng'),
    ('LOAI03', N'Cát đá', N'Cát và đá xây dựng');

-- Vật tư
INSERT INTO VAT_TU
    (MaVT, TenVT, MaLoai, DonViTinh, TonToiThieu, MoTa, TrangThai)
VALUES
    ('VT01', N'Thép phi 10', 'LOAI01',
     N'Cây', 50, N'Thép xây dựng phi 10', 1),

    ('VT02', N'Xi măng Hà Tiên', 'LOAI02',
     N'Bao', 100, N'Xi măng PCB40', 1),

    ('VT03', N'Cát vàng', 'LOAI03',
     N'Mét khối', 20, N'Cát vàng xây thô', 1),

    ('VT04', N'Đá 1x2', 'LOAI03',
     N'Mét khối', 20, N'Đá xây dựng 1x2', 1);

-- Nhà cung cấp
INSERT INTO NHA_CUNG_CAP
    (MaNCC, TenNCC, DiaChi, SoDienThoai, Email, TrangThai)
VALUES
    ('NCC01', N'Công ty Thép Việt',
     N'12 Lê Lợi, Quận 1, TP.HCM',
     '0901111111', 'contact@thepviet.vn', 1),

    ('NCC02', N'Công ty VLXD Minh Phát',
     N'45 Cách Mạng Tháng 8, TP.HCM',
     '0902222222', 'sales@minhphat.vn', 1);

-- Kho
INSERT INTO KHO
    (MaKho, TenKho, DiaChi, MoTa, TrangThai)
VALUES
    ('KHO01', N'Kho chính',
     N'Thành phố Thủ Đức, TP.HCM',
     N'Kho lưu trữ chính', 1),

    ('KHO02', N'Kho phụ',
     N'Quận 9, TP.HCM',
     N'Kho lưu trữ phụ', 1);

-- Công trình
INSERT INTO CONG_TRINH
    (MaCT, TenCT, DiaDiem, NgayBatDau,
     NgayKetThucDuKien, TrangThai)
VALUES
    ('CT01', N'Chung cư An Phú',
     N'Quận 2, TP.HCM',
     '2026-01-10', '2026-12-31', 'DANG_THI_CONG'),

    ('CT02', N'Nhà xưởng Bình Dương',
     N'Bình Dương',
     '2026-03-01', '2026-09-30', 'DANG_THI_CONG');

-- Phiếu nhập thứ nhất: nhập thép vào kho chính
INSERT INTO PHIEU_NHAP
    (MaPN, MaNCC, MaKho, NgayNhap,
     NguoiLap, GhiChu, TrangThai)
VALUES
    ('PN01', 'NCC01', 'KHO01', '2026-07-01',
     'TK02', N'Nhập thép đợt 1', 'HOAN_THANH');

INSERT INTO CT_PHIEU_NHAP
    (MaPN, MaVT, SoLuong, DonGia)
VALUES
    ('PN01', 'VT01', 500, 150000);

-- Phiếu nhập thứ hai: nhập xi măng vào kho chính
INSERT INTO PHIEU_NHAP
    (MaPN, MaNCC, MaKho, NgayNhap,
     NguoiLap, GhiChu, TrangThai)
VALUES
    ('PN02', 'NCC02', 'KHO01', '2026-07-02',
     'TK02', N'Nhập xi măng đợt 1', 'HOAN_THANH');

INSERT INTO CT_PHIEU_NHAP
    (MaPN, MaVT, SoLuong, DonGia)
VALUES
    ('PN02', 'VT02', 200, 90000);

-- Phiếu nhập thứ ba: nhập cát và đá vào kho phụ
INSERT INTO PHIEU_NHAP
    (MaPN, MaNCC, MaKho, NgayNhap,
     NguoiLap, GhiChu, TrangThai)
VALUES
    ('PN03', 'NCC02', 'KHO02', '2026-07-03',
     'TK02', N'Nhập cát và đá', 'HOAN_THANH');

INSERT INTO CT_PHIEU_NHAP
    (MaPN, MaVT, SoLuong, DonGia)
VALUES
    ('PN03', 'VT03', 1000, 350000),
    ('PN03', 'VT04', 800, 450000);

-- Xuất 20 cây thép cho công trình CT01
INSERT INTO PHIEU_XUAT
    (MaPX, MaKho, MaCT, NgayXuat,
     NguoiLap, GhiChu, TrangThai)
VALUES
    ('PX01', 'KHO01', 'CT01', '2026-07-05',
     'TK02', N'Xuất thép cho công trình An Phú',
     'HOAN_THANH');

INSERT INTO CT_PHIEU_XUAT
    (MaPX, MaVT, SoLuong)
VALUES
    ('PX01', 'VT01', 20);

-- Chuyển 10 cây thép từ kho chính sang kho phụ
INSERT INTO PHIEU_CHUYEN_KHO
    (MaPCK, MaKhoNguon, MaKhoDich, NgayChuyen,
     NguoiLap, GhiChu, TrangThai)
VALUES
    ('PCK01', 'KHO01', 'KHO02', '2026-07-08',
     'TK02', N'Chuyển thép sang kho phụ',
     'HOAN_THANH');

INSERT INTO CT_CHUYEN_KHO
    (MaPCK, MaVT, SoLuong)
VALUES
    ('PCK01', 'VT01', 10);

-- Kiểm kê kho chính: thép từ 470 còn 465
INSERT INTO PHIEU_DIEU_CHINH
    (MaPDC, MaKho, NgayDieuChinh,
     NguoiLap, LyDo, TrangThai)
VALUES
    ('PDC01', 'KHO01', '2026-07-10',
     'TK01', N'Kiểm kê thực tế thiếu 5 cây thép',
     'HOAN_THANH');

INSERT INTO CT_DIEU_CHINH
    (MaPDC, MaVT, SoLuongTruoc, SoLuongSau)
VALUES
    ('PDC01', 'VT01', 470, 465);

-- Tồn kho hiện tại sau các phiếu mẫu
INSERT INTO TON_KHO
    (MaKho, MaVT, SoLuongTon)
VALUES
    ('KHO01', 'VT01', 465),
    ('KHO01', 'VT02', 200),
    ('KHO02', 'VT01', 10),
    ('KHO02', 'VT03', 1000),
    ('KHO02', 'VT04', 800);
