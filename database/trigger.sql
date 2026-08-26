USE QuanLyVatTuXayDung;
GO

-- Trigger ch?n xóa v?t t? n?u v?n còn t?n kho
CREATE OR ALTER TRIGGER trg_VatTu_NgauXoa
ON VAT_TU
INSTEAD OF DELETE
AS
BEGIN
    SET NOCOUNT ON;

    -- Ki?m tra n?u v?t t? yêu c?u xóa v?n còn s? l??ng t?n > 0 t?i b?t k? kho nào
    IF EXISTS (
        SELECT 1 
        FROM TON_KHO tk
        JOIN deleted d ON tk.MaVT = d.MaVT
        WHERE tk.SoLuongTon > 0
    )
    BEGIN
        RAISERROR (N'L?i nghi?p v?: Không th? xóa v?t t? vì v?n còn s? l??ng t?n trong kho!', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END;

    -- N?u t?n kho b?ng 0 thì cho phép xóa m?m (chuy?n tr?ng thái sang ng?ng ho?t ??ng)
    UPDATE VAT_TU
    SET TrangThai = 0
    WHERE MaVT IN (SELECT MaVT FROM deleted);

    PRINT N'?ã c?p nh?t tr?ng thái v?t t? sang ng?ng ho?t ??ng thành công.';
END;
GO