"""
Personel Tahakkuk Fişi, Borç Çeşitleri ve Raporlama API Modülü (handlers_accruals.py)
"""

from db_manager import get_db_connection


def handle_accrual_routes(method, path, query, body):
    """Personel tahakkuk fişleri, borç çeşitleri ve rapor rotalarını işler."""

    # 1. Borç Çeşitleri Listesi
    if path == "/api/employee-debt-types" and method == "GET":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM personel_borc_turleri WHERE aktif = 1 ORDER BY id ASC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows, 200

    # 2. Yeni Borç Çeşidi Ekleme
    if path == "/api/employee-debt-types" and method == "POST":
        kod = str(body.get("kod", "")).strip().upper().replace(" ", "_")
        ad = str(body.get("ad", "")).strip()
        yon = str(body.get("yon", "BORC")).strip().upper()
        varsayilan_tutar = float(body.get("varsayilan_tutar", 0) or 0)

        if not kod or not ad:
            return {"error": "Tür kodu ve adı zorunludur."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO personel_borc_turleri (kod, ad, yon, varsayilan_tutar, aktif)
                VALUES (?, ?, ?, ?, 1)
            """, (kod, ad, yon, varsayilan_tutar))
            new_id = cur.lastrowid
            conn.commit()
            conn.close()
            return {"success": True, "id": new_id, "kod": kod, "ad": ad}, 201
        except Exception as e:
            conn.close()
            return {"error": f"Borç çeşidi eklenemedi: {str(e)}"}, 400

    # 3. Borç Çeşidi Silme
    if path == "/api/employee-debt-types" and method == "DELETE":
        type_id = query.get("id", [None])[0] or body.get("id")
        if not type_id:
            return {"error": "Silinecek borç çeşidi ID belirtilmedi."}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM personel_borc_turleri WHERE id = ?", (type_id,))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Borç çeşidi silindi."}, 200

    # 4. Personel Tahakkuk Fişi Kaydı
    if path == "/api/employees/accrual-voucher" and method == "POST":
        tarih = body.get("tarih")
        donem_yil = int(body.get("donem_yil", 0))
        donem_ay = int(body.get("donem_ay", 0))
        aciklama = body.get("aciklama", "").strip() or f"{donem_yil}/{donem_ay:02d} Personel Tahakkuk Fişi"
        satirlar = body.get("satirlar", [])

        if not tarih or not donem_yil or not donem_ay:
            return {"error": "Tarih, yıl ve ay seçimi zorunludur."}, 400

        if not satirlar:
            return {"error": "Tahakkuk fişinde en az bir personel satırı bulunmalıdır."}, 400

        conn = get_db_connection()
        cur = conn.cursor()

        valid_rows = []
        toplam_tutar = 0.0

        for idx, s in enumerate(satirlar, start=1):
            pid = s.get("personel_id")
            tur = str(s.get("tur", "MAAS")).strip().upper()
            try:
                tutar = round(float(s.get("tutar", 0)), 2)
            except (ValueError, TypeError):
                conn.close()
                return {"error": f"{idx}. satırda geçersiz tutar."}, 400

            if tutar <= 0:
                continue

            cur.execute("SELECT ad_soyad FROM personeller WHERE id = ?", (pid,))
            p_row = cur.fetchone()
            if not p_row:
                conn.close()
                return {"error": f"{idx}. satırdaki personel bulunamadı."}, 400

            s_desc = s.get("aciklama", "").strip() or f"{p_row['ad_soyad']} - {tur} Hakedişi"
            valid_rows.append((pid, tur, tutar, s_desc, p_row["ad_soyad"]))
            toplam_tutar += tutar

        if not valid_rows:
            conn.close()
            return {"error": "Tahakkuk edilecek geçerli tutarlı satır bulunamadı."}, 400

        toplam_tutar = round(toplam_tutar, 2)

        try:
            # Otomatik Genel Muhasebe Fişi (Tip: TAHAKKUK) oluştur
            cur.execute("SELECT COALESCE(MAX(no), 0) + 1 FROM fisler")
            fis_no = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO fisler (no, tarih, tip, aciklama)
                VALUES (?, ?, 'TAHAKKUK', ?)
            """, (fis_no, tarih, aciklama))
            fis_id = cur.lastrowid

            # Borç: 770.01 Personel Ücret ve Giderleri
            cur.execute("""
                INSERT INTO fis_satirlari (fis_id, satir_no, hesap_kod, aciklama, borc, alacak)
                VALUES (?, 1, '770.01', ?, ?, 0)
            """, (fis_id, aciklama, toplam_tutar))

            # Alacak: 335.01 Personele Borçlar
            cur.execute("""
                INSERT INTO fis_satirlari (fis_id, satir_no, hesap_kod, aciklama, borc, alacak)
                VALUES (?, 2, '335.01', ?, 0, ?)
            """, (fis_id, aciklama, toplam_tutar))

            # Personel Tahakkuk Satırlarını Kaydet
            cur.execute("SELECT id FROM gun_oturumlar WHERE durum = 'ACIK' ORDER BY id DESC LIMIT 1")
            act_gun = cur.fetchone()
            if act_gun:
                gun_id = act_gun[0]
            else:
                cur.execute("SELECT id FROM gun_oturumlar ORDER BY id DESC LIMIT 1")
                last_gun = cur.fetchone()
                if last_gun:
                    gun_id = last_gun[0]
                else:
                    cur.execute("""
                        INSERT INTO gun_oturumlar (tarih, donem_yil, donem_ay, durum, notlar)
                        VALUES (?, ?, ?, 'ACIK', 'Otomatik Gün Oturumu')
                    """, (tarih, donem_yil, donem_ay))
                    gun_id = cur.lastrowid

            for pid, tur, tutar, s_desc, p_name in valid_rows:
                cur.execute("""
                    INSERT INTO personel_tahakkuklari 
                    (personel_id, gun_id, donem_yil, donem_ay, tur, tekrar_tipi, tarih, tutar, aciklama, fis_id)
                    VALUES (?, ?, ?, ?, ?, 'TEK_SEFERLIK', ?, ?, ?, ?)
                """, (pid, gun_id, donem_yil, donem_ay, tur, tarih, tutar, s_desc, fis_id))

            conn.commit()
            conn.close()
            return {
                "success": True,
                "fis_id": fis_id,
                "fis_no": fis_no,
                "toplam_tutar": toplam_tutar,
                "kayit_sayisi": len(valid_rows),
                "message": f"#{fis_no} no'lu Personel Tahakkuk Fişi başarıyla oluşturuldu ({toplam_tutar:.2f} TL)."
            }, 201
        except Exception as e:
            conn.rollback()
            conn.close()
            return {"error": f"Tahakkuk fişi oluşturulurken hata: {str(e)}"}, 500

    # 5. Ay ve Borç Çeşidi Bazlı Personel Tahakkuk Raporu
    if path == "/api/employees/accrual-report" and method == "GET":
        yil = query.get("yil", [None])[0]
        ay = query.get("ay", [None])[0]
        tur = query.get("tur", [None])[0]
        personel_id = query.get("personel_id", [None])[0]

        sql = """
            SELECT pt.id, pt.personel_id, p.ad_soyad, pt.donem_yil, pt.donem_ay,
                   pt.tur, pt.tarih, pt.tutar, pt.aciklama, pt.fis_id, f.no as fis_no,
                   COALESCE(pbt.ad, pt.tur) as tur_adi
            FROM personel_tahakkuklari pt
            JOIN personeller p ON pt.personel_id = p.id
            LEFT JOIN fisler f ON pt.fis_id = f.id
            LEFT JOIN personel_borc_turleri pbt ON pt.tur = pbt.kod
            WHERE 1=1
        """
        params = []
        if yil:
            sql += " AND pt.donem_yil = ?"
            params.append(int(yil))
        if ay:
            sql += " AND pt.donem_ay = ?"
            params.append(int(ay))
        if tur and tur != "TUMU":
            sql += " AND pt.tur = ?"
            params.append(tur.strip().upper())
        if personel_id:
            sql += " AND pt.personel_id = ?"
            params.append(int(personel_id))

        sql += " ORDER BY pt.tarih DESC, pt.id DESC"

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        raw_rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        tur_toplamlari = {}
        personel_toplamlari = {}
        genel_toplam = 0.0

        for r in raw_rows:
            t = r["tur"]
            t_ad = r["tur_adi"]
            p_ad = r["ad_soyad"]
            val = float(r["tutar"])

            genel_toplam += val
            tur_toplamlari[t_ad] = round(tur_toplamlari.get(t_ad, 0.0) + val, 2)
            personel_toplamlari[p_ad] = round(personel_toplamlari.get(p_ad, 0.0) + val, 2)

        return {
            "satirlar": raw_rows,
            "tur_toplamlari": tur_toplamlari,
            "personel_toplamlari": personel_toplamlari,
            "genel_toplam": round(genel_toplam, 2),
            "kayit_sayisi": len(raw_rows)
        }, 200

    return None, None
