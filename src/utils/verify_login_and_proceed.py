import sys
import os
import time
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import get_page_client
from src.utils.screen_capture import capture_screen

def verify_login():
    client = get_page_client()
    js = """
    (() => {
        const userBtn = document.querySelector('button[aria-label="User menu"], a[href^="/settings/profile"], [data-testid="user-avatar"], a[href="/logout"], header img[alt*="avatar"], nav img[alt*="avatar"], .user-avatar');
        const loginBtn = document.querySelector('a[href="/login"], button[aria-label="Log in"]');
        return {
            url: window.location.href,
            title: document.title,
            isLoggedIn: userBtn !== null,
            loginBtnPresent: loginBtn !== null,
            cookiePresent: document.cookie.includes('token') || document.cookie.includes('hf')
        };
    })()
    """
    res = client.send_cmd("Runtime.evaluate", {"expression": js, "returnByValue": True})
    val = res.get("result", {}).get("value")
    print("Login verification result:", val)

    bmp = r"E:\okal llm benschmark\data\screenshots\desktop_post_login_verification.bmp"
    capture_screen(bmp)
    client.close()

    png = bmp.replace(".bmp", ".png")
    subprocess.run([
        "powershell", "-ExecutionPolicy", "Bypass", "-File",
        r"E:\okal llm benschmark\src\utils\bmp_to_png.ps1",
        "-InputBmp", bmp,
        "-OutputPng", png
    ], check=True)
    print("Screenshot saved to:", png)
    return val

if __name__ == "__main__":
    verify_login()
