import sys
import os
import json
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import get_page_client

def test_token():
    with open(os.path.join(PROJECT_ROOT, "data", ".hf_token")) as f:
        token = f.read().strip()

    c = get_page_client(url_filter="openbmb-minicpm5-2b-demo")
    js = f"""
    (async () => {{
        try {{
            const {{ Client }} = await import('https://cdn.jsdelivr.net/npm/@gradio/client/dist/index.min.js');
            const cl = await Client.connect(window.location.origin, {{ hf_token: {json.dumps(token)} }});
            const res = await cl.predict('/predict', {{
                message: 'Hello MiniCPM5! Reply with exact word TEST_OK.',
                history: [],
                thinking_mode: false,
                temperature: 0.1,
                top_p: 0.95
            }});
            return {{ success: true, res }};
        }} catch (e) {{
            return {{ success: false, err: e.toString(), stack: e.stack }};
        }}
    }})()
    """
    res = c.send_cmd("Runtime.evaluate", {"expression": js, "awaitPromise": True, "returnByValue": True})
    print(json.dumps(res.get("result", {}).get("value"), indent=2))
    c.close()

if __name__ == "__main__":
    test_token()
