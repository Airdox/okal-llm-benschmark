import sys
import os
import time
import json
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import get_page_client
from src.utils.screen_capture import capture_screen

def test_minicpm5_single():
    client = get_page_client(url_filter="openbmb-minicpm5-2b-demo")
    prompt = "In einem Raum befinden sich 3 Personen. Jede Person schüttelt jeder anderen Person genau einmal die Hand. Wie viele Händedrücke gibt es insgesamt? Begründe deine Antwort kurz und gib am Ende das Ergebnis im Format 'Ergebnis: X' an."

    js_send = f"""
    (() => {{
        const ta = document.querySelector('textarea');
        if (!ta) return {{ success: false, error: 'No textarea' }};
        ta.focus();
        ta.value = {json.dumps(prompt)};
        ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
        ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
        
        const btn = document.querySelector('button.send-btn') || Array.from(document.querySelectorAll('button')).find(b => b.className.includes('send-btn'));
        if (btn) {{
            btn.click();
            return {{ success: true, method: 'btn_click' }};
        }}
        return {{ success: false, error: 'No send btn' }};
    }})()
    """
    res = client.send_cmd("Runtime.evaluate", {"expression": js_send, "returnByValue": True})
    print("Send result:", res.get("result", {}).get("value"))

    t0 = time.perf_counter()
    print("Waiting for MiniCPM5-2B response...")
    final_resp = ""
    for sec in range(40):
        time.sleep(1)
        js_read = """
        (() => {
            const bubbles = Array.from(document.querySelectorAll('.prose, [data-message-author-role="assistant"], .bot-message, .message-bubble, div[class*="chat-message"]'));
            if (bubbles.length === 0) {
                // Fallback: look for text containers in chat
                const allDivs = Array.from(document.querySelectorAll('div[class*="message"], div[class*="bubble"], div[class*="content"]'));
                return allDivs.map(d => d.innerText).filter(t => t.length > 5);
            }
            return bubbles.map(b => b.innerText);
        })()
        """
        r = client.send_cmd("Runtime.evaluate", {"expression": js_read, "returnByValue": True})
        val = r.get("result", {}).get("value")
        if val and len(val) > 0:
            last = val[-1].strip()
            if len(last) > 10 and not last.startswith("In einem Raum"):
                final_resp = last
                dur = round(time.perf_counter() - t0, 2)
                print(f"[{sec}s] Response received ({dur}s):\n{final_resp[:120]}...")
                break
        if sec % 5 == 0:
            print(f"[{sec}s] waiting... (current DOM nodes: {len(val) if val else 0})")

    time.sleep(2)
    bmp = r"E:\okal llm benschmark\data\screenshots\desktop_minicpm5_qs_r1.bmp"
    capture_screen(bmp)
    client.close()

    png = bmp.replace(".bmp", ".png")
    subprocess.run([
        "powershell", "-ExecutionPolicy", "Bypass", "-File",
        r"E:\okal llm benschmark\src\utils\bmp_to_png.ps1",
        "-InputBmp", bmp,
        "-OutputPng", png
    ], check=True)
    print("Saved screenshot:", png)
    print("\n--- FINAL OUTPUT ---\n", final_resp)

if __name__ == "__main__":
    test_minicpm5_single()
