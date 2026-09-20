"""
Ana API Yönlendirici (api_handlers.py)
REST API rotalarını ilgili modüllere (session, debts, employees, receivables, accounts) yönlendirir.
"""

from urllib.parse import urlparse, parse_qs
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
    """Gelen REST API çağrısını alt modüllere sırayla devreder."""

    if "?" in path:
        parsed = urlparse(path)
        path = parsed.path
        if not query:
            query = parse_qs(parsed.query)

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
