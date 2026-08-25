
USE QuanLyVatTuXayDung;
GO

CREATE OR ALTER PROCEDURE sp_NhapKho
    @MaPN VARCHAR(20),
    @MaNCC VARCHAR(20),
    @MaKho VARCHAR(20),
    @NgayNhap DATETIME,
    @NguoiLap VARCHAR(20),
    @GhiChu NVARCHAR(255),
    @TrangThai NVARCHAR(50),
    @MaVT VARCHAR(20),
    @SoLuong DECIMAL(18,2),
    @DonGia DECIMAL(18,2)
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Kiểm tra điều kiện số lượng
        IF @SoLuong <= 0
        BEGIN
            RAISERROR(N'Lỗi: Số lượng nhập phải lớn hơn 0!', 16, 1);
            RETURN;
        END

        -- Kiểm tra tồn tại khóa ngoại
        IF NOT EXISTS (SELECT 1 FROM NHA_CUNG_CAP WHERE MaNCC = @MaNCC)
        BEGIN
            RAISERROR(N'Lỗi: Mã Nhà cung cấp không tồn tại!', 16, 1);
            RETURN;
        END

        IF NOT EXISTS (SELECT 1 FROM KHO WHERE MaKho = @MaKho)
        BEGIN
            RAISERROR(N'Lỗi: Mã Kho không tồn tại!', 16, 1);
            RETURN;
        END

        IF NOT EXISTS (SELECT 1 FROM VAT_TU WHERE MaVT = @MaVT)
        BEGIN
            RAISERROR(N'Lỗi: Mã Vật tư không tồn tại!', 16, 1);
            RETURN;
        END

        -- Bắt đầu giao tác
        BEGIN TRANSACTION;

        -- 1. Insert phiếu nhập
        INSERT INTO PHIEU_NHAP (MaPN, MaNCC, MaKho, NgayNhap, NguoiLap, GhiChu, TrangThai)
        VALUES (@MaPN, @MaNCC, @MaKho, @NgayNhap, @NguoiLap, @GhiChu, @TrangThai);

        -- 2. Insert chi tiết phiếu nhập
        INSERT INTO CT_PHIEU_NHAP (MaPN, MaVT, SoLuong, DonGia)
        VALUES (@MaPN, @MaVT, @SoLuong, @DonGia);

        -- 3. Cập nhật tồn kho
        IF EXISTS (SELECT 1 FROM TON_KHO WHERE MaKho = @MaKho AND MaVT = @MaVT)
        BEGIN
            UPDATE TON_KHO
            SET SoLuongTon = SoLuongTon + @SoLuong
            WHERE MaKho = @MaKho AND MaVT = @MaVT;
        END
        ELSE
        BEGIN
            INSERT INTO TON_KHO (MaKho, MaVT, SoLuongTon)
            VALUES (@MaKho, @MaVT, @SoLuong);
        END

        -- 4. Commit giao tác
        COMMIT TRANSACTION;
        PRINT N'Nhập kho thành công!';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END;
GO