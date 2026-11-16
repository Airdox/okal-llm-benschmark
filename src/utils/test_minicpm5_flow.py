import sys
import os
import json
import time
import ctypes
from ctypes import wintypes
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import get_page_client, SimpleCDPClient
from src.utils.screen_capture import capture_screen
import urllib.request

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
                title = buff.value
                if "Chrome" in title or "Hugging" in title or "MiniCPM" in title or "Spark" in title:
                    windows.append((hwnd, title))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumDesktopWindows(h_default, WNDENUMPROC(enum_proc), 0)
    
    target_hwnd = None
    for hwnd, title in windows:
        if "Hugging" in title or "MiniCPM" in title or "Spark" in title:
            target_hwnd = hwnd
            break
    if not target_hwnd and windows:
        target_hwnd = windows[0][0]
        
    if target_hwnd:
        curr_tid = ctypes.windll.kernel32.GetCurrentThreadId()
        fore_hwnd = user32.GetForegroundWindow()
        fore_tid = user32.GetWindowThreadProcessId(fore_hwnd, 0)
        if curr_tid != fore_tid:
            user32.AttachThreadInput(curr_tid, fore_tid, True)
            
        user32.ShowWindow(target_hwnd, 3) # SW_MAXIMIZE
        user32.SetWindowPos(target_hwnd, -1, 0, 0, 1366, 730, 0x0040)
        user32.SetForegroundWindow(target_hwnd)
        
        if curr_tid != fore_tid:
            user32.AttachThreadInput(curr_tid, fore_tid, False)
        print(f"Brought Chrome (HWND {target_hwnd}) to visible foreground.")
    return target_hwnd

def test_minicpm5_ui_flow():
    bring_chrome_to_foreground()
    with open(os.path.join(PROJECT_ROOT, "data", ".hf_token")) as f:
        token = f.read().strip()
        
    client = get_page_client(url_filter="openbmb-minicpm5-2b-demo")
    
    prompt = "In einem Raum befinden sich 3 Personen. Jede Person schüttelt jeder anderen Person genau einmal die Hand. Wie viele Händedrücke gibt es insgesamt? Begründe deine Antwort kurz und gib am Ende das Ergebnis im Format 'Ergebnis: X' an."
    
    # 1. Type prompt into UI
    js_type = f"""
    (() => {{
        const input = document.getElementById('user-input');
        if (!input) return {{ error: 'no input' }};
        input.value = {json.dumps(prompt)};
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        input.style.height = input.scrollHeight + 'px';
        return {{ ok: true }};
    }})()
    """
    res_type = client.send_cmd("Runtime.evaluate", {"expression": js_type, "returnByValue": True})
    print("Typed into UI:", res_type.get("result", {}).get("value"))
    time.sleep(1)
    
    # 2. Append user message & bot typing indicator in DOM, then call API with token and stream response into DOM
    js_run = f"""
    (async () => {{
        const text = {json.dumps(prompt)};
        const token = {json.dumps(token)};
        const input = document.getElementById('user-input');
        if (input) input.value = '';
        
        // Use page appendMessage
        const chatContainer = document.getElementById('chat-container');
        const userDiv = document.createElement('div');
        userDiv.className = 'flex gap-3 items-start flex-row-reverse';
        userDiv.innerHTML = `<div class="user-message message-bubble shadow-sm"><div class="content-container leading-relaxed text-[15px]">${{text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</div></div>`;
        chatContainer.appendChild(userDiv);
        
        const botDiv = document.createElement('div');
        botDiv.className = 'flex gap-3 items-start';
        botDiv.innerHTML = `<div class="bot-message message-bubble shadow-sm"><div class="thinking-container hidden"></div><div class="content-container leading-relaxed text-[15px]"><div class="flex gap-1.5 py-2"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div></div></div>`;
        chatContainer.appendChild(botDiv);
        
        const chatScroll = document.getElementById('chat-messages');
        if (chatScroll) chatScroll.scrollTo({{ top: chatScroll.scrollHeight, behavior: 'smooth' }});
        
        const contentContainer = botDiv.querySelector('.content-container');
        const thinkingContainer = botDiv.querySelector('.thinking-container');
        
        const {{ Client }} = await import('https://cdn.jsdelivr.net/npm/@gradio/client/dist/index.min.js');
        const cl = await Client.connect(window.location.origin, {{ hf_token: token }});
        
        const job = cl.submit('/predict', {{
            message: text,
            history: [],
            thinking_mode: true,
            temperature: 0.1,
            top_p: 0.95
        }});
        
        let finalAnswer = '';
        for await (const msg of job) {{
            if (msg.type === 'data' && msg.data) {{
                const fullText = msg.data[0];
                let cleaned = fullText.replace('<think>', '').replace('<|im_end|>', '');
                const pos = cleaned.indexOf('</think>');
                let thinking = '';
                let answer = '';
                if (pos === -1) {{
                    thinking = cleaned.trim();
                }} else {{
                    thinking = cleaned.slice(0, pos).trim();
                    answer = cleaned.slice(pos + 8).trim();
                }}
                if (thinking) {{
                    thinkingContainer.classList.remove('hidden');
                    thinkingContainer.innerHTML = `<div class="thinking-block" style="background:#f1f5f9;padding:8px;border-radius:6px;font-size:13px;color:#64748b;margin-bottom:8px;"><em>Denkprozess:</em><br>${{thinking}}</div>`;
                }}
                if (answer) {{
                    contentContainer.innerHTML = marked.parse(answer);
                    finalAnswer = answer;
                }}
                if (chatScroll) chatScroll.scrollTo({{ top: chatScroll.scrollHeight, behavior: 'smooth' }});
            }}
        }}
        return {{ success: true, answer: finalAnswer }};
    }})()
    """
    t0 = time.perf_counter()
    res = client.send_cmd("Runtime.evaluate", {"expression": js_run, "awaitPromise": True, "returnByValue": True})
    dur = round(time.perf_counter() - t0, 2)
    val = res.get("result", {}).get("value")
    print(f"Execution completed in {dur}s:")
    print("Result:", json.dumps(val, indent=2))
    
    # Capture desktop screenshot
    bmp = r"E:\okal llm benschmark\data\screenshots\desktop_minicpm5_qsr1_verified.bmp"
    capture_screen(bmp)
    png = bmp.replace(".bmp", ".png")
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", r"E:\okal llm benschmark\src\utils\bmp_to_png.ps1", "-InputBmp", bmp, "-OutputPng", png], check=True)
    print("Screenshot saved to:", png)
    client.close()

if __name__ == "__main__":
    test_minicpm5_ui_flow()
