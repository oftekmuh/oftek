"""
Sistem & Kurum Profili API İşleyicileri (handlers_settings.py)
Kurum ünvanı, türü, para birimi ve iletişim ayarlarını yönetir.
"""

from db_manager import get_db_connection


def handle_settings_routes(method, path, query, body):
    """Kurum profili ve sistem ayarları rotalarını yönetir."""

    if path == "/api/settings/profile" and method == "GET":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sistem_ayarlari WHERE id = 1")
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else {}, 200

    if path == "/api/settings/profile" and method == "POST":
        kurum_adi = str(body.get("kurum_adi", "")).strip() or "oftek"
        kurum_turu = str(body.get("kurum_turu", "")).strip().upper() or "GENEL"
        para_birimi = str(body.get("para_birimi", "")).strip() or "₺"
        vergi_no = str(body.get("vergi_no", "")).strip()
        adres = str(body.get("adres", "")).strip()
        telefon = str(body.get("telefon", "")).strip()
        eposta = str(body.get("eposta", "")).strip()
        web_adresi = str(body.get("web_adresi", "")).strip()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE sistem_ayarlari
            SET kurum_adi = ?, kurum_turu = ?, para_birimi = ?, vergi_no = ?,
                adres = ?, telefon = ?, eposta = ?, web_adresi = ?,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (kurum_adi, kurum_turu, para_birimi, vergi_no, adres, telefon, eposta, web_adresi))
        conn.commit()

        cur.execute("SELECT * FROM sistem_ayarlari WHERE id = 1")
        updated = cur.fetchone()
        conn.close()
        return {"success": True, "message": "Kurum profili başarıyla güncellendi.", "profile": dict(updated)}, 200

    return None, None
