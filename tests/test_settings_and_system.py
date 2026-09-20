"""
Sistem ve Ayarlar Rota Testleri (test_settings_and_system.py)
"""

import unittest
from api_handlers import handle_api_request
from handlers_session import handle_session_routes
from handlers_employees import handle_employee_routes
from handlers_accruals import handle_accrual_routes
from db_manager import init_database


class TestSettingsAndSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database()

    def test_active_session_empty_returns_dict_and_200(self):
        """Açık gün oturumu yokken 404 değil, 200 ve boş dict dönmeli."""
        res, status = handle_api_request(None, "GET", "/api/session/active", {}, {})
        self.assertEqual(status, 200)
        self.assertIsInstance(res, dict)

    def test_reset_database_requires_confirmation(self):
        """Kırmızı alan sıfırlaması onay kodu olmadan 400 dönmeli."""
        res, status = handle_api_request(None, "POST", "/api/system/reset-database", {}, {"onay_kodu": "YANLIS"})
        self.assertEqual(status, 400)
        self.assertIn("error", res)

    def test_reset_database_with_valid_confirmation(self):
        """Kırmızı alan sıfırlaması SIFIRLA onayıyla 200 dönmeli."""
        res, status = handle_api_request(None, "POST", "/api/system/reset-database", {}, {"onay_kodu": "SIFIRLA"})
        self.assertEqual(status, 200)
        self.assertTrue(res.get("success"))

    def test_employee_types_routes(self):
        """Personel türleri listeleme ve ekleme rotaları çalışmalı."""
        res, status = handle_api_request(None, "GET", "/api/employee-types", {}, {})
        self.assertEqual(status, 200)
        self.assertIsInstance(res, list)

        import time
        ts = int(time.time() * 1000)
        # Yeni tür ekleme
        res_post, status_post = handle_api_request(None, "POST", "/api/employee-types", {}, {"ad": f"Uzman {ts}"})
        self.assertIn(status_post, [201, 200])

    def test_debt_types_routes(self):
        """Personel borç çeşitleri listeleme ve ekleme rotaları çalışmalı."""
        import time
        ts = int(time.time() * 1000)
        res, status = handle_api_request(None, "GET", "/api/employee-debt-types", {}, {})
        self.assertEqual(status, 200)
        self.assertIsInstance(res, list)

        # Yeni borç çeşidi ekleme
        res_post, status_post = handle_api_request(None, "POST", "/api/employee-debt-types", {}, {
            "kod": f"ODUL_{ts}",
            "ad": f"Ödül Primi {ts}",
            "yon": "BORC"
        })
        self.assertIn(status_post, [201, 200])
    def test_institution_profile_routes(self):
        """Kurum profili getirme ve güncelleme çalışmalı."""
        res, status = handle_api_request(None, "GET", "/api/settings/profile", {}, {})
        self.assertEqual(status, 200)
        self.assertIsInstance(res, dict)
        self.assertIn("kurum_adi", res)

        # Güncelleme
        update_body = {
            "kurum_adi": "Evrensel Vakfı",
            "kurum_turu": "DERNEK_VAKIF",
            "para_birimi": "₺",
            "vergi_no": "1234567890",
            "eposta": "info@evrensel.org"
        }
        res_post, status_post = handle_api_request(None, "POST", "/api/settings/profile", {}, update_body)
        self.assertEqual(status_post, 200)
        self.assertTrue(res_post.get("success"))
        self.assertEqual(res_post["profile"]["kurum_adi"], "Evrensel Vakfı")

        # Fabrika ayarına geri al
        handle_api_request(None, "POST", "/api/settings/profile", {}, {"kurum_adi": "oftek", "kurum_turu": "GENEL", "para_birimi": "₺"})


if __name__ == "__main__":
    unittest.main()
