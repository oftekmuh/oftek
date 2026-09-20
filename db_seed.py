"""
Veritabanı Başlangıç Tohum Verileri (db_seed.py)
Standart Genel Hesap Planı, varsayılan personel türleri ve borç çeşitlerini içerir.
"""

# Standart Genel Hesap Planı (Yalnızca Temel Ana Hesaplar - Seviye 1)
DEFAULT_ACCOUNTS = [
    ('100', 'KASA', 'AKTIF', 1),
    ('102', 'BANKALAR', 'AKTIF', 1),
    ('103', 'VERİLEN ÇEKLER VE ÖDEME EMİRLERİ (-)', 'PASIF', 1),
    ('120', 'ALICILAR', 'AKTIF', 1),
    ('153', 'TİCARİ MALLAR', 'AKTIF', 1),
    ('191', 'İNDİRİLECEK KDV', 'AKTIF', 1),
    ('255', 'DEMİRBAŞLAR', 'AKTIF', 1),
    ('257', 'BİRİKMİŞ AMORTİSMANLAR (-)', 'PASIF', 1),
    ('300', 'BANKA KREDİLERİ', 'PASIF', 1),
    ('320', 'SATICILAR', 'PASIF', 1),
    ('335', 'PERSONELE BORÇLAR', 'PASIF', 1),
    ('360', 'ÖDENECEK VERGİ VE FONLAR', 'PASIF', 1),
    ('391', 'HESAPLANAN KDV', 'PASIF', 1),
    ('500', 'SERMAYE', 'PASIF', 1),
    ('590', 'DÖNEM NET KÂRI', 'PASIF', 1),
    ('600', 'YURTİÇİ SATIŞLAR', 'PASIF', 1),
    ('621', 'SATILAN TİCARİ MALLAR MALİYETİ (-)', 'AKTIF', 1),
    ('642', 'FAİZ GELİRLERİ', 'PASIF', 1),
    ('649', 'DİĞER OLAĞAN GELİR VE KÂRLAR', 'PASIF', 1),
    ('679', 'DİĞER OLAĞANDIŞI GELİR VE KÂRLAR', 'PASIF', 1),
    ('770', 'GENEL YÖNETİM GİDERLERİ', 'AKTIF', 1)
]

# Varsayılan Personel Tahakkuk / Borç Çeşitleri
DEFAULT_DEBT_TYPES = [
    ('MAAS', 'Aylık Normal Maaş Hakedişi', 'BORC', 0),
    ('FAZLA_MESAI', 'Fazla Mesai Ücreti', 'BORC', 0),
    ('PRIM', 'Performans / Satış Primi', 'BORC', 0),
    ('YOL_YEMEK', 'Yol ve Yemek Desteği', 'BORC', 0),
    ('IKRAMIYE', 'Dönemsel İkramiye / Prim', 'BORC', 0),
    ('KESINTI', 'Yasal / İdari Kesinti', 'ALACAK', 0)
]

# Varsayılan Personel Türleri
DEFAULT_EMP_TYPES = [
    ('GENEL', 'Genel Personel'),
    ('YONETIM', 'Yönetim / İdari'),
    ('BEYAZ_YAKA', 'Beyaz Yaka / Ofis'),
    ('MAVI_YAKA', 'Mavi Yaka / Üretim'),
    ('SAHA', 'Saha / Satış'),
    ('STAJYER', 'Stajyer / Çırak')
]


def seed_defaults(cursor):
    """Standart hesap planı, borç çeşitleri ve personel türlerini yükler."""
    cursor.executemany("""
        INSERT OR IGNORE INTO hesap_plani (kod, ad, karakter, seviye)
        VALUES (?, ?, ?, ?)
    """, DEFAULT_ACCOUNTS)

    cursor.executemany("""
        INSERT OR IGNORE INTO personel_borc_turleri (kod, ad, yon, varsayilan_tutar)
        VALUES (?, ?, ?, ?)
    """, DEFAULT_DEBT_TYPES)

    cursor.executemany("INSERT OR IGNORE INTO personel_turleri (kod, ad) VALUES (?, ?)", DEFAULT_EMP_TYPES)
