"""
oftek Raporlama, Mizan ve Dashboard Servis İşleyicisi
"""

from db_manager import get_db_connection, DB_FILENAME, DB_PATH


def _q(query, key, default=""):
    v = query.get(key, default)
    return v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else default)


def handle_report_routes(method, path, query, body):
    if method != "GET":
        return None, None

    # 1. Genel Durum & Sistem Bilgisi
    if path == "/api/status":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM fisler")
        voucher_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM hesap_plani")
        account_count = cur.fetchone()[0]
        conn.close()
        return {
            "status": "online",
            "db_file": DB_FILENAME,
            "db_path": DB_PATH,
            "voucher_count": voucher_count,
            "account_count": account_count
        }, 200

    # 2. Dashboard Özet Metrikleri
    if path == "/api/dashboard":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(borc - alacak), 0) FROM fis_satirlari 
            WHERE hesap_kod LIKE '100%' OR hesap_kod LIKE '102%'
        """)
        kasa = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(kalan_tutar), 0) FROM alacaklar WHERE durum != 'KAPANDI'")
        toplam_alacak = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(kalan_tutar), 0) FROM borclar WHERE durum != 'KAPANDI'")
        toplam_borc = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(tutar), 0) FROM personel_tahakkuklari")
        tot_hakedis = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(tutar), 0) FROM gunluk_islemler WHERE islem_turu = 'PERSONEL_ODEME'")
        tot_odenen = cur.fetchone()[0]
        personel_borc = max(0.0, tot_hakedis - tot_odenen)

        cur.execute("""
            SELECT f.id, f.no, f.tarih, f.tip, f.aciklama, COALESCE(SUM(s.borc), 0) as toplam
            FROM fisler f
            LEFT JOIN fis_satirlari s ON s.fis_id = f.id
            GROUP BY f.id
            ORDER BY f.no DESC
            LIMIT 5
        """)
        recent_vouchers = [dict(row) for row in cur.fetchall()]
        conn.close()
        return {
            "kasa": kasa,
            "toplam_alacak": toplam_alacak,
            "toplam_borc": toplam_borc,
            "personel_borc": personel_borc,
            "recent_vouchers": recent_vouchers
        }, 200

    # 3. Genel Geçici Mizan
    if path == "/api/mizan":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT h.kod, h.ad,
                   COALESCE(SUM(s.borc), 0) as tot_borc,
                   COALESCE(SUM(s.alacak), 0) as tot_alacak
            FROM hesap_plani h
            LEFT JOIN fis_satirlari s ON s.hesap_kod = h.kod
            GROUP BY h.kod, h.ad
            HAVING tot_borc > 0 OR tot_alacak > 0
            ORDER BY h.kod ASC
        """)
        mizan_rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return mizan_rows, 200

    # 4. Muavin Defteri (Hesap Ekstresi & Yürüyen Bakiye)
    if path == "/api/muavin":
        acc_kod = _q(query, "kod")
        start_date = _q(query, "start")
        end_date = _q(query, "end")
        if not acc_kod:
            return {"hesap": None, "ozet": {"toplam_borc": 0, "toplam_alacak": 0, "bakiye": 0}, "hareketler": []}, 200

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT kod, ad, karakter FROM hesap_plani WHERE kod = ?", (acc_kod,))
        hesap_row = cur.fetchone()
        hesap = dict(hesap_row) if hesap_row else {"kod": acc_kod, "ad": "", "karakter": "AKTIF"}

        sql = """
            SELECT f.id as fis_id, f.tarih, f.no, f.tip, s.aciklama, s.borc, s.alacak
            FROM fis_satirlari s
            JOIN fisler f ON f.id = s.fis_id
            WHERE s.hesap_kod = ?
        """
        params = [acc_kod]
        if start_date:
            sql += " AND f.tarih >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND f.tarih <= ?"
            params.append(end_date)
        sql += " ORDER BY f.tarih ASC, f.no ASC, s.satir_no ASC"
        cur.execute(sql, tuple(params))

        hareketler = []
        tot_borc, tot_alacak, yuruyen = 0.0, 0.0, 0.0
        for r in cur.fetchall():
            d = dict(r)
            b = d.get("borc", 0.0) or 0.0
            a = d.get("alacak", 0.0) or 0.0
            tot_borc += b
            tot_alacak += a
            yuruyen += (b - a)
            d["yuruyen_bakiye"] = yuruyen
            hareketler.append(d)

        conn.close()
        return {
            "hesap": hesap,
            "ozet": {
                "toplam_borc": tot_borc,
                "toplam_alacak": tot_alacak,
                "bakiye": tot_borc - tot_alacak
            },
            "hareketler": hareketler
        }, 200

    # 5. Kasa & Nakit Akış Raporu (Hızlı Filtreli)
    if path == "/api/reports/cash-flow":
        start_date = _q(query, "start")
        end_date = _q(query, "end")
        yil = _q(query, "yil")
        ay = _q(query, "ay")
        hesap = _q(query, "hesap")

        conn = get_db_connection()
        cur = conn.cursor()
        sql = """
            SELECT g.id, g.tarih, g.islem_turu, g.kategori, g.aciklama, g.tutar, g.karsi_hesap,
                   g.kaynak_hesap, c.unvan as cari_unvan, p.ad_soyad as personel_ad
            FROM gunluk_islemler g
            LEFT JOIN cariler c ON c.id = g.cari_id
            LEFT JOIN personeller p ON p.id = g.personel_id
            WHERE 1=1
        """
        params = []
        if start_date:
            sql += " AND g.tarih >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND g.tarih <= ?"
            params.append(end_date)
        if yil:
            sql += " AND g.donem_yil = ?"
            params.append(int(yil))
        if ay:
            sql += " AND g.donem_ay = ?"
            params.append(int(ay))
        if hesap:
            sql += " AND (g.kaynak_hesap LIKE ? OR g.karsi_hesap LIKE ?)"
            params.extend([f"{hesap}%", f"{hesap}%"])

        sql += " ORDER BY g.tarih DESC, g.id DESC"
        cur.execute(sql, tuple(params))

        tot_giris, tot_cikis = 0.0, 0.0
        hareketler = []
        for r in cur.fetchall():
            d = dict(r)
            t = d.get("tutar", 0.0) or 0.0
            if d.get("islem_turu") in ("TAHSILAT", "NORMAL_GELIR"):
                d["yon"], d["borc"], d["alacak"] = "GIRIS", t, 0.0
                tot_giris += t
            else:
                d["yon"], d["borc"], d["alacak"] = "CIKIS", 0.0, t
                tot_cikis += t
            hareketler.append(d)

        conn.close()
        return {
            "ozet": {
                "toplam_giris": tot_giris,
                "toplam_cikis": tot_cikis,
                "net_bakiye": tot_giris - tot_cikis
            },
            "hareketler": hareketler
        }, 200

    # 6. Cari Borç & Alacak Bakiye Raporu
    if path == "/api/reports/balances":
        tip = _q(query, "tip")
        sadece_bakiyeli = _q(query, "sadece_bakiyeli")

        conn = get_db_connection()
        cur = conn.cursor()
        sql = """
            SELECT c.id, c.unvan, c.tip, c.telefon, c.vergi_no,
                   COALESCE((SELECT SUM(kalan_tutar) FROM alacaklar WHERE cari_id = c.id AND durum != 'KAPANDI'), 0) as toplam_alacak,
                   COALESCE((SELECT SUM(kalan_tutar) FROM borclar WHERE cari_id = c.id AND durum != 'KAPANDI'), 0) as toplam_borc
            FROM cariler c
            WHERE 1=1
        """
        params = []
        if tip:
            sql += " AND c.tip = ?"
            params.append(tip)

        sql += " ORDER BY c.unvan ASC"
        cur.execute(sql, tuple(params))

        cariler = []
        tot_alacak, tot_borc = 0.0, 0.0
        for r in cur.fetchall():
            d = dict(r)
            bakiye = (d.get("toplam_alacak") or 0.0) - (d.get("toplam_borc") or 0.0)
            d["bakiye"] = bakiye
            if sadece_bakiyeli == "1" and abs(bakiye) < 0.005:
                continue
            tot_alacak += (d.get("toplam_alacak") or 0.0)
            tot_borc += (d.get("toplam_borc") or 0.0)
            cariler.append(d)

        conn.close()
        return {
            "toplam_alacak": tot_alacak,
            "toplam_borc": tot_borc,
            "net_pozisyon": tot_alacak - tot_borc,
            "cariler": cariler
        }, 200

    # 7. Personel Bordro / Hakediş & Kalan Bakiye Raporu
    if path == "/api/reports/payroll":
        yil = _q(query, "yil")
        ay = _q(query, "ay")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.ad_soyad, p.tc_kimlik, p.telefon, pt.ad as gorev,
                   COALESCE((SELECT SUM(tutar) FROM personel_tahakkuklari WHERE personel_id = p.id), 0) as toplam_hakedis,
                   COALESCE((SELECT SUM(tutar) FROM gunluk_islemler WHERE personel_id = p.id AND islem_turu = 'PERSONEL_ODEME'), 0) as toplam_odenen
            FROM personeller p
            LEFT JOIN personel_turleri pt ON pt.kod = p.personel_turu_kod
            WHERE p.durum = 'AKTIF'
            ORDER BY p.ad_soyad ASC
        """)
        personeller = []
        tot_hak, tot_ode = 0.0, 0.0
        for r in cur.fetchall():
            d = dict(r)
            h = d.get("toplam_hakedis") or 0.0
            o = d.get("toplam_odenen") or 0.0
            d["kalan_bakiye"] = max(0.0, h - o)
            tot_hak += h
            tot_ode += o
            personeller.append(d)

        conn.close()
        return {
            "toplam_hakedis": tot_hak,
            "toplam_odenen": tot_ode,
            "toplam_kalan": max(0.0, tot_hak - tot_ode),
            "personeller": personeller
        }, 200

    return None, None
