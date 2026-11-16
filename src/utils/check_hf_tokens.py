import sys
import os
import json
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import get_page_client

def check_tokens():
    client = get_page_client(url_filter="settings/tokens")
    js = """
    (() => {
        const modals = Array.from(document.querySelectorAll('div[class*="fixed"], div[class*="modal"], div[class*="overlay"]'));
        return modals.map(m => m.innerText.trim()).filter(t => t.length > 0);
    })()
    """
    res = client.send_cmd("Runtime.evaluate", {"expression": js, "returnByValue": True})
    val = res.get("result", {}).get("value")
    print(json.dumps(val, indent=2))
    client.close()

if __name__ == "__main__":
    check_tokens()
