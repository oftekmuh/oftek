"""
Veritabanı Yönetim Modülü (db_manager.py)
SQLite veritabanı bağlantısı, tablo oluşturma, indeksleme ve migrasyonları yönetir.
"""

import os
import sqlite3
from db_seed import seed_defaults

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILENAME = "muhasebe.db"
DB_PATH = os.path.join(BASE_DIR, DB_FILENAME)


def get_db_connection():
    """SQLite veritabanı bağlantısı döndürür."""
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Tüm veritabanı tablolarını, performans indekslerini oluşturur ve tohum verileri yükler."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Genel Muhasebe Tabloları
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS hesap_plani (
            kod TEXT PRIMARY KEY,
            ad TEXT NOT NULL,
            karakter TEXT DEFAULT 'AKTIF',
            seviye INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS fisler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            no INTEGER UNIQUE,
            tarih TEXT NOT NULL,
            tip TEXT NOT NULL,
            aciklama TEXT,
            olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS fis_satirlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fis_id INTEGER NOT NULL,
            satir_no INTEGER NOT NULL,
            hesap_kod TEXT NOT NULL,
            aciklama TEXT,
            borc REAL DEFAULT 0,
            alacak REAL DEFAULT 0,
            FOREIGN KEY(fis_id) REFERENCES fisler(id) ON DELETE CASCADE,
            FOREIGN KEY(hesap_kod) REFERENCES hesap_plani(kod)
        );
    """)

    # 2. Ön Muhasebe & Operasyonel Tablolar
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS gun_oturumlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT UNIQUE NOT NULL,
            donem_yil INTEGER NOT NULL,
            donem_ay INTEGER NOT NULL,
            durum TEXT DEFAULT 'ACIK',
            acilis_zamani DATETIME DEFAULT CURRENT_TIMESTAMP,
            kapanis_zamani DATETIME,
            kapanis_fis_id INTEGER,
            notlar TEXT,
            FOREIGN KEY(kapanis_fis_id) REFERENCES fisler(id)
        );

        CREATE TABLE IF NOT EXISTS cariler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tip TEXT NOT NULL,
            kod TEXT UNIQUE,
            unvan TEXT NOT NULL,
            yetkili TEXT,
            vergi_no TEXT,
            telefon TEXT,
            hesap_kodu TEXT,
            bakiye REAL DEFAULT 0,
            durum TEXT DEFAULT 'AKTIF'
        );

        CREATE TABLE IF NOT EXISTS personel_turleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kod TEXT UNIQUE NOT NULL,
            ad TEXT NOT NULL,
            aktif INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS personeller (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_soyad TEXT NOT NULL,
            tc_kimlik TEXT,
            telefon TEXT,
            iban TEXT,
            maas REAL NOT NULL DEFAULT 0,
            hesap_kodu TEXT DEFAULT '335.01',
            personel_turu_kod TEXT DEFAULT 'GENEL',
            durum TEXT DEFAULT 'AKTIF',
            olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS personel_ek_bilgiler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personel_id INTEGER NOT NULL,
            baslik TEXT NOT NULL,
            veri_tipi TEXT NOT NULL DEFAULT 'METIN',
            deger TEXT,
            FOREIGN KEY(personel_id) REFERENCES personeller(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS personel_borc_turleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kod TEXT UNIQUE NOT NULL,
            ad TEXT NOT NULL,
            yon TEXT DEFAULT 'BORC',
            varsayilan_tutar REAL DEFAULT 0,
            aktif INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS personel_tahakkuklari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personel_id INTEGER NOT NULL,
            gun_id INTEGER,
            donem_yil INTEGER NOT NULL,
            donem_ay INTEGER NOT NULL,
            tur TEXT NOT NULL,
            tekrar_tipi TEXT DEFAULT 'TEK_SEFERLIK',
            tarih TEXT NOT NULL,
            tutar REAL NOT NULL,
            aciklama TEXT,
            fis_id INTEGER,
            FOREIGN KEY(personel_id) REFERENCES personeller(id),
            FOREIGN KEY(gun_id) REFERENCES gun_oturumlar(id),
            FOREIGN KEY(fis_id) REFERENCES fisler(id)
        );

        CREATE TABLE IF NOT EXISTS alacaklar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_id INTEGER NOT NULL,
            gun_id INTEGER NOT NULL,
            donem_yil INTEGER NOT NULL,
            donem_ay INTEGER NOT NULL,
            kategori TEXT NOT NULL,
            belge_no TEXT,
            tarih TEXT NOT NULL,
            vade_tarihi TEXT,
            toplam_tutar REAL NOT NULL,
            tahsil_edilen REAL DEFAULT 0,
            kalan_tutar REAL NOT NULL,
            durum TEXT DEFAULT 'ACIK',
            aciklama TEXT,
            FOREIGN KEY(cari_id) REFERENCES cariler(id),
            FOREIGN KEY(gun_id) REFERENCES gun_oturumlar(id)
        );

        CREATE TABLE IF NOT EXISTS borclar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cari_id INTEGER NOT NULL,
            gun_id INTEGER NOT NULL,
            donem_yil INTEGER NOT NULL,
            donem_ay INTEGER NOT NULL,
            belge_no TEXT,
            tarih TEXT NOT NULL,
            vade_tarihi TEXT,
            toplam_tutar REAL NOT NULL,
            odenen_tutar REAL DEFAULT 0,
            kalan_tutar REAL NOT NULL,
            durum TEXT DEFAULT 'ACIK',
            aciklama TEXT,
            FOREIGN KEY(cari_id) REFERENCES cariler(id),
            FOREIGN KEY(gun_id) REFERENCES gun_oturumlar(id)
        );

        CREATE TABLE IF NOT EXISTS gunluk_islemler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gun_id INTEGER NOT NULL,
            donem_yil INTEGER NOT NULL,
            donem_ay INTEGER NOT NULL,
            islem_turu TEXT NOT NULL,
            kaynak_hesap TEXT NOT NULL,
            karsi_hesap TEXT,
            kategori TEXT,
            cari_id INTEGER,
            personel_id INTEGER,
            tutar REAL NOT NULL,
            tarih TEXT NOT NULL,
            aciklama TEXT,
            FOREIGN KEY(gun_id) REFERENCES gun_oturumlar(id),
            FOREIGN KEY(cari_id) REFERENCES cariler(id),
            FOREIGN KEY(personel_id) REFERENCES personeller(id)
        );

        CREATE TABLE IF NOT EXISTS tahsilat_dagitimi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            islem_id INTEGER NOT NULL,
            alacak_id INTEGER NOT NULL,
            dagitilan_tutar REAL NOT NULL,
            FOREIGN KEY(islem_id) REFERENCES gunluk_islemler(id) ON DELETE CASCADE,
            FOREIGN KEY(alacak_id) REFERENCES alacaklar(id)
        );
    """)

    # 3. Kurum / İşletme Profili & Sistem Ayarları
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS sistem_ayarlari (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            kurum_adi TEXT NOT NULL DEFAULT 'oftek',
            kurum_turu TEXT NOT NULL DEFAULT 'GENEL',
            para_birimi TEXT NOT NULL DEFAULT '₺',
            vergi_no TEXT DEFAULT '',
            adres TEXT DEFAULT '',
            telefon TEXT DEFAULT '',
            eposta TEXT DEFAULT '',
            web_adresi TEXT DEFAULT '',
            guncelleme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        INSERT OR IGNORE INTO sistem_ayarlari (id, kurum_adi, kurum_turu, para_birimi) VALUES (1, 'oftek', 'GENEL', '₺');

        -- 4. Kimlik Doğrulama & Oturum Tabloları
        CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_adi TEXT UNIQUE NOT NULL,
            sifre_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            ad_soyad TEXT DEFAULT '',
            olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
            son_giris_tarihi DATETIME
        );
        CREATE TABLE IF NOT EXISTS oturumlar (
            token TEXT PRIMARY KEY,
            kullanici_id INTEGER NOT NULL,
            olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
            son_islem_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(kullanici_id) REFERENCES kullanicilar(id) ON DELETE CASCADE
        );
    """)

    # 5. Performans & Hız İndeksleri (B-Tree)
    cursor.executescript("""
        CREATE INDEX IF NOT EXISTS idx_fis_satirlari_hesap ON fis_satirlari(hesap_kod);
        CREATE INDEX IF NOT EXISTS idx_fis_satirlari_fis ON fis_satirlari(fis_id);
        CREATE INDEX IF NOT EXISTS idx_fisler_tarih ON fisler(tarih);
        CREATE INDEX IF NOT EXISTS idx_fisler_no ON fisler(no);
        CREATE INDEX IF NOT EXISTS idx_alacaklar_cari_durum ON alacaklar(cari_id, durum);
        CREATE INDEX IF NOT EXISTS idx_borclar_cari_durum ON borclar(cari_id, durum);
        CREATE INDEX IF NOT EXISTS idx_gunluk_islemler_gun ON gunluk_islemler(gun_id);
        CREATE INDEX IF NOT EXISTS idx_gunluk_islemler_tarih ON gunluk_islemler(tarih);
        CREATE INDEX IF NOT EXISTS idx_gunluk_islemler_donem ON gunluk_islemler(donem_yil, donem_ay);
        CREATE INDEX IF NOT EXISTS idx_gunluk_islemler_tur ON gunluk_islemler(islem_turu);
        CREATE INDEX IF NOT EXISTS idx_personel_tahakkuk_donem ON personel_tahakkuklari(donem_yil, donem_ay);
        CREATE INDEX IF NOT EXISTS idx_oturumlar_token ON oturumlar(token);
        CREATE INDEX IF NOT EXISTS idx_kullanicilar_kadi ON kullanicilar(kullanici_adi);
    """)

    # Standart tohum verilerini yükle
    seed_defaults(cursor)

    # Migrasyon kontrolleri
    for sql in [
        "ALTER TABLE gunluk_islemler ADD COLUMN karsi_hesap TEXT",
        "ALTER TABLE gunluk_islemler ADD COLUMN kategori TEXT",
        "ALTER TABLE personel_tahakkuklari ADD COLUMN fis_id INTEGER",
        "ALTER TABLE personeller ADD COLUMN personel_turu_kod TEXT DEFAULT 'GENEL'",
        "ALTER TABLE cariler ADD COLUMN yetkili TEXT",
        "ALTER TABLE cariler ADD COLUMN hesap_kodu TEXT"
    ]:
        try:
            cursor.execute(sql)
        except Exception:
            pass

    conn.commit()
    conn.close()


def reset_all_operational_data(conn):
    """Tüm operasyonel verileri (hareketler, fişler, cariler vb.) sıfırlar; hesap planı ve kurum profili korunur."""
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF")
    tables_to_clear = [
        "tahsilat_dagitimi", "gunluk_islemler", "alacaklar", "borclar",
        "personel_tahakkuklari", "personel_ek_bilgiler", "personeller",
        "cariler", "fis_satirlari", "fisler", "gun_oturumlar"
    ]
    for table in tables_to_clear:
        cur.execute(f"DELETE FROM {table}")
    try:
        cur.execute("DELETE FROM sqlite_sequence WHERE name IN ({})".format(
            ",".join(f"'{t}'" for t in tables_to_clear)
        ))
    except Exception:
        pass
    cur.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    return True
