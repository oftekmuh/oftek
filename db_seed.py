"""
Veritabanı Başlangıç Tohum Verileri (db_seed.py)
Standart Genel Hesap Planı, varsayılan personel türleri ve borç çeşitlerini içerir.
"""

# Standart Genel Hesap Planı
DEFAULT_ACCOUNTS = [
    ('100', 'KASA', 'AKTIF', 1), ('100.01', 'Merkez TL Kasası', 'AKTIF', 2),
    ('102', 'BANKALAR', 'AKTIF', 1), ('102.01', 'Ziraat Bankası Vadesiz TL', 'AKTIF', 2),
    ('103', 'VERİLEN ÇEKLER VE ÖDEME EMİRLERİ (-)', 'PASIF', 1),
    ('120', 'ALICILAR', 'AKTIF', 1), ('120.01', 'Yurtiçi Müşteriler', 'AKTIF', 2),
    ('153', 'TİCARİ MALLAR', 'AKTIF', 1), ('153.01', 'Ticari Emtia Malları', 'AKTIF', 2),
    ('191', 'İNDİRİLECEK KDV', 'AKTIF', 1), ('191.20', '%20 İndirilecek KDV', 'AKTIF', 2),
    ('255', 'DEMİRBAŞLAR', 'AKTIF', 1), ('257', 'BİRİKMİŞ AMORTİSMANLAR (-)', 'PASIF', 1),
    ('300', 'BANKA KREDİLERİ', 'PASIF', 1),
    ('320', 'SATICILAR', 'PASIF', 1), ('320.01', 'Yurtiçi Tedarikçiler', 'PASIF', 2),
    ('335', 'PERSONELE BORÇLAR', 'PASIF', 1), ('335.01', 'Personele Net Maaş Borçları', 'PASIF', 2),
    ('360', 'ÖDENECEK VERGİ VE FONLAR', 'PASIF', 1),
    ('391', 'HESAPLANAN KDV', 'PASIF', 1), ('391.20', '%20 Hesaplanan KDV', 'PASIF', 2),
    ('500', 'SERMAYE', 'PASIF', 1), ('590', 'DÖNEM NET KÂRI', 'PASIF', 1),
    ('600', 'YURTİÇİ SATIŞLAR', 'PASIF', 1), ('600.01', 'Muhtelif Satış ve Hizmet Gelirleri', 'PASIF', 2),
    ('600.20', '%20 Yurtiçi Satış Gelirleri', 'PASIF', 2),
    ('621', 'SATILAN TİCARİ MALLAR MALİYETİ (-)', 'AKTIF', 1),
    ('642', 'FAİZ GELİRLERİ', 'PASIF', 1), ('642.01', 'Mevduat Faiz Gelirleri', 'PASIF', 2),
    ('649', 'DİĞER OLAĞAN GELİR VE KÂRLAR', 'PASIF', 1), ('649.01', 'Muhtelif Diğer Olağan Gelirler', 'PASIF', 2),
    ('679', 'DİĞER OLAĞANDIŞI GELİR VE KÂRLAR', 'PASIF', 1), ('679.01', 'Muhtelif Olağandışı Gelirler', 'PASIF', 2),
    ('770', 'GENEL YÖNETİM GİDERLERİ', 'AKTIF', 1), ('770.01', 'Personel Ücret ve Giderleri', 'AKTIF', 2),
    ('770.02', 'Ofis, Kırtasiye ve İletişim Giderleri', 'AKTIF', 2),
    ('770.03', 'Yol, Yemek ve Ulaşım Giderleri', 'AKTIF', 2),
    ('770.04', 'Kira, Aidat ve Tesis Giderleri', 'AKTIF', 2),
    ('770.05', 'Elektrik, Su ve Doğalgaz Giderleri', 'AKTIF', 2)
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
