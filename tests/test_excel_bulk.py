"""
Excel Toplu Hesap Aktarımı Testi (tests/test_excel_bulk.py)
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db_manager import init_database, get_db_connection
from handlers_accounts import handle_account_routes


class TestAccountsBulk(unittest.TestCase):

    def setUp(self):
        init_database()

    def test_bulk_accounts_import(self):
        sample_accounts = [
            {"kod": "100.02", "ad": "Kadıköy Şube Kasası", "karakter": "AKTIF"},
            {"kod": "120.01.001", "ad": "Gerçek Müşteri A.Ş.", "karakter": "AKTIF"},
            {"kod": "320.01.001", "ad": "Gerçek Tedarikçi Ltd.", "karakter": "PASIF"}
        ]

        res, status = handle_account_routes("POST", "/api/accounts/bulk", {}, {
            "accounts": sample_accounts,
            "clear_first": False
        })
        self.assertEqual(status, 200)
        self.assertTrue(res["success"])
        self.assertEqual(res["count"], 3)

        # DB Kontrolü
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT ad, karakter FROM hesap_plani WHERE kod = '120.01.001'")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["ad"], "Gerçek Müşteri A.Ş.")
        self.assertEqual(row["karakter"], "AKTIF")
        conn.close()


if __name__ == "__main__":
    unittest.main()
