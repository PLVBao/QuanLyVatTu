USE QuanLyVatTuXayDung;
GO

CREATE OR ALTER PROCEDURE sp_DieuChinhKho
    @MaPDC VARCHAR(10),
    @MaKho VARCHAR(10),
    @MaVT VARCHAR(10),
    @SoLuongSau DECIMAL(18,2),
    @NguoiLap VARCHAR(10),
    @LyDo NVARCHAR(500)
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        IF @SoLuongSau < 0
        BEGIN
            RAISERROR(N'Lỗi: Số lượng sau điều chỉnh không được nhỏ hơn 0!', 16, 1);
            RETURN;
        END

        IF LEN(LTRIM(RTRIM(ISNULL(@LyDo, '')))) = 0
        BEGIN
            RAISERROR(N'Lỗi: Lý do điều chỉnh không được để trống!', 16, 1);
            RETURN;
        END

        IF NOT EXISTS (SELECT 1 FROM TAI_KHOAN WHERE MaTK = @NguoiLap AND TrangThai = 1)
        BEGIN
            RAISERROR(N'Lỗi: Người lập không tồn tại hoặc bị khóa!', 16, 1);
            RETURN;
        END

        IF EXISTS (SELECT 1 FROM PHIEU_DIEU_CHINH WHERE MaPDC = @MaPDC)
        BEGIN
            RAISERROR(N'Lỗi: Mã phiếu điều chỉnh đã tồn tại!', 16, 1);
            RETURN;
        END

        BEGIN TRANSACTION;
            DECLARE @SoLuongTruoc DECIMAL(18,2);
            
            -- Đọc tồn kho có khóa UPDLOCK
            SELECT @SoLuongTruoc = SoLuongTon
            FROM TON_KHO WITH (UPDLOCK)
            WHERE MaKho = @MaKho AND MaVT = @MaVT;

            IF @SoLuongTruoc IS NULL
            BEGIN
                RAISERROR(N'Lỗi: Không tìm thấy vật tư này trong kho để điều chỉnh!', 16, 1);
                ROLLBACK TRANSACTION;
                RETURN;
            END

            IF @SoLuongTruoc = @SoLuongSau
            BEGIN
                RAISERROR(N'Lỗi: Số lượng sau điều chỉnh trùng khớp với hiện tại, không cần điều chỉnh!', 16, 1);
                ROLLBACK TRANSACTION;
                RETURN;
            END

            -- Cập nhật tồn kho
            UPDATE TON_KHO
            SET SoLuongTon = @SoLuongSau
            WHERE MaKho = @MaKho AND MaVT = @MaVT;

            -- Lập phiếu điều chỉnh
            INSERT INTO PHIEU_DIEU_CHINH (MaPDC, MaKho, NgayDieuChinh, NguoiLap, LyDo, TrangThai)
            VALUES (@MaPDC, @MaKho, GETDATE(), @NguoiLap, @LyDo, 'HOAN_THANH');

            INSERT INTO CT_DIEU_CHINH (MaPDC, MaVT, SoLuongTruoc, SoLuongSau)
            VALUES (@MaPDC, @MaVT, @SoLuongTruoc, @SoLuongSau);

        COMMIT TRANSACTION;
        PRINT N'Điều chỉnh kho thành công!';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END;
GO
