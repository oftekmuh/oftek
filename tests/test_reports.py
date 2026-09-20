"""
Raporlama ve Analiz Servisleri Test Paketi
"""

import unittest
from db_manager import init_database, get_db_connection, reset_all_operational_data
from handlers_reports import handle_report_routes
from handlers_session import handle_session_routes


class TestReportsAndAnalysis(unittest.TestCase):
    def setUp(self):
        init_database()
        conn = get_db_connection()
        reset_all_operational_data(conn)
        conn.close()

    def tearDown(self):
        conn = get_db_connection()
        reset_all_operational_data(conn)
        conn.close()

    def test_01_status_and_dashboard_routes(self):
        """Status ve Dashboard özetlerinin başarılı döndüğünü doğrular."""
        res, status = handle_report_routes("GET", "/api/status", {}, {})
        self.assertEqual(status, 200)
        self.assertEqual(res["status"], "online")
        self.assertIn("voucher_count", res)

        res, status = handle_report_routes("GET", "/api/dashboard", {}, {})
        self.assertEqual(status, 200)
        self.assertIn("kasa", res)
        self.assertIn("toplam_alacak", res)
        self.assertIn("toplam_borc", res)

    def test_02_reports_endpoints(self):
        """Nakit akış, cari bakiye ve personel bordro rapor rotalarını test eder."""
        # Nakit akış
        res, status = handle_report_routes("GET", "/api/reports/cash-flow", {"start": ["2026-01-01"], "end": ["2026-12-31"]}, {})
        self.assertEqual(status, 200)
        self.assertIn("ozet", res)
        self.assertIn("hareketler", res)

        # Cari bakiyeler
        res, status = handle_report_routes("GET", "/api/reports/balances", {}, {})
        self.assertEqual(status, 200)
        self.assertIn("toplam_alacak", res)
        self.assertIn("cariler", res)

        # Personel bordro
        res, status = handle_report_routes("GET", "/api/reports/payroll", {"yil": ["2026"], "ay": ["3"]}, {})
        self.assertEqual(status, 200)
        self.assertIn("toplam_hakedis", res)
        self.assertIn("personeller", res)


if __name__ == "__main__":
    unittest.main()
