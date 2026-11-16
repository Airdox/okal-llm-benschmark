import time
import json
import os
import sys
import ctypes
from ctypes import wintypes
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import get_page_client
from src.utils.screen_capture import capture_screen

def bring_chrome_to_foreground():
    user32 = ctypes.windll.user32
    h_default = user32.OpenDesktopW('default', 0, False, 0x01FF)
    if h_default:
        user32.SetThreadDesktop(h_default)

    windows = []
    def enum_proc(hwnd, lp):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                if "Qwen" in buff.value or "Hugging Face" in buff.value or "Google Chrome" in buff.value:
                    windows.append((hwnd, buff.value))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumDesktopWindows(h_default, WNDENUMPROC(enum_proc), 0)
    
    target_hwnd = None
    for hwnd, title in windows:
        if "Qwen" in title or "Hugging" in title:
            target_hwnd = hwnd
            break
    if not target_hwnd and windows:
        target_hwnd = windows[0][0]
        
    if target_hwnd:
        user32.ShowWindow(target_hwnd, 3) # SW_MAXIMIZE
        user32.SetForegroundWindow(target_hwnd)
        print(f"Foreground window set to HWND {target_hwnd}")
    return target_hwnd

def run_test():
    print("=== Start Verbindlicher Chrome-Sichtbarkeitstest ===")
    bring_chrome_to_foreground()
    time.sleep(1)

    client = get_page_client(url_filter="qwen2-5-coder")
    print("CDP-Verbindung zum Tab 'Qwen 2.5 Coder 1.5B GGUF' hergestellt.")

    test_prompt = "Schreibe eine Python-Funktion `add(a: int, b: int) -> int`, die zwei Zahlen addiert. Gib NUR den Python-Code in einem ```python ... ``` Block aus."
    print(f"Test-Prompt:\n{test_prompt}\n")

    # Set value in textarea and trigger events
    js_type = f"""
    (() => {{
        const ta = document.querySelector('textarea.svelte-1hguek3, textarea');
        if (!ta) return {{ success: false, error: "Textarea not found" }};
        ta.focus();
        ta.value = {json.dumps(test_prompt)};
        ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
        ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
        return {{ success: true }};
    }})()
    """
    res_type = client.send_cmd("Runtime.evaluate", {"expression": js_type, "returnByValue": True})
    print("Prompt eingetragen:", res_type.get("result", {}).get("value"))

    time.sleep(1)
    # Screenshot: Prompt entered
    bmp1 = r"E:\okal llm benschmark\data\screenshots\step1_prompt_submitted_desktop.bmp"
    capture_screen(bmp1)
    print("Screenshot 1 (Prompt im sichtbaren Browser) erfasst.")

    # Click Submit button
    js_click = """
    (() => {
        const btn = document.querySelector('button.submit-button, button[aria-label="Submit"]');
        if (!btn) return { success: false, error: "Submit button not found" };
        btn.click();
        return { success: true };
    })()
    """
    t0 = time.perf_counter()
    res_click = client.send_cmd("Runtime.evaluate", {"expression": js_click, "returnByValue": True})
    print("Submit geklickt:", res_click.get("result", {}).get("value"))

    # Poll for response in chatbot
    print("Warte auf Modellantwort von Qwen2.5-Coder-1.5B (CPU-Inferenz auf HF Spaces)...")
    final_output = ""
    for sec in range(60):
        time.sleep(1)
        js_get_response = """
        (() => {
            const msgs = document.querySelectorAll('.message.bot, [data-testid="bot"], .bot');
            if (msgs.length === 0) return null;
            const lastMsg = msgs[msgs.length - 1];
            return {
                text: lastMsg.innerText,
                html: lastMsg.innerHTML
            };
        })()
        """
        r_resp = client.send_cmd("Runtime.evaluate", {"expression": js_get_response, "returnByValue": True})
        val = r_resp.get("result", {}).get("value")
        if val and isinstance(val, dict) and len(val.get("text", "").strip()) > 10:
            final_output = val["text"].strip()
            elapsed = round(time.perf_counter() - t0, 2)
            print(f"\n[+{elapsed}s] Modellantwort empfangen!\n")
            break
        elif sec % 5 == 0:
            print(f"[{sec}s] Generierung läuft...")

    time.sleep(2)
    # Screenshot: Final response on desktop
    bmp2 = r"E:\okal llm benschmark\data\screenshots\step2_model_response_desktop.bmp"
    capture_screen(bmp2)
    print("Screenshot 2 (Modellantwort im sichtbaren Browser) erfasst.")

    client.close()

    # Convert screenshots to PNG
    for bmp_file in [bmp1, bmp2]:
        png_file = bmp_file.replace(".bmp", ".png")
        subprocess.run([
            "powershell", "-ExecutionPolicy", "Bypass", "-File",
            r"E:\okal llm benschmark\src\utils\bmp_to_png.ps1",
            "-InputBmp", bmp_file,
            "-OutputPng", png_file
        ], check=True)
        print(f"Konvertiert zu PNG: {png_file}")

    print("\n================ TESTERGEBNIS ================")
    print(final_output)
    print("===============================================")
    return final_output

if __name__ == "__main__":
    run_test()
