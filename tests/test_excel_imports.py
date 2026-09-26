"""
Excel Toplu Aktarım Testleri (tests/test_excel_imports.py)
Hesap planı listesi, personel, çoklu fiş ve alacak/borç fatura tahakkuku aktarımlarını doğrular.
"""

import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db_manager import init_database, get_db_connection
from handlers_accounts import handle_account_routes
from handlers_imports import handle_import_routes
from accounting_voucher import close_day_and_generate_voucher


class TestExcelImports(unittest.TestCase):

    def setUp(self):
        init_database()
        self.tag = uuid.uuid4().hex[:8]
        handle_account_routes("POST", "/api/accounts/bulk", {}, {"accounts": [
            {"kod": "100.01", "ad": "Nakit Kasa", "karakter": "AKTIF"},
            {"kod": "120.01", "ad": "Alıcılar", "karakter": "AKTIF"},
            {"kod": "320.01", "ad": "Satıcılar", "karakter": "PASIF"},
            {"kod": "600.01", "ad": "Bağış ve Yardımlar", "karakter": "PASIF"},
        ]})

    def test_accounts_list(self):
        res, status = handle_account_routes("GET", "/api/accounts", {}, {})
        self.assertEqual(status, 200)
        self.assertIsInstance(res, list)
        kodlar = [r["kod"] for r in res]
        self.assertIn("100.01", kodlar)
        self.assertEqual(kodlar, sorted(kodlar))

    def test_employee_bulk_insert_and_update(self):
        name = f"Test Personel {self.tag}"
        tc = self.tag + "999"
        res, status = handle_import_routes("POST", "/api/employees/bulk", {}, {"employees": [
            {"ad_soyad": name, "tc_kimlik": tc, "maas": "25.000,50", "personel_turu": f"Kurs {self.tag}"},
        ]})
        self.assertEqual(status, 200, res)
        self.assertEqual(res["eklenen"], 1)

        res, status = handle_import_routes("POST", "/api/employees/bulk", {}, {"employees": [
            {"ad_soyad": name, "tc_kimlik": tc, "maas": 30000},
        ]})
        self.assertEqual(status, 200, res)
        self.assertEqual(res["guncellenen"], 1)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), MAX(maas) FROM personeller WHERE tc_kimlik = ?", (tc,))
        cnt, maas = cur.fetchone()
        conn.close()
        self.assertEqual(cnt, 1)
        self.assertEqual(maas, 30000)

    def test_employee_bulk_rejects_invalid_rows(self):
        res, status = handle_import_routes("POST", "/api/employees/bulk", {}, {"employees": [
            {"ad_soyad": "", "maas": 100, "satir": 2},
        ]})
        self.assertEqual(status, 400)
        self.assertIn("Excel satır 2", res["error"])

    def test_voucher_bulk_all_or_nothing(self):
        good = {"grup": "A", "tarih": "15.01.2026", "aciklama": f"Excel fiş {self.tag}", "rows": [
            {"hesap_kod": "100.01", "borc": "1.500,00", "alacak": ""},
            {"hesap_kod": "600.01", "borc": "", "alacak": 1500},
        ]}
        bad = {"grup": "B", "tarih": "2026-01-16", "rows": [
            {"hesap_kod": "100.01", "borc": 10, "alacak": 0},
            {"hesap_kod": "600.01", "borc": 0, "alacak": 9},
        ]}
        res, status = handle_import_routes("POST", "/api/vouchers/bulk", {}, {"vouchers": [good, bad]})
        self.assertEqual(status, 400)
        self.assertIn("Fiş 'B'", res["error"])

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM fisler WHERE aciklama = ?", (good["aciklama"],))
        self.assertEqual(cur.fetchone()[0], 0)

        res, status = handle_import_routes("POST", "/api/vouchers/bulk", {}, {"vouchers": [good]})
        self.assertEqual(status, 201, res)
        cur.execute("SELECT tarih FROM fisler WHERE aciklama = ?", (good["aciklama"],))
        self.assertEqual(cur.fetchone()[0], "2026-01-15")
        conn.close()

    def test_receivable_bulk_creates_voucher_and_is_not_double_posted(self):
        unvan = f"Excel Müşteri {self.tag}"
        res, status = handle_import_routes("POST", "/api/receivables/bulk", {}, {
            "karsi_hesap": "600.01",
            "kalemler": [
                {"cari": unvan, "tarih": "2026-02-01", "belge_no": "F1", "kategori": "Kurban", "tutar": 1000},
                {"cari": unvan.upper(), "tarih": "2026-02-01", "belge_no": "F2", "tutar": 500},
            ]
        })
        self.assertEqual(status, 201, res)
        self.assertEqual(res["yeni_cari"], 1)
        self.assertEqual(len(res["fis_nolari"]), 1)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, bakiye FROM cariler WHERE unvan = ?", (unvan,))
        cari = cur.fetchone()
        self.assertEqual(cari["bakiye"], 1500)
        cur.execute("SELECT gun_id, fis_id FROM alacaklar WHERE cari_id = ?", (cari["id"],))
        rows = cur.fetchall()
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r["fis_id"] for r in rows))

        cur.execute("SELECT SUM(borc), SUM(alacak) FROM fis_satirlari WHERE fis_id = ?", (rows[0]["fis_id"],))
        b, a = cur.fetchone()
        self.assertEqual((b, a), (1500, 1500))

        # Gün sonu kapanışı aynı faturaları tekrar yevmiyelememeli
        gun_id = rows[0]["gun_id"]
        cur.execute("SELECT durum FROM gun_oturumlar WHERE id = ?", (gun_id,))
        if cur.fetchone()["durum"] == "ACIK":
            result = close_day_and_generate_voucher(conn, gun_id)
            if result["fis_id"]:
                cur.execute("SELECT COUNT(*) FROM fis_satirlari WHERE fis_id = ? AND aciklama LIKE ?",
                            (result["fis_id"], f"%{unvan}%"))
                self.assertEqual(cur.fetchone()[0], 0)
            conn.rollback()
        conn.close()

    def test_debt_bulk_requires_existing_cari_when_disabled(self):
        res, status = handle_import_routes("POST", "/api/debts/bulk", {}, {
            "cari_olustur": False,
            "kalemler": [{"cari": f"Olmayan Firma {self.tag}", "tutar": 100, "satir": 3}]
        })
        self.assertEqual(status, 400)
        self.assertIn("Excel satır 3", res["error"])


if __name__ == "__main__":
    unittest.main()
