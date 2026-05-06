import os
import django
import sys
from datetime import date, timedelta, datetime

# Cấu hình môi trường Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_dev')
django.setup()

from apps.authentication.models import TaiKhoan
from apps.staff.models import NhanVien
from apps.tables.models import Ban
from apps.menu.models import ThucDon
from apps.inventory.models import TonKho
from apps.promotions.models import KhuyenMai
import bcrypt

def hash_password(password):
    return password

def seed_data():
    print("Xóa dữ liệu cũ...")
    # Xóa theo thứ tự đúng (child trước, parent sau) để tránh lỗi PROTECT FK
    from apps.orders.models import HoaDon, ChiTietHoaDon
    from apps.customers.models import KhachHang
    ChiTietHoaDon.objects.all().delete()
    HoaDon.objects.all().delete()
    KhachHang.objects.all().delete()
    NhanVien.objects.all().delete()
    TaiKhoan.objects.all().delete()
    Ban.objects.all().delete()
    ThucDon.objects.all().delete()
    TonKho.objects.all().delete()
    KhuyenMai.objects.all().delete()

    print("1. Tạo Tài khoản và Nhân viên...")
    # Manager
    tk_ql = TaiKhoan.objects.create(
        ten_dang_nhap='admin', 
        mat_khau=hash_password('123456'), 
        ma_phan_quyen=TaiKhoan.PhanQuyen.QUAN_LY
    )
    NhanVien.objects.create(ho_ten='Nguyễn Quản Lý', sdt='0901234567', ma_tk=tk_ql)

    # 3 Employees
    for i in range(1, 4):
        tk_nv = TaiKhoan.objects.create(
            ten_dang_nhap=f'staff0{i}', 
            mat_khau=hash_password('123456'), 
            ma_phan_quyen=TaiKhoan.PhanQuyen.NHAN_VIEN
        )
        NhanVien.objects.create(ho_ten=f'Trần Nhân Viên {i}', sdt=f'090900000{i}', ma_tk=tk_nv)

    print("2. Tạo Bàn (10 Bàn)...")
    from django.db import connection
    # Reset AUTO_INCREMENT về 1
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE ban AUTO_INCREMENT = 1;")

    bang_data = [
        (1, 'Trong nhà'),
        (2, 'Trong nhà'),
        (3, 'Trong nhà'),
        (4, 'Trong nhà'),
        (5, 'Trong nhà'),
        (6, 'Ngoài trời'),
        (7, 'Ngoài trời'),
        (8, 'Ngoài trời'),
        (9, 'Ngoài trời'),
        (10, 'Ngoài trời'),
    ]
    for ma, khu_vuc in bang_data:
        Ban.objects.create(ma_ban=ma, ten_khu_vuc=khu_vuc)

    print("3. Tạo Thực Đơn (15 Món)...")
    menu_items = [
        # Coffee
        ('Cà phê Đen', 'Coffee', 25000, 'https://images.unsplash.com/photo-1559496417-e7f25cb247f3?q=80&w=500&auto=format&fit=crop'), 
        ('Cà phê Sữa', 'Coffee', 30000, 'https://images.unsplash.com/photo-1541167760496-162955ed8a9f?q=80&w=500&auto=format&fit=crop'), 
        ('Bạc xỉu', 'Coffee', 35000, 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?q=80&w=500&auto=format&fit=crop'), 
        ('Espresso', 'Coffee', 40000, 'https://images.unsplash.com/photo-1510591509098-f4fdc6d0ff04?q=80&w=500&auto=format&fit=crop'), 
        ('Americano', 'Coffee', 40000, 'https://images.unsplash.com/photo-1551030173-122aabc4489c?q=80&w=500&auto=format&fit=crop'),
        # Tea
        ('Trà Đào Cam Sả', 'Tea', 45000, 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?q=80&w=500&auto=format&fit=crop'), 
        ('Trà Vải', 'Tea', 45000, 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?q=80&w=500&auto=format&fit=crop'), 
        ('Trà Sen Vàng', 'Tea', 50000, 'https://images.unsplash.com/photo-1594631252845-29fc458695d1?q=80&w=500&auto=format&fit=crop'), 
        ('Trà Ô Long', 'Tea', 40000, 'https://images.unsplash.com/photo-1564890369478-c89ca6d9cde9?q=80&w=500&auto=format&fit=crop'), 
        ('Lục Trà', 'Tea', 35000, 'https://images.unsplash.com/photo-1523906630133-f6934a1ab2b9?q=80&w=500&auto=format&fit=crop'),
        # Juice
        ('Nước Ép Cam', 'Juice', 40000, 'https://images.unsplash.com/photo-1600266177646-33d98d05eeed?q=80&w=500&auto=format&fit=crop'), 
        ('Nước Ép Dưa Hấu', 'Juice', 40000, 'https://images.unsplash.com/photo-1562158074-27928c9ca6a1?q=80&w=500&auto=format&fit=crop'),
        ('Nước Ép Thơm', 'Juice', 40000, 'https://images.unsplash.com/photo-1613478223719-2ab802602423?q=80&w=500&auto=format&fit=crop'), 
        ('Sinh tố Bơ', 'Juice', 50000, 'https://images.unsplash.com/photo-1525385133336-e4226ca43d97?q=80&w=500&auto=format&fit=crop'), 
        ('Sinh tố Dâu', 'Juice', 50000, 'https://images.unsplash.com/photo-1543362906-acfc16c67564?q=80&w=500&auto=format&fit=crop'),
    ]
    for item in menu_items:
        ThucDon.objects.create(
            ten_mon=item[0], ma_loai=item[1], 
            don_gia=item[2], hinh_anh=item[3], trang_thai=1
        )

    print("4. Tạo Kho Nguyên Liệu (5 Loại)...")
    inventory_items = [
        ('Hạt Cà phê', 'kg', 5, 2),
        ('Sữa đặc', 'lon', 50, 10),
        ('Đường cát', 'kg', 10, 3),
        ('Trà sấy', 'kg', 3, 1),
        ('Ly nhựa', 'cái', 1000, 200),
    ]
    for item in inventory_items:
        TonKho.objects.create(
            ten_nl=item[0], don_vi_tinh=item[1], 
            so_luong_ton=item[2], nguong_bao_dong=item[3]
        )

    print("5. Tạo Khuyến Mãi...")
    today = date.today()
    # Active Promo
    KhuyenMai.objects.create(
        ten_chuong_trinh='Giảm 20% Khai Trương',
        ngay_bd=today - timedelta(days=1), ngay_kt=today + timedelta(days=30),
        phan_tram_giam=20, dieu_kien_toi_thieu=100000, is_active=True
    )
    # Expired Promo
    KhuyenMai.objects.create(
        ten_chuong_trinh='Lì xì Tết',
        ngay_bd=today - timedelta(days=60), ngay_kt=today - timedelta(days=30),
        phan_tram_giam=15, dieu_kien_toi_thieu=50000, is_active=True
    )

    print("Hoàn tất Seed Data!")

def seed_sample_orders():
    """Tạo dữ liệu hóa đơn mẫu đã hoàn tất chỉ cho HÔM NAY để dashboard thực tế."""
    from apps.orders.models import HoaDon, ChiTietHoaDon
    from apps.staff.models import NhanVien
    from apps.tables.models import Ban
    from apps.menu.models import ThucDon
    from django.utils import timezone

    print("6. Tạo Hóa đơn mẫu hôm nay...")

    nv = NhanVien.objects.first()
    bans = list(Ban.objects.all())
    mons = list(ThucDon.objects.all())

    if not nv or not bans or not mons:
        print("   [Bỏ qua] Thiếu nhân viên / bàn / món.")
        return

    # Tất cả hóa đơn đều trong ngày hôm nay
    today = timezone.localtime(timezone.now())

    sample_orders = [
        # (bàn index, danh sách (món index, số lượng))
        (0, [(0, 2), (5, 1), (10, 1)]),
        (1, [(1, 3), (6, 2)]),
        (2, [(2, 1), (7, 1), (11, 2)]),
        (3, [(3, 2), (8, 1)]),
        (4, [(4, 1), (9, 2), (12, 1)]),
        (0, [(0, 1), (1, 2), (5, 1)]),
        (1, [(6, 3), (11, 1)]),
        (2, [(2, 2), (7, 2)]),
        (3, [(3, 1), (8, 3), (13, 1)]),
        (4, [(4, 2), (9, 1)]),
    ]

    for ban_idx, items in sample_orders:
        ban = bans[ban_idx % len(bans)]

        hd = HoaDon.objects.create(
            ma_nv=nv, ma_ban=ban,
            trang_thai=HoaDon.TrangThai.HOAN_TAT,
            phuong_thuc=HoaDon.PhuongThucThanhToan.TIEN_MAT,
        )
        # Ghi đè ngay_lap về hôm nay giờ local
        HoaDon.objects.filter(pk=hd.pk).update(ngay_lap=today)

        tong = 0
        for mon_idx, so_luong in items:
            mon = mons[mon_idx % len(mons)]
            ChiTietHoaDon.objects.create(
                ma_hd=hd, ma_mon=mon,
                so_luong=so_luong, gia_ban=mon.don_gia
            )
            tong += so_luong * mon.don_gia

        HoaDon.objects.filter(pk=hd.pk).update(tong_tien=tong)

    print(f"   Đã tạo {len(sample_orders)} hóa đơn mẫu cho hôm nay.")



if __name__ == '__main__':
    seed_data()
    seed_sample_orders()
