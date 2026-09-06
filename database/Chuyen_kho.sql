CREAT OR ALTER   PROCEDURE sp_ChuyenKho
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
        -- Kiểm tra điều kiện số lượng
        IF @SoLuongChuyen <= 0
        BEGIN
            RAISERROR(N'Lỗi: Số lượng chuyển phải lớn hơn 0!', 16, 1);
            RETURN;
        END

        -- Kiểm tra kho nguồn và kho đích
        IF @MaKhoNguon = @MaKhoDich
        BEGIN
            RAISERROR(N'Lỗi: Kho nguồn và kho đích không được trùng nhau!', 16, 1);
            RETURN;
        END

        -- Kiểm tra kho tồn tại
        IF NOT EXISTS (SELECT 1 FROM KHO WHERE MaKho = @MaKhoNguon)
        BEGIN
            RAISERROR(N'Lỗi: Kho nguồn không tồn tại!', 16, 1);
            RETURN;
        END

        IF NOT EXISTS (SELECT 1 FROM KHO WHERE MaKho = @MaKhoDich)
        BEGIN
            RAISERROR(N'Lỗi: Kho đích không tồn tại!', 16, 1);
            RETURN;
        END

        -- Kiểm tra vật tư tồn tại
        IF NOT EXISTS (SELECT 1 FROM VAT_TU WHERE MaVT = @MaVT)
        BEGIN
            RAISERROR(N'Lỗi: Vật tư không tồn tại!', 16, 1);
            RETURN;
        END

        -- Kiểm tra mã phiếu chuyển đã tồn tại
        IF EXISTS (SELECT 1 FROM PHIEU_CHUYEN_KHO WHERE MaPCK = @MaPCK)
        BEGIN
            RAISERROR(N'Lỗi: Mã phiếu chuyển kho đã tồn tại!', 16, 1);
            RETURN;
        END

        DECLARE @TonKhoNguon DECIMAL(18,2);

        -- Bắt đầu giao tác
        BEGIN TRANSACTION;

        -- Kiểm tra tồn kho nguồn
        SELECT @TonKhoNguon = SoLuongTon
        FROM TON_KHO
        WHERE MaKho = @MaKhoNguon AND MaVT = @MaVT;

        IF @TonKhoNguon IS NULL OR @TonKhoNguon < @SoLuongChuyen
        BEGIN
            RAISERROR(N'Lỗi: Số lượng tồn ở kho nguồn không đủ hoặc không tồn tại!', 16, 1);
            ROLLBACK TRANSACTION;
            RETURN;
        END

        -- 1. Insert phiếu chuyển kho
        INSERT INTO PHIEU_CHUYEN_KHO (MaPCK, MaKhoNguon, MaKhoDich, NgayChuyen, NguoiLap, TrangThai)
        VALUES (@MaPCK, @MaKhoNguon, @MaKhoDich, GETDATE(), @NguoiLap, N'HOAN_THANH');

        -- 2. Insert chi tiết chuyển kho
        INSERT INTO CT_CHUYEN_KHO (MaPCK, MaVT, SoLuong)
        VALUES (@MaPCK, @MaVT, @SoLuongChuyen);

        -- 3. Trừ tồn kho nguồn
        UPDATE TON_KHO
        SET SoLuongTon = SoLuongTon - @SoLuongChuyen
        WHERE MaKho = @MaKhoNguon AND MaVT = @MaVT;

        -- 4. Cộng tồn kho đích
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

        -- Commit giao tác
        COMMIT TRANSACTION;
        PRINT N'Chuyển kho thành công!';

    END TRY

    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        DECLARE @ErrorMessage NVARCHAR(4000);
        SET @ErrorMessage = ERROR_MESSAGE();

        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END;
