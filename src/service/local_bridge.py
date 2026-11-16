"""
Sichere, authentifizierte lokale Kommunikations- und Steuerungs-Bridge (Phase 1 / 5).
Ermöglicht eine entkoppelte, deterministische und sichere Auftragsabwicklung zwischen
Steuerungs-Agent und lokaler Ollama-Inferenzumgebung.
Lauscht strikt auf 127.0.0.1 (keine externe Netzwerk-Exposition).
"""
import os
import sys
import json
import time
import secrets
import threading
import psutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUTH_FILE = os.path.join(PROJECT_ROOT, "data", ".bridge_auth")

def get_or_create_auth_token() -> str:
    """Erzeugt oder liest ein kryptografisch sicheres lokales Auth-Token."""
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            tok = f.read().strip()
            if len(tok) >= 32:
                return tok
    tok = secrets.token_hex(32)
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        f.write(tok)
    return tok

AUTH_TOKEN = get_or_create_auth_token()

class BridgeRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: Dict[str, Any]):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _verify_auth(self) -> bool:
        auth_hdr = self.headers.get("Authorization", "")
        if auth_hdr == f"Bearer {AUTH_TOKEN}":
            return True
        return False

    def do_GET(self):
        if not self._verify_auth():
            self._send_json(401, {"error": "Unauthorized: Ungültiges oder fehlendes Bearer-Token"})
            return

        if self.path == "/health":
            mem = psutil.virtual_memory()
            disk_e = psutil.disk_usage("E:\\") if os.path.exists("E:\\") else None
            disk_c = psutil.disk_usage("C:\\") if os.path.exists("C:\\") else None
            
            payload = {
                "status": "healthy",
                "timestamp": time.time(),
                "system": {
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "ram_total_mb": round(mem.total / 1e6, 1),
                    "ram_available_mb": round(mem.available / 1e6, 1),
                    "disk_c_free_mb": round(disk_c.free / 1e6, 1) if disk_c else 0,
                    "disk_e_free_mb": round(disk_e.free / 1e6, 1) if disk_e else 0
                }
            }
            self._send_json(200, payload)
        else:
            self._send_json(404, {"error": "Endpunkt nicht gefunden"})

    def do_POST(self):
        if not self._verify_auth():
            self._send_json(401, {"error": "Unauthorized: Ungültiges oder fehlendes Bearer-Token"})
            return

        if self.path == "/execute_ping":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            try:
                data = json.loads(body)
            except Exception:
                data = {}
            self._send_json(200, {
                "status": "ack",
                "received_message": data.get("message", "pong"),
                "echo_time": time.time()
            })
        else:
            self._send_json(404, {"error": "Endpunkt nicht gefunden"})

    def log_message(self, format, *args):
        # Ruhiges Logging
        return

class LocalBenchmarkBridge:
    def __init__(self, host: str = "127.0.0.1", port: int = 11435):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self):
        self.server = HTTPServer((self.host, self.port), BridgeRequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"[BRIDGE] Lokale Authentifizierte Bridge aktiv auf http://{self.host}:{self.port}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("[BRIDGE] Bridge beendet.")

if __name__ == "__main__":
    bridge = LocalBenchmarkBridge()
    bridge.start()
    print(f"Token: {AUTH_TOKEN}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bridge.stop()
