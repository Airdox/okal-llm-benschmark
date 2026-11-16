import sys
import os
import time
import ctypes
from ctypes import wintypes
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import get_page_client
from src.utils.screen_capture import capture_screen

def check_login():
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    h_default = user32.OpenDesktopW('default', 0, False, 0x01FF)
    user32.SetThreadDesktop(h_default)

    hwnd = 2556090 # Visible Benchmark Chrome
    HWND_TOPMOST = -1
    SWP_SHOWWINDOW = 0x0040

    fore_hwnd = user32.GetForegroundWindow()
    fore_tid = user32.GetWindowThreadProcessId(fore_hwnd, None)
    curr_tid = kernel32.GetCurrentThreadId()

    user32.AttachThreadInput(curr_tid, fore_tid, True)
    user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 1366, 730, SWP_SHOWWINDOW)
    user32.SetForegroundWindow(hwnd)
    user32.AttachThreadInput(curr_tid, fore_tid, False)

    client = get_page_client()
    print("Navigating visible Chrome to https://huggingface.co/login ...")
    client.send_cmd("Page.navigate", {"url": "https://huggingface.co/login"})
    time.sleep(4)

    # Check login status
    js_check = """
    (() => {
        const isLoggedOut = document.querySelector('input[name="username"], input[type="password"], button[type="submit"]') !== null;
        const userMenu = document.querySelector('button[aria-label="User menu"], a[href^="/settings/profile"], a[href="/logout"], [data-testid="user-avatar"]');
        return {
            isLoggedIn: userMenu !== null,
            isLoginPage: isLoggedOut,
            url: window.location.href,
            title: document.title
        };
    })()
    """
    res = client.send_cmd("Runtime.evaluate", {"expression": js_check, "returnByValue": True})
    status_info = res.get("result", {}).get("value")
    print("Login status info:", status_info)

    time.sleep(1)
    bmp = r"E:\okal llm benschmark\data\screenshots\desktop_huggingface_login_screen.bmp"
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
    return status_info

if __name__ == "__main__":
    check_login()
