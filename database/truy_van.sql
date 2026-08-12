USE QuanLyVatTuXayDung;
GO

--EXEC sp_ChuyenKho 
--    @MaPCK = 'PCK03', 
--    @MaKhoNguon = 'KHO01', 
--    @MaKhoDich = 'KHO01',
--    @MaVT = 'VT01', 
--    @SoLuongChuyen = 5, 
--    @NguoiLap = 'TK02';

--EXEC sp_ChuyenKho 
--	@MaPCK = 'PCK_TEST2',
--	@MaKhoNguon = 'KHO01',
--	@MaKhoDich = 'KHO02', 
--	@MaVT = 'VT01',
--	@SoLuongChuyen = -10, 
--	@NguoiLap = 'TK02';

--EXEC sp_ChuyenKho 
--    @MaPCK = 'PCK02', 
--    @MaKhoNguon = 'KHO01', 
--    @MaKhoDich = 'KHO02', 
--    @MaVT = 'VT01', 
--    @SoLuongChuyen = 20, 
--    @NguoiLap = 'TK02';


--SELECT * FROM TON_KHO WHERE MaVT = 'VT01';
--EXEC sp_ChuyenKho 
--    @MaPCK = 'PCK_TC2', 
--    @MaKhoNguon = 'KHO01', 
--    @MaKhoDich = 'KHO02', 
--    @MaVT = 'VT01', 
--    @SoLuongChuyen = 20, 
--    @NguoiLap = 'TK02';	
--SELECT * FROM TON_KHO WHERE MaVT = 'VT01';
--SELECT * FROM PHIEU_CHUYEN_KHO WHERE MaPCK = 'PCK_TC2';
--SELECT * FROM CT_CHUYEN_KHO WHERE MaPCK = 'PCK_TC2';
