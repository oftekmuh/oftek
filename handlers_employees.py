"""
Personel ve Tahakkuk API İşleyicileri (handlers_employees.py)
"""

import re
from db_manager import get_db_connection
from accounting_engine import accrue_monthly_salaries, get_employee_balance


def handle_employee_routes(method, path, query, body):
    # 1. Personel Türleri (Kullanıcı Tanımlı)
    if path == "/api/employee-types" and method == "GET":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM personel_turleri WHERE aktif = 1 ORDER BY id ASC")
        types = [dict(r) for r in cur.fetchall()]
        conn.close()
        return types, 200

    if path == "/api/employee-types" and method == "POST":
        ad = body.get("ad", "").strip()
        kod = body.get("kod", "").strip().upper()
        if not ad:
            return {"error": "Personel türü adı zorunludur."}, 400
        if not kod:
            kod = re.sub(r'[^A-Z0-9_]', '_', ad.upper())[:30]

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO personel_turleri (kod, ad, aktif)
                VALUES (?, ?, 1)
                ON CONFLICT(kod) DO UPDATE SET ad = excluded.ad, aktif = 1
            """, (kod, ad))
            conn.commit()
            tur_id = cur.lastrowid
            conn.close()
            return {"success": True, "id": tur_id, "kod": kod, "ad": ad}, 201
        except Exception as e:
            conn.close()
            return {"error": f"Personel türü kaydedilemedi: {str(e)}"}, 400

    if path == "/api/employee-types" and method == "DELETE":
        kod = query.get("kod", [None])[0] or body.get("kod")
        tur_id = query.get("id", [None])[0] or body.get("id")
        if not kod and not tur_id:
            return {"error": "Silinecek tür kodu veya ID belirtilmedi."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        if kod:
            cur.execute("UPDATE personel_turleri SET aktif = 0 WHERE kod = ?", (kod,))
        else:
            cur.execute("UPDATE personel_turleri SET aktif = 0 WHERE id = ?", (tur_id,))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Personel türü kaldırıldı."}, 200

    # 2. Personel Kartları ve Ek Bilgiler
    if path == "/api/employees" and method == "GET":
        yil = query.get("yil", [None])[0]
        ay = query.get("ay", [None])[0]
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.*, COALESCE(pt.ad, 'Genel Personel') as personel_turu_ad
            FROM personeller p
            LEFT JOIN personel_turleri pt ON pt.kod = p.personel_turu_kod
            WHERE p.durum != 'PASIF'
            ORDER BY p.ad_soyad ASC
        """)
        employees = []
        for r in cur.fetchall():
            emp = dict(r)
            bakiye_bilgi = get_employee_balance(cur, emp["id"], int(yil) if yil else None, int(ay) if ay else None)
            emp.update(bakiye_bilgi)
            cur.execute("SELECT id, baslik, veri_tipi, deger FROM personel_ek_bilgiler WHERE personel_id = ? ORDER BY id ASC", (emp["id"],))
            emp["ek_bilgiler"] = [dict(eb) for eb in cur.fetchall()]
            employees.append(emp)
        conn.close()
        return employees, 200

    if path == "/api/employees" and method == "POST":
        ad_soyad = body.get("ad_soyad", "").strip()
        tc_kimlik = body.get("tc_kimlik", "").strip()
        telefon = body.get("telefon", "").strip()
        iban = body.get("iban", "").strip()
        maas = float(body.get("maas", 0))
        hesap_kodu = body.get("hesap_kodu", "335.01").strip()
        personel_turu_kod = body.get("personel_turu_kod", "GENEL").strip().upper()
        ek_bilgiler = body.get("ek_bilgiler", [])

        if not ad_soyad or maas < 0:
            return {"error": "Personel adı ve geçerli maaş zorunludur."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO personeller (ad_soyad, tc_kimlik, telefon, iban, maas, hesap_kodu, personel_turu_kod, durum)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'AKTIF')
        """, (ad_soyad, tc_kimlik, telefon, iban, maas, hesap_kodu, personel_turu_kod))
        emp_id = cur.lastrowid

        for item in ek_bilgiler:
            baslik = str(item.get("baslik", "")).strip()
            veri_tipi = str(item.get("veri_tipi", "METIN")).strip().upper()
            deger = str(item.get("deger", "")).strip()
            if baslik:
                cur.execute("""
                    INSERT INTO personel_ek_bilgiler (personel_id, baslik, veri_tipi, deger)
                    VALUES (?, ?, ?, ?)
                """, (emp_id, baslik, veri_tipi, deger))

        conn.commit()
        conn.close()
        return {"success": True, "id": emp_id, "ad_soyad": ad_soyad}, 201

    if path == "/api/employees" and method == "DELETE":
        emp_id = query.get("id", [None])[0] or body.get("id")
        if not emp_id:
            return {"error": "Silinecek personel ID belirtilmedi."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, ad_soyad FROM personeller WHERE id = ?", (emp_id,))
        emp = cur.fetchone()
        if not emp:
            conn.close()
            return {"error": "Personel bulunamadı."}, 404

        # Hareket kontrolü
        cur.execute("SELECT COUNT(*) FROM personel_tahakkuklari WHERE personel_id = ?", (emp_id,))
        tahakkuk_sayisi = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM gunluk_islemler WHERE personel_id = ?", (emp_id,))
        islem_sayisi = cur.fetchone()[0]

        if tahakkuk_sayisi > 0 or islem_sayisi > 0:
            cur.execute("UPDATE personeller SET durum = 'PASIF' WHERE id = ?", (emp_id,))
            msg = f"{emp['ad_soyad']} isimli personelin geçmiş kayıtları olduğu için kaydı pasife alındı."
        else:
            cur.execute("DELETE FROM personeller WHERE id = ?", (emp_id,))
            msg = f"{emp['ad_soyad']} personeli kalıcı olarak silindi."

        conn.commit()
        conn.close()
        return {"success": True, "message": msg}, 200

    if path == "/api/employees/accrue-month" and method == "POST":
        gun_id = body.get("gun_id")
        donem_yil = int(body.get("donem_yil", 0))
        donem_ay = int(body.get("donem_ay", 0))

        if not gun_id or not donem_yil or not donem_ay:
            return {"error": "Gün oturumu, yıl ve ay seçimi zorunludur."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT tarih, durum FROM gun_oturumlar WHERE id = ?", (gun_id,))
        gun = cur.fetchone()
        if not gun or gun["durum"] != "ACIK":
            conn.close()
            return {"error": "Açık gün oturumu bulunamadı."}, 400

        res = accrue_monthly_salaries(cur, gun_id, donem_yil, donem_ay, gun["tarih"])
        conn.commit()
        conn.close()
        return {"success": True, **res}, 200

    if path == "/api/employees/accrual" and method == "POST":
        gun_id = body.get("gun_id")
        personel_id = body.get("personel_id")
        tur = body.get("tur", "PRIM").upper()
        tutar = float(body.get("tutar", 0))
        aciklama = body.get("aciklama", "").strip()

        if not gun_id or not personel_id or tutar <= 0:
            return {"error": "Eksik parametreler veya geçersiz tutar."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT tarih, donem_yil, donem_ay, durum FROM gun_oturumlar WHERE id = ?", (gun_id,))
        gun = cur.fetchone()
        if not gun or gun["durum"] != "ACIK":
            conn.close()
            return {"error": "Açık gün oturumu bulunamadı."}, 400

        cur.execute("""
            INSERT INTO personel_tahakkuklari (personel_id, gun_id, donem_yil, donem_ay, tur, tekrar_tipi, tarih, tutar, aciklama)
            VALUES (?, ?, ?, ?, ?, 'TEK_SEFERLIK', ?, ?, ?)
        """, (personel_id, gun_id, gun["donem_yil"], gun["donem_ay"], tur, gun["tarih"], tutar, aciklama))
        conn.commit()
        conn.close()
        return {"success": True, "message": f"{tur} hakedişi tahakkuk ettirildi."}, 201

    if path == "/api/employees/pay" and method == "POST":
        gun_id = body.get("gun_id")
        personel_id = body.get("personel_id")
        tutar = float(body.get("tutar", 0))
        kaynak_hesap = body.get("kaynak_hesap", "100.01")
        aciklama = body.get("aciklama", "Personel Avans/Maaş Ödemesi").strip()

        if not gun_id or not personel_id or tutar <= 0:
            return {"error": "Eksik veya geçersiz ödeme bilgisi."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT tarih, donem_yil, donem_ay, durum FROM gun_oturumlar WHERE id = ?", (gun_id,))
        gun = cur.fetchone()
        if not gun or gun["durum"] != "ACIK":
            conn.close()
            return {"error": "Açık gün oturumu bulunamadı."}, 400

        cur.execute("""
            INSERT INTO gunluk_islemler (gun_id, donem_yil, donem_ay, islem_turu, kaynak_hesap, personel_id, tutar, tarih, aciklama)
            VALUES (?, ?, ?, 'PERSONEL_ODEME', ?, ?, ?, ?, ?)
        """, (gun_id, gun["donem_yil"], gun["donem_ay"], kaynak_hesap, personel_id, tutar, gun["tarih"], aciklama))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Personel ödemesi kaydedildi."}, 200

    return None, None
