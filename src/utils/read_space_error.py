import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import get_page_client

client = get_page_client(url_filter="llama-3-2-3b-instruct")
js = """
(() => {
    const el = document.querySelector('.toast, .error, [data-testid="toast-body"], .toast-body');
    return el ? el.innerText : "No specific error element found";
})()
"""
res = client.send_cmd("Runtime.evaluate", {"expression": js, "returnByValue": True})
print("Error element text:", res.get("result", {}).get("value"))
client.close()
