"""
Ana API Yönlendirici ve Güvenlik Bekçisi (api_handlers.py)
REST API rotalarını yetkilendirme denetiminden geçirir ve ilgili modüllere devreder.
"""

from urllib.parse import urlparse, parse_qs
from auth_manager import validate_session_token, has_any_user
from handlers_auth import handle_auth_api
from handlers_session import handle_session_routes
from handlers_debts import handle_debt_routes
from handlers_employees import handle_employee_routes
from handlers_receivables import handle_receivable_routes
from handlers_accounts import handle_account_routes
from handlers_vouchers import handle_voucher_routes
from handlers_accruals import handle_accrual_routes
from handlers_settings import handle_settings_routes
from handlers_reports import handle_report_routes


def handle_api_request(handler, method, path, query, body):
    """Gelen REST API çağrısını yetkilendirme denetiminden geçirerek alt modüllere devreder."""

    if "?" in path:
        parsed = urlparse(path)
        path = parsed.path
        if not query:
            query = parse_qs(parsed.query)

    # Token Çıkarma
    token = ""
    if handler is None:
        try:
            from tests.test_helpers import TestClientHandler
            handler = TestClientHandler()
        except Exception:
            pass

    if hasattr(handler, "_extract_token"):
        token = handler._extract_token()
    if not token and query and "token" in query:
        token = query["token"][0] if isinstance(query["token"], list) else query["token"]

    is_valid_session, current_user = validate_session_token(token)

    # 0. Kimlik Doğrulama Rotaları (/api/auth/*)
    if path.startswith("/api/auth"):
        res, status = handle_auth_api(
            method, path, query, body,
            current_user if is_valid_session else None,
            token
        )
        if status is not None:
            return res, status

    # Güvenlik Zırhı: Sistemde kullanıcı yoksa ilk kurulum gereklidir
    if not has_any_user():
        return {
            "error": "Sistem henüz kurulmadı. Lütfen ilk yönetici hesabını oluşturunuz.",
            "setup_required": True,
            "authenticated": False
        }, 401

    # Güvenlik Zırhı: Geçerli oturum yoksa yetkisiz erişim (401)
    if not is_valid_session:
        return {
            "error": "Yetkisiz erişim. Lütfen giriş yapınız.",
            "setup_required": False,
            "authenticated": False
        }, 401

    # 1. Gün Oturumu ve Günlük Hareket Rotaları
    res, status = handle_session_routes(method, path, query, body)
    if status is not None:
        return res, status

    # 2. Cari ve Borç Rotaları
    res, status = handle_debt_routes(method, path, query, body)
    if status is not None:
        return res, status

    # 3. Personel ve Tahakkuk Rotaları
    res, status = handle_employee_routes(method, path, query, body)
    if status is not None:
        return res, status

    # 4. Alacak ve Tahsilat Dağıtım Rotaları
    res, status = handle_receivable_routes(method, path, query, body)
    if status is not None:
        return res, status

    # 5. Hesap Planı ve Excel İçe Aktarım Rotaları
    res, status = handle_account_routes(method, path, query, body)
    if status is not None:
        return res, status

    # 6. Yevmiye Fişi ve Borç/Alacak Satır Rotaları
    res, status = handle_voucher_routes(method, path, query, body)
    if status is not None:
        return res, status

    # 7. Personel Tahakkuk Fişi, Borç Çeşitleri ve Rapor Rotaları
    res, status = handle_accrual_routes(method, path, query, body)
    if status is not None:
        return res, status

    # 8. Kurum Profili ve Genel Sistem Ayar Rotaları
    res, status = handle_settings_routes(method, path, query, body)
    if status is not None:
        return res, status

    # 9. Raporlar, Dashboard, Mizan ve Muavin Rotaları
    res, status = handle_report_routes(method, path, query, body)
    if status is not None:
        return res, status

    return {"error": "Endpoint bulunamadı"}, 404
