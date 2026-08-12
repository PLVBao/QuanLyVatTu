USE QuanLyVatTuXayDung;
GO

EXEC sp_ChuyenKho 
    @MaPCK = 'PCK03', 
    @MaKhoNguon = 'KHO01', 
    @MaKhoDich = 'KHO01', -- Lỗi: Kho nguồn và kho đích trùng nhau
    @MaVT = 'VT01', 
    @SoLuongChuyen = 5, 
    @NguoiLap = 'TK02';


--EXEC sp_ChuyenKho 
--    @MaPCK = 'PCK02', 
--    @MaKhoNguon = 'KHO01', 
--    @MaKhoDich = 'KHO02', 
--    @MaVT = 'VT01', 
--    @SoLuongChuyen = 20, 
--    @NguoiLap = 'TK02';

--SELECT * FROM TON_KHO WHERE MaVT = 'VT01';