USE QuanLyVatTuXayDung;
GO

-- Cách chạy:
-- Lưu ý: Không chạy toàn bộ file cùng lúc.
-- 1. Mở 2 tab Query trong SSMS.
-- 2. Tab 1 chạy SESSION 1 trước, chờ lệnh WAITFOR.
-- 3. Trong lúc đó, Tab 2 chạy READ UNCOMMITTED để kiểm tra Dirty Read.
-- 4. Sau đó chạy READ COMMITTED ở Tab 2 để kiểm tra khắc phục.
-- UPDATE TON_KHO tạm thời trong Transaction, ROLLBACK nên dữ liệu không thay đổi.


-- SESSION 1: Tạo dữ liệu chưa COMMIT

BEGIN TRANSACTION;

UPDATE TON_KHO
SET SoLuongTon = 999.00
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';

WAITFOR DELAY '00:00:10';

ROLLBACK TRANSACTION;

PRINT N'Session 1 đã Rollback hoàn toàn dữ liệu!';


-- SESSION 2: Đọc dữ liệu chưa COMMIT bằng READ UNCOMMITTED

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SELECT MaKho, MaVT, SoLuongTon
FROM TON_KHO
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';


-- SESSION 2: Khắc phục Dirty Read bằng READ COMMITTED

SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

SELECT MaKho, MaVT, SoLuongTon
FROM TON_KHO
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';