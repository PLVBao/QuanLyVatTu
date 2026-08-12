CREATE OR ALTER PROC sp_ChuyenKho
    @MaPCK VARCHAR(10),
    @MaKhoNguon VARCHAR(10),
    @MaKhoDich VARCHAR(10),
    @MaVT VARCHAR(10),
    @SoLuongChuyen DECIMAL(18,2),
    @NguoiLap VARCHAR(10)
AS
BEGIN
	
	IF (@SoLuongChuyen <= 0)
    BEGIN
        PRINT N'Lỗi: Số lượng chuyển phải lớn hơn 0!';
        RETURN;
    END

    IF (@MaKhoNguon = @MaKhoDich)
    BEGIN
        PRINT N'Lỗi: Kho nguồn và kho đích không được trùng nhau!';
        RETURN;
    END


    DECLARE @TonKhoNguon DECIMAL(18,2);
    
    BEGIN TRANSACTION;

	-- Kiểm tra tồn kho của kho nguồn có đủ để chuyển không
    SELECT @TonKhoNguon = SoLuongTon 
    FROM TON_KHO 
    WHERE MaKho = @MaKhoNguon AND MaVT = @MaVT;

    IF (@TonKhoNguon IS NULL OR @TonKhoNguon < @SoLuongChuyen)
    BEGIN
        PRINT N'Lỗi: Số lượng tồn ở kho nguồn không đủ hoặc không tồn tại!';
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Thêm dữ liệu vào bảng PHIEU_CHUYEN_KHO
    INSERT INTO PHIEU_CHUYEN_KHO (MaPCK, MaKhoNguon, MaKhoDich, NgayChuyen, NguoiLap, TrangThai)
    VALUES (@MaPCK, @MaKhoNguon, @MaKhoDich, GETDATE(), @NguoiLap, 'HOAN_THANH');
    
    IF (@@error <> 0) -- Có lỗi xảy ra khi Insert phiếu
    BEGIN
        PRINT N'Lỗi khi tạo phiếu chuyển kho!';
        ROLLBACK TRAN;
        RETURN;
    END

    -- Thêm dữ liệu vào bảng CT_CHUYEN_KHO
    INSERT INTO CT_CHUYEN_KHO (MaPCK, MaVT, SoLuong)
    VALUES (@MaPCK, @MaVT, @SoLuongChuyen);
    
    IF (@@error <> 0) -- Có lỗi xảy ra khi Insert chi tiết
    BEGIN
        PRINT N'Lỗi khi tạo chi tiết chuyển kho!';
        ROLLBACK TRAN;
        RETURN;
    END

    -- Cập nhật giảm số lượng ở KHO NGUỒN
    UPDATE TON_KHO 
    SET SoLuongTon = SoLuongTon - @SoLuongChuyen 
    WHERE MaKho = @MaKhoNguon AND MaVT = @MaVT;
    
    IF (@@error <> 0) -- Có lỗi xảy ra khi trừ kho nguồn
    BEGIN
        PRINT N'Lỗi khi trừ số lượng ở kho nguồn!';
        ROLLBACK TRAN;
        RETURN;
    END

    -- Cập nhật tăng số lượng ở KHO ĐÍCH
    IF EXISTS (SELECT * FROM TON_KHO WHERE MaKho = @MaKhoDich AND MaVT = @MaVT)
    BEGIN
        UPDATE TON_KHO 
        SET SoLuongTon = SoLuongTon + @SoLuongChuyen 
        WHERE MaKho = @MaKhoDich AND MaVT = @MaVT;
        
        IF (@@error <> 0) -- Có lỗi xảy ra khi cộng kho đích
        BEGIN
            PRINT N'Lỗi khi cộng số lượng ở kho đích!';
            ROLLBACK TRAN;
            RETURN;
        END
    END
    ELSE
    BEGIN
        -- Nếu kho đích chưa có vật tư này thì Insert dòng mới
        INSERT INTO TON_KHO (MaKho, MaVT, SoLuongTon) 
        VALUES (@MaKhoDich, @MaVT, @SoLuongChuyen);
        
        IF (@@error <> 0) -- Có lỗi xảy ra khi thêm mới tồn kho
        BEGIN
            PRINT N'Lỗi khi thêm mới vật tư vào kho đích!';
            ROLLBACK TRAN;
            RETURN;
        END
    END

    COMMIT TRANSACTION;
    PRINT N'Thành công: Đã chuyển kho hoàn tất!';
END;