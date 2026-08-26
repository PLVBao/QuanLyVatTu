USE QuanLyVatTuXayDung;
GO

-- Cách ch?y:
-- L?u ý: Không ch?y toàn b? file cùng lúc.
-- 1. Reset d? li?u v? 465.00 tr??c khi ch?y: UPDATE TON_KHO SET SoLuongTon = 465.00 WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
-- 2. M? 2 tab Query trong SSMS.
-- 3. Ch?y Tab 1 tr??c, sau ?ó chuy?n sang Tab 2 b?m ch?y ngay l?p t?c.
-- 4. Ki?m tra s? t?n: SELECT MaKho, MaVT, SoLuongTon FROM TON_KHO WHERE MaKho = 'KHO01' AND MaVT = 'VT01';


-- ==========================================
-- PH?N 1: MÔ PH?NG L?I LOST UPDATE
-- ==========================================

-- Tab 1: SESSION 1 (Xu?t 15 cây - Gi? tr? 8 giây)
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
PRINT N'Session 1 (L?i) hoàn t?t!';


-- Tab 2: SESSION 2 (Nh?p 50 cây - Ch?y ?è lên Session 1)
BEGIN TRANSACTION;
    DECLARE @ton DECIMAL(18,2);
    SELECT @ton = SoLuongTon 
    FROM TON_KHO 
    WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
    
    UPDATE TON_KHO 
    SET SoLuongTon = @ton + 50 
    WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
COMMIT TRANSACTION;
PRINT N'Session 2 (L?i) hoàn t?t!';


-- ==========================================
-- PH?N 2: KH?C PH?C L?I B?NG UPDLOCK
-- ==========================================

-- Tab 1: SESSION 1 (Khóa c?p nh?t UPDLOCK)
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
PRINT N'Session 1 (UPDLOCK) hoàn t?t!';


-- Tab 2: SESSION 2 (B? ch?n ch? Session 1 hoàn t?t)
BEGIN TRANSACTION;
    DECLARE @ton DECIMAL(18,2);
    SELECT @ton = SoLuongTon 
    FROM TON_KHO WITH (UPDLOCK) 
    WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
    
    UPDATE TON_KHO 
    SET SoLuongTon = @ton + 50 
    WHERE MaKho = 'KHO01' AND MaVT = 'VT01';
COMMIT TRANSACTION;
PRINT N'Session 2 (UPDLOCK) hoàn t?t!';