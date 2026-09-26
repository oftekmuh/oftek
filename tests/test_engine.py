"""
Otomatik Muhasebe & Dağıtım Motoru Testleri (tests/test_engine.py)
FIFO, Seçimli Dağıtım, Yıl/Ay Dönemsellik ve Gün Kapanış Fiş Denkliği Testleri.
"""

import os
import sys
import sqlite3
import unittest

# Üst dizini sys.path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db_manager import get_db_connection, init_database
from accounting_engine import (
    allocate_collection,
    pay_company_debt,
    accrue_monthly_salaries,
    get_employee_balance,
    close_day_and_generate_voucher
)


class TestAccountingEngine(unittest.TestCase):

    def setUp(self):
        """Test için geçici bir SQLite in-memory veya test veritabanı kur."""
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Tabloları oluştur
        cursor = self.conn.cursor()
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
            CREATE TABLE IF NOT EXISTS gun_oturumlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih TEXT NOT NULL,
                donem_yil INTEGER NOT NULL,
                donem_ay INTEGER NOT NULL,
                acilis_zamani DATETIME DEFAULT CURRENT_TIMESTAMP,
                kapanis_zamani DATETIME,
                durum TEXT DEFAULT 'ACIK',
                kapanis_fis_id INTEGER,
                notlar TEXT
            );
            CREATE TABLE IF NOT EXISTS cariler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tip TEXT NOT NULL,
                unvan TEXT NOT NULL,
                yetkili TEXT,
                telefon TEXT,
                vergi_no TEXT,
                hesap_kodu TEXT NOT NULL,
                bakiye REAL DEFAULT 0,
                olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS personeller (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_soyad TEXT NOT NULL,
                tc_kimlik TEXT,
                telefon TEXT,
                iban TEXT,
                maas REAL NOT NULL DEFAULT 0,
                hesap_kodu TEXT DEFAULT '335.01',
                durum TEXT DEFAULT 'AKTIF',
                olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS personel_tahakkuklari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personel_id INTEGER NOT NULL,
                gun_id INTEGER NOT NULL,
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
                UNIQUE(personel_id, donem_yil, donem_ay, tur)
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
                fis_id INTEGER,
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
                fis_id INTEGER,
                FOREIGN KEY(cari_id) REFERENCES cariler(id),
                FOREIGN KEY(gun_id) REFERENCES gun_oturumlar(id)
            );
            CREATE TABLE IF NOT EXISTS gunluk_islemler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gun_id INTEGER NOT NULL,
                donem_yil INTEGER NOT NULL,
                donem_ay INTEGER NOT NULL,
                islem_turu TEXT NOT NULL,
                kaynak_hesap TEXT DEFAULT '100.01',
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

        # Standart hesapları ekle
        cursor.executemany("INSERT INTO hesap_plani (kod, ad) VALUES (?, ?)", [
            ('100.01', 'Kasa'),
            ('102.01', 'Banka'),
            ('120.01', 'Müşteriler'),
            ('153.01', 'Ticari Mallar'),
            ('320.01', 'Satıcılar'),
            ('335.01', 'Personele Borçlar'),
            ('600.20', 'Yurtiçi Satışlar'),
            ('649.01', 'Diğer Olağan Gelir ve Karlar'),
            ('770.01', 'Genel Yönetim Giderleri'),
            ('770.02', 'Kırtasiye ve Büro Malzemeleri')
        ])

        # Test gün oturumu aç (2026/03)
        cursor.execute("INSERT INTO gun_oturumlar (tarih, donem_yil, donem_ay, durum) VALUES ('2026-03-18', 2026, 3, 'ACIK')")
        self.gun_id = cursor.lastrowid

        # Test müşterisi ve tedarikçisi ekle
        cursor.execute("INSERT INTO cariler (tip, unvan, hesap_kodu) VALUES ('MUSTERI', 'Beta Ticaret', '120.01')")
        self.musteri_id = cursor.lastrowid
        cursor.execute("INSERT INTO cariler (tip, unvan, hesap_kodu) VALUES ('FIRMA', 'Kaya Tedarik Ltd.', '320.01')")
        self.firma_id = cursor.lastrowid

        # Test personeli ekle
        cursor.execute("INSERT INTO personeller (ad_soyad, maas, hesap_kodu) VALUES ('Ali Yılmaz', 30000, '335.01')")
        self.personel_id = cursor.lastrowid

        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_fifo_collection_allocation(self):
        """FIFO kuralıyla en eski faturanın önce kapatıldığını doğrula."""
        cur = self.conn.cursor()
        # 2 Alacak faturası ekle (Fatura 1: 1000 TL, Fatura 2: 2500 TL)
        cur.execute("""
            INSERT INTO alacaklar (cari_id, gun_id, donem_yil, donem_ay, kategori, belge_no, tarih, vade_tarihi, toplam_tutar, kalan_tutar, durum)
            VALUES (?, ?, 2026, 3, 'URUN_SATISI', 'FAT-001', '2026-03-01', '2026-03-10', 1000, 1000, 'ACIK')
        """, (self.musteri_id, self.gun_id))
        f1_id = cur.lastrowid

        cur.execute("""
            INSERT INTO alacaklar (cari_id, gun_id, donem_yil, donem_ay, kategori, belge_no, tarih, vade_tarihi, toplam_tutar, kalan_tutar, durum)
            VALUES (?, ?, 2026, 3, 'URUN_SATISI', 'FAT-002', '2026-03-05', '2026-03-20', 2500, 2500, 'ACIK')
        """, (self.musteri_id, self.gun_id))
        f2_id = cur.lastrowid

        # 1500 TL tahsilat gir
        cur.execute("INSERT INTO gunluk_islemler (gun_id, donem_yil, donem_ay, islem_turu, tutar, tarih) VALUES (?, 2026, 3, 'ALACAK_TAHSILAT', 1500, '2026-03-18')", (self.gun_id,))
        islem_id = cur.lastrowid

        allocate_collection(cur, self.musteri_id, 1500, islem_id, mod="FIFO")

        cur.execute("SELECT kalan_tutar, durum FROM alacaklar WHERE id = ?", (f1_id,))
        f1 = cur.fetchone()
        self.assertEqual(f1["kalan_tutar"], 0.0)
        self.assertEqual(f1["durum"], "KAPANDI")

        cur.execute("SELECT kalan_tutar, durum FROM alacaklar WHERE id = ?", (f2_id,))
        f2 = cur.fetchone()
        self.assertEqual(f2["kalan_tutar"], 2000.0)
        self.assertEqual(f2["durum"], "KISMI")

    def test_custom_selective_allocation(self):
        """Seçimli modda kullanıcının belirlediği faturanın kapatıldığını doğrula."""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO alacaklar (cari_id, gun_id, donem_yil, donem_ay, kategori, belge_no, tarih, vade_tarihi, toplam_tutar, kalan_tutar, durum)
            VALUES (?, ?, 2026, 3, 'URUN_SATISI', 'FAT-001', '2026-03-01', '2026-03-10', 1000, 1000, 'ACIK')
        """, (self.musteri_id, self.gun_id))
        f1_id = cur.lastrowid

        cur.execute("""
            INSERT INTO alacaklar (cari_id, gun_id, donem_yil, donem_ay, kategori, belge_no, tarih, vade_tarihi, toplam_tutar, kalan_tutar, durum)
            VALUES (?, ?, 2026, 3, 'URUN_SATISI', 'FAT-002', '2026-03-05', '2026-03-20', 2000, 2000, 'ACIK')
        """, (self.musteri_id, self.gun_id))
        f2_id = cur.lastrowid

        # Kullanıcı sadece 2. faturaya 1200 TL yatırıyor
        cur.execute("INSERT INTO gunluk_islemler (gun_id, donem_yil, donem_ay, islem_turu, tutar, tarih) VALUES (?, 2026, 3, 'ALACAK_TAHSILAT', 1200, '2026-03-18')", (self.gun_id,))
        islem_id = cur.lastrowid

        secimler = [{"alacak_id": f2_id, "tutar": 1200}]
        allocate_collection(cur, self.musteri_id, 1200, islem_id, mod="SECIMLI", secimler=secimler)

        cur.execute("SELECT kalan_tutar FROM alacaklar WHERE id = ?", (f1_id,))
        self.assertEqual(cur.fetchone()["kalan_tutar"], 1000.0)  # Fatura 1'e dokunulmadı

        cur.execute("SELECT kalan_tutar, durum FROM alacaklar WHERE id = ?", (f2_id,))
        f2 = cur.fetchone()
        self.assertEqual(f2["kalan_tutar"], 800.0)
        self.assertEqual(f2["durum"], "KISMI")

    def test_monthly_payroll_accrual_and_duplicate_check(self):
        """Aylık maaş tahakkukunun çalıştığını ve mükerrerliği engellediğini doğrula."""
        cur = self.conn.cursor()
        res1 = accrue_monthly_salaries(cur, self.gun_id, 2026, 3, '2026-03-18')
        self.assertEqual(res1["created_count"], 1)

        # Tekrar aynı ay çalıştırılırsa atlamalı
        res2 = accrue_monthly_salaries(cur, self.gun_id, 2026, 3, '2026-03-18')
        self.assertEqual(res2["created_count"], 0)
        self.assertEqual(res2["skipped_count"], 1)

    def test_employee_instant_balance(self):
        """Personel anlık net borç hesabını doğrula."""
        cur = self.conn.cursor()
        # 30.000 TL maaş + 5.000 TL prim tahakkuku
        accrue_monthly_salaries(cur, self.gun_id, 2026, 3, '2026-03-18')
        cur.execute("""
            INSERT INTO personel_tahakkuklari (personel_id, gun_id, donem_yil, donem_ay, tur, tarih, tutar)
            VALUES (?, ?, 2026, 3, 'PRIM', '2026-03-18', 5000)
        """, (self.personel_id, self.gun_id))

        # 12.000 TL avans ödemesi yap
        cur.execute("""
            INSERT INTO gunluk_islemler (gun_id, donem_yil, donem_ay, islem_turu, personel_id, tutar, tarih)
            VALUES (?, 2026, 3, 'PERSONEL_ODEME', ?, 12000, '2026-03-18')
        """, (self.gun_id, self.personel_id))

        bakiye = get_employee_balance(cur, self.personel_id)
        self.assertEqual(bakiye["genel_hakedis"], 35000.0)
        self.assertEqual(bakiye["genel_odenen"], 12000.0)
        self.assertEqual(bakiye["anlik_borc"], 23000.0)

    def test_close_day_voucher_balance(self):
        """Gün kapatıldığında üretilen yevmiye fişinin Borç == Alacak eşitliğini sağladığını doğrula."""
        cur = self.conn.cursor()

        # 1. Tahsilat: 5.000 TL
        cur.execute("""
            INSERT INTO gunluk_islemler (gun_id, donem_yil, donem_ay, islem_turu, kaynak_hesap, cari_id, tutar, tarih)
            VALUES (?, 2026, 3, 'ALACAK_TAHSILAT', '100.01', ?, 5000, '2026-03-18')
        """, (self.gun_id, self.musteri_id))

        # 2. Firma Ödemesi: 3.000 TL
        cur.execute("""
            INSERT INTO gunluk_islemler (gun_id, donem_yil, donem_ay, islem_turu, kaynak_hesap, cari_id, tutar, tarih)
            VALUES (?, 2026, 3, 'BORC_ODEME', '100.01', ?, 3000, '2026-03-18')
        """, (self.gun_id, self.firma_id))

        # 3. Personel Ödemesi: 2.000 TL
        cur.execute("""
            INSERT INTO gunluk_islemler (gun_id, donem_yil, donem_ay, islem_turu, kaynak_hesap, personel_id, tutar, tarih)
            VALUES (?, 2026, 3, 'PERSONEL_ODEME', '100.01', ?, 2000, '2026-03-18')
        """, (self.gun_id, self.personel_id))

        # 4. Personel Maaş Tahakkuku: 30.000 TL
        accrue_monthly_salaries(cur, self.gun_id, 2026, 3, '2026-03-18')

        self.conn.commit()

        # Günü kapat
        res = close_day_and_generate_voucher(self.conn, self.gun_id)
        self.assertTrue(res["success"])
        self.assertIsNotNone(res["fis_id"])

        # Fiş satırlarının borç-alacak eşitliğini kontrol et
        cur.execute("SELECT SUM(borc) as tot_b, SUM(alacak) as tot_a FROM fis_satirlari WHERE fis_id = ?", (res["fis_id"],))
        satir = cur.fetchone()
        self.assertAlmostEqual(satir["tot_b"], satir["tot_a"], places=2)
        self.assertGreater(satir["tot_b"], 0)

        # Gün oturumunun KAPALI olduğunu doğrula
        cur.execute("SELECT durum FROM gun_oturumlar WHERE id = ?", (self.gun_id,))
        self.assertEqual(cur.fetchone()["durum"], "KAPALI")


if __name__ == "__main__":
    unittest.main()
