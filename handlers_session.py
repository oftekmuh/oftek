"""
Gün Oturumu ve Günlük Hareket API İşleyicileri (handlers_session.py)
"""

from datetime import datetime
from db_manager import get_db_connection, reset_all_operational_data
from accounting_engine import close_day_and_generate_voucher


def handle_session_routes(method, path, query, body):
    if path in ["/api/system/reset-database", "/api/system/reset-all"] and method == "POST":
        onay_kodu = str(body.get("onay_kodu", "")).strip().upper()
        if onay_kodu != "SIFIRLA":
            return {"error": "Onay kodu hatalı. Veritabanını sıfırlamak için tam olarak 'SIFIRLA' yazmalısınız."}, 400

        conn = get_db_connection()
        try:
            reset_all_operational_data(conn)
            conn.close()
            return {"success": True, "message": "Tüm operasyonel veriler ve geçmiş kayıtlar başarıyla sıfırlandı."}, 200
        except Exception as e:
            conn.close()
            return {"error": f"Sıfırlama hatası: {str(e)}"}, 500

    if path == "/api/session/active" and method == "GET":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM gun_oturumlar WHERE durum = 'ACIK' ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        return (dict(row) if row else {}), 200

    if path == "/api/session/open" and method == "POST":
        tarih = body.get("tarih") or datetime.now().strftime("%Y-%m-%d")
        notlar = body.get("notlar", "")
        parts = tarih.split("-")
        donem_yil = int(parts[0])
        donem_ay = int(parts[1])

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, tarih FROM gun_oturumlar WHERE durum = 'ACIK'")
        open_session = cur.fetchone()
        if open_session:
            conn.close()
            return {"error": f"Halen açık bir gün oturumu var (#{open_session['id']} - {open_session['tarih']}). Önce o günü kapatmalısınız!"}, 400

        cur.execute("""
            INSERT INTO gun_oturumlar (tarih, donem_yil, donem_ay, durum, notlar)
            VALUES (?, ?, ?, 'ACIK', ?)
        """, (tarih, donem_yil, donem_ay, notlar))
        session_id = cur.lastrowid
        conn.commit()
        conn.close()
        return {"success": True, "id": session_id, "tarih": tarih, "donem_yil": donem_yil, "donem_ay": donem_ay}, 201

    if path == "/api/session/close" and method == "POST":
        gun_id = body.get("gun_id")
        if not gun_id:
            return {"error": "Kapatılacak gün ID belirtilmedi."}, 400
        conn = get_db_connection()
        try:
            res = close_day_and_generate_voucher(conn, gun_id)
            conn.commit()
            conn.close()
            return res, 200
        except Exception as e:
            conn.rollback()
            conn.close()
            return {"error": str(e)}, 400

    if path == "/api/daily-transactions" and method == "GET":
        gun_id = query.get("gun_id", [None])[0]
        if not gun_id:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id FROM gun_oturumlar WHERE durum = 'ACIK' ORDER BY id DESC LIMIT 1")
            r = cur.fetchone()
            gun_id = r["id"] if r else None
            conn.close()

        if not gun_id:
            return [], 200

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT i.*, 
                   c.unvan as cari_unvan,
                   p.ad_soyad as personel_ad_soyad
            FROM gunluk_islemler i
            LEFT JOIN cariler c ON c.id = i.cari_id
            LEFT JOIN personeller p ON p.id = i.personel_id
            WHERE i.gun_id = ?
            ORDER BY i.id DESC
        """, (gun_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows, 200

    if path == "/api/quick-expense" and method == "POST":
        gun_id = body.get("gun_id")
        tutar = float(body.get("tutar", 0))
        kaynak_hesap = body.get("kaynak_hesap", "100.01")
        karsi_hesap = body.get("karsi_hesap", "770.01")
        kategori = body.get("kategori", "DIGER")
        aciklama = body.get("aciklama", "").strip()

        if not gun_id or tutar <= 0:
            return {"error": "Geçerli bir gün oturumu ve pozitif tutar zorunludur."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT tarih, donem_yil, donem_ay, durum FROM gun_oturumlar WHERE id = ?", (gun_id,))
        gun = cur.fetchone()
        if not gun or gun["durum"] != "ACIK":
            conn.close()
            return {"error": "Açık gün oturumu bulunamadı."}, 400

        cur.execute("""
            INSERT INTO gunluk_islemler (gun_id, donem_yil, donem_ay, islem_turu, kaynak_hesap, karsi_hesap, kategori, tutar, tarih, aciklama)
            VALUES (?, ?, ?, 'NORMAL_GIDER', ?, ?, ?, ?, ?, ?)
        """, (gun_id, gun["donem_yil"], gun["donem_ay"], kaynak_hesap, karsi_hesap, kategori, tutar, gun["tarih"], aciklama))
        tx_id = cur.lastrowid
        conn.commit()
        conn.close()
        return {"success": True, "id": tx_id, "message": "Gider başarıyla kaydedildi."}, 201

    if path == "/api/quick-income" and method == "POST":
        gun_id = body.get("gun_id")
        tutar = float(body.get("tutar", 0))
        kaynak_hesap = body.get("kaynak_hesap", "100.01")
        karsi_hesap = body.get("karsi_hesap", "649.01")
        kategori = body.get("kategori", "DIGER")
        aciklama = body.get("aciklama", "").strip()

        if not gun_id or tutar <= 0:
            return {"error": "Geçerli bir gün oturumu ve pozitif tutar zorunludur."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT tarih, donem_yil, donem_ay, durum FROM gun_oturumlar WHERE id = ?", (gun_id,))
        gun = cur.fetchone()
        if not gun or gun["durum"] != "ACIK":
            conn.close()
            return {"error": "Açık gün oturumu bulunamadı."}, 400

        cur.execute("""
            INSERT INTO gunluk_islemler (gun_id, donem_yil, donem_ay, islem_turu, kaynak_hesap, karsi_hesap, kategori, tutar, tarih, aciklama)
            VALUES (?, ?, ?, 'NORMAL_GELIR', ?, ?, ?, ?, ?, ?)
        """, (gun_id, gun["donem_yil"], gun["donem_ay"], kaynak_hesap, karsi_hesap, kategori, tutar, gun["tarih"], aciklama))
        tx_id = cur.lastrowid
        conn.commit()
        conn.close()
        return {"success": True, "id": tx_id, "message": "Gelir başarıyla kaydedildi."}, 201

    return None, None
