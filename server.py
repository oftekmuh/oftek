"""
Ana HTTP Sunucusu (server.py)
Python standart kütüphaneleriyle çalışan, harici bağımlılık gerektirmeyen yerel web ve API sunucusu.
"""

import os
import sys
import json
import time
import socket
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from db_manager import init_database, get_db_connection, DB_PATH, DB_FILENAME
from api_handlers import handle_api_request

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")


def get_local_ip():
    """Yerel LAN IP adresini tespit eder."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class MainRequestHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def _send_json(self, data, status=200):
        self._set_headers(status, "application/json; charset=utf-8")
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(body)

    def _extract_token(self):
        token = self.headers.get("X-Session-Token")
        if token:
            return token.strip()
        auth = self.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
        cookie_str = self.headers.get("Cookie", "")
        if cookie_str:
            for part in cookie_str.split(";"):
                if "=" in part:
                    k, v = part.strip().split("=", 1)
                    if k in ["oftek_token", "session_token"]:
                        return v.strip()
        return ""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Statik Dosyalar (HTML, JS, CSS, İmaj)
        clean_path = path.lstrip("/")
        if path in ["/", "/index.html"]:
            clean_path = "index.html"

        # Güvenlik Zırhı: Hassas sistem ve veritabanı dosyalarını kesinlikle dışarı verme
        if any(clean_path.lower().endswith(ext) for ext in [".db", ".sqlite", ".py", ".bat", ".env", ".key"]):
            self._set_headers(403, "text/plain; charset=utf-8")
            self.wfile.write("Erişim Engellendi (403 Forbidden)".encode("utf-8"))
            return

        potential_static = os.path.normpath(os.path.join(WEB_DIR, clean_path))
        if os.path.commonpath([potential_static, WEB_DIR]) == WEB_DIR and os.path.isfile(potential_static):
            ext = os.path.splitext(potential_static)[1].lower()
            mimes = {
                ".html": "text/html; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".ico": "image/x-icon",
                ".svg": "image/svg+xml",
                ".json": "application/json; charset=utf-8"
            }
            content_type = mimes.get(ext, "application/octet-stream")
            with open(potential_static, "rb") as f:
                content = f.read()
            self._set_headers(200, content_type)
            self.wfile.write(content)
            return

        if path == "/logo.png":
            logo_path = os.path.join(BASE_DIR, "logo.png")
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    content = f.read()
                self._set_headers(200, "image/png")
                self.wfile.write(content)
            else:
                self._set_headers(404)
            return

        if path in ["/kullanim_kilavuzu.html", "/kilavuz"]:
            guide_path = os.path.join(BASE_DIR, "kullanim_kilavuzu.html")
            if os.path.exists(guide_path):
                with open(guide_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self._set_headers(200, "text/html; charset=utf-8")
                self.wfile.write(content.encode("utf-8"))
                return

        # REST API İsteklerini Modüler Yönlendiriciye Devret
        res, status = handle_api_request(self, "GET", path, query, {})
        self._send_json(res, status)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        body = self._read_json_body()

        res, status = handle_api_request(self, "POST", path, query, body)
        self._send_json(res, status)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        try:
            body = self._read_json_body()
        except Exception:
            body = {}

        res, status = handle_api_request(self, "DELETE", path, query, body)
        self._send_json(res, status)


def main():
    init_database()
    local_ip = get_local_ip()

    server_address = ("0.0.0.0", PORT)
    httpd = HTTPServer(server_address, MainRequestHandler)

    # Tarayıcıyı otomatik aç
    def _open_ui():
        time.sleep(0.8)
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except Exception:
            pass

    threading.Thread(target=_open_ui, daemon=True).start()

    print("\n" + "=" * 68)
    print("  OFTEK")
    print("=" * 68)
    print(f"  * SQLite Veritabanı Dosyası : {DB_PATH}")
    print(f"  * Bilgisayardan Giriş       : http://localhost:{PORT}")
    print(f"  * Mobilden Giriş (Aynı WiFi): http://{local_ip}:{PORT}")
    print("=" * 68 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu kapatılıyor...")
        httpd.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()
