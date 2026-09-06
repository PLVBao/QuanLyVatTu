USE QuanLyVatTuXayDung;
GO

-- Cách chạy:
-- Lưu ý: Không chạy toàn bộ file cùng lúc.
-- 1. Reset dữ liệu trước khi chạy (chạy reset_data.sql).
-- 2. Mở 2 tab Query trong SSMS.
-- 3. Chạy Tab 1 trước, sau đó chuyển sang Tab 2 bấm chạy ngay lập tức.
-- 4. Kiểm tra số tồn

-- ==========================================
-- PHẦN 1: MÔ PHỎNG LỖI NON-REPEATABLE READ (READ COMMITTED)
-- ==========================================

-- Tab 1: SESSION 1
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

BEGIN TRANSACTION;

SELECT MaKho, MaVT, SoLuongTon
FROM TON_KHO
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';

WAITFOR DELAY '00:00:08';

SELECT MaKho, MaVT, SoLuongTon
FROM TON_KHO
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';

COMMIT TRANSACTION;
PRINT N'Session 1 hoàn tất';

-- SESSION 2
BEGIN TRANSACTION;

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon + 100
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';

COMMIT TRANSACTION;
PRINT N'Session 2 hoàn tất';

-- ==========================================
-- PHẦN 2: KHẮC PHỤC BẰNG REPEATABLE READ
-- ==========================================

-- SESSION 1
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

BEGIN TRANSACTION;

SELECT MaKho, MaVT, SoLuongTon
FROM TON_KHO
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';

WAITFOR DELAY '00:00:08';

SELECT MaKho, MaVT, SoLuongTon
FROM TON_KHO
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';

COMMIT TRANSACTION;
PRINT N'Session 1 hoàn tất';

-- SESSION 2
BEGIN TRANSACTION;

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon + 100
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';

COMMIT TRANSACTION;
PRINT N'Session 2 hoàn tất';
