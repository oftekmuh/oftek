"""
Test Yardımcıları (tests/test_helpers.py)
Birim ve entegrasyon testlerinde kullanılmak üzere geçerli test oturumu ve token sağlar.
"""

import secrets
from db_manager import get_db_connection
from auth_manager import (
    create_first_admin,
    validate_session_token
)


class TestClientHandler:
    """Test istekleri için geçerli ve dinamik bir oturum anahtarı (token) sağlayan handler."""
    
    _cached_token = None

    @classmethod
    def get_token(cls):
        # 1. Bellekteki token hala geçerli mi?
        if cls._cached_token:
            valid, _ = validate_session_token(cls._cached_token)
            if valid:
                return cls._cached_token

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, kullanici_adi FROM kullanicilar ORDER BY id ASC LIMIT 1")
            row = cur.fetchone()

            if row:
                user_id = row[0]
                token = secrets.token_hex(32)
                cur.execute(
                    "INSERT INTO oturumlar (token, kullanici_id) VALUES (?, ?)",
                    (token, user_id)
                )
                conn.commit()
                cls._cached_token = token
                return token
        finally:
            conn.close()

        # Sistemde kullanıcı yoksa ilk admini oluştur
        ok, _, _, token = create_first_admin("admin", "Admin*123", "Test Yöneticisi")
        if ok:
            cls._cached_token = token
            return token

        return ""

    def _extract_token(self):
        return self.get_token()
