"""
Entegrasyon Testi (tests/test_api_integration.py)
API Handler uç noktalarının uçtan uca akışını test eder.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db_manager import init_database, get_db_connection
from api_handlers import handle_api_request


class TestApiIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Demo verilerini temizle ve sıfırdan başlat
        init_database()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM tahsilat_dagitimi")
        cur.execute("DELETE FROM gunluk_islemler")
        cur.execute("DELETE FROM alacaklar")
        cur.execute("DELETE FROM borclar")
        cur.execute("DELETE FROM personel_tahakkuklari")
        cur.execute("DELETE FROM personeller")
        cur.execute("DELETE FROM cariler")
        cur.execute("DELETE FROM gun_oturumlar")
        cur.execute("DELETE FROM fis_satirlari")
        cur.execute("DELETE FROM fisler")
        conn.commit()
        conn.close()

    def test_full_workflow(self):
        # 1. Gün Aç (Ara gün: 2026-03-15)
        res, status = handle_api_request(None, "POST", "/api/session/open", {}, {"tarih": "2026-03-15", "notlar": "Test Seansı"})
        self.assertEqual(status, 201)
        gun_id = res["id"]

        # 2. Firma Tanımla ve Borç Faturası Ekle
        c_res, c_stat = handle_api_request(None, "POST", "/api/cariler", {}, {
            "tip": "FIRMA", "unvan": "Anadolu Tedarik A.Ş.", "yetkili": "Ahmet Bey", "telefon": "5551112233"
        })
        self.assertEqual(c_stat, 201)
        firma_id = c_res["id"]

        d_res, d_stat = handle_api_request(None, "POST", "/api/debts", {}, {
            "gun_id": gun_id, "cari_id": firma_id, "toplam_tutar": 10000, "belge_no": "FAT-100", "vade_tarihi": "2026-03-30", "aciklama": "Hammadde Alımı"
        })
        self.assertEqual(d_stat, 201)
        borc_id = d_res["id"]

        # 3. Firmaya Parçalı Ödeme Yap (3.500 TL)
        p_res, p_stat = handle_api_request(None, "POST", "/api/debts/pay", {}, {
            "gun_id": gun_id, "borc_id": borc_id, "tutar": 3500, "kaynak_hesap": "100.01", "aciklama": "Kısmi Nakit Ödeme"
        })
        self.assertEqual(p_stat, 200)

        # 4. Personel Ekle, Maaş Tahakkuk Ettir ve Avans Öde
        emp_res, emp_stat = handle_api_request(None, "POST", "/api/employees", {}, {
            "ad_soyad": "Caner Demir", "tc_kimlik": "12345678901", "maas": 25000, "iban": "TR001"
        })
        self.assertEqual(emp_stat, 201)
        emp_id = emp_res["id"]

        # Maaş Tahakkuku (2026 / 3. Ay)
        m_res, m_stat = handle_api_request(None, "POST", "/api/employees/accrue-month", {}, {
            "gun_id": gun_id, "donem_yil": 2026, "donem_ay": 3
        })
        self.assertEqual(m_stat, 200)
        self.assertEqual(m_res["created_count"], 1)

        # Personele 5.000 TL Avans Öde
        pay_res, pay_stat = handle_api_request(None, "POST", "/api/employees/pay", {}, {
            "gun_id": gun_id, "personel_id": emp_id, "tutar": 5000, "kaynak_hesap": "100.01", "aciklama": "Maaş Avansı"
        })
        self.assertEqual(pay_stat, 200)

        # 5. Müşteri Tanımla, 2 Adet Satış Alacağı Ekle
        cust_res, cust_stat = handle_api_request(None, "POST", "/api/cariler", {}, {
            "tip": "MUSTERI", "unvan": "Marmara Perakende", "yetkili": "Selin Hanım"
        })
        self.assertEqual(cust_stat, 201)
        musteri_id = cust_res["id"]

        # Fatura 1: 4.000 TL
        handle_api_request(None, "POST", "/api/receivables", {}, {
            "gun_id": gun_id, "cari_id": musteri_id, "kategori": "URUN_SATISI", "toplam_tutar": 4000, "belge_no": "SAT-01", "vade_tarihi": "2026-03-20"
        })
        # Fatura 2: 6.000 TL
        handle_api_request(None, "POST", "/api/receivables", {}, {
            "gun_id": gun_id, "cari_id": musteri_id, "kategori": "SERVIS_HIZMET", "toplam_tutar": 6000, "belge_no": "SAT-02", "vade_tarihi": "2026-03-25"
        })

        # 6. Tahsilat Al (FIFO Modu: 5.500 TL)
        # Fatura 1 (4.000 TL) tamamen kapanmalı, Fatura 2'den 1.500 TL düşmeli (Kalan: 4.500 TL)
        col_res, col_stat = handle_api_request(None, "POST", "/api/receivables/collect", {}, {
            "gun_id": gun_id, "cari_id": musteri_id, "tutar": 5500, "kaynak_hesap": "100.01", "mod": "FIFO"
        })
        self.assertEqual(col_stat, 200)

        # 7. Normal Gelir & Gider Günlük Fiş Kaydı
        # Hızlı Gider: 750 TL Kırtasiye (770.02 / 100.01)
        exp_res, exp_stat = handle_api_request(None, "POST", "/api/quick-expense", {}, {
            "gun_id": gun_id, "tutar": 750.0, "kaynak_hesap": "100.01", "karsi_hesap": "770.02",
            "kategori": "KIRTASIYE", "aciklama": "Ofis kağıt ve toner alımı"
        })
        self.assertEqual(exp_stat, 201)

        # Hızlı Gelir: 1.250 TL Faiz/Olağan Gelir (102.01 / 649.01)
        inc_res, inc_stat = handle_api_request(None, "POST", "/api/quick-income", {}, {
            "gun_id": gun_id, "tutar": 1250.0, "kaynak_hesap": "102.01", "karsi_hesap": "649.01",
            "kategori": "DIGER_OLAGAN", "aciklama": "Banka mevduat faiz getirisi"
        })
        self.assertEqual(inc_stat, 201)

        # Günlük işlemleri sorgula
        daily_txs, daily_stat = handle_api_request(None, "GET", f"/api/daily-transactions?gun_id={gun_id}", {}, {})
        self.assertEqual(daily_stat, 200)
        self.assertTrue(any(t["islem_turu"] == "NORMAL_GIDER" for t in daily_txs))
        self.assertTrue(any(t["islem_turu"] == "NORMAL_GELIR" for t in daily_txs))

        # 8. Günü Kapat ve Fişe Dönüştür
        close_res, close_stat = handle_api_request(None, "POST", "/api/session/close", {}, {
            "gun_id": gun_id
        })
        self.assertEqual(close_stat, 200)
        self.assertTrue(close_res["success"])
        self.assertIsNotNone(close_res["fis_id"])

        # Fiş satırlarının Borç == Alacak denkliğini teyit et
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT SUM(borc) as b, SUM(alacak) as a FROM fis_satirlari WHERE fis_id = ?", (close_res["fis_id"],))
        totals = cur.fetchone()
        self.assertAlmostEqual(totals["b"], totals["a"], places=2)
        self.assertGreater(totals["b"], 0)
        conn.close()

    def test_manual_multi_row_voucher(self):
        """Satır satır borç ve alacak girilen yevmiye fişini test eder."""
        # 1. Sıradaki fiş numarasını al
        no_res, no_stat = handle_api_request(None, "GET", "/api/vouchers/next-no", {}, {})
        self.assertEqual(no_stat, 200)
        next_no = no_res["next_no"]

        # 2. Dengesiz fiş denemesi (Borç 1000, Alacak 900)
        unbal_res, unbal_stat = handle_api_request(None, "POST", "/api/vouchers", {}, {
            "no": next_no,
            "tarih": "2026-03-16",
            "tip": "MAHSUP",
            "aciklama": "Dengesiz Fiş",
            "rows": [
                {"hesap_kod": "770", "borc": 1000.0, "alacak": 0.0},
                {"hesap_kod": "100", "borc": 0.0, "alacak": 900.0}
            ]
        })
        self.assertEqual(unbal_stat, 400)
        self.assertIn("dengesiz", unbal_res["error"].lower())

        # 3. Geçersiz hesap kodlu fiş denemesi
        inv_res, inv_stat = handle_api_request(None, "POST", "/api/vouchers", {}, {
            "no": next_no,
            "tarih": "2026-03-16",
            "tip": "MAHSUP",
            "rows": [
                {"hesap_kod": "999.99", "borc": 500.0, "alacak": 0.0},
                {"hesap_kod": "100", "borc": 0.0, "alacak": 500.0}
            ]
        })
        self.assertEqual(inv_stat, 400)

        # 4. Dengeli 3 Satırlı Fiş (600 TL Kırtasiye + 120 TL KDV = 720 TL Kasa Çıkış)
        valid_res, valid_stat = handle_api_request(None, "POST", "/api/vouchers", {}, {
            "no": next_no,
            "tarih": "2026-03-16",
            "tip": "MAHSUP",
            "aciklama": "Ofis Malzemesi ve Kırtasiye Alımı",
            "rows": [
                {"hesap_kod": "770", "aciklama": "Kırtasiye Bedeli", "borc": 600.0, "alacak": 0.0},
                {"hesap_kod": "191", "aciklama": "%20 KDV", "borc": 120.0, "alacak": 0.0},
                {"hesap_kod": "100", "aciklama": "Kasa Nakit Ödeme", "borc": 0.0, "alacak": 720.0}
            ]
        })
        self.assertEqual(valid_stat, 201)
        self.assertTrue(valid_res["success"])
        self.assertEqual(valid_res["toplam"], 720.0)

        # 5. Veritabanındaki satırları doğrula
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT SUM(borc) as b, SUM(alacak) as a FROM fis_satirlari WHERE fis_id = ?", (valid_res["id"],))
        v_totals = cur.fetchone()
        self.assertEqual(v_totals["b"], 720.0)
        self.assertEqual(v_totals["a"], 720.0)
        conn.close()


if __name__ == "__main__":
    unittest.main()
