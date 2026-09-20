import unittest
import os
import json
import sqlite3
from api_handlers import handle_api_request
import db_manager

class TestReportsAndModularFrontend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_manager.init_database()

    def test_01_html_structure_and_no_month_in_header(self):
        """Header'da ay seçici olmadığını, mali yıl butonları ve modüler scriptlerin olduğunu doğrular."""
        html_path = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. 0 select tag
        self.assertNotIn("<select", content)

        # 2. 0 tekdüzen
        self.assertNotIn("tekdüzen", content.lower())
        self.assertNotIn("tekduzen", content.lower())

        # 3. Header'da ay seçici popover ve buton YOK
        header_part = content.split('<header')[1].split('</header>')[0]
        self.assertNotIn("id=\"btn-month-display\"", header_part)
        self.assertNotIn("id=\"month-picker-popover\"", header_part)

        # 4. Header'da dinamik mali yıl seçici kapsayıcısı VAR
        self.assertIn("id=\"header-period-years\"", header_part)
        app_js_path = os.path.join(os.path.dirname(__file__), "..", "web", "js", "app.js")
        with open(app_js_path, "r", encoding="utf-8") as f:
            self.assertIn("initDynamicYearSelectors", f.read())

        # 5. Raporlar sekmesi VAR
        self.assertIn("id=\"tab-raporlar\"", content)
        self.assertIn("exportReportToExcel()", content)
        self.assertIn("switchTab('raporlar')", content)

        # 6. CSS ve Modüler JS bağlantıları
        self.assertIn('<link rel="stylesheet" href="css/style.css">', content)
        js_modules = [
            'js/api.js', 'js/session.js', 'js/dashboard.js', 'js/debts.js',
            'js/receivables.js', 'js/employees.js', 'js/vouchers.js',
            'js/accruals.js', 'js/accounts.js', 'js/settings.js',
            'js/reports.js', 'js/app.js'
        ]
        for mod in js_modules:
            self.assertIn(f'<script src="{mod}"></script>', content)

    def test_02_all_modular_js_files_exist_and_not_empty(self):
        """web/js/ altındaki 12 dosyanın ve css/style.css dosyasının var ve dolu olduğunu doğrular."""
        base_dir = os.path.join(os.path.dirname(__file__), "..", "web")
        css_file = os.path.join(base_dir, "css", "style.css")
        self.assertTrue(os.path.exists(css_file))
        self.assertGreater(os.path.getsize(css_file), 50)

        js_files = [
            'api.js', 'session.js', 'dashboard.js', 'debts.js',
            'receivables.js', 'employees.js', 'vouchers.js',
            'accruals.js', 'accounts.js', 'settings.js',
            'reports.js', 'app.js'
        ]
        for jf in js_files:
            p = os.path.join(base_dir, "js", jf)
            self.assertTrue(os.path.exists(p), f"{jf} dosyası bulunamadı!")
            self.assertGreater(os.path.getsize(p), 100, f"{jf} dosyası boş veya çok küçük!")

    def test_03_report_endpoints_response(self):
        """Raporlama API'lerinin başarılı yanıt verdiğini doğrular."""
        res, status = handle_api_request(None, "GET", "/api/reports/cash-flow", {"yil": "2026"}, {})
        self.assertEqual(status, 200)
        self.assertIn("ozet", res)
        self.assertIn("hareketler", res)

        res, status = handle_api_request(None, "GET", "/api/reports/balances", {}, {})
        self.assertEqual(status, 200)
        self.assertIn("toplam_alacak", res)
        self.assertIn("cariler", res)

        res, status = handle_api_request(None, "GET", "/api/reports/payroll", {"yil": "2026"}, {})
        self.assertEqual(status, 200)
        self.assertIn("toplam_hakedis", res)
        self.assertIn("personeller", res)

        res, status = handle_api_request(None, "GET", "/api/mizan", {}, {})
        self.assertEqual(status, 200)
        self.assertIsInstance(res, list)

    def test_04_muavin_and_voucher_detail_endpoints(self):
        """Muavin Defteri (yürüyen bakiye) ve Fiş Detay API'lerinin doğruluğunu test eder."""
        # Muavin defteri testi (kod '100' Kasa)
        res, status = handle_api_request(None, "GET", "/api/muavin", {"kod": "100"}, {})
        self.assertEqual(status, 200)
        self.assertIn("hesap", res)
        self.assertIn("ozet", res)
        self.assertIn("hareketler", res)
        self.assertIn("toplam_borc", res["ozet"])
        self.assertIn("toplam_alacak", res["ozet"])
        self.assertIn("bakiye", res["ozet"])

        # Fiş detay API'si (hatalı çağrı kontrolü)
        res, status = handle_api_request(None, "GET", "/api/vouchers/detail", {}, {})
        self.assertEqual(status, 400)

    def test_05_enhanced_report_ui_elements(self):
        """Index.html içindeki canlı raporlama filtreleri, muavin paneli ve fiş modalını doğrular."""
        html_path = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. 5 alt sekme
        self.assertIn("setReportSubTab('cash_flow')", content)
        self.assertIn("setReportSubTab('balances')", content)
        self.assertIn("setReportSubTab('payroll')", content)
        self.assertIn("setReportSubTab('mizan')", content)
        self.assertIn("setReportSubTab('muavin')", content)

        # 2. Hızlı dönem butonları ve serbest tarih
        self.assertIn("setReportQuickPeriod('today'", content)
        self.assertIn("setReportQuickPeriod('week'", content)
        self.assertIn("setReportQuickPeriod('month'", content)
        self.assertIn("setReportQuickPeriod('year'", content)
        self.assertIn("setReportQuickPeriod('all'", content)
        self.assertIn("id=\"rep-start-date\"", content)
        self.assertIn("id=\"rep-end-date\"", content)

        # 3. Canlı Tablo Arama Kutusu
        self.assertIn("id=\"rep-instant-search\"", content)
        self.assertIn("filterCurrentReportTable(this.value)", content)

        # 4. Muavin paneli
        self.assertIn("id=\"report-panel-muavin\"", content)
        self.assertIn("selectMuavinAccount('100')", content)
        self.assertIn("id=\"rep-muavin-table-body\"", content)

        # 5. Yevmiye Fişi İnceleme Modalı
        self.assertIn("id=\"modal-report-voucher-detail\"", content)
        self.assertIn("id=\"rep-vd-table-body\"", content)
        self.assertIn("id=\"rep-vd-balance-status\"", content)

    def test_06_new_logos_and_ui_branding(self):
        """Yeni logo varlıklarının (logo-sade, logo-isim) ve arayüz entegrasyonlarının doğruluğunu test eder."""
        base_dir = os.path.join(os.path.dirname(__file__), "..")
        logo_sade = os.path.join(base_dir, "web", "img", "logo-sade.png")
        logo_isim = os.path.join(base_dir, "web", "img", "logo-isim.png")

        # 1. Logo dosyaları mevcut ve dolu
        self.assertTrue(os.path.exists(logo_sade), "logo-sade.png dosyası web/img altında bulunamadı!")
        self.assertTrue(os.path.exists(logo_isim), "logo-isim.png dosyası web/img altında bulunamadı!")
        self.assertGreater(os.path.getsize(logo_sade), 10000)
        self.assertGreater(os.path.getsize(logo_isim), 10000)

        # 2. web/index.html logo entegrasyonu
        html_path = os.path.join(base_dir, "web", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('href="img/logo-sade.png"', content)
        self.assertIn('src="img/logo-sade.png"', content)
        self.assertIn('src="img/logo-isim.png"', content)

        # 3. kullanim_kilavuzu.html logo entegrasyonu
        guide_path = os.path.join(base_dir, "kullanim_kilavuzu.html")
        with open(guide_path, "r", encoding="utf-8") as f:
            guide_content = f.read()

        self.assertIn('logo-sade.png', guide_content)
        self.assertIn('logo-isim.png', guide_content)

if __name__ == "__main__":
    unittest.main()
