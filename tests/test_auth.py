"""
Kimlik Doğrulama & Güvenlik Zırhı Testleri (tests/test_auth.py)
PBKDF2 şifreleme, oturum yönetimi ve korumalı API rotalarını test eder.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db_manager import init_database, get_db_connection
from auth_manager import (
    hash_password,
    verify_password,
    has_any_user,
    create_first_admin,
    authenticate_user,
    validate_session_token,
    terminate_session,
    change_password
)
from api_handlers import handle_api_request


class DummyAuthHandler:
    """Testler için token sağlayan sahte HTTP handler."""
    def __init__(self, token=""):
        self.token = token

    def _extract_token(self):
        return self.token


class TestAuthAndSecurity(unittest.TestCase):

    def setUp(self):
        init_database()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM oturumlar")
        cur.execute("DELETE FROM kullanicilar")
        conn.commit()
        conn.close()

    def test_01_password_hashing_and_verification(self):
        """PBKDF2-HMAC-SHA256 şifreleme ve doğrulama mantığını test eder."""
        password = "GizliSifre*2026"
        pwd_hash, salt = hash_password(password)

        self.assertNotEqual(password, pwd_hash)
        self.assertEqual(len(salt), 32)  # 16 byte hex = 32 karakter
        self.assertEqual(len(pwd_hash), 64)  # SHA-256 hex = 64 karakter

        # Doğru şifre teyidi
        self.assertTrue(verify_password(password, pwd_hash, salt))
        # Yanlış şifre reddi
        self.assertFalse(verify_password("YanlisSifre", pwd_hash, salt))

    def test_02_create_first_admin_and_prevent_duplicate(self):
        """İlk admin oluşturulur; ikinci kez kurulum yapılması engellenmelidir."""
        self.assertFalse(has_any_user())

        # İlk kurulum
        ok, msg, user, token = create_first_admin("yonetici", "Yonetici1234", "Baş Yönetici")
        self.assertTrue(ok)
        self.assertEqual(user["kullanici_adi"], "yonetici")
        self.assertTrue(len(token) > 0)
        self.assertTrue(has_any_user())

        # İkinci kez ilk kurulum çağrılamaz
        ok2, msg2, _, _ = create_first_admin("hacker", "hack1234", "Korsan")
        self.assertFalse(ok2)
        self.assertIn("zaten kayıtlı kullanıcı mevcuttur", msg2)

    def test_03_authenticate_user_and_token_lifecycle(self):
        """Giriş yapma, token geçerliliği ve çıkış yapma yaşam döngüsü."""
        create_first_admin("muhasebeci", "Muhas*8899", "Muhasebe Sorumlusu")

        # Yanlış şifre ile giriş
        ok, msg, _, _ = authenticate_user("muhasebeci", "YanlisSifre")
        self.assertFalse(ok)

        # Doğru şifre ile giriş
        ok, msg, user, token = authenticate_user("muhasebeci", "Muhas*8899")
        self.assertTrue(ok)
        self.assertEqual(user["kullanici_adi"], "muhasebeci")

        # Token doğrulama
        is_valid, token_user = validate_session_token(token)
        self.assertTrue(is_valid)
        self.assertEqual(token_user["id"], user["id"])

        # Oturumu kapatma (Logout)
        self.assertTrue(terminate_session(token))

        # Kapatılan token artık geçersiz olmalı
        is_valid_after, _ = validate_session_token(token)
        self.assertFalse(is_valid_after)

    def test_04_api_unauthorized_blocking(self):
        """Tokensız isteklerin 401 Unauthorized ile engellendiğini doğrular."""
        # Kullanıcı oluştur
        create_first_admin("patron", "Patron*345", "Şirket Sahibi")

        # Tokensız çağrı (Saldırgan konsoldan curl atıyor gibi)
        unauth_handler = DummyAuthHandler(token="")
        res, status = handle_api_request(unauth_handler, "GET", "/api/dashboard", {}, {})
        self.assertEqual(status, 401)
        self.assertIn("Yetkisiz", res.get("error", ""))

        # Geçersiz sahte token ile çağrı
        fake_handler = DummyAuthHandler(token="sahte_token_1234567890")
        res2, status2 = handle_api_request(fake_handler, "GET", "/api/dashboard", {}, {})
        self.assertEqual(status2, 401)

        # Geçerli token ile çağrı (Yetkili)
        _, _, _, valid_token = authenticate_user("patron", "Patron*345")
        auth_handler = DummyAuthHandler(token=valid_token)
        res3, status3 = handle_api_request(auth_handler, "GET", "/api/dashboard", {}, {})
        self.assertEqual(status3, 200)

    def test_05_change_password(self):
        """Şifre değiştirme fonksiyonu eski şifreyi doğrulamalıdır."""
        _, _, user, token = create_first_admin("kasiyer", "Kasa123", "Kasiyer Ali")
        user_id = user["id"]

        # Yanlış eski şifre
        ok, msg = change_password(user_id, "YanlisEskiSifre", "YeniKasa999")
        self.assertFalse(ok)

        # Doğru eski şifre
        ok, msg = change_password(user_id, "Kasa123", "YeniKasa999")
        self.assertTrue(ok)

        # Artık eski şifreyle giriş yapılamaz
        ok_old, _, _, _ = authenticate_user("kasiyer", "Kasa123")
        self.assertFalse(ok_old)

        # Yeni şifreyle giriş yapılabilir
        ok_new, _, _, _ = authenticate_user("kasiyer", "YeniKasa999")
        self.assertTrue(ok_new)


if __name__ == "__main__":
    unittest.main()
