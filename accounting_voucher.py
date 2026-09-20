"""
Yevmiye Fişi Üretim Motoru (accounting_voucher.py)
Gün sonu kapanışında tüm operasyonları tarar ve çift taraflı yevmiye fişine dönüştürür.
"""


def close_day_and_generate_voucher(conn, gun_id):
    """
    Günü kapatır, o güne ait tüm operasyonları tek ve dengeli bir yevmiye fişine dönüştürür.
    """
    cursor = conn.cursor()

    cursor.execute("SELECT id, tarih, donem_yil, donem_ay, durum FROM gun_oturumlar WHERE id = ?", (gun_id,))
    gun = cursor.fetchone()
    if not gun:
        raise ValueError("Belirtilen gün oturumu bulunamadı.")
    if gun["durum"] != "ACIK":
        raise ValueError("Bu gün oturumu zaten kapatılmış.")

    tarih = gun["tarih"]
    yil = gun["donem_yil"]
    ay = gun["donem_ay"]
    voucher_rows = []

    # 1. Alacak Tahsilatları: 100/102 Borç, 120 Alacak
    cursor.execute("""
        SELECT i.tutar, i.kaynak_hesap, i.aciklama, c.unvan, c.hesap_kodu
        FROM gunluk_islemler i
        JOIN cariler c ON c.id = i.cari_id
        WHERE i.gun_id = ? AND i.islem_turu = 'ALACAK_TAHSILAT'
    """, (gun_id,))
    for r in cursor.fetchall():
        hesap = r["hesap_kodu"] or "120.01"
        kasa_hesap = r["kaynak_hesap"] or "100.01"
        aciklama = f"Tahsilat: {r['unvan']} ({r['aciklama'] or 'Cari Tahsilat'})"
        voucher_rows.append({"hesap": kasa_hesap, "aciklama": aciklama, "borc": float(r["tutar"]), "alacak": 0.0})
        voucher_rows.append({"hesap": hesap, "aciklama": aciklama, "borc": 0.0, "alacak": float(r["tutar"])})

    # 2. Firma Borç Ödemeleri: 320 Borç, 100/102 Alacak
    cursor.execute("""
        SELECT i.tutar, i.kaynak_hesap, i.aciklama, c.unvan, c.hesap_kodu
        FROM gunluk_islemler i
        JOIN cariler c ON c.id = i.cari_id
        WHERE i.gun_id = ? AND i.islem_turu = 'BORC_ODEME'
    """, (gun_id,))
    for r in cursor.fetchall():
        hesap = r["hesap_kodu"] or "320.01"
        kasa_hesap = r["kaynak_hesap"] or "100.01"
        aciklama = f"Ödeme: {r['unvan']} ({r['aciklama'] or 'Tedarikçi Ödemesi'})"
        voucher_rows.append({"hesap": hesap, "aciklama": aciklama, "borc": float(r["tutar"]), "alacak": 0.0})
        voucher_rows.append({"hesap": kasa_hesap, "aciklama": aciklama, "borc": 0.0, "alacak": float(r["tutar"])})

    # 3. Personel Ödemeleri: 335 Borç, 100/102 Alacak
    cursor.execute("""
        SELECT i.tutar, i.kaynak_hesap, i.aciklama, p.ad_soyad, p.hesap_kodu
        FROM gunluk_islemler i
        JOIN personeller p ON p.id = i.personel_id
        WHERE i.gun_id = ? AND i.islem_turu = 'PERSONEL_ODEME'
    """, (gun_id,))
    for r in cursor.fetchall():
        hesap = r["hesap_kodu"] or "335.01"
        kasa_hesap = r["kaynak_hesap"] or "100.01"
        aciklama = f"Personel Ödemesi: {r['ad_soyad']} ({r['aciklama'] or 'Maaş/Avans'})"
        voucher_rows.append({"hesap": hesap, "aciklama": aciklama, "borc": float(r["tutar"]), "alacak": 0.0})
        voucher_rows.append({"hesap": kasa_hesap, "aciklama": aciklama, "borc": 0.0, "alacak": float(r["tutar"])})

    # 4. Personel Tahakkukları: 770 Borç, 335 Alacak
    cursor.execute("""
        SELECT t.tutar, t.tur, t.aciklama, p.ad_soyad, p.hesap_kodu
        FROM personel_tahakkuklari t
        JOIN personeller p ON p.id = t.personel_id
        WHERE t.gun_id = ?
    """, (gun_id,))
    for r in cursor.fetchall():
        hesap = r["hesap_kodu"] or "335.01"
        aciklama = f"Personel Hakediş Tahakkuku: {r['ad_soyad']} [{r['tur']}] ({r['aciklama'] or ''})"
        voucher_rows.append({"hesap": "770.01", "aciklama": aciklama, "borc": float(r["tutar"]), "alacak": 0.0})
        voucher_rows.append({"hesap": hesap, "aciklama": aciklama, "borc": 0.0, "alacak": float(r["tutar"])})

    # 5. Yeni Satış / Alacak Tahakkukları: 120 Borç, 600 Alacak
    cursor.execute("""
        SELECT a.toplam_tutar, a.kategori, a.belge_no, a.aciklama, c.unvan, c.hesap_kodu
        FROM alacaklar a
        JOIN cariler c ON c.id = a.cari_id
        WHERE a.gun_id = ?
    """, (gun_id,))
    for r in cursor.fetchall():
        hesap = r["hesap_kodu"] or "120.01"
        aciklama = f"Satış/Alacak Tahakkuku: {r['unvan']} [{r['kategori']}] Belge: {r['belge_no'] or '-'}"
        voucher_rows.append({"hesap": hesap, "aciklama": aciklama, "borc": float(r["toplam_tutar"]), "alacak": 0.0})
        voucher_rows.append({"hesap": "600.20", "aciklama": aciklama, "borc": 0.0, "alacak": float(r["toplam_tutar"])})

    # 6. Yeni Alım / Borç Tahakkukları: 153 Borç, 320 Alacak
    cursor.execute("""
        SELECT b.toplam_tutar, b.belge_no, b.aciklama, c.unvan, c.hesap_kodu
        FROM borclar b
        JOIN cariler c ON c.id = b.cari_id
        WHERE b.gun_id = ?
    """, (gun_id,))
    for r in cursor.fetchall():
        hesap = r["hesap_kodu"] or "320.01"
        aciklama = f"Alım/Borç Tahakkuku: {r['unvan']} Belge: {r['belge_no'] or '-'}"
        voucher_rows.append({"hesap": "153.01", "aciklama": aciklama, "borc": float(r["toplam_tutar"]), "alacak": 0.0})
        voucher_rows.append({"hesap": hesap, "aciklama": aciklama, "borc": 0.0, "alacak": float(r["toplam_tutar"])})

    # 7. Normal Giderler: Gider Hesabı (770 vb.) Borç, Kasa/Banka (100/102) Alacak
    cursor.execute("""
        SELECT tutar, kaynak_hesap, karsi_hesap, kategori, aciklama
        FROM gunluk_islemler
        WHERE gun_id = ? AND islem_turu = 'NORMAL_GIDER'
    """, (gun_id,))
    for r in cursor.fetchall():
        gider_hesap = r["karsi_hesap"] or "770.01"
        kasa_hesap = r["kaynak_hesap"] or "100.01"
        aciklama = f"Gider [{r['kategori'] or 'Genel'}]: {r['aciklama'] or 'Nakit/Banka Gideri'}"
        voucher_rows.append({"hesap": gider_hesap, "aciklama": aciklama, "borc": float(r["tutar"]), "alacak": 0.0})
        voucher_rows.append({"hesap": kasa_hesap, "aciklama": aciklama, "borc": 0.0, "alacak": float(r["tutar"])})

    # 8. Normal Gelirler: Kasa/Banka (100/102) Borç, Gelir Hesabı (600/649 vb.) Alacak
    cursor.execute("""
        SELECT tutar, kaynak_hesap, karsi_hesap, kategori, aciklama
        FROM gunluk_islemler
        WHERE gun_id = ? AND islem_turu = 'NORMAL_GELIR'
    """, (gun_id,))
    for r in cursor.fetchall():
        kasa_hesap = r["kaynak_hesap"] or "100.01"
        gelir_hesap = r["karsi_hesap"] or "600.20"
        aciklama = f"Gelir [{r['kategori'] or 'Genel'}]: {r['aciklama'] or 'Nakit/Banka Geliri'}"
        voucher_rows.append({"hesap": kasa_hesap, "aciklama": aciklama, "borc": float(r["tutar"]), "alacak": 0.0})
        voucher_rows.append({"hesap": gelir_hesap, "aciklama": aciklama, "borc": 0.0, "alacak": float(r["tutar"])})

    # Yevmiye Fişi Kaydı
    fis_id = None
    if voucher_rows:
        tot_b = sum(r["borc"] for r in voucher_rows)
        tot_a = sum(r["alacak"] for r in voucher_rows)

        if abs(tot_b - tot_a) >= 0.01:
            raise ValueError(f"Muhasebe denkliği sağlanamadı! Borç: {tot_b:.2f} TL, Alacak: {tot_a:.2f} TL")

        cursor.execute("SELECT COALESCE(MAX(no), 0) + 1 FROM fisler")
        yeni_no = cursor.fetchone()[0]

        fis_aciklama = f"{tarih} Tarihli Gün Sonu Mahsup Fişi (Dönem: {yil}/{ay}, Oturum #{gun_id})"
        cursor.execute("""
            INSERT INTO fisler (no, tarih, tip, aciklama)
            VALUES (?, ?, 'MAHSUP', ?)
        """, (yeni_no, tarih, fis_aciklama))
        fis_id = cursor.lastrowid

        for idx, row in enumerate(voucher_rows, start=1):
            cursor.execute("""
                INSERT INTO fis_satirlari (fis_id, satir_no, hesap_kod, aciklama, borc, alacak)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (fis_id, idx, row["hesap"], row["aciklama"], row["borc"], row["alacak"]))

    # Gün Oturumunu Kapat ve Kilitle
    cursor.execute("""
        UPDATE gun_oturumlar
        SET durum = 'KAPALI', kapanis_zamani = CURRENT_TIMESTAMP, kapanis_fis_id = ?
        WHERE id = ?
    """, (fis_id, gun_id))

    return {
        "success": True,
        "gun_id": gun_id,
        "tarih": tarih,
        "donem_yil": yil,
        "donem_ay": ay,
        "fis_id": fis_id,
        "satir_sayisi": len(voucher_rows),
        "toplam_tutar": sum(r["borc"] for r in voucher_rows) if voucher_rows else 0.0
    }
