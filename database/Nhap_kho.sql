USE QuanLyVatTuXayDung;
GO

CREATE OR ALTER PROCEDURE sp_NhapKho
    @MaPN      VARCHAR(10),
    @MaNCC     VARCHAR(10),
    @MaKho     VARCHAR(10),
    @NgayNhap  DATETIME,
    @NguoiLap  VARCHAR(10),
    @GhiChu    NVARCHAR(500),
    @TrangThai VARCHAR(20),
    @MaVT      VARCHAR(10),
    @SoLuong   DECIMAL(18,2),
    @DonGia    DECIMAL(18,2)
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- 1. Kiểm tra điều kiện số lượng và đơn giá
        IF @SoLuong <= 0
        BEGIN
            RAISERROR(N'Lỗi: Số lượng nhập phải lớn hơn 0!', 16, 1);
            RETURN;
        END

        IF @DonGia <= 0
        BEGIN
            RAISERROR(N'Lỗi: Đơn giá nhập phải lớn hơn 0!', 16, 1);
            RETURN;
        END

        -- 2. Kiểm tra tồn tại danh mục và trạng thái hoạt động
        IF NOT EXISTS (SELECT 1 FROM NHA_CUNG_CAP WHERE MaNCC = @MaNCC AND TrangThai = 1)
        BEGIN
            RAISERROR(N'Lỗi: Nhà cung cấp không tồn tại hoặc đã ngừng hợp tác!', 16, 1);
            RETURN;
        END

        IF NOT EXISTS (SELECT 1 FROM KHO WHERE MaKho = @MaKho AND TrangThai = 1)
        BEGIN
            RAISERROR(N'Lỗi: Kho nhập không tồn tại hoặc đã ngừng hoạt động!', 16, 1);
            RETURN;
        END

        IF NOT EXISTS (SELECT 1 FROM VAT_TU WHERE MaVT = @MaVT AND TrangThai = 1)
        BEGIN
            RAISERROR(N'Lỗi: Vật tư không tồn tại hoặc đã ngừng sử dụng!', 16, 1);
            RETURN;
        END

        IF NOT EXISTS (SELECT 1 FROM TAI_KHOAN WHERE MaTK = @NguoiLap AND TrangThai = 1)
        BEGIN
            RAISERROR(N'Lỗi: Tài khoản người lập không tồn tại hoặc bị khóa!', 16, 1);
            RETURN;
        END

        IF EXISTS (SELECT 1 FROM PHIEU_NHAP WHERE MaPN = @MaPN)
        BEGIN
            RAISERROR(N'Lỗi: Mã phiếu nhập đã tồn tại!', 16, 1);
            RETURN;
        END

        -- Bắt đầu giao tác
        BEGIN TRANSACTION;

        -- 1. Insert phiếu nhập
        INSERT INTO PHIEU_NHAP (MaPN, MaNCC, MaKho, NgayNhap, NguoiLap, GhiChu, TrangThai)
        VALUES (@MaPN, @MaNCC, @MaKho, ISNULL(@NgayNhap, GETDATE()), @NguoiLap, @GhiChu, @TrangThai);

        -- 2. Insert chi tiết phiếu nhập
        INSERT INTO CT_PHIEU_NHAP (MaPN, MaVT, SoLuong, DonGia)
        VALUES (@MaPN, @MaVT, @SoLuong, @DonGia);

        -- 3. Cập nhật tồn kho an toàn
        IF EXISTS (SELECT 1 FROM TON_KHO WITH (UPDLOCK) WHERE MaKho = @MaKho AND MaVT = @MaVT)
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
