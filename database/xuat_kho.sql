USE QuanLyVatTuXayDung;
GO

CREATE OR ALTER PROCEDURE sp_XuatKho
    @MaPX       VARCHAR(10),
    @MaKho      VARCHAR(10),
    @MaCT       VARCHAR(10),
    @NgayXuat   DATETIME,
    @NguoiLap   VARCHAR(10),
    @GhiChu     NVARCHAR(500),
    @TrangThai  VARCHAR(20),
    @MaVT       VARCHAR(10),
    @SoLuong    DECIMAL(18,2)
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        -- 1. Kiểm tra số lượng xuất
        IF @SoLuong <= 0
        BEGIN
            RAISERROR(N'Lỗi: Số lượng xuất phải lớn hơn 0!', 16, 1);
            RETURN;
        END

        -- 2. Kiểm tra tồn tại và tính hợp lệ của danh mục
        IF NOT EXISTS (SELECT 1 FROM KHO WHERE MaKho = @MaKho AND TrangThai = 1)
        BEGIN
            RAISERROR(N'Lỗi: Kho xuất không tồn tại hoặc đã ngừng hoạt động!', 16, 1);
            RETURN;
        END

        IF NOT EXISTS (SELECT 1 FROM CONG_TRINH WHERE MaCT = @MaCT)
        BEGIN
            RAISERROR(N'Lỗi: Công trình nhận không tồn tại!', 16, 1);
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

        IF EXISTS (SELECT 1 FROM PHIEU_XUAT WHERE MaPX = @MaPX)
        BEGIN
            RAISERROR(N'Lỗi: Mã phiếu xuất đã tồn tại!', 16, 1);
            RETURN;
        END

        -- Bắt đầu giao tác
        BEGIN TRANSACTION;

        -- 3. Kiểm tra tồn kho an toàn với UPDLOCK
        DECLARE @TonKho DECIMAL(18,2);
        SELECT @TonKho = SoLuongTon
        FROM TON_KHO WITH (UPDLOCK)
        WHERE MaKho = @MaKho AND MaVT = @MaVT;

        IF (@TonKho IS NULL OR @TonKho < @SoLuong)
        BEGIN
            RAISERROR(N'Lỗi: Số lượng tồn ở kho không đủ hoặc vật tư không có trong kho!', 16, 1);
            ROLLBACK TRANSACTION;
            RETURN;
        END

        -- 4. Ghi nhận phiếu xuất
        INSERT INTO PHIEU_XUAT (MaPX, MaKho, MaCT, NgayXuat, NguoiLap, GhiChu, TrangThai)
        VALUES (@MaPX, @MaKho, @MaCT, ISNULL(@NgayXuat, GETDATE()), @NguoiLap, @GhiChu, @TrangThai);

        -- 5. Ghi nhận chi tiết phiếu xuất
        INSERT INTO CT_PHIEU_XUAT (MaPX, MaVT, SoLuong)
        VALUES (@MaPX, @MaVT, @SoLuong);

        -- 6. Cập nhật giảm tồn kho
        UPDATE TON_KHO
        SET SoLuongTon = SoLuongTon - @SoLuong
        WHERE MaKho = @MaKho AND MaVT = @MaVT;

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
