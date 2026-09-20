"""
Firma ve Borç Yönetimi API İşleyicileri (handlers_debts.py)
"""

from db_manager import get_db_connection
from accounting_engine import pay_company_debt


def handle_debt_routes(method, path, query, body):
    if path == "/api/companies" and method == "GET":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM cariler WHERE tip = 'FIRMA' ORDER BY unvan ASC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows, 200

    if path == "/api/customers" and method == "GET":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM cariler WHERE tip = 'MUSTERI' ORDER BY unvan ASC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows, 200

    if path == "/api/cariler" and method == "POST":
        tip = body.get("tip", "FIRMA").upper()
        unvan = body.get("unvan", "").strip()
        yetkili = body.get("yetkili", "").strip()
        telefon = body.get("telefon", "").strip()
        vergi_no = body.get("vergi_no", "").strip()
        hesap_kodu = body.get("hesap_kodu", "320.01" if tip == "FIRMA" else "120.01").strip()

        if not unvan:
            return {"error": "Cari unvanı zorunludur."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO cariler (tip, unvan, yetkili, telefon, vergi_no, hesap_kodu)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tip, unvan, yetkili, telefon, vergi_no, hesap_kodu))
        cari_id = cur.lastrowid
        conn.commit()
        conn.close()
        return {"success": True, "id": cari_id, "unvan": unvan}, 201

    if path == "/api/debts" and method == "GET":
        cari_id = query.get("cari_id", [None])[0]
        yil = query.get("yil", [None])[0]
        ay = query.get("ay", [None])[0]

        sql = "SELECT b.*, c.unvan as cari_unvan FROM borclar b JOIN cariler c ON c.id = b.cari_id WHERE 1=1"
        params = []
        if cari_id:
            sql += " AND b.cari_id = ?"
            params.append(cari_id)
        if yil:
            sql += " AND b.donem_yil = ?"
            params.append(yil)
        if ay:
            sql += " AND b.donem_ay = ?"
            params.append(ay)
        sql += " ORDER BY b.tarih DESC, b.id DESC"

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows, 200

    if path == "/api/debts" and method == "POST":
        gun_id = body.get("gun_id")
        cari_id = body.get("cari_id")
        toplam_tutar = float(body.get("toplam_tutar", 0))
        belge_no = body.get("belge_no", "").strip()
        vade_tarihi = body.get("vade_tarihi", "").strip()
        aciklama = body.get("aciklama", "").strip()

        if not gun_id or not cari_id or toplam_tutar <= 0:
            return {"error": "Geçerli bir gün oturumu, firma ve pozitif tutar zorunludur."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT tarih, donem_yil, donem_ay, durum FROM gun_oturumlar WHERE id = ?", (gun_id,))
        gun = cur.fetchone()
        if not gun or gun["durum"] != "ACIK":
            conn.close()
            return {"error": "İşlem yapılacak gün oturumu açık değil!"}, 400

        cur.execute("""
            INSERT INTO borclar (cari_id, gun_id, donem_yil, donem_ay, belge_no, tarih, vade_tarihi, toplam_tutar, odenen_tutar, kalan_tutar, durum, aciklama)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'ACIK', ?)
        """, (cari_id, gun_id, gun["donem_yil"], gun["donem_ay"], belge_no, gun["tarih"], vade_tarihi, toplam_tutar, toplam_tutar, aciklama))
        borc_id = cur.lastrowid
        cur.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id = ?", (toplam_tutar, cari_id))
        conn.commit()
        conn.close()
        return {"success": True, "id": borc_id}, 201

    if path == "/api/debts/pay" and method == "POST":
        gun_id = body.get("gun_id")
        borc_id = body.get("borc_id")
        tutar = float(body.get("tutar", 0))
        kaynak_hesap = body.get("kaynak_hesap", "100.01")
        aciklama = body.get("aciklama", "").strip()

        if not gun_id or not borc_id or tutar <= 0:
            return {"error": "Eksik parametreler veya geçersiz ödeme tutarı."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT tarih, donem_yil, donem_ay, durum FROM gun_oturumlar WHERE id = ?", (gun_id,))
        gun = cur.fetchone()
        if not gun or gun["durum"] != "ACIK":
            conn.close()
            return {"error": "Açık gün oturumu bulunamadı."}, 400

        cur.execute("SELECT cari_id FROM borclar WHERE id = ?", (borc_id,))
        borc = cur.fetchone()
        if not borc:
            conn.close()
            return {"error": "Borç kaydı bulunamadı."}, 404

        try:
            pay_company_debt(cur, borc_id, tutar, borc["cari_id"])
            cur.execute("""
                INSERT INTO gunluk_islemler (gun_id, donem_yil, donem_ay, islem_turu, kaynak_hesap, cari_id, tutar, tarih, aciklama)
                VALUES (?, ?, ?, 'BORC_ODEME', ?, ?, ?, ?, ?)
            """, (gun_id, gun["donem_yil"], gun["donem_ay"], kaynak_hesap, borc["cari_id"], tutar, gun["tarih"], aciklama))
            conn.commit()
            conn.close()
            return {"success": True, "message": "Ödeme başarıyla kaydedildi."}, 200
        except Exception as e:
            conn.rollback()
            conn.close()
            return {"error": str(e)}, 400

    return None, None
