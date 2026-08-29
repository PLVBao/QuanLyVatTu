USE QuanLyVatTuXayDung;
GO

-- Cách chạy:
-- Lưu ý: Không chạy toàn bộ file cùng lúc.
-- 1. Chạy reset_data.sql trước để đưa TON_KHO về trạng thái ban đầu.
-- 2. Mở 2 tab Query trong SSMS.
-- 3. Tab 1 chạy SESSION 1 trước, chờ lệnh WAITFOR.
-- 4. Trong lúc đó, Tab 2 chạy SESSION 2 ngay.
-- 5. Hai giao tác sẽ khóa chéo nhau -> một trong hai bị lỗi Msg 1205 Deadlock Victim.
-- 6. Sau khi test xong, chạy lại reset_data.sql.


-- SESSION 1: Chuyển VT01 từ KHO01 sang KHO02
BEGIN TRANSACTION;

PRINT N'[SESSION 1] Bat dau chuyen kho: KHO01 -> KHO02, VT01, SL = 5';

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon - 5
WHERE MaKho = 'KHO01'
  AND MaVT = 'VT01';

PRINT N'[SESSION 1] Da tru kho nguon KHO01. Dang giu khoa...';
WAITFOR DELAY '00:00:05';
PRINT N'[SESSION 1] Chuan bi cong kho dich KHO02...';

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon + 5
WHERE MaKho = 'KHO02'
  AND MaVT = 'VT01';

PRINT N'[SESSION 1] Thanh cong, tien hanh COMMIT.';

COMMIT TRANSACTION;

-- SESSION 2: Chuyển VT01 từ KHO02 sang KHO01
BEGIN TRANSACTION;

PRINT N'[SESSION 2] Bat dau chuyen kho: KHO02 -> KHO01, VT01, SL = 2';

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon - 2
WHERE MaKho = 'KHO02'
  AND MaVT = 'VT01';

PRINT N'[SESSION 2] Da tru kho nguon KHO02. Dang giu khoa...';
WAITFOR DELAY '00:00:05';
PRINT N'[SESSION 2] Chuan bi cong kho dich KHO01...';

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon + 2
WHERE MaKho = 'KHO01'
  AND MaVT = 'VT01';

PRINT N'[SESSION 2] Thanh cong, tien hanh COMMIT.';

COMMIT TRANSACTION;

-- Kết quả mong đợi:
-- Một trong hai Session bị lỗi Msg 1205 - Deadlock Victim.
-- Session còn lại COMMIT thành công.


-- GIẢI PHÁP: Sắp xếp thứ tự khóa (Lock Ordering)
-- Luôn khóa KHO01 trước KHO02 để tránh khóa chéo.


-- SESSION 1: Chuyển VT01 từ KHO01 sang KHO02
BEGIN TRANSACTION;

PRINT N'[LOCK ORDERING - SESSION 1] Bat dau chuyen KHO01 -> KHO02';

-- Luôn khóa KHO01 trước
UPDATE TON_KHO
SET SoLuongTon = SoLuongTon - 5
WHERE MaKho = 'KHO01'
  AND MaVT = 'VT01';

PRINT N'[SESSION 1] Da khoa KHO01. Dang giu khoa 5 giay...';
WAITFOR DELAY '00:00:05';

-- Sau đó mới khóa KHO02
UPDATE TON_KHO
SET SoLuongTon = SoLuongTon + 5
WHERE MaKho = 'KHO02'
  AND MaVT = 'VT01';

PRINT N'[SESSION 1] Da cap nhat KHO02.';
PRINT N'[SESSION 1] COMMIT thanh cong.';

COMMIT TRANSACTION;

-- SESSION 2: Chuyển VT01 từ KHO02 sang KHO01
BEGIN TRANSACTION;

PRINT N'[LOCK ORDERING - SESSION 2] Bat dau chuyen KHO02 -> KHO01';

-- Dù chuyển từ KHO02 về KHO01,
-- vẫn phải khóa KHO01 trước
UPDATE TON_KHO
SET SoLuongTon = SoLuongTon + 2
WHERE MaKho = 'KHO01'
  AND MaVT = 'VT01';

PRINT N'[SESSION 2] Da khoa KHO01. Dang giu khoa 5 giay...';
WAITFOR DELAY '00:00:05';

-- Sau đó mới khóa KHO02
UPDATE TON_KHO
SET SoLuongTon = SoLuongTon - 2
WHERE MaKho = 'KHO02'
  AND MaVT = 'VT01';

PRINT N'[SESSION 2] Da cap nhat KHO02.';
PRINT N'[SESSION 2] COMMIT thanh cong.';

COMMIT TRANSACTION;
