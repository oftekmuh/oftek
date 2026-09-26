"""
Excel Toplu Aktarım API İşleyicileri (handlers_imports.py)
Personel kartları, çoklu yevmiye fişleri ve alacak/borç fatura tahakkuklarını
tek işlemde (hepsi ya da hiçbiri) veritabanına aktarır.
"""

import re
from datetime import date
from db_manager import get_db_connection
from accounting_voucher import _resolve_account, get_or_create_gun_id, next_voucher_no
from handlers_vouchers import validate_voucher_rows, VOUCHER_TYPE_MAP


def _text(val):
    return str(val if val is not None else "").strip()


def _amount(val):
    """Sayısal tutar veya '1.234,56' / '1234.56' biçimli metni float'a çevirir."""
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    s = _text(val).replace("₺", "").replace("TL", "").replace(" ", "")
    if not s:
        return 0.0
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return round(float(s), 2)


def _iso_date(val, default=None):
    """YYYY-MM-DD veya GG.AA.YYYY biçimli tarihi doğrulayıp ISO metne çevirir."""
    s = _text(val)
    if not s:
        return default
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r"^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$", s)
        if not m:
            raise ValueError(f"'{s}' geçerli bir tarih değil (GG.AA.YYYY bekleniyor)")
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return date(y, mo, d).isoformat()


def _row_label(item, idx):
    return f"Excel satır {item.get('satir') or idx}"


def _norm(s):
    return _text(s).casefold()


def _find_cari(cur, tip, ref):
    """Cariyi kod veya unvan (büyük/küçük harf duyarsız) ile bulur."""
    cur.execute("SELECT * FROM cariler WHERE tip = ? AND kod = ?", (tip, ref))
    row = cur.fetchone()
    if row:
        return row
    cur.execute("SELECT * FROM cariler WHERE tip = ?", (tip,))
    key = _norm(ref)
    for r in cur.fetchall():
        if _norm(r["unvan"]) == key:
            return r
    return None


def _import_employees(body):
    items = body.get("employees", [])
    update_existing = bool(body.get("update_existing", True))
    if not items:
        return {"error": "Aktarılacak personel listesi boş!"}, 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT kod, ad FROM personel_turleri")
        type_by_key = {}
        for r in cur.fetchall():
            type_by_key[_norm(r["kod"])] = r["kod"]
            type_by_key[_norm(r["ad"])] = r["kod"]

        cur.execute("SELECT id, ad_soyad, tc_kimlik FROM personeller WHERE durum != 'PASIF'")
        existing = cur.fetchall()
        by_tc = {_text(r["tc_kimlik"]): r["id"] for r in existing if _text(r["tc_kimlik"])}
        by_name = {_norm(r["ad_soyad"]): r["id"] for r in existing}

        errors, prepared = [], []
        for idx, it in enumerate(items, start=1):
            label = _row_label(it, idx)
            ad_soyad = _text(it.get("ad_soyad"))
            if not ad_soyad:
                errors.append(f"{label}: Ad Soyad boş olamaz.")
                continue
            try:
                maas = _amount(it.get("maas"))
            except ValueError:
                errors.append(f"{label}: Maaş tutarı geçersiz.")
                continue
            if maas < 0:
                errors.append(f"{label}: Maaş negatif olamaz.")
                continue
            prepared.append({
                "ad_soyad": ad_soyad,
                "tc_kimlik": _text(it.get("tc_kimlik")),
                "telefon": _text(it.get("telefon")),
                "iban": _text(it.get("iban")).replace(" ", "").upper(),
                "maas": maas,
                "hesap_kodu": _text(it.get("hesap_kodu")) or "335.01",
                "tur": _text(it.get("personel_turu")) or "GENEL",
            })

        if errors:
            conn.close()
            return {"error": "Aktarım yapılmadı. Hatalı satırlar:\n" + "\n".join(errors[:20]), "errors": errors}, 400

        added = updated = skipped = 0
        for p in prepared:
            tur_kod = type_by_key.get(_norm(p["tur"]))
            if not tur_kod:
                # Excel'de geçen yeni personel türünü otomatik tanımla
                tur_kod = re.sub(r'[^A-Z0-9_]', '_', p["tur"].upper())[:30]
                cur.execute("""
                    INSERT INTO personel_turleri (kod, ad, aktif) VALUES (?, ?, 1)
                    ON CONFLICT(kod) DO UPDATE SET aktif = 1
                """, (tur_kod, p["tur"]))
                type_by_key[_norm(p["tur"])] = tur_kod
                type_by_key[_norm(tur_kod)] = tur_kod

            emp_id = by_tc.get(p["tc_kimlik"]) if p["tc_kimlik"] else None
            if emp_id is None:
                emp_id = by_name.get(_norm(p["ad_soyad"]))

            if emp_id is not None:
                if not update_existing:
                    skipped += 1
                    continue
                cur.execute("""
                    UPDATE personeller
                    SET ad_soyad = ?, tc_kimlik = COALESCE(NULLIF(?, ''), tc_kimlik),
                        telefon = COALESCE(NULLIF(?, ''), telefon), iban = COALESCE(NULLIF(?, ''), iban),
                        maas = ?, hesap_kodu = ?, personel_turu_kod = ?
                    WHERE id = ?
                """, (p["ad_soyad"], p["tc_kimlik"], p["telefon"], p["iban"], p["maas"],
                      p["hesap_kodu"], tur_kod, emp_id))
                updated += 1
            else:
                cur.execute("""
                    INSERT INTO personeller (ad_soyad, tc_kimlik, telefon, iban, maas, hesap_kodu, personel_turu_kod, durum)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'AKTIF')
                """, (p["ad_soyad"], p["tc_kimlik"], p["telefon"], p["iban"], p["maas"], p["hesap_kodu"], tur_kod))
                new_id = cur.lastrowid
                if p["tc_kimlik"]:
                    by_tc[p["tc_kimlik"]] = new_id
                by_name[_norm(p["ad_soyad"])] = new_id
                added += 1

        conn.commit()
        conn.close()
        return {
            "success": True, "eklenen": added, "guncellenen": updated, "atlanan": skipped,
            "message": f"{added} personel eklendi, {updated} personel güncellendi" + (f", {skipped} kayıt atlandı." if skipped else ".")
        }, 200
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"error": f"Personel aktarımı sırasında hata: {str(e)}"}, 500


def _import_vouchers(body):
    vouchers = body.get("vouchers", [])
    tip = VOUCHER_TYPE_MAP.get(_text(body.get("tip", "MAHSUP")).upper(), "MAHSUP")
    if not vouchers:
        return {"error": "Aktarılacak fiş bulunamadı!"}, 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        errors, prepared = [], []
        for idx, v in enumerate(vouchers, start=1):
            grup = _text(v.get("grup")) or str(idx)
            try:
                tarih = _iso_date(v.get("tarih"))
            except ValueError as e:
                errors.append(f"Fiş '{grup}': {e}")
                continue
            if not tarih:
                errors.append(f"Fiş '{grup}': Tarih zorunludur.")
                continue
            rows = v.get("rows", [])
            if len(rows) < 2:
                errors.append(f"Fiş '{grup}': En az 2 satır (Borç ve Alacak) bulunmalıdır.")
                continue
            aciklama = _text(v.get("aciklama"))
            try:
                rows = [{**r, "borc": _amount(r.get("borc")), "alacak": _amount(r.get("alacak"))} for r in rows]
            except ValueError:
                errors.append(f"Fiş '{grup}': Geçersiz tutar formatı.")
                continue
            validated, toplam, err = validate_voucher_rows(cur, rows, aciklama)
            if err:
                errors.append(f"Fiş '{grup}': {err}")
                continue
            prepared.append((tarih, aciklama, validated, toplam))

        if errors:
            conn.close()
            return {"error": "Aktarım yapılmadı. Hatalı fişler:\n" + "\n".join(errors[:20]), "errors": errors}, 400

        no = next_voucher_no(cur)
        first_no = no
        genel_toplam = 0.0
        for tarih, aciklama, validated, toplam in prepared:
            cur.execute("INSERT INTO fisler (no, tarih, tip, aciklama) VALUES (?, ?, ?, ?)", (no, tarih, tip, aciklama))
            fis_id = cur.lastrowid
            for satir_no, hkod, s_desc, b_val, a_val in validated:
                cur.execute("""
                    INSERT INTO fis_satirlari (fis_id, satir_no, hesap_kod, aciklama, borc, alacak)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (fis_id, satir_no, hkod, s_desc, b_val, a_val))
            genel_toplam += toplam
            no += 1

        conn.commit()
        conn.close()
        last_no = no - 1
        rng = f"#{first_no}" if first_no == last_no else f"#{first_no} - #{last_no}"
        return {
            "success": True, "fis_sayisi": len(prepared), "ilk_no": first_no, "son_no": last_no,
            "toplam": round(genel_toplam, 2),
            "message": f"{len(prepared)} yevmiye fişi ({rng}) başarıyla aktarıldı."
        }, 201
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"error": f"Fiş aktarımı sırasında hata: {str(e)}"}, 500


# Fatura tahakkuku türleri: alacak (müşteri satış faturası) ve borç (tedarikçi alış faturası)
_INVOICE_KINDS = {
    "alacak": {
        "tablo": "alacaklar", "cari_tip": "MUSTERI", "cari_hesap": ["120.01", "120"],
        "karsi_varsayilan": "600", "etiket": "Alacak", "cari_etiket": "Müşteri",
    },
    "borc": {
        "tablo": "borclar", "cari_tip": "FIRMA", "cari_hesap": ["320.01", "320"],
        "karsi_varsayilan": "153", "etiket": "Borç", "cari_etiket": "Firma",
    },
}


def _import_invoices(body, kind):
    cfg = _INVOICE_KINDS[kind]
    items = body.get("kalemler", [])
    cari_olustur = bool(body.get("cari_olustur", True))
    varsayilan_karsi = _text(body.get("karsi_hesap")) or cfg["karsi_varsayilan"]
    if not items:
        return {"error": "Aktarılacak fatura satırı bulunamadı!"}, 400

    bugun = date.today().isoformat()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        errors, prepared = [], []
        new_caris = {}
        for idx, it in enumerate(items, start=1):
            label = _row_label(it, idx)
            cari_ref = _text(it.get("cari"))
            if not cari_ref:
                errors.append(f"{label}: {cfg['cari_etiket']} unvanı/kodu boş olamaz.")
                continue
            try:
                tutar = _amount(it.get("tutar"))
                tarih = _iso_date(it.get("tarih"), bugun)
                vade = _iso_date(it.get("vade_tarihi"), "")
            except ValueError as e:
                errors.append(f"{label}: {e}")
                continue
            if tutar <= 0:
                errors.append(f"{label}: Tutar sıfırdan büyük olmalıdır.")
                continue

            cari = _find_cari(cur, cfg["cari_tip"], cari_ref)
            if not cari and not cari_olustur:
                errors.append(f"{label}: '{cari_ref}' {cfg['cari_etiket'].lower()} kaydı bulunamadı.")
                continue
            if not cari:
                new_caris.setdefault(_norm(cari_ref), cari_ref)

            karsi_ref = _text(it.get("karsi_hesap")) or varsayilan_karsi
            karsi = _resolve_account(cur, [karsi_ref])
            cur.execute("SELECT 1 FROM hesap_plani WHERE kod = ?", (karsi,))
            if not cur.fetchone():
                errors.append(f"{label}: '{karsi_ref}' karşı hesabı hesap planında bulunamadı.")
                continue

            prepared.append({
                "cari_ref": cari_ref, "cari": cari, "tarih": tarih, "vade": vade, "tutar": tutar,
                "belge_no": _text(it.get("belge_no")),
                "kategori": _text(it.get("kategori")).upper().replace(" ", "_") or "URUN_SATISI",
                "aciklama": _text(it.get("aciklama")), "karsi": karsi,
            })

        if errors:
            conn.close()
            return {"error": "Aktarım yapılmadı. Hatalı satırlar:\n" + "\n".join(errors[:20]), "errors": errors}, 400

        # Eksik carileri oluştur
        created_caris = {}
        for key, unvan in new_caris.items():
            cur.execute("INSERT INTO cariler (tip, unvan, hesap_kodu) VALUES (?, ?, ?)",
                        (cfg["cari_tip"], unvan, cfg["cari_hesap"][0]))
            cur.execute("SELECT * FROM cariler WHERE id = ?", (cur.lastrowid,))
            created_caris[key] = cur.fetchone()

        # Her tarih için bir TAHAKKUK fişi kesilir
        by_date = {}
        for p in prepared:
            if p["cari"] is None:
                p["cari"] = created_caris[_norm(p["cari_ref"])]
            by_date.setdefault(p["tarih"], []).append(p)

        fis_nolari = []
        toplam = 0.0
        for tarih in sorted(by_date):
            kalemler = by_date[tarih]
            yil, ay = int(tarih[:4]), int(tarih[5:7])
            gun_id = get_or_create_gun_id(cur, tarih, yil, ay)
            fis_no = next_voucher_no(cur)
            fis_aciklama = f"{tarih} Excel {cfg['etiket']} Fatura Tahakkuku ({len(kalemler)} kalem)"
            cur.execute("INSERT INTO fisler (no, tarih, tip, aciklama) VALUES (?, ?, 'TAHAKKUK', ?)",
                        (fis_no, tarih, fis_aciklama))
            fis_id = cur.lastrowid
            fis_nolari.append(fis_no)

            satir_no = 0
            for p in kalemler:
                cari = p["cari"]
                cari_hesap = _resolve_account(cur, [cari["hesap_kodu"]] + cfg["cari_hesap"])
                desc = f"{cari['unvan']} Belge: {p['belge_no'] or '-'}" + (f" ({p['aciklama']})" if p["aciklama"] else "")
                if kind == "alacak":
                    borc_hesap, alacak_hesap = cari_hesap, p["karsi"]
                    cur.execute("""
                        INSERT INTO alacaklar (cari_id, gun_id, donem_yil, donem_ay, kategori, belge_no, tarih, vade_tarihi,
                                               toplam_tutar, tahsil_edilen, kalan_tutar, durum, aciklama, fis_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'ACIK', ?, ?)
                    """, (cari["id"], gun_id, yil, ay, p["kategori"], p["belge_no"], tarih, p["vade"],
                          p["tutar"], p["tutar"], p["aciklama"], fis_id))
                else:
                    borc_hesap, alacak_hesap = p["karsi"], cari_hesap
                    cur.execute("""
                        INSERT INTO borclar (cari_id, gun_id, donem_yil, donem_ay, belge_no, tarih, vade_tarihi,
                                             toplam_tutar, odenen_tutar, kalan_tutar, durum, aciklama, fis_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'ACIK', ?, ?)
                    """, (cari["id"], gun_id, yil, ay, p["belge_no"], tarih, p["vade"],
                          p["tutar"], p["tutar"], p["aciklama"], fis_id))
                cur.execute("UPDATE cariler SET bakiye = bakiye + ? WHERE id = ?", (p["tutar"], cari["id"]))

                for hesap, b_val, a_val in ((borc_hesap, p["tutar"], 0), (alacak_hesap, 0, p["tutar"])):
                    satir_no += 1
                    cur.execute("""
                        INSERT INTO fis_satirlari (fis_id, satir_no, hesap_kod, aciklama, borc, alacak)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (fis_id, satir_no, hesap, desc, b_val, a_val))
                toplam += p["tutar"]

        conn.commit()
        conn.close()
        return {
            "success": True, "kayit_sayisi": len(prepared), "yeni_cari": len(created_caris),
            "fis_nolari": fis_nolari, "toplam": round(toplam, 2),
            "message": f"{len(prepared)} {cfg['etiket'].lower()} faturası aktarıldı, {len(fis_nolari)} tahakkuk fişi kesildi"
                       + (f", {len(created_caris)} yeni cari açıldı." if created_caris else ".")
        }, 201
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"error": f"Fatura aktarımı sırasında hata: {str(e)}"}, 500


def handle_import_routes(method, path, query, body):
    if method != "POST":
        return None, None
    if path == "/api/employees/bulk":
        return _import_employees(body)
    if path == "/api/vouchers/bulk":
        return _import_vouchers(body)
    if path == "/api/receivables/bulk":
        return _import_invoices(body, "alacak")
    if path == "/api/debts/bulk":
        return _import_invoices(body, "borc")
    return None, None
