"""
Kimlik Doğrulama & Oturum REST API İşleyicisi (handlers_auth.py)
/api/auth/* uç noktalarını yönetir.
"""

from auth_manager import (
    has_any_user,
    create_first_admin,
    authenticate_user,
    terminate_session,
    change_password
)


def handle_auth_api(method: str, path: str, query: dict, body: dict, current_user: dict = None, token: str = "") -> tuple[dict, int]:
    """Kimlik doğrulama rotalarını yönetir."""
    
    # 1. Durum Kontrolü (Kurulum gerekli mi? Oturum açık mı?)
    if method == "GET" and path == "/api/auth/status":
        setup_required = not has_any_user()
        authenticated = bool(current_user and current_user.get("id"))
        return {
            "success": True,
            "setup_required": setup_required,
            "authenticated": authenticated,
            "user": current_user or {}
        }, 200

    # 2. İlk Yönetici Kurulumu (Yalnızca kullanıcı yokken çalışır)
    if method == "POST" and path == "/api/auth/setup":
        username = body.get("kullanici_adi") or body.get("username")
        password = body.get("sifre") or body.get("password")
        full_name = body.get("ad_soyad") or body.get("full_name") or "Yönetici"
        
        ok, msg, user_info, new_token = create_first_admin(username, password, full_name)
        status_code = 200 if ok else 400
        return {
            "success": ok,
            "message": msg,
            "user": user_info,
            "token": new_token
        }, status_code

    # 3. Giriş Yap (Login)
    if method == "POST" and path == "/api/auth/login":
        username = body.get("kullanici_adi") or body.get("username")
        password = body.get("sifre") or body.get("password")
        
        ok, msg, user_info, new_token = authenticate_user(username, password)
        status_code = 200 if ok else 401
        return {
            "success": ok,
            "message": msg,
            "user": user_info,
            "token": new_token
        }, status_code

    # 4. Çıkış Yap (Logout)
    if method == "POST" and path == "/api/auth/logout":
        if token:
            terminate_session(token)
        return {
            "success": True,
            "message": "Oturum başarıyla kapatıldı."
        }, 200

    # 5. Şifre Değiştirme (Korumalı)
    if method == "POST" and path == "/api/auth/change-password":
        if not current_user or not current_user.get("id"):
            return {
                "success": False,
                "message": "Yetkisiz işlem. Lütfen önce giriş yapınız."
            }, 401

        old_pwd = body.get("eski_sifre") or body.get("old_password")
        new_pwd = body.get("yeni_sifre") or body.get("new_password")
        
        ok, msg = change_password(current_user["id"], old_pwd, new_pwd)
        status_code = 200 if ok else 400
        return {
            "success": ok,
            "message": msg
        }, status_code

    return None, None
