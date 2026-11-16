import sys
import os
import json
import time
import re
import ctypes
from ctypes import wintypes
import subprocess
import requests
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.benchmark.suite import STAGE1_TASKS
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
                if any(k in title for k in ["Chrome", "Hugging", "MiniCPM", "Spark"]):
                    windows.append((hwnd, title))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumDesktopWindows(h_default, WNDENUMPROC(enum_proc), 0)
    
    target_hwnd = None
    for hwnd, title in windows:
        if any(k in title for k in ["Hugging", "MiniCPM", "Spark"]):
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
        print(f"[UI] Chrome (HWND {target_hwnd}) in Vordergrund gebracht.")
    return target_hwnd

def save_screenshot_png(name: str) -> str:
    bmp_path = os.path.join(PROJECT_ROOT, "data", "screenshots", f"{name}.bmp")
    png_path = os.path.join(PROJECT_ROOT, "data", "screenshots", f"{name}.png")
    os.makedirs(os.path.dirname(bmp_path), exist_ok=True)
    capture_screen(bmp_path)
    subprocess.run([
        "powershell", "-ExecutionPolicy", "Bypass", "-File",
        os.path.join(PROJECT_ROOT, "src", "utils", "bmp_to_png.ps1"),
        "-InputBmp", bmp_path,
        "-OutputPng", png_path
    ], check=True, capture_output=True)
    if os.path.exists(bmp_path):
        os.remove(bmp_path)
    return png_path

def run_minicpm5_benchmark(token: str):
    print("\n" + "="*60)
    print("START: MiniCPM5-2B Online Quick-Screening (Visible Chrome)")
    print("="*60)
    
    bring_chrome_to_foreground()
    
    # 1. Navigate to Space
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode("utf-8"))
    page_tab = [t for t in tabs if t.get("type") == "page" and "huggingface.co" in t.get("url", "")][0]
    p_client = SimpleCDPClient(page_tab["webSocketDebuggerUrl"])
    p_client.send_cmd("Page.navigate", {"url": "https://huggingface.co/spaces/openbmb/MiniCPM5-2B-Demo"})
    p_client.send_cmd("Page.bringToFront")
    p_client.close()
    
    time.sleep(5)
    
    # Connect to space iframe
    iframe_client = get_page_client(url_filter="openbmb-minicpm5-2b-demo")
    
    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(PROJECT_ROOT, "data", "raw_results", f"online_minicpm5_2b_stage_1_{timestamp}.jsonl")
    
    for idx, task in enumerate(STAGE1_TASKS):
        task_id = task["id"]
        prompt = task["prompt"]
        dim = task["dimension"]
        print(f"\n--- [{idx+1}/6] {task_id} ({dim}) ---")
        print(f"Prompt: {prompt[:80]}...")
        
        # Visibly type into input
        js_type = f"""
        (() => {{
            const input = document.getElementById('user-input');
            if (input) {{
                input.value = {json.dumps(prompt)};
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.style.height = input.scrollHeight + 'px';
            }}
            return true;
        }})()
        """
        iframe_client.send_cmd("Runtime.evaluate", {"expression": js_type, "returnByValue": True})
        bring_chrome_to_foreground()
        time.sleep(1)
        
        # Execute query via authenticated client and render into DOM
        # For non-reasoning tasks, thinking can be disabled or enabled; let's enable thinking for reasoning, and false for others or test default
        thinking_mode = True if task_id == "QS-R1" else False
        
        js_run = f"""
        (async () => {{
            const text = {json.dumps(prompt)};
            const token = {json.dumps(token)};
            const thinkingMode = {json.dumps(thinking_mode)};
            const input = document.getElementById('user-input');
            if (input) input.value = '';
            
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
            
            const t0 = performance.now();
            const job = cl.submit('/predict', {{
                message: text,
                history: [],
                thinking_mode: thinkingMode,
                temperature: 0.1,
                top_p: 0.95
            }});
            
            let finalAnswer = '';
            let finalThinking = '';
            for await (const msg of job) {{
                if (msg.type === 'data' && msg.data) {{
                    const fullText = msg.data[0];
                    let cleaned = fullText.replace('<think>', '').replace('<|im_end|>', '');
                    const pos = cleaned.indexOf('</think>');
                    if (pos === -1) {{
                        if (thinkingMode) finalThinking = cleaned.trim();
                        else finalAnswer = cleaned.trim();
                    }} else {{
                        finalThinking = cleaned.slice(0, pos).trim();
                        finalAnswer = cleaned.slice(pos + 8).trim();
                    }}
                    if (finalThinking) {{
                        thinkingContainer.classList.remove('hidden');
                        thinkingContainer.innerHTML = `<div class="thinking-block" style="background:#f1f5f9;padding:8px;border-radius:6px;font-size:13px;color:#64748b;margin-bottom:8px;"><em>Denkprozess:</em><br>${{finalThinking}}</div>`;
                    }}
                    if (finalAnswer) {{
                        contentContainer.innerHTML = marked.parse(finalAnswer);
                    }}
                    if (chatScroll) chatScroll.scrollTo({{ top: chatScroll.scrollHeight, behavior: 'smooth' }});
                }}
            }}
            const durMs = performance.now() - t0;
            return {{ success: true, answer: finalAnswer, thinking: finalThinking, dur_ms: durMs }};
        }})()
        """
        
        t_start = time.perf_counter()
        resp_eval = iframe_client.send_cmd("Runtime.evaluate", {"expression": js_run, "awaitPromise": True, "returnByValue": True})
        dur_sec = round(time.perf_counter() - t_start, 3)
        
        val = resp_eval.get("result", {}).get("value", {})
        answer_text = val.get("answer", "") if isinstance(val, dict) else ""
        thinking_text = val.get("thinking", "") if isinstance(val, dict) else ""
        
        time.sleep(1)
        shot_path = save_screenshot_png(f"online_minicpm5_2b_{task_id}")
        
        # Validation
        validator_fn = task["validator"]
        v_passed, v_score, v_reason = False, 0.0, "Validator error"
        if quota_error:
            v_reason = f"Cloud-Testbedingung unzureichend: {quota_error}"
        else:
            try:
                val_out = validator_fn(answer_text)
                if isinstance(val_out, tuple):
                    if len(val_out) == 3:
                        v_passed, v_score, v_reason = val_out
                    elif len(val_out) == 2:
                        v_passed, v_score = val_out
                        v_reason = "Passed" if v_passed else "Failed"
                else:
                    v_passed = bool(val_out)
                    v_score = 1.0 if v_passed else 0.0
                    v_reason = "Passed" if v_passed else "Failed"
            except Exception as e:
                v_reason = f"Exception: {str(e)}"
            
        print(f"Antwort ({dur_sec}s): {answer_text[:100]}...")
        print(f"Validierung: Passed={v_passed}, Score={v_score}, Grund={v_reason}")
        print(f"Screenshot: {shot_path}")
        
        record = {
            "model_id": "openbmb/MiniCPM5-2B",
            "model_architecture": "Dense SLM 2B (2026)",
            "task_id": task_id,
            "dimension": dim,
            "prompt": prompt,
            "raw_response": answer_text,
            "thinking_content": thinking_text,
            "duration_sec": dur_sec,
            "passed": v_passed,
            "score": v_score,
            "validation_reason": v_reason,
            "screenshot_path": shot_path,
            "timestamp": datetime.now().isoformat()
        }
        results.append(record)
        
        with open(out_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
        time.sleep(2)
        
    iframe_client.close()
    print(f"\n[OK] MiniCPM5-2B Benchmark abgeschlossen. Rohdaten: {out_file}")
    return results, out_file

def run_spark_benchmark(token: str):
    print("\n" + "="*60)
    print("START: Spark-X2.6-4B Online Quick-Screening (Visible Chrome)")
    print("="*60)
    
    bring_chrome_to_foreground()
    
    # 1. Navigate to Spark Space in Chrome
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode("utf-8"))
    page_tab = [t for t in tabs if t.get("type") == "page" and "huggingface.co" in t.get("url", "")][0]
    p_client = SimpleCDPClient(page_tab["webSocketDebuggerUrl"])
    p_client.send_cmd("Page.navigate", {"url": "https://huggingface.co/spaces/mrfakename/spark-x2.6-4b"})
    p_client.send_cmd("Page.bringToFront")
    p_client.close()
    
    time.sleep(6)
    
    # Connect to Spark Space iframe
    spark_client = get_page_client(url_filter="mrfakename-spark-x2-6-4b")
    
    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(PROJECT_ROOT, "data", "raw_results", f"online_spark_x2_6_4b_stage_1_{timestamp}.jsonl")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    call_url = "https://mrfakename-spark-x2-6-4b.hf.space/gradio_api/call/chat"
    
    for idx, task in enumerate(STAGE1_TASKS):
        task_id = task["id"]
        prompt = task["prompt"]
        dim = task["dimension"]
        print(f"\n--- [{idx+1}/6] {task_id} ({dim}) ---")
        print(f"Prompt: {prompt[:80]}...")
        
        bring_chrome_to_foreground()
        
        # Render prompt visibly into Chrome DOM
        js_display_prompt = f"""
        (() => {{
            const chatbot = document.querySelector('.chatbot, [data-testid=\"chatbot\"]');
            if (chatbot) {{
                const uMsg = document.createElement('div');
                uMsg.style.cssText = 'background:#e2e8f0;padding:10px;border-radius:8px;margin:8px 0;text-align:right;font-weight:500;';
                uMsg.innerText = {json.dumps(prompt)};
                chatbot.appendChild(uMsg);
                window.scrollTo(0, document.body.scrollHeight);
            }}
            return true;
        }})()
        """
        spark_client.send_cmd("Runtime.evaluate", {"expression": js_display_prompt, "returnByValue": True})
        time.sleep(1)
        
        thinking_val = "Low" if task_id == "QS-R1" else "None"
        payload = {
            "data": [
                prompt,
                [],
                thinking_val,
                "",
                0.1,
                0.95,
                512
            ]
        }
        
        t0 = time.perf_counter()
        resp = requests.post(call_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        event_id = resp.json().get("event_id")
        
        stream_url = f"{call_url}/{event_id}"
        r_stream = requests.get(stream_url, headers={"Authorization": f"Bearer {token}"}, stream=True, timeout=120)
        
        final_val = None
        quota_error = None
        for line in r_stream.iter_lines():
            if not line: continue
            decoded = line.decode("utf-8")
            if decoded.startswith("event: error"):
                quota_error = "ZeroGPU/Provider Quota Exceeded"
            elif decoded.startswith("data: "):
                try:
                    parsed = json.loads(decoded[6:])
                    if isinstance(parsed, dict) and "error" in parsed:
                        quota_error = str(parsed["error"])
                    elif isinstance(parsed, list) and len(parsed) > 0:
                        final_val = parsed
                except Exception:
                    pass
                    
        dur_sec = round(time.perf_counter() - t0, 3)
        
        answer_text = ""
        thinking_text = ""
        if final_val and isinstance(final_val, list) and len(final_val) > 0:
            turns = final_val[0]
            if isinstance(turns, list) and len(turns) > 0:
                last_turn = turns[-1]
                if last_turn.get("role") == "assistant":
                    contents = last_turn.get("content", [])
                    if contents:
                        answer_text = contents[0].get("text", "").strip()
                # Check for reasoning metadata
                meta = last_turn.get("metadata", {})
                if meta:
                    thinking_text = str(meta)
                    
        # Render response visibly into Chrome DOM
        js_display_resp = f"""
        (() => {{
            const chatbot = document.querySelector('.chatbot, [data-testid=\"chatbot\"]');
            if (chatbot) {{
                const aMsg = document.createElement('div');
                aMsg.style.cssText = 'background:#f8fafc;border:1px solid #cbd5e1;padding:12px;border-radius:8px;margin:8px 0;font-family:sans-serif;';
                aMsg.innerHTML = '<strong>Spark-X2.6-4B:</strong><br>' + {json.dumps(answer_text.replace('\n', '<br>'))};
                chatbot.appendChild(aMsg);
                window.scrollTo(0, document.body.scrollHeight);
            }}
            return true;
        }})()
        """
        spark_client.send_cmd("Runtime.evaluate", {"expression": js_display_resp, "returnByValue": True})
        time.sleep(1)
        
        shot_path = save_screenshot_png(f"online_spark_x2_6_4b_{task_id}")
        
        # Validation
        validator_fn = task["validator"]
        v_passed, v_score, v_reason = False, 0.0, "Validator error"
        if quota_error:
            v_reason = f"Cloud-Testbedingung unzureichend: {quota_error}"
        else:
            try:
                val_out = validator_fn(answer_text)
                if isinstance(val_out, tuple):
                    if len(val_out) == 3:
                        v_passed, v_score, v_reason = val_out
                    elif len(val_out) == 2:
                        v_passed, v_score = val_out
                        v_reason = "Passed" if v_passed else "Failed"
                else:
                    v_passed = bool(val_out)
                    v_score = 1.0 if v_passed else 0.0
                    v_reason = "Passed" if v_passed else "Failed"
            except Exception as e:
                v_reason = f"Exception: {str(e)}"
            
        print(f"Antwort ({dur_sec}s): {answer_text[:100]}...")
        print(f"Validierung: Passed={v_passed}, Score={v_score}, Grund={v_reason}")
        print(f"Screenshot: {shot_path}")
        
        record = {
            "model_id": "XHToken/Spark-X2.6-4B",
            "model_architecture": "Hybrid Reasoning 4B (2026)",
            "task_id": task_id,
            "dimension": dim,
            "prompt": prompt,
            "raw_response": answer_text,
            "thinking_content": thinking_text,
            "duration_sec": dur_sec,
            "passed": v_passed,
            "score": v_score,
            "validation_reason": v_reason,
            "screenshot_path": shot_path,
            "timestamp": datetime.now().isoformat()
        }
        results.append(record)
        
        with open(out_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
        time.sleep(2)
        
    spark_client.close()
    print(f"\n[OK] Spark-X2.6-4B Benchmark abgeschlossen. Rohdaten: {out_file}")
    return results, out_file

def main():
    token_path = os.path.join(PROJECT_ROOT, "data", ".hf_token")
    if not os.path.exists(token_path):
        raise RuntimeError("No .hf_token found in data/.hf_token")
    with open(token_path) as f:
        token = f.read().strip()
        
    print("=== START VOLLSTÄNDIGER ONLINE-BENCHMARK (PHASE 5) ===")
    mini_results, mini_file = run_minicpm5_benchmark(token)
    spark_results, spark_file = run_spark_benchmark(token)
    
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG ONLINE-ERGEBNISSE:")
    print("="*60)
    
    mini_passed = sum(1 for r in mini_results if r["passed"])
    spark_passed = sum(1 for r in spark_results if r["passed"])
    
    print(f"MiniCPM5-2B:    {mini_passed}/6 ({round(mini_passed/6*100, 1)}%) bestanden.")
    print(f"Spark-X2.6-4B:  {spark_passed}/6 ({round(spark_passed/6*100, 1)}%) bestanden.")
    print(f"Dateien:\n  - {mini_file}\n  - {spark_file}")

if __name__ == "__main__":
    main()
