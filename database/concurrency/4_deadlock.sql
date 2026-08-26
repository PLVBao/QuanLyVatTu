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

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon - 5
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';

WAITFOR DELAY '00:00:05';

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon + 5
WHERE MaKho = 'KHO02' AND MaVT = 'VT01';

COMMIT TRANSACTION;

PRINT N'Session 1 đã chuyển kho thành công!';


-- SESSION 2: Chuyển VT01 từ KHO02 sang KHO01

BEGIN TRANSACTION;

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon - 5
WHERE MaKho = 'KHO02' AND MaVT = 'VT01';

WAITFOR DELAY '00:00:05';

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon + 5
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';

COMMIT TRANSACTION;

PRINT N'Session 2 đã chuyển kho thành công!';


-- Kết quả mong đợi:
-- Một trong hai Session bị lỗi Msg 1205 - Deadlock Victim.
-- Session còn lại COMMIT thành công.


-- GIẢI PHÁP: Sắp xếp thứ tự khóa (Lock Ordering)
-- Luôn khóa KHO01 trước KHO02 để tránh khóa chéo.


-- SESSION 1: Chuyển VT01 từ KHO01 sang KHO02

BEGIN TRANSACTION;

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon - 5
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon + 5
WHERE MaKho = 'KHO02' AND MaVT = 'VT01';

COMMIT TRANSACTION;

PRINT N'Session 1 đã chuyển kho thành công với Lock Ordering!';


-- SESSION 2: Chuyển VT01 từ KHO02 sang KHO01
-- Vẫn khóa KHO01 trước KHO02

BEGIN TRANSACTION;

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon + 5
WHERE MaKho = 'KHO01' AND MaVT = 'VT01';

UPDATE TON_KHO
SET SoLuongTon = SoLuongTon - 5
WHERE MaKho = 'KHO02' AND MaVT = 'VT01';

COMMIT TRANSACTION;

PRINT N'Session 2 đã chuyển kho thành công với Lock Ordering!';
