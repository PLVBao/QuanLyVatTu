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
    BEGIN TRY
        BEGIN TRANSACTION;
        DECLARE @SoLuongTruoc DECIMAL(18,2);
        
		-- LƯU SỐ LƯỢNG TRƯỚC ĐIỀU CHỈNH
        SELECT @SoLuongTruoc = SoLuongTon
        FROM TON_KHO
        WHERE MaKho = @MaKho AND MaVT = @MaVT;

        -- Nếu vật tư chưa từng có trong kho
        IF @SoLuongTruoc IS NULL
        BEGIN
            RAISERROR(N'Lỗi: Không tìm thấy vật tư này trong kho!', 16, 1);
        END

        -- Nếu số lượng không thay đổi
        IF @SoLuongTruoc = @SoLuongSau
        BEGIN
            RAISERROR(N'Lỗi: Số lượng sau điều chỉnh trùng khớp với hiện tại, không cần điều chỉnh!', 16, 1);
        END

        -- CẬP NHẬT SỐ LƯỢNG SAU ĐIỀU CHỈNH VÀO TỒN KHO
        UPDATE TON_KHO
        SET SoLuongTon = @SoLuongSau
        WHERE MaKho = @MaKho AND MaVT = @MaVT;


        -- LẬP PHIẾU ĐIỀU CHỈNH
        -- Thêm vào bảng PHIEU_DIEU_CHINH
        INSERT INTO PHIEU_DIEU_CHINH (MaPDC, MaKho, NgayDieuChinh, NguoiLap, LyDo, TrangThai)
        VALUES (@MaPDC, @MaKho, GETDATE(), @NguoiLap, @LyDo, 'HOAN_THANH');

        INSERT INTO CT_DIEU_CHINH (MaPDC, MaVT, SoLuongTruoc, SoLuongSau)
        VALUES (@MaPDC, @MaVT, @SoLuongTruoc, @SoLuongSau);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END;
