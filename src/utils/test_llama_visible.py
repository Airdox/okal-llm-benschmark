import sys
import os
import time
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import get_page_client
from src.utils.screen_capture import capture_screen

def test_llama():
    client = get_page_client(url_filter="llama-3-2-3b-instruct")
    prompt = "In einem Raum befinden sich 3 Personen. Jede Person schüttelt jeder anderen Person genau einmal die Hand. Wie viele Händedrücke gibt es insgesamt? Begründe deine Antwort kurz und gib am Ende das Ergebnis im Format 'Ergebnis: X' an."

    js_type = f"""
    (() => {{
        const ta = document.querySelector('textarea');
        if (!ta) return {{ success: false, error: 'No textarea' }};
        ta.focus();
        ta.value = {json.dumps(prompt)};
        ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
        ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
        return {{ success: true }};
    }})()
    """
    res = client.send_cmd("Runtime.evaluate", {"expression": js_type, "returnByValue": True})
    print("Type prompt:", res.get("result", {}).get("value"))

    time.sleep(1)
    
    # Click submit (SVG button or enter key)
    js_click = """
    (() => {
        const btn = document.querySelector('button.submit-button, button[aria-label="Submit"]') || 
                    Array.from(document.querySelectorAll('button')).find(b => b.querySelector('svg') !== null);
        if (btn) {
            btn.click();
            return { success: true, method: 'click' };
        }
        const ta = document.querySelector('textarea');
        if (ta) {
            ta.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
            return { success: true, method: 'enter' };
        }
        return { success: false, error: 'No submit button or textarea' };
    })()
    """
    res_c = client.send_cmd("Runtime.evaluate", {"expression": js_click, "returnByValue": True})
    print("Click submit:", res_c.get("result", {}).get("value"))

    # Poll for answer
    print("Waiting for Llama 3.2 3B response...")
    response_text = ""
    for sec in range(30):
        time.sleep(1)
        js_bot = """
        (() => {
            const msgs = document.querySelectorAll('.message.bot, [data-testid="bot"], .bot, .prose');
            if (msgs.length === 0) return null;
            return msgs[msgs.length - 1].innerText;
        })()
        """
        r_bot = client.send_cmd("Runtime.evaluate", {"expression": js_bot, "returnByValue": True})
        val = r_bot.get("result", {}).get("value")
        if val and len(val.strip()) > 5:
            response_text = val.strip()
            print(f"[{sec}s] Response: {response_text[:80]}...")
            break
        elif sec % 5 == 0:
            print(f"[{sec}s] waiting...")

    time.sleep(2)
    bmp = r"E:\okal llm benschmark\data\screenshots\llama32_response_test.bmp"
    capture_screen(bmp)
    client.close()
    
    import subprocess
    png = bmp.replace(".bmp", ".png")
    subprocess.run([
        "powershell", "-ExecutionPolicy", "Bypass", "-File",
        r"E:\okal llm benschmark\src\utils\bmp_to_png.ps1",
        "-InputBmp", bmp,
        "-OutputPng", png
    ], check=True)
    print("Saved PNG:", png)
    print("Response text:\n", response_text)

if __name__ == "__main__":
    test_llama()
