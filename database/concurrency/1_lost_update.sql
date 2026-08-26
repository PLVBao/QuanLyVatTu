USE QuanLyVatTuXayDung;
GO

-- Cách chạy:
-- Lưu ý: Không chạy toàn bộ file cùng lúc.
-- 1. Reset dữ liệu về 465.00 trước khi chạy: UPDATE TON_KHO SET SoLuongTon = 465.00 WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
-- 2. Mở 2 tab Query trong SSMS.
-- 3. Chạy Tab 1 trước, sau đó chuyển sang Tab 2 bấm chạy ngay lập tức.
-- 4. Kiểm tra số tồn: SELECT MaKho, MaVT, SoLuongTon FROM TON_KHO WHERE MaKho = 'KHO01' AND MaVT = 'VT01';


-- ==========================================
-- PHẦN 1: MÔ PHỎNG LỖI LOST UPDATE
-- ==========================================

-- Tab 1: SESSION 1 (Xuất 15 cây - Giữ trễ 8 giây)
BEGIN TRANSACTION;
    DECLARE @ton DECIMAL(18,2);
    SELECT @ton = SoLuongTon 
    FROM TON_KHO 
    WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
    
    WAITFOR DELAY '00:00:08';
    
    UPDATE TON_KHO 
    SET SoLuongTon = @ton - 15 
    WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
COMMIT TRANSACTION;
PRINT N'Session 1 (Lỗi) hoàn tất!';


-- Tab 2: SESSION 2 (Nhập 50 cây - Chạy đè lên Session 1)
BEGIN TRANSACTION;
    DECLARE @ton DECIMAL(18,2);
    SELECT @ton = SoLuongTon 
    FROM TON_KHO 
    WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
    
    UPDATE TON_KHO 
    SET SoLuongTon = @ton + 50 
    WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
COMMIT TRANSACTION;
PRINT N'Session 2 (Lỗi) hoàn tất!';


-- ==========================================
-- PHẦN 2: KHẮC PHỤC LỖI BẰNG UPDLOCK
-- ==========================================

-- Tab 1: SESSION 1 (Khóa cập nhật UPDLOCK)
BEGIN TRANSACTION;
    DECLARE @ton DECIMAL(18,2);
    SELECT @ton = SoLuongTon 
    FROM TON_KHO WITH (UPDLOCK) 
    WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
    
    WAITFOR DELAY '00:00:08';
    
    UPDATE TON_KHO 
    SET SoLuongTon = @ton - 15 
    WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
COMMIT TRANSACTION;
PRINT N'Session 1 (UPDLOCK) hoàn tất!';


-- Tab 2: SESSION 2 (Bị chặn chờ Session 1 hoàn tất)
BEGIN TRANSACTION;
    DECLARE @ton DECIMAL(18,2);
    SELECT @ton = SoLuongTon 
    FROM TON_KHO WITH (UPDLOCK) 
    WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
    
    UPDATE TON_KHO 
    SET SoLuongTon = @ton + 50 
    WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
COMMIT TRANSACTION;
PRINT N'Session 2 (UPDLOCK) hoàn tất!';
