"""
Yevmiye Fişi Yönetimi ve Borç/Alacak Satır Girişi API'leri (handlers_vouchers.py)
"""

from db_manager import get_db_connection

VOUCHER_TYPE_MAP = {
    "MAHSUP": "MAHSUP",
    "DÜZELTME": "DUZELTME",
    "DUZELTME": "DUZELTME",
    "TAHAKKUK": "TAHAKKUK",
    "AÇILIŞ": "ACILIS",
    "ACILIS": "ACILIS",
    "KAPANIŞ": "KAPANIS",
    "KAPANIS": "KAPANIS"
}


def validate_voucher_rows(cur, rows, aciklama):
    """
    Fiş satırlarını doğrular (hesap varlığı, tek yönlü tutar, denklik).
    (validated_rows, toplam_borc, hata_mesaji) döndürür; hata yoksa hata_mesaji None'dır.
    """
    tot_borc = 0.0
    tot_alacak = 0.0
    validated_rows = []

    for idx, r in enumerate(rows, start=1):
        hkod = str(r.get("hesap_kod", "")).strip()
        if not hkod:
            return None, 0, f"{idx}. satırda hesap kodu boş bırakılamaz."

        # Hesap planında var mı kontrol et
        cur.execute("SELECT kod, ad FROM hesap_plani WHERE kod = ?", (hkod,))
        if not cur.fetchone():
            return None, 0, f"{idx}. satırdaki '{hkod}' hesap planında bulunamadı."

        try:
            b_val = round(float(r.get("borc", 0) or 0), 2)
            a_val = round(float(r.get("alacak", 0) or 0), 2)
        except (ValueError, TypeError):
            return None, 0, f"{idx}. satırda geçersiz tutar formatı."

        if b_val < 0 or a_val < 0:
            return None, 0, f"{idx}. satırda borç veya alacak tutarı negatif olamaz."

        if b_val == 0 and a_val == 0:
            return None, 0, f"{idx}. satırda hem borç hem alacak 0 olamaz."

        if b_val > 0 and a_val > 0:
            return None, 0, f"{idx}. satırda hem borç hem alacak aynı anda girilemez (Tek yönlü olmalı)."

        tot_borc += b_val
        tot_alacak += a_val
        satir_desc = str(r.get("aciklama", "") or "").strip() or aciklama
        validated_rows.append((idx, hkod, satir_desc, b_val, a_val))

    tot_borc = round(tot_borc, 2)
    tot_alacak = round(tot_alacak, 2)

    if tot_borc <= 0:
        return None, 0, "Fiş toplamı 0'dan büyük olmalıdır."

    if abs(tot_borc - tot_alacak) >= 0.01:
        return None, 0, f"Fiş dengesiz! Toplam Borç ({tot_borc:.2f} TL) ile Toplam Alacak ({tot_alacak:.2f} TL) eşit olmalıdır."

    return validated_rows, tot_borc, None


def handle_voucher_routes(method, path, query, body):
    """Yevmiye fişleri ile ilgili REST API rotalarını işler."""

    if path == "/api/vouchers/next-no" and method == "GET":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(MAX(no), 0) + 1 FROM fisler")
        next_no = cur.fetchone()[0]
        conn.close()
        return {"next_no": next_no}, 200

    if path == "/api/vouchers/descriptions" and method == "GET":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT aciklama FROM fisler WHERE aciklama IS NOT NULL AND TRIM(aciklama) != ''
            UNION
            SELECT DISTINCT aciklama FROM fis_satirlari WHERE aciklama IS NOT NULL AND TRIM(aciklama) != ''
            UNION
            SELECT DISTINCT aciklama FROM gunluk_islemler WHERE aciklama IS NOT NULL AND TRIM(aciklama) != ''
            ORDER BY aciklama ASC
            LIMIT 100
        """)
        descs = [r[0] for r in cur.fetchall()]
        conn.close()
        return {"descriptions": descs}, 200

    if path == "/api/vouchers" and method == "GET":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT f.id, f.no, f.tarih, f.tip, f.aciklama,
                   s.satir_no, s.hesap_kod, h.ad as hesap_ad, s.aciklama as satir_aciklama, s.borc, s.alacak
            FROM fisler f
            JOIN fis_satirlari s ON s.fis_id = f.id
            LEFT JOIN hesap_plani h ON h.kod = s.hesap_kod
            ORDER BY f.no ASC, s.satir_no ASC
        """)
        vouchers_map = {}
        for r in cur.fetchall():
            fid = r["id"]
            if fid not in vouchers_map:
                vouchers_map[fid] = {
                    "id": r["id"], "no": r["no"], "tarih": r["tarih"],
                    "tip": r["tip"], "aciklama": r["aciklama"], "rows": []
                }
            vouchers_map[fid]["rows"].append({
                "satir_no": r["satir_no"], "hesap_kod": r["hesap_kod"],
                "hesap_ad": r["hesap_ad"] or "", "aciklama": r["satir_aciklama"] or "",
                "borc": r["borc"], "alacak": r["alacak"]
            })
        conn.close()
        return list(vouchers_map.values()), 200

    if path == "/api/vouchers/detail" and method == "GET":
        def _get_q(k):
            v = query.get(k, "")
            return v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else "")
        v_no = _get_q("no")
        v_id = _get_q("id")
        conn = get_db_connection()
        cur = conn.cursor()
        if v_no:
            cur.execute("SELECT id, no, tarih, tip, aciklama FROM fisler WHERE no = ?", (int(v_no),))
        elif v_id:
            cur.execute("SELECT id, no, tarih, tip, aciklama FROM fisler WHERE id = ?", (int(v_id),))
        else:
            conn.close()
            return {"error": "Fiş numarası veya id zorunludur"}, 400

        frow = cur.fetchone()
        if not frow:
            conn.close()
            return {"error": "Fiş bulunamadı"}, 404

        v_data = dict(frow)
        cur.execute("""
            SELECT s.satir_no, s.hesap_kod, h.ad as hesap_ad, s.aciklama, s.borc, s.alacak
            FROM fis_satirlari s
            LEFT JOIN hesap_plani h ON h.kod = s.hesap_kod
            WHERE s.fis_id = ?
            ORDER BY s.satir_no ASC
        """, (v_data["id"],))
        v_data["rows"] = [dict(r) for r in cur.fetchall()]
        conn.close()
        return v_data, 200

    if path == "/api/vouchers" and method == "POST":
        no = body.get("no")
        tarih = body.get("tarih")
        raw_tip = str(body.get("tip", "MAHSUP")).upper().strip()
        tip = VOUCHER_TYPE_MAP.get(raw_tip, "MAHSUP")
        aciklama = body.get("aciklama", "").strip()
        rows = body.get("rows", [])

        if not rows or len(rows) < 2:
            return {"error": "Bir yevmiye fişinde en az 2 satır (Borç ve Alacak) bulunmalıdır."}, 400

        if not tarih:
            return {"error": "Fiş tarihi zorunludur."}, 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Fiş numarası verilmediyse sıradakini al
        if not no:
            cur.execute("SELECT COALESCE(MAX(no), 0) + 1 FROM fisler")
            no = cur.fetchone()[0]
        else:
            try:
                no = int(no)
            except ValueError:
                conn.close()
                return {"error": "Geçerli bir fiş numarası giriniz."}, 400

            # Numara çakışması kontrolü
            cur.execute("SELECT id FROM fisler WHERE no = ?", (no,))
            if cur.fetchone():
                conn.close()
                return {"error": f"#{no} numaralı yevmiye fişi zaten mevcut! Başka bir numara seçiniz."}, 400

        validated_rows, tot_borc, err = validate_voucher_rows(cur, rows, aciklama)
        if err:
            conn.close()
            return {"error": err}, 400

        try:
            cur.execute("""
                INSERT INTO fisler (no, tarih, tip, aciklama)
                VALUES (?, ?, ?, ?)
            """, (no, tarih, tip, aciklama))
            fis_id = cur.lastrowid

            for idx, hkod, s_desc, b_val, a_val in validated_rows:
                cur.execute("""
                    INSERT INTO fis_satirlari (fis_id, satir_no, hesap_kod, aciklama, borc, alacak)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (fis_id, idx, hkod, s_desc, b_val, a_val))

            conn.commit()
            conn.close()
            return {
                "success": True,
                "id": fis_id,
                "no": no,
                "toplam": tot_borc,
                "message": f"#{no} no'lu Yevmiye Fişi ({tip}) başarıyla kaydedildi."
            }, 201
        except Exception as e:
            conn.rollback()
            conn.close()
            return {"error": f"Fiş kaydedilirken hata oluştu: {str(e)}"}, 500

    return None, None
