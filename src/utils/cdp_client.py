import socket
import base64
import os
import json
import struct
import requests
from typing import Dict, Any, Optional

class SimpleCDPClient:
    def __init__(self, ws_url: str, timeout: float = 120.0):
        parts = ws_url.replace("ws://", "").split("/", 1)
        host, port = parts[0].split(":")
        self.path = "/" + parts[1]
        self.sock = socket.create_connection((host, int(port)), timeout=timeout)
        self.sock.settimeout(timeout)
        self._handshake(host, port)
        self.msg_id = 0

    def _handshake(self, host: str, port: str):
        key = base64.b64encode(os.urandom(16)).decode('ascii')
        req = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode('ascii'))
        resp = self.sock.recv(4096)
        if b" 101 " not in resp:
            raise RuntimeError(f"WebSocket handshake failed: {resp[:200]}")

    def send_cmd(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.msg_id += 1
        msg = {
            "id": self.msg_id,
            "method": method,
            "params": params or {}
        }
        payload = json.dumps(msg).encode('utf-8')
        
        header = bytearray([0x81]) # FIN + Text frame
        mask = os.urandom(4)
        length = len(payload)
        if length <= 125:
            header.append(0x80 | length)
        elif length <= 65535:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
            
        header.extend(mask)
        masked_payload = bytearray(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(header + masked_payload)
        
        while True:
            head = self._recv_exact(2)
            b1, b2 = head[0], head[1]
            opcode = b1 & 0x0F
            masked = bool(b2 & 0x80)
            payload_len = b2 & 0x7F
            if payload_len == 126:
                payload_len = struct.unpack("!H", self._recv_exact(2))[0]
            elif payload_len == 127:
                payload_len = struct.unpack("!Q", self._recv_exact(8))[0]
                
            mask_key = self._recv_exact(4) if masked else None
            raw_bytes = self._recv_exact(payload_len)
            if masked:
                raw_bytes = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(raw_bytes))
                
            if opcode == 0x01: # text frame
                data = json.loads(raw_bytes.decode('utf-8', errors='replace'))
                if data.get("id") == self.msg_id:
                    if "error" in data:
                        raise RuntimeError(f"CDP Error ({method}): {data['error']}")
                    return data.get("result", {})

    def _recv_exact(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise EOFError("Socket connection closed")
            buf.extend(chunk)
        return bytes(buf)

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

def get_page_client(port: int = 9222, url_filter: str = "", allow_iframe: bool = True) -> SimpleCDPClient:
    tabs = requests.get(f"http://127.0.0.1:{port}/json/list").json()
    valid_types = ("page", "iframe") if allow_iframe else ("page",)
    candidates = [t for t in tabs if t.get("type") in valid_types and t.get("url", "").startswith("http")]
    if url_filter:
        matching = [t for t in candidates if url_filter.lower() in t.get("url", "").lower()]
        if matching:
            candidates = matching
        else:
            raise RuntimeError(f"No target found matching url_filter='{url_filter}'. Available: {[t.get('url') for t in candidates]}")
    if not candidates:
        candidates = [t for t in tabs if t.get("type") == "page"]
    if not candidates:
        raise RuntimeError("No active browser page found.")
    ws_url = candidates[0]["webSocketDebuggerUrl"]
    return SimpleCDPClient(ws_url)

if __name__ == "__main__":
    client = get_page_client()
    res = client.send_cmd("Runtime.evaluate", {"expression": "document.title"})
    print("Page Title via CDP:", res.get("result", {}).get("value"))
    client.close()
