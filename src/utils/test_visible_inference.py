import time
import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import get_page_client
from src.utils.screen_capture import capture_screen

def run_visible_test():
    client = get_page_client()
    print("Connected to visible Chrome CDP.")

    # 1. Close any chrome popup by clicking body
    client.send_cmd("Runtime.evaluate", {"expression": "document.body.click()"})
    time.sleep(1)

    # 2. Set value in textbox and trigger Gradio input events
    test_prompt = "Schreibe eine Python-Funktion add(a, b) -> int, die zwei Zahlen addiert. Gib nur den Code aus."
    
    js_set_prompt = f"""
    (() => {{
        const ta = document.querySelector('textarea, input[type="text"]');
        if (!ta) return {{ success: false, error: "No textarea found" }};
        
        ta.focus();
        ta.value = {json.dumps(test_prompt)};
        ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
        ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
        
        return {{ success: true, value: ta.value }};
    }})()
    """
    res = client.send_cmd("Runtime.evaluate", {"expression": js_set_prompt, "returnByValue": True})
    print("Set prompt result:", res.get("result", {}).get("value"))

    # Capture screenshot with prompt entered
    time.sleep(1)
    capture_screen(r"E:\okal llm benschmark\data\screenshots\step1_prompt_entered.bmp")

    # 3. Submit by pressing Enter or clicking submit button
    js_submit = """
    (() => {
        const btn = document.querySelector('button#submit, button.submit, button[aria-label="Submit"], button[data-testid="submit"]');
        if (btn) {
            btn.click();
            return { method: "button_click" };
        }
        const ta = document.querySelector('textarea, input[type="text"]');
        if (ta) {
            ta.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
            return { method: "enter_key" };
        }
        return { error: "Neither button nor textarea found" };
    })()
    """
    res_sub = client.send_cmd("Runtime.evaluate", {"expression": js_submit, "returnByValue": True})
    print("Submit result:", res_sub.get("result", {}).get("value"))

    # 4. Poll for model response in the chatbot
    print("Waiting for Qwen2.5-Coder model response...")
    response_text = ""
    for sec in range(45):
        time.sleep(1)
        js_get_bot = """
        (() => {
            const botMsgs = document.querySelectorAll('.bot, [data-testid="bot"], .message.bot, .prose');
            if (botMsgs.length === 0) return null;
            return botMsgs[botMsgs.length - 1].innerText;
        })()
        """
        r_bot = client.send_cmd("Runtime.evaluate", {"expression": js_get_bot, "returnByValue": True})
        val = r_bot.get("result", {}).get("value")
        if val and len(val.strip()) > 5:
            response_text = val.strip()
            print(f"[{sec}s] Received response: {response_text[:80]}...")
            break
        elif sec % 5 == 0:
            print(f"[{sec}s] Waiting for inference...")

    time.sleep(2)
    # 5. Capture final desktop screenshot with response
    out_bmp = r"E:\okal llm benschmark\data\screenshots\step2_model_response_visible.bmp"
    capture_screen(out_bmp)
    print("Captured final desktop screenshot:", out_bmp)
    
    client.close()
    return response_text

if __name__ == "__main__":
    resp = run_visible_test()
    print("\n================ FINAL RESPONSE ================")
    print(resp)
