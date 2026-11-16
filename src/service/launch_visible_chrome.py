import subprocess
import os
import time
import requests
import ctypes
from ctypes import wintypes

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = r"E:\okal llm benschmark\chrome_benchmark_profile"

def launch_chrome():
    os.makedirs(PROFILE_DIR, exist_ok=True)
    
    # Check if already running on port 9222
    try:
        r = requests.get("http://127.0.0.1:9222/json/version", timeout=1)
        if r.status_code == 200:
            print("Chrome already active on port 9222.")
            return True
    except Exception:
        pass

    # Launch detached visible Chrome on default desktop
    si = subprocess.STARTUPINFO()
    si.lpDesktop = r"WinSta0\default"
    
    cmd = [
        CHROME_EXE,
        "--remote-debugging-port=9222",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1280,720",
        "--window-position=40,40",
        "https://huggingface.co/"
    ]
    
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    
    print(f"Launching visible Chrome with profile {PROFILE_DIR}...")
    proc = subprocess.Popen(
        cmd,
        startupinfo=si,
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        close_fds=True
    )
    print("Process spawned, PID:", proc.pid)
    
    # Poll for port 9222 readiness
    for i in range(20):
        time.sleep(1)
        try:
            r = requests.get("http://127.0.0.1:9222/json/version", timeout=1)
            if r.status_code == 200:
                print("CDP successfully initialized:", r.json().get("Browser"))
                bring_chrome_to_front()
                return True
        except Exception:
            pass
            
    print("Failed to connect to CDP on 9222.")
    return False

def bring_chrome_to_front():
    user32 = ctypes.windll.user32
    h_default = user32.OpenDesktopW("default", 0, False, 0x01FF)
    if h_default:
        user32.SetThreadDesktop(h_default)

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    hwnds = []

    def enum_proc(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                if "Hugging Face" in title or "Chrome" in title:
                    hwnds.append((hwnd, title))
        return True

    user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
    for hwnd, title in hwnds:
        user32.ShowWindow(hwnd, 9) # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        print(f"SetForegroundWindow: {hwnd} ({title})")
        break

if __name__ == "__main__":
    success = launch_chrome()
    print("Launch success:", success)
