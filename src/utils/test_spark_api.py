import sys
import os
import json
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import SimpleCDPClient
import urllib.request

def test_spark():
    with open(os.path.join(PROJECT_ROOT, "data", ".hf_token")) as f:
        token = f.read().strip()

    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode("utf-8"))
    tab = [t for t in tabs if t.get("type") == "page" and "huggingface.co" in t.get("url", "")][0]
    c = SimpleCDPClient(tab["webSocketDebuggerUrl"])
    
    # Test gradio client connection from Chrome to mrfakename/spark-x2.6-4b
    js = f"""
    (async () => {{
        try {{
            const {{ Client }} = await import('https://cdn.jsdelivr.net/npm/@gradio/client/dist/index.min.js');
            const cl = await Client.connect("mrfakename/spark-x2.6-4b", {{ hf_token: {json.dumps(token)} }});
            const info = await cl.view_api();
            return {{ success: true, info }};
        }} catch (e) {{
            return {{ success: false, err: e.toString() }};
        }}
    }})()
    """
    res = c.send_cmd("Runtime.evaluate", {"expression": js, "awaitPromise": True, "returnByValue": True})
    val = res.get("result", {}).get("value")
    print("Spark API inspection:")
    if val and val.get("success"):
        named_endpoints = val.get("info", {}).get("named_endpoints", {})
        print("Named endpoints:", list(named_endpoints.keys()))
        for ep, ep_info in named_endpoints.items():
            print(f"Endpoint {ep}:", json.dumps(ep_info, indent=2))
    else:
        print("Error / Val:", val)
    c.close()

if __name__ == "__main__":
    test_spark()
