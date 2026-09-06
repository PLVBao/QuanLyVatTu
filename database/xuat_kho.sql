USE QuanLyVatTuXayDung;
GO

CREATE OR ALTER PROCEDURE sp_XuatKho
    @MaPX       VARCHAR(20),
    @MaKho      VARCHAR(20),
    @MaCT       VARCHAR(20),
    @NgayXuat   DATETIME,
    @NguoiLap   VARCHAR(20),
    @GhiChu     NVARCHAR(255),
    @TrangThai  NVARCHAR(50),
    @MaVT       VARCHAR(20),
    @SoLuong    DECIMAL(18,2)
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        -- 1. Kiểm tra điều kiện số lượng xuất
        IF @SoLuong <= 0
            BEGIN
                RAISERROR(N'Lỗi: Số lượng xuất phải lớn hơn 0!', 16, 1);
                RETURN;
            END

        -- 2. Kiểm tra tồn tại các khóa ngoại
        IF NOT EXISTS (SELECT 1 FROM KHO WHERE MaKho = @MaKho)
            BEGIN
                RAISERROR(N'Lỗi: Mã kho không tồn tại!', 16, 1);
                RETURN;
            END

        IF NOT EXISTS (SELECT 1 FROM VAT_TU WHERE MaVT = @MaVT)
            BEGIN
                RAISERROR(N'Lỗi: Mã vật tư không tồn tại!', 16, 1);
                RETURN;
            END

        -- 3. Kiểm tra tồn kho của kho xuất
        DECLARE @TonKho DECIMAL(18,2);
        SELECT @TonKho = SoLuongTon
        FROM TON_KHO
        WHERE MaKho = @MaKho AND MaVT = @MaVT;

        IF (@TonKho IS NULL OR @TonKho < @SoLuong)
            BEGIN
                RAISERROR(N'Lỗi: Số lượng tồn ở kho không đủ hoặc vật tư không có trong kho!', 16, 1);
                RETURN;
            END

        -- Bắt đầu giao tác
        BEGIN TRANSACTION;

        -- 4. Thêm dữ liệu vào bảng PHIEU_XUAT
        INSERT INTO PHIEU_XUAT (MaPX, MaKho, MaCT, NgayXuat, NguoiLap, GhiChu, TrangThai)
        VALUES (@MaPX, @MaKho, @MaCT, @NgayXuat, @NguoiLap, @GhiChu, @TrangThai);

        -- 5. Thêm dữ liệu vào bảng CT_PHIEU_XUAT
        INSERT INTO CT_PHIEU_XUAT (MaPX, MaVT, SoLuong)
        VALUES (@MaPX, @MaVT, @SoLuong);

        -- 6. Cập nhật giảm số lượng tồn kho
        UPDATE TON_KHO
        SET SoLuongTon = SoLuongTon - @SoLuong
        WHERE MaKho = @MaKho AND MaVT = @MaVT;

        -- Commit giao tác
        COMMIT TRANSACTION;
        PRINT N'Xuất kho thành công!';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END;
GO

/*
-- ==========================================
-- TRƯỜNG HỢP 1: THÀNH CÔNG (Dữ liệu hợp lệ, đủ tồn kho)
-- ==========================================
EXEC sp_XuatKho
     @MaPX      = 'PX003',
     @MaKho     = 'KHO01',
     @MaCT      = 'CT01',
     @NgayXuat  = '2026-09-03',
     @NguoiLap  = 'TK01',
     @GhiChu    = N'Xuất vật tư thi công công trình',
     @TrangThai = N'HOAN_THANH',
     @MaVT      = 'VT01',
     @SoLuong   = 5;

-- Kiểm tra kết quả sau khi xuất thành công
SELECT * FROM PHIEU_XUAT WHERE MaPX = 'PX003';
SELECT * FROM CT_PHIEU_XUAT WHERE MaPX = 'PX003';
SELECT * FROM TON_KHO WHERE MaKho = 'KHO01' AND MaVT = 'VT01';


-- ==========================================
-- TRƯỜNG HỢP 2: THẤT BẠI (Số lượng xuất vượt quá tồn kho)
-- ==========================================
EXEC sp_XuatKho
     @MaPX      = 'PX002',
     @MaKho     = 'KHO01',
     @MaCT      = 'CT01',
     @NgayXuat  = '2026-09-03',
     @NguoiLap  = 'NV01',
     @GhiChu    = N'Test xuất vượt tồn kho',
     @TrangThai = N'HOAN_THANH',
     @MaVT      = 'VT01',
     @SoLuong   = 999999; -- Số lượng quá lớn

-- Kiểm tra lại: Phiếu PX002 sẽ không được tạo và tồn kho giữ nguyên
SELECT * FROM PHIEU_XUAT WHERE MaPX = 'PX002';


-- ==========================================
-- TRƯỜNG HỢP 3: THẤT BẠI (Số lượng <= 0 hoặc Mã kho/Mã VT không tồn tại)
-- ==========================================
EXEC sp_XuatKho
     @MaPX      = 'PX003',
     @MaKho     = 'KHO_KHONG_TON_TAI',
     @MaCT      = 'CT01',
     @NgayXuat  = '2026-09-03',
     @NguoiLap  = 'NV01',
     @GhiChu    = N'Test sai mã kho',
     @TrangThai = N'HOAN_THANH',
     @MaVT      = 'VT01',
     @SoLuong   = 5;
*/