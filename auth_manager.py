"""
oftek Kimlik Doğrulama & Oturum Yönetim Motoru (auth_manager.py)
PBKDF2-HMAC-SHA256 ve secrets tabanlı, sıfır dış bağımlılıkla çalışan güvenlik altyapısı.
"""

import hmac
import hashlib
import secrets
from datetime import datetime
from db_manager import get_db_connection


PBKDF2_ITERATIONS = 100000


def hash_password(password: str, salt_hex: str = None) -> tuple[str, str]:
    """Şifreyi PBKDF2-HMAC-SHA256 ile tuzlayarak güvenli şekilde hash'ler."""
    if not salt_hex:
        salt_hex = secrets.token_hex(16)
    salt_bytes = bytes.fromhex(salt_hex)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        PBKDF2_ITERATIONS
    )
    return hash_bytes.hex(), salt_hex


def verify_password(password: str, stored_hash: str, salt_hex: str) -> bool:
    """Zamanlama saldırılarına karşı güvenli (timing attack-safe) şifre doğrulaması yapar."""
    try:
        computed_hash, _ = hash_password(password, salt_hex)
        return hmac.compare_digest(computed_hash, stored_hash)
    except Exception:
        return False


def has_any_user() -> bool:
    """Veritabanında kayıtlı en az bir kullanıcı olup olmadığını kontrol eder."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM kullanicilar")
        count = cur.fetchone()[0]
        return count > 0
    finally:
        conn.close()


def create_first_admin(username: str, password: str, full_name: str = "Yönetici") -> tuple[bool, str, dict, str]:
    """İlk kurulumda yönetici hesabını ve ilk oturum anahtarını oluşturur."""
    username = (username or "").strip()
    if len(username) < 3:
        return False, "Kullanıcı adı en az 3 karakter olmalıdır.", {}, ""
    if len(password or "") < 4:
        return False, "Şifre en az 4 karakter olmalıdır.", {}, ""

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM kullanicilar")
        if cur.fetchone()[0] > 0:
            return False, "Sistemde zaten kayıtlı kullanıcı mevcuttur.", {}, ""

        pwd_hash, salt = hash_password(password)
        cur.execute(
            """
            INSERT INTO kullanicilar (kullanici_adi, sifre_hash, salt, ad_soyad, son_giris_tarihi)
            VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
            """,
            (username, pwd_hash, salt, full_name.strip() or "Yönetici")
        )
        user_id = cur.lastrowid

        token = secrets.token_hex(32)
        cur.execute(
            "INSERT INTO oturumlar (token, kullanici_id) VALUES (?, ?)",
            (token, user_id)
        )
        conn.commit()

        user_info = {
            "id": user_id,
            "kullanici_adi": username,
            "ad_soyad": full_name.strip() or "Yönetici"
        }
        return True, "Yönetici hesabı başarıyla oluşturuldu.", user_info, token
    except Exception as e:
        conn.rollback()
        return False, f"Hesap oluşturulurken hata: {str(e)}", {}, ""
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> tuple[bool, str, dict, str]:
    """Kullanıcı adı ve şifreyi doğrular, geçerli ise yeni oturum anahtarı (token) üretir."""
    username = (username or "").strip()
    if not username or not password:
        return False, "Kullanıcı adı ve şifre zorunludur.", {}, ""

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, kullanici_adi, sifre_hash, salt, ad_soyad FROM kullanicilar WHERE kullanici_adi = ?",
            (username,)
        )
        row = cur.fetchone()
        if not row:
            return False, "Kullanıcı adı veya şifre hatalı.", {}, ""

        user_id, uname, stored_hash, salt, full_name = row
        if not verify_password(password, stored_hash, salt):
            return False, "Kullanıcı adı veya şifre hatalı.", {}, ""

        token = secrets.token_hex(32)
        cur.execute(
            "INSERT INTO oturumlar (token, kullanici_id) VALUES (?, ?)",
            (token, user_id)
        )
        cur.execute(
            "UPDATE kullanicilar SET son_giris_tarihi = datetime('now', 'localtime') WHERE id = ?",
            (user_id,)
        )
        conn.commit()

        user_info = {
            "id": user_id,
            "kullanici_adi": uname,
            "ad_soyad": full_name or uname
        }
        return True, "Giriş başarılı.", user_info, token
    except Exception as e:
        return False, f"Kimlik doğrulama hatası: {str(e)}", {}, ""
    finally:
        conn.close()


def validate_session_token(token: str) -> tuple[bool, dict]:
    """Verilen oturum anahtarının geçerliliğini denetler ve kullanıcı bilgilerini döner."""
    if not token or not isinstance(token, str):
        return False, {}

    token = token.strip()
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT u.id, u.kullanici_adi, u.ad_soyad
            FROM oturumlar o
            JOIN kullanicilar u ON o.kullanici_id = u.id
            WHERE o.token = ?
            """,
            (token,)
        )
        row = cur.fetchone()
        if not row:
            return False, {}

        # Son işlem zamanını güncelle
        cur.execute(
            "UPDATE oturumlar SET son_islem_tarihi = datetime('now', 'localtime') WHERE token = ?",
            (token,)
        )
        conn.commit()

        return True, {
            "id": row[0],
            "kullanici_adi": row[1],
            "ad_soyad": row[2] or row[1]
        }
    except Exception:
        return False, {}
    finally:
        conn.close()


def terminate_session(token: str) -> bool:
    """Oturum anahtarını veritabanından silerek oturumu güvenle sonlandırır (Logout)."""
    if not token:
        return False
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM oturumlar WHERE token = ?", (token.strip(),))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def change_password(user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
    """Mevcut şifreyi teyit ederek kullanıcının şifresini güvenle günceller."""
    if len(new_password or "") < 4:
        return False, "Yeni şifre en az 4 karakter olmalıdır."

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT sifre_hash, salt FROM kullanicilar WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            return False, "Kullanıcı bulunamadı."

        stored_hash, salt = row
        if not verify_password(old_password, stored_hash, salt):
            return False, "Mevcut şifreniz hatalı."

        new_hash, new_salt = hash_password(new_password)
        cur.execute(
            "UPDATE kullanicilar SET sifre_hash = ?, salt = ? WHERE id = ?",
            (new_hash, new_salt, user_id)
        )
        # Şifre değiştiğinde diğer eski oturumları kapat
        cur.execute("DELETE FROM oturumlar WHERE kullanici_id = ?", (user_id,))
        conn.commit()
        return True, "Şifreniz başarıyla değiştirildi. Lütfen yeni şifrenizle tekrar giriş yapınız."
    except Exception as e:
        conn.rollback()
        return False, f"Şifre değiştirme hatası: {str(e)}"
    finally:
        conn.close()
