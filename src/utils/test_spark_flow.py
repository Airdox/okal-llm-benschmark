import sys
import os
import json
import time
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import SimpleCDPClient
from src.utils.screen_capture import capture_screen
import urllib.request

def test_spark_flow():
    with open(os.path.join(PROJECT_ROOT, "data", ".hf_token")) as f:
        token = f.read().strip()
        
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode("utf-8"))
    tab = [t for t in tabs if t.get("type") == "page" and "huggingface.co" in t.get("url", "")][0]
    c = SimpleCDPClient(tab["webSocketDebuggerUrl"])
    
    # Navigate to spark space
    print("Navigating to mrfakename/spark-x2.6-4b...")
    c.send_cmd("Page.navigate", {"url": "https://huggingface.co/spaces/mrfakename/spark-x2.6-4b"})
    c.close()
    
    time.sleep(5)
    
    # Re-connect to page
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode("utf-8"))
    tab = [t for t in tabs if t.get("type") == "page" and "spark" in t.get("url", "").lower()][0]
    c = SimpleCDPClient(tab["webSocketDebuggerUrl"])
    c.send_cmd("Page.bringToFront")
    
    # Test query using Client
    js = f"""
    (async () => {{
        try {{
            const {{ Client }} = await import('https://cdn.jsdelivr.net/npm/@gradio/client/dist/index.min.js');
            const cl = await Client.connect("mrfakename/spark-x2.6-4b", {{ hf_token: {json.dumps(token)} }});
            const res = await cl.predict("/chat", {{
                message: "Ein Händler kauft 14 Kisten mit je 6 Flaschen Saft. Er verkauft 27 Flaschen. Wie viele Flaschen hat er noch übrig? Antworte ausschließlich mit der Zahl als Ziffer.",
                history: [],
                thinking: "Low",
                system_prompt: "",
                temperature: 0.1,
                top_p: 0.95,
                max_new_tokens: 512
            }});
            return {{ success: true, res }};
        }} catch (e) {{
            return {{ success: false, err: e.toString() }};
        }}
    }})()
    """
    print("Running Spark-X2.6-4B test query...")
    t0 = time.perf_counter()
    r = c.send_cmd("Runtime.evaluate", {"expression": js, "awaitPromise": True, "returnByValue": True})
    dur = round(time.perf_counter() - t0, 2)
    val = r.get("result", {}).get("value")
    print(f"Spark query finished in {dur}s:")
    print(json.dumps(val, indent=2))
    
    bmp = r"E:\okal llm benschmark\data\screenshots\desktop_spark_qsr1.bmp"
    capture_screen(bmp)
    png = bmp.replace(".bmp", ".png")
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", r"E:\okal llm benschmark\src\utils\bmp_to_png.ps1", "-InputBmp", bmp, "-OutputPng", png], check=True)
    print("Saved screenshot:", png)
    c.close()

if __name__ == "__main__":
    test_spark_flow()
