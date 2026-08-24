use QuanLyVatTuXayDung;
go

delete from TON_KHO;

insert into TON_KHO (MaKho, MaVT, SoLuongTon)
values
    ('KHO01', 'VT01', 465),
    ('KHO01', 'VT02', 200),
    ('KHO02', 'VT01', 10),
    ('KHO02', 'VT03', 1000),
    ('KHO02', 'VT04', 800);

print n'?ã reset d? li?u b?ng TON_KHO v? tr?ng thái ban ??u!';