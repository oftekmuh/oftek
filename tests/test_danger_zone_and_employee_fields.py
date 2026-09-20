"""
Kırmızı Tehlike Alanı (Danger Zone), Personel Türleri ve Dinamik Ek Bilgiler Testleri
"""

import unittest
from db_manager import init_database, get_db_connection, reset_all_operational_data
from handlers_session import handle_session_routes
from handlers_employees import handle_employee_routes


class TestDangerZoneAndEmployeeFields(unittest.TestCase):
    def setUp(self):
        init_database()
        conn = get_db_connection()
        reset_all_operational_data(conn)
        conn.close()

    def tearDown(self):
        conn = get_db_connection()
        reset_all_operational_data(conn)
        conn.close()

    def test_01_danger_zone_reset_validation(self):
        """Kırmızı alan sıfırlamasında yanlış onay kodunun reddedildiğini ve SIFIRLA ile sıfırlandığını test eder."""
        # 1. Yanlış kod ile deneme
        res, status = handle_session_routes("POST", "/api/system/reset-database", {}, {"onay_kodu": "YANLIS"})
        self.assertEqual(status, 400)
        self.assertIn("Onay kodu hatalı", res["error"])

        # 2. Örnek bir kayıt ekle
        handle_employee_routes("POST", "/api/employees", {}, {
            "ad_soyad": "Geçici Personel",
            "maas": 25000,
            "hesap_kodu": "335.01"
        })

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM personeller")
        self.assertEqual(cur.fetchone()[0], 1)
        conn.close()

        # 3. Doğru kod ile sıfırla
        res, status = handle_session_routes("POST", "/api/system/reset-database", {}, {"onay_kodu": "SIFIRLA"})
        self.assertEqual(status, 200)
        self.assertTrue(res["success"])

        # 4. Kayıtların silindiğini doğrula
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM personeller")
        self.assertEqual(cur.fetchone()[0], 0)
        conn.close()

    def test_02_employee_types_crud(self):
        """Personel türleri listeleme, ekleme ve pasife alma testleri."""
        # 1. Varsayılan türleri listele
        res, status = handle_employee_routes("GET", "/api/employee-types", {}, {})
        self.assertEqual(status, 200)
        codes = [t["kod"] for t in res]
        self.assertIn("GENEL", codes)
        self.assertIn("BEYAZ_YAKA", codes)

        # 2. Yeni tür ekle
        res, status = handle_employee_routes("POST", "/api/employee-types", {}, {
            "kod": "GUVENLIK",
            "ad": "Güvenlik Personeli"
        })
        self.assertEqual(status, 201)
        self.assertEqual(res["kod"], "GUVENLIK")

        # 3. Tekrar listele
        res, _ = handle_employee_routes("GET", "/api/employee-types", {}, {})
        codes = [t["kod"] for t in res]
        self.assertIn("GUVENLIK", codes)

        # 4. Türü sil
        res, status = handle_employee_routes("DELETE", "/api/employee-types", {"kod": ["GUVENLIK"]}, {})
        self.assertEqual(status, 200)

        res, _ = handle_employee_routes("GET", "/api/employee-types", {}, {})
        codes = [t["kod"] for t in res]
        self.assertNotIn("GUVENLIK", codes)

    def test_03_employee_custom_fields(self):
        """Personel eklerken dinamik ek alanların ve türün kaydedildiğini ve getirildiğini test eder."""
        body = {
            "ad_soyad": "Ayşe Yılmaz",
            "tc_kimlik": "12345678901",
            "telefon": "05551234567",
            "iban": "TR123456",
            "maas": 35000,
            "hesap_kodu": "335.01",
            "personel_turu_kod": "BEYAZ_YAKA",
            "ek_bilgiler": [
                {"baslik": "Kan Grubu", "veri_tipi": "METIN", "deger": "0 Rh+"},
                {"baslik": "İşe Giriş", "veri_tipi": "TARIH", "deger": "2026-03-01"},
                {"baslik": "Çocuk Sayısı", "veri_tipi": "SAYI", "deger": "2"}
            ]
        }
        res, status = handle_employee_routes("POST", "/api/employees", {}, body)
        self.assertEqual(status, 201)
        emp_id = res["id"]

        # Personelleri getir
        employees, status = handle_employee_routes("GET", "/api/employees", {}, {})
        self.assertEqual(status, 200)
        self.assertEqual(len(employees), 1)
        emp = employees[0]
        self.assertEqual(emp["ad_soyad"], "Ayşe Yılmaz")
        self.assertEqual(emp["personel_turu_kod"], "BEYAZ_YAKA")
        self.assertEqual(emp["personel_turu_ad"], "Beyaz Yaka / Ofis")

        # Ek bilgileri kontrol et
        ek_bilgiler = emp.get("ek_bilgiler", [])
        self.assertEqual(len(ek_bilgiler), 3)
        basliklar = [b["baslik"] for b in ek_bilgiler]
        self.assertIn("Kan Grubu", basliklar)
        self.assertIn("İşe Giriş", basliklar)
        self.assertIn("Çocuk Sayısı", basliklar)

    def test_04_html_danger_zone_in_settings_not_dashboard(self):
        """Kırmızı alanın dashboard'da olmadığını, ayarlar sekmesinde olduğunu ve yasaklı kelime/dropdown olmadığını doğrular."""
        import os
        html_path = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. 0 select tag
        self.assertNotIn("<select", content)

        # 2. 0 tekdüzen
        self.assertNotIn("tekdüzen", content.lower())
        self.assertNotIn("tekduzen", content.lower())

        # 3. Dashboard'da kırmızı alan yok
        dashboard_part = content.split('id="tab-dashboard"')[1].split('id="tab-gunluk_kasa"')[0]
        self.assertNotIn("openDangerResetModal()", dashboard_part)
        self.assertNotIn("Kırmızı Alan", dashboard_part)

        # 4. Ayarlar sekmesi mevcut ve kırmızı alan içeriyor
        self.assertIn('id="tab-ayarlar"', content)
        settings_part = content.split('id="tab-ayarlar"')[1].split('</main>')[0]
        self.assertIn("openDangerResetModal()", settings_part)
        self.assertIn("Kırmızı Alan", settings_part)
        self.assertIn("switchTab('ayarlar')", content)

        # 5. Sade "oftek" kuralı: Sekme başlığı sadece oftek olmalı, görünür kullanıcı arayüzünde (body) muhasebe geçmemeli
        title_tag = [line.strip() for line in content.splitlines() if "<title>" in line][0]
        self.assertEqual("<title>oftek</title>", title_tag)
        self.assertNotIn("oftek muhasebe", content.lower())
        body_part = content.split("<body")[1] if "<body" in content else content
        self.assertNotIn("muhasebe", body_part.lower())
        self.assertIn('id="header-brand-title"', content)
        self.assertIn('>oftek</h1>', content)

    def test_05_autocomplete_tab_first_select_logic(self):
        """Otomatik tamamlamada Tab tuşuna basıldığında ilk seçeneğin seçilip sonraki alana odaklanma mantığını doğrular."""
        import os
        html_path = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Modüler mimari: web/js/*.js dosyalarını da içeriğe ekle
        js_dir = os.path.join(os.path.dirname(__file__), "..", "web", "js")
        if os.path.exists(js_dir):
            for fname in os.listdir(js_dir):
                if fname.endswith(".js"):
                    with open(os.path.join(js_dir, fname), "r", encoding="utf-8") as jf:
                        content += "\n" + jf.read()

        # 1. focusNextElement fonksiyonu tanımlı
        self.assertIn("function focusNextElement", content)

        # 2. attachAccountAutocomplete içinde Tab ile ilk seçeneği alma
        self.assertIn("e.key === 'Tab' || e.key === 'Enter'", content)
        self.assertIn("chooseAccount(currentMatches[idx])", content)
        self.assertIn("Tab ⇥", content)

        # 3. attachDescriptionAutocomplete içinde Tab ile ilk seçeneği alma
        self.assertIn("chooseDesc(currentMatches[idx])", content)

        # 4. attachEmployeeAutocomplete ve attachCariAutocomplete içinde Tab desteği
        self.assertIn("chooseEmployee(currentMatches[idx])", content)
        self.assertIn("chooseCari(currentMatches[idx])", content)


if __name__ == "__main__":
    unittest.main()
