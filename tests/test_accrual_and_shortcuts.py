"""
Personel Tahakkuk Fişi, Borç Çeşitleri ve Fiş Açıklamaları Testleri (test_accrual_and_shortcuts.py)
"""

import unittest
from db_manager import init_database, get_db_connection
from api_handlers import handle_api_request


class TestAccrualAndShortcuts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database()

    def setUp(self):
        self.conn = get_db_connection()
        self.cur = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def test_employee_debt_types_crud(self):
        """Borç çeşitleri listeleme ve ekleme test edilir."""
        res, code = handle_api_request(None, "GET", "/api/employee-debt-types", {}, {})
        self.assertEqual(code, 200)
        self.assertTrue(len(res) >= 5)

        # Yeni borç türü ekle
        post_data = {
            "kod": "BAYRAM_HARCLIGI",
            "ad": "Kurban Bayramı Harçlığı",
            "yon": "BORC",
            "varsayilan_tutar": 5000
        }
        res_post, code_post = handle_api_request(None, "POST", "/api/employee-debt-types", {}, post_data)
        self.assertEqual(code_post, 201)
        self.assertTrue(res_post["success"])

        # Silme
        del_res, del_code = handle_api_request(None, "DELETE", f"/api/employee-debt-types?id={res_post['id']}", {"id": [str(res_post["id"])]}, {})
        self.assertEqual(del_code, 200)

    def test_employee_accrual_voucher_and_report(self):
        """Personel tahakkuk fişi kesildiğinde otomatik muhasebe fişi oluşması ve raporlama test edilir."""
        # 1. Personel ekle
        p_res, p_code = handle_api_request(None, "POST", "/api/employees", {}, {
            "ad_soyad": "Deneme Personel A",
            "tc_kimlik": "11111111111",
            "maas": 30000
        })
        self.assertEqual(p_code, 201)
        pid = p_res["id"]

        # 2. Tahakkuk fişi oluştur
        acc_data = {
            "tarih": "2026-03-15",
            "donem_yil": 2026,
            "donem_ay": 3,
            "aciklama": "2026 Mart Maaş ve Prim Tahakkuk Fişi",
            "satirlar": [
                {"personel_id": pid, "tur": "MAAS", "tutar": 30000, "aciklama": "Mart Maaş"},
                {"personel_id": pid, "tur": "PRIM", "tutar": 5000, "aciklama": "Mart Prim"}
            ]
        }
        res, code = handle_api_request(None, "POST", "/api/employees/accrual-voucher", {}, acc_data)
        self.assertEqual(code, 201)
        self.assertTrue(res["success"])
        self.assertEqual(res["toplam_tutar"], 35000.0)
        self.assertTrue(res["fis_id"] > 0)

        # 3. Raporu çek (oluşturulan personel bazında)
        rep, rcode = handle_api_request(None, "GET", f"/api/employees/accrual-report?yil=2026&ay=3&personel_id={pid}", {"yil": ["2026"], "ay": ["3"], "personel_id": [str(pid)]}, {})
        self.assertEqual(rcode, 200)
        self.assertEqual(rep["genel_toplam"], 35000.0)

        # 4. Personel Silme
        del_emp, del_code = handle_api_request(None, "DELETE", f"/api/employees?id={pid}", {"id": [str(pid)]}, {})
        self.assertEqual(del_code, 200)

    def test_voucher_descriptions_autocomplete(self):
        """Geçmiş açıklamaların getirilmesi test edilir."""
        res, code = handle_api_request(None, "GET", "/api/vouchers/descriptions", {}, {})
        self.assertEqual(code, 200)
        self.assertIn("descriptions", res)
        self.assertIsInstance(res["descriptions"], list)


if __name__ == "__main__":
    unittest.main()
