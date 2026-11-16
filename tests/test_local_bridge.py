"""
Integrationstest für die lokale Authentifizierte Bridge (Cloud-Lokal-Kommunikation).
"""
import sys
import os
import time
import requests

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.service.local_bridge import LocalBenchmarkBridge, AUTH_TOKEN

def test_bridge_communication():
    print("Starte Local Bridge Test auf Port 11435...")
    bridge = LocalBenchmarkBridge(port=11435)
    bridge.start()
    time.sleep(0.5)

    base_url = "http://127.0.0.1:11435"
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    try:
        # 1. Unautorisierter Zugriff testen (Muss 401 zurückgeben)
        res_unauth = requests.get(f"{base_url}/health", timeout=3)
        assert res_unauth.status_code == 401, f"Erwartet 401, erhalten {res_unauth.status_code}"
        print("✅ Sicherheitstest 1: Unautorisierter Zugriff abgewiesen (HTTP 401).")

        # 2. Autorisierter Health-Check
        res_health = requests.get(f"{base_url}/health", headers=headers, timeout=3)
        assert res_health.status_code == 200, f"Erwartet 200, erhalten {res_health.status_code}"
        data = res_health.json()
        assert data["status"] == "healthy"
        assert "cpu_percent" in data["system"]
        assert "ram_total_mb" in data["system"]
        print(f"✅ Funktionstest 2: Health-Check erfolgreich (RAM: {data['system']['ram_total_mb']} MB, C: {data['system']['disk_c_free_mb']} MB frei).")

        # 3. Ping/Pong RPC-Befehl
        res_ping = requests.post(f"{base_url}/execute_ping", headers=headers, json={"message": "Benchmark-Ping-123"}, timeout=3)
        assert res_ping.status_code == 200
        data_ping = res_ping.json()
        assert data_ping["received_message"] == "Benchmark-Ping-123"
        print(f"✅ Funktionstest 3: Zwei-Wege-RPC Echo erfolgreich (Status: {data_ping['status']}).")

    finally:
        bridge.stop()

    print("\nAlle Cloud-Lokal-Kommunikationstests erfolgreich bestanden! ✅")

if __name__ == "__main__":
    test_bridge_communication()
