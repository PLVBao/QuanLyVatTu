USE QuanLyVatTuXayDung;
GO

-- Trigger chặn xóa vật tư nếu vẫn còn tồn kho
CREATE OR ALTER TRIGGER trg_VatTu_NgauXoa
ON VAT_TU
INSTEAD OF DELETE
AS
BEGIN
    SET NOCOUNT ON;

    -- Kiểm tra nếu vật tư yêu cầu xóa vẫn còn số lượng tồn > 0 tại bất kỳ kho nào
    IF EXISTS (
        SELECT 1 
        FROM TON_KHO tk
        JOIN deleted d ON tk.MaVT = d.MaVT
        WHERE tk.SoLuongTon > 0
    )
    BEGIN
        RAISERROR (N'Lỗi nghiệp vụ: Không thể xóa vật tư vì vẫn còn số lượng tồn trong kho!', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END;

    -- Nếu tồn kho bằng 0 thì cho phép xóa mềm (chuyển trạng thái sang ngừng hoạt động)
    UPDATE VAT_TU
    SET TrangThai = 0
    WHERE MaVT IN (SELECT MaVT FROM deleted);

    PRINT N'Đã cập nhật trạng thái vật tư sang ngừng hoạt động thành công.';
END;
GO
