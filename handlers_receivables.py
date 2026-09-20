"""
Alacak ve Tahsilat Dağıtım API İşleyicileri (handlers_receivables.py)
"""

from db_manager import get_db_connection
from accounting_engine import allocate_collection


def handle_receivable_routes(method, path, query, body):
    if path == "/api/receivables" and method == "GET":
        cari_id = query.get("cari_id", [None])[0]
        kategori = query.get("kategori", [None])[0]
        yil = query.get("yil", [None])[0]
        ay = query.get("ay", [None])[0]
        durum = query.get("durum", [None])[0]

        sql = "SELECT a.*, c.unvan as cari_unvan FROM alacaklar a JOIN cariler c ON c.id = a.cari_id WHERE 1=1"
        params = []
        if cari_id:
            sql += " AND a.cari_id = ?"
            params.append(cari_id)
        if kategori:
            sql += " AND a.kategori = ?"
            params.append(kategori)
        if yil:
            sql += " AND a.donem_yil = ?"
            params.append(yil)
        if ay:
            sql += " AND a.donem_ay = ?"
            params.append(ay)
        if durum:
            sql += " AND a.durum = ?"
            params.append(durum)
        sql += " ORDER BY a.tarih DESC, a.id DESC"

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows, 200

    if path == "/api/receivables" and method == "POST":
        gun_id = body.get("gun_id")
        cari_id = body.get("cari_id")
        kategori = body.get("kategori", "URUN_SATISI")
        toplam_tutar = float(body.get("toplam_tutar", 0))
        belge_no = body.get("belge_no", "").strip()
        vade_tarihi = body.get("vade_tarihi", "").strip()
        aciklama = body.get("aciklama", "").strip()

        if not gun_id or not cari_id or toplam_tutar <= 0:
            return {"error": "Geçerli müşteri, gün ve pozitif tutar zorunludur."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT tarih, donem_yil, donem_ay, durum FROM gun_oturumlar WHERE id = ?", (gun_id,))
        gun = cur.fetchone()
        if not gun or gun["durum"] != "ACIK":
            conn.close()
            return {"error": "Açık gün oturumu bulunamadı."}, 400

        cur.execute("""
            INSERT INTO alacaklar (cari_id, gun_id, donem_yil, donem_ay, kategori, belge_no, tarih, vade_tarihi, toplam_tutar, tahsil_edilen, kalan_tutar, durum, aciklama)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'ACIK', ?)
        """, (cari_id, gun_id, gun["donem_yil"], gun["donem_ay"], kategori, belge_no, gun["tarih"], vade_tarihi, toplam_tutar, toplam_tutar, aciklama))
        alacak_id = cur.lastrowid
        cur.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id = ?", (toplam_tutar, cari_id))
        conn.commit()
        conn.close()
        return {"success": True, "id": alacak_id}, 201

    if path == "/api/receivables/collect" and method == "POST":
        gun_id = body.get("gun_id")
        cari_id = body.get("cari_id")
        tutar = float(body.get("tutar", 0))
        kaynak_hesap = body.get("kaynak_hesap", "100.01")
        mod = body.get("mod", "FIFO").upper()
        secimler = body.get("secimler", [])
        aciklama = body.get("aciklama", "Müşteri Tahsilatı").strip()

        if not gun_id or not cari_id or tutar <= 0:
            return {"error": "Geçersiz tahsilat parametreleri."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT tarih, donem_yil, donem_ay, durum FROM gun_oturumlar WHERE id = ?", (gun_id,))
        gun = cur.fetchone()
        if not gun or gun["durum"] != "ACIK":
            conn.close()
            return {"error": "Açık gün oturumu bulunamadı."}, 400

        try:
            cur.execute("""
                INSERT INTO gunluk_islemler (gun_id, donem_yil, donem_ay, islem_turu, kaynak_hesap, cari_id, tutar, tarih, aciklama)
                VALUES (?, ?, ?, 'ALACAK_TAHSILAT', ?, ?, ?, ?, ?)
            """, (gun_id, gun["donem_yil"], gun["donem_ay"], kaynak_hesap, cari_id, tutar, gun["tarih"], aciklama))
            islem_id = cur.lastrowid

            allocate_collection(cur, cari_id, tutar, islem_id, mod=mod, secimler=secimler)
            conn.commit()
            conn.close()
            return {"success": True, "message": f"{mod} moduyla tahsilat dağıtıldı.", "islem_id": islem_id}, 200
        except Exception as e:
            conn.rollback()
            conn.close()
            return {"error": str(e)}, 400

    return None, None
