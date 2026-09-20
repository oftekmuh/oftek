import urllib.request
import urllib.error
import json

def check(name, url, method='GET', body=None):
    try:
        data = json.dumps(body).encode('utf-8') if body else None
        headers = {'Content-Type': 'application/json'} if body else {}
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            print(f"[OK] {name} -> HTTP {resp.status} : {content[:70]}")
    except urllib.error.HTTPError as e:
        err_content = e.read().decode('utf-8')
        print(f"[HTTP {e.code}] {name} -> {err_content[:70]}")
    except Exception as e:
        print(f"[ERR] {name} -> {e}")

if __name__ == '__main__':
    check('GET active session', 'http://localhost:8080/api/session/active')
    check('GET employee types', 'http://localhost:8080/api/employee-types')
    check('GET debt types', 'http://localhost:8080/api/employee-debt-types')
    check('GET descriptions', 'http://localhost:8080/api/vouchers/descriptions')
    check('POST reset invalid', 'http://localhost:8080/api/system/reset-database', 'POST', {'onay_kodu': 'X'})
    check('POST reset valid', 'http://localhost:8080/api/system/reset-database', 'POST', {'onay_kodu': 'SIFIRLA'})
