"""
Muhasebe ve Hesaplama Motoru (accounting_engine.py)
FIFO & Seçimli Tahsilat Dağıtımı, Borç Ödeme, Dönemsel (Yıl/Ay) Personel Hakedişi.
"""

from accounting_voucher import close_day_and_generate_voucher


def allocate_collection(cursor, cari_id, tutar, islem_id, mod="FIFO", secimler=None):
    """
    Müşteriden yapılan tahsilatı açık alacaklara dağıtır.
    mod="FIFO" -> En eski vadeli/tarihli açık alacaktan başlayarak otomatik dağıtır.
    mod="SECIMLI" -> secimler=[{"alacak_id": 1, "tutar": 500}] listesine göre manuel dağıtır.
    """
    odenen_toplam = float(tutar)

    if mod == "SECIMLI" and secimler:
        toplam_secim = sum(float(s.get("tutar", 0)) for s in secimler)
        if abs(toplam_secim - odenen_toplam) > 0.01:
            raise ValueError(f"Seçilen faturalara dağıtılan toplam ({toplam_secim:.2f} TL) tahsilat tutarına ({odenen_toplam:.2f} TL) eşit olmalıdır!")

        for s in secimler:
            rec_id = int(s["alacak_id"])
            dagitilan = float(s["tutar"])
            if dagitilan <= 0:
                continue

            cursor.execute("SELECT kalan_tutar, tahsil_edilen FROM alacaklar WHERE id = ? AND cari_id = ?", (rec_id, cari_id))
            rec = cursor.fetchone()
            if not rec:
                raise ValueError(f"Fatura ID {rec_id} bulunamadı.")

            kalan = float(rec["kalan_tutar"])
            suanki_tahsil = float(rec["tahsil_edilen"])

            if dagitilan > (kalan + 0.01):
                raise ValueError(f"Fatura #{rec_id} için girilen tutar ({dagitilan:.2f} TL), kalan borçtan ({kalan:.2f} TL) fazla olamaz!")

            yeni_kalan = max(0.0, kalan - dagitilan)
            yeni_durum = "KAPANDI" if yeni_kalan <= 0.001 else "KISMI"

            cursor.execute("""
                UPDATE alacaklar
                SET tahsil_edilen = ?, kalan_tutar = ?, durum = ?
                WHERE id = ?
            """, (suanki_tahsil + dagitilan, yeni_kalan, yeni_durum, rec_id))

            cursor.execute("""
                INSERT INTO tahsilat_dagitimi (islem_id, alacak_id, dagitilan_tutar)
                VALUES (?, ?, ?)
            """, (islem_id, rec_id, dagitilan))

    else:
        # Standart FIFO Otomatik Dağıtım Modu
        cursor.execute("""
            SELECT id, kalan_tutar, toplam_tutar, tahsil_edilen
            FROM alacaklar
            WHERE cari_id = ? AND kalan_tutar > 0
            ORDER BY CASE WHEN vade_tarihi IS NOT NULL AND vade_tarihi != '' THEN vade_tarihi ELSE tarih END ASC, id ASC
        """, (cari_id,))
        open_receivables = cursor.fetchall()

        remaining = odenen_toplam
        for rec in open_receivables:
            if remaining <= 0:
                break

            rec_id = rec["id"]
            kalan = float(rec["kalan_tutar"])
            suanki_tahsil = float(rec["tahsil_edilen"])

            if remaining >= kalan:
                dagitilan = kalan
                yeni_kalan = 0.0
                yeni_durum = "KAPANDI"
                remaining -= kalan
            else:
                dagitilan = remaining
                yeni_kalan = kalan - remaining
                yeni_durum = "KISMI"
                remaining = 0.0

            cursor.execute("""
                UPDATE alacaklar
                SET tahsil_edilen = ?, kalan_tutar = ?, durum = ?
                WHERE id = ?
            """, (suanki_tahsil + dagitilan, yeni_kalan, yeni_durum, rec_id))

            cursor.execute("""
                INSERT INTO tahsilat_dagitimi (islem_id, alacak_id, dagitilan_tutar)
                VALUES (?, ?, ?)
            """, (islem_id, rec_id, dagitilan))

    # Carinin genel alacak bakiyesini düşür
    cursor.execute("UPDATE cariler SET bakiye = bakiye - ? WHERE id = ?", (odenen_toplam, cari_id))


def pay_company_debt(cursor, borc_id, tutar, cari_id):
    """Firmaya ait borç kaydına parçalı ödeme uygular."""
    cursor.execute("SELECT odenen_tutar, kalan_tutar, toplam_tutar FROM borclar WHERE id = ?", (borc_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError("Borç kaydı bulunamadı.")

    suanki_odenen = float(row["odenen_tutar"])
    suanki_kalan = float(row["kalan_tutar"])
    odeme = float(tutar)

    if odeme > (suanki_kalan + 0.01):
        raise ValueError(f"Ödeme tutarı ({odeme:.2f} TL) kalan borçtan ({suanki_kalan:.2f} TL) büyük olamaz!")

    yeni_odenen = suanki_odenen + odeme
    yeni_kalan = max(0.0, suanki_kalan - odeme)
    yeni_durum = "KAPANDI" if yeni_kalan <= 0.001 else "KISMI"

    cursor.execute("""
        UPDATE borclar
        SET odenen_tutar = ?, kalan_tutar = ?, durum = ?
        WHERE id = ?
    """, (yeni_odenen, yeni_kalan, yeni_durum, borc_id))

    cursor.execute("UPDATE cariler SET bakiye = bakiye - ? WHERE id = ?", (odeme, cari_id))


def accrue_monthly_salaries(cursor, gun_id, donem_yil, donem_ay, tarih):
    """
    Belirtilen yıl ve ay için tüm aktif personelin maaş tahakkuklarını tek tıkla oluşturur.
    Mükerrer tahakkukları otomatik filtreler.
    """
    cursor.execute("SELECT id, ad_soyad, maas FROM personeller WHERE durum = 'AKTIF' AND maas > 0")
    active_employees = cursor.fetchall()

    created_count = 0
    skipped_count = 0

    ay_isimleri = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    ay_metin = ay_isimleri[donem_ay - 1] if 1 <= donem_ay <= 12 else str(donem_ay)

    for emp in active_employees:
        emp_id = emp["id"]
        maas = float(emp["maas"])

        # Mükerrer kontrolü
        cursor.execute("""
            SELECT id FROM personel_tahakkuklari
            WHERE personel_id = ? AND donem_yil = ? AND donem_ay = ? AND tur = 'MAAS'
        """, (emp_id, donem_yil, donem_ay))

        if cursor.fetchone():
            skipped_count += 1
            continue

        aciklama = f"{donem_yil} Yılı {ay_metin} Ayı Maaş Tahakkuku"
        cursor.execute("""
            INSERT INTO personel_tahakkuklari (personel_id, gun_id, donem_yil, donem_ay, tur, tekrar_tipi, tarih, tutar, aciklama)
            VALUES (?, ?, ?, ?, 'MAAS', 'TEKRAR_EDEN_AYLIK', ?, ?, ?)
        """, (emp_id, gun_id, donem_yil, donem_ay, tarih, maas, aciklama))
        created_count += 1

    return {"created_count": created_count, "skipped_count": skipped_count}


def get_employee_balance(cursor, personel_id, donem_yil=None, donem_ay=None):
    """Personelin toplam hakediş, ödeme ve anlık borcunu hesaplar."""
    sql_tahakkuk = "SELECT COALESCE(SUM(tutar), 0) FROM personel_tahakkuklari WHERE personel_id = ?"
    params_t = [personel_id]
    if donem_yil:
        sql_tahakkuk += " AND donem_yil = ?"
        params_t.append(donem_yil)
    if donem_ay:
        sql_tahakkuk += " AND donem_ay = ?"
        params_t.append(donem_ay)
    cursor.execute(sql_tahakkuk, params_t)
    donem_hakedis = float(cursor.fetchone()[0])

    sql_odenen = "SELECT COALESCE(SUM(tutar), 0) FROM gunluk_islemler WHERE personel_id = ? AND islem_turu = 'PERSONEL_ODEME'"
    params_o = [personel_id]
    if donem_yil:
        sql_odenen += " AND donem_yil = ?"
        params_o.append(donem_yil)
    if donem_ay:
        sql_odenen += " AND donem_ay = ?"
        params_o.append(donem_ay)
    cursor.execute(sql_odenen, params_o)
    donem_odenen = float(cursor.fetchone()[0])

    # Kümülatif anlık toplam borç
    cursor.execute("SELECT COALESCE(SUM(tutar), 0) FROM personel_tahakkuklari WHERE personel_id = ?", (personel_id,))
    genel_hakedis = float(cursor.fetchone()[0])
    cursor.execute("SELECT COALESCE(SUM(tutar), 0) FROM gunluk_islemler WHERE personel_id = ? AND islem_turu = 'PERSONEL_ODEME'", (personel_id,))
    genel_odenen = float(cursor.fetchone()[0])

    return {
        "donem_hakedis": donem_hakedis,
        "donem_odenen": donem_odenen,
        "genel_hakedis": genel_hakedis,
        "genel_odenen": genel_odenen,
        "anlik_borc": max(0.0, genel_hakedis - genel_odenen)
    }
