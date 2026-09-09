USE QuanLyVatTuXayDung;
GO

CREATE OR ALTER PROCEDURE sp_ChuyenKho
    @MaPCK VARCHAR(10),
    @MaKhoNguon VARCHAR(10),
    @MaKhoDich VARCHAR(10),
    @MaVT VARCHAR(10),
    @SoLuongChuyen DECIMAL(18,2),
    @NguoiLap VARCHAR(10)
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        -- 1. Kiểm tra số lượng chuyển
        IF @SoLuongChuyen <= 0
        BEGIN
            RAISERROR(N'Lỗi: Số lượng chuyển phải lớn hơn 0!', 16, 1);
            RETURN;
        END

        -- 2. Kiểm tra kho nguồn và kho đích
        IF @MaKhoNguon = @MaKhoDich
        BEGIN
            RAISERROR(N'Lỗi: Kho nguồn và kho đích không được trùng nhau!', 16, 1);
            RETURN;
        END

        -- 3. Kiểm tra kho tồn tại và đang hoạt động
        IF NOT EXISTS (SELECT 1 FROM KHO WHERE MaKho = @MaKhoNguon AND TrangThai = 1)
        BEGIN
            RAISERROR(N'Lỗi: Kho nguồn không tồn tại hoặc đã ngừng hoạt động!', 16, 1);
            RETURN;
        END

        IF NOT EXISTS (SELECT 1 FROM KHO WHERE MaKho = @MaKhoDich AND TrangThai = 1)
        BEGIN
            RAISERROR(N'Lỗi: Kho đích không tồn tại hoặc đã ngừng hoạt động!', 16, 1);
            RETURN;
        END

        -- 4. Kiểm tra vật tư tồn tại và đang hoạt động
        IF NOT EXISTS (SELECT 1 FROM VAT_TU WHERE MaVT = @MaVT AND TrangThai = 1)
        BEGIN
            RAISERROR(N'Lỗi: Vật tư không tồn tại hoặc đã ngừng sử dụng!', 16, 1);
            RETURN;
        END

        -- 5. Kiểm tra người lập
        IF NOT EXISTS (SELECT 1 FROM TAI_KHOAN WHERE MaTK = @NguoiLap AND TrangThai = 1)
        BEGIN
            RAISERROR(N'Lỗi: Tài khoản người lập không tồn tại hoặc bị khóa!', 16, 1);
            RETURN;
        END

        -- 6. Kiểm tra mã phiếu trùng lặp
        IF EXISTS (SELECT 1 FROM PHIEU_CHUYEN_KHO WHERE MaPCK = @MaPCK)
        BEGIN
            RAISERROR(N'Lỗi: Mã phiếu chuyển kho đã tồn tại!', 16, 1);
            RETURN;
        END

        DECLARE @TonKhoNguon DECIMAL(18,2);

        -- Bắt đầu giao tác
        BEGIN TRANSACTION;

        -- Khóa cập nhật (UPDLOCK) trên kho nguồn để đảm bảo toàn vẹn
        SELECT @TonKhoNguon = SoLuongTon
        FROM TON_KHO WITH (UPDLOCK)
        WHERE MaKho = @MaKhoNguon AND MaVT = @MaVT;

        IF @TonKhoNguon IS NULL OR @TonKhoNguon < @SoLuongChuyen
        BEGIN
            RAISERROR(N'Lỗi: Số lượng tồn ở kho nguồn không đủ hoặc vật tư chưa có trong kho!', 16, 1);
            ROLLBACK TRANSACTION;
            RETURN;
        END

        -- Thêm thông tin phiếu chuyển
        INSERT INTO PHIEU_CHUYEN_KHO (MaPCK, MaKhoNguon, MaKhoDich, NgayChuyen, NguoiLap, TrangThai)
        VALUES (@MaPCK, @MaKhoNguon, @MaKhoDich, GETDATE(), @NguoiLap, 'HOAN_THANH');

        -- Thêm chi tiết chuyển kho
        INSERT INTO CT_CHUYEN_KHO (MaPCK, MaVT, SoLuong)
        VALUES (@MaPCK, @MaVT, @SoLuongChuyen);

        -- Trừ tồn kho nguồn
        UPDATE TON_KHO
        SET SoLuongTon = SoLuongTon - @SoLuongChuyen
        WHERE MaKho = @MaKhoNguon AND MaVT = @MaVT;

        -- Cộng tồn kho đích (tạo mới nếu kho đích chưa từng có mặt hàng này)
        IF EXISTS (SELECT 1 FROM TON_KHO WHERE MaKho = @MaKhoDich AND MaVT = @MaVT)
        BEGIN
            UPDATE TON_KHO
            SET SoLuongTon = SoLuongTon + @SoLuongChuyen
            WHERE MaKho = @MaKhoDich AND MaVT = @MaVT;
        END
        ELSE
        BEGIN
            INSERT INTO TON_KHO (MaKho, MaVT, SoLuongTon)
            VALUES (@MaKhoDich, @MaVT, @SoLuongChuyen);
        END

        COMMIT TRANSACTION;
        PRINT N'Chuyển kho thành công!';

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END;
GO
