"""
Hesap Planı ve Excel Toplu Aktarım API İşleyicileri (handlers_accounts.py)
"""

from db_manager import get_db_connection


def handle_account_routes(method, path, query, body):
    # Toplu Excel/CSV Hesap Aktarımı
    if path == "/api/accounts/bulk" and method == "POST":
        accounts = body.get("accounts", [])
        clear_first = body.get("clear_first", False)

        if not accounts:
            return {"error": "Aktarılacak hesap listesi boş!"}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            if clear_first:
                cur.execute("SELECT COUNT(*) FROM fis_satirlari")
                if cur.fetchone()[0] > 0:
                    conn.close()
                    return {"error": "Yevmiye hareketleri varken hesap planı temizlenemez! Önce fişleri sıfırlayınız."}, 400
                cur.execute("DELETE FROM hesap_plani")

            inserted = 0
            for acc in accounts:
                kod = str(acc.get("kod", "")).strip()
                ad = str(acc.get("ad", "")).strip()
                karakter = str(acc.get("karakter", "AKTIF")).strip().upper()
                if karakter not in ["AKTIF", "PASIF"]:
                    karakter = "AKTIF"
                seviye = int(acc.get("seviye", kod.count(".") + 1 if "." in kod else 1))
                if kod and ad:
                    cur.execute("""
                        INSERT OR REPLACE INTO hesap_plani (kod, ad, karakter, seviye)
                        VALUES (?, ?, ?, ?)
                    """, (kod, ad, karakter, seviye))
                    inserted += 1

            conn.commit()
            conn.close()
            return {"success": True, "count": inserted, "message": f"{inserted} hesap veritabanına aktarıldı."}, 200
        except Exception as e:
            conn.rollback()
            conn.close()
            return {"error": str(e)}, 500

    return None, None
