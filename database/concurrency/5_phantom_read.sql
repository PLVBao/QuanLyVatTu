-- Cách chạy lỗi
-- TAB 1: SESSION 1 (Chạy khối lệnh này trước, nó sẽ bị delay 10s chờ Tab 2)

USE QuanLyVatTuXayDung;
GO
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
BEGIN TRAN;

    -- Lần 1: Quản lý đếm xem Kho 02 đang chứa bao nhiêu LOẠI vật tư
    SELECT COUNT(*) AS SoLoaiVatTu_Lan1
    FROM TON_KHO WHERE MaKho = 'KHO02';
    
    PRINT N'Đang chờ 10 giây để Session 2 thêm vật tư mới...';
    WAITFOR DELAY '00:00:10'; 
    
    -- Lần 2: Quản lý đếm lại, tự nhiên thấy số lượng tăng lên 1 (Bóng ma xuất hiện)
    SELECT COUNT(*) AS SoLoaiVatTu_Lan2_BongMa
    FROM TON_KHO WHERE MaKho = 'KHO02';

COMMIT TRAN;

-- TAB 2: SESSION 2 (Bôi đen và chạy ngay lập tức khi Tab 1 đang đếm giờ)

USE QuanLyVatTuXayDung;
GO
BEGIN TRAN;
    -- Nhân viên bất ngờ nhập thêm 1 loại vật tư mới (VT02) vào Kho 02
    INSERT INTO TON_KHO (MaKho, MaVT, SoLuongTon)
    VALUES ('KHO02', 'VT02', 50);
COMMIT TRAN;



-- Cách giải quyết
-- TAB 1: SESSION 1 (Chạy khối lệnh này trước, nó sẽ bị delay 10s chờ Tab 2)
USE QuanLyVatTuXayDung;
GO
-- NÂNG MỨC CÔ LẬP LÊN CAO NHẤT ĐỂ CHẶN INSERT BÓNG MA
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
BEGIN TRAN;

    SELECT COUNT(*) AS SoLoaiVatTu_Lan1
    FROM TON_KHO WHERE MaKho = 'KHO02';
    
    WAITFOR DELAY '00:00:10'; 
    
    SELECT COUNT(*) AS SoLoaiVatTu_Lan2_DaKhacPhuc
    FROM TON_KHO WHERE MaKho = 'KHO02';

COMMIT TRAN;


-- TAB 2: SESSION 2 (Bôi đen và chạy ngay lập tức khi Tab 1 đang đếm giờ)

USE QuanLyVatTuXayDung;
GO
BEGIN TRAN;
    INSERT INTO TON_KHO (MaKho, MaVT, SoLuongTon)
    VALUES ('KHO02', 'VT02', 50);
COMMIT TRAN;