import sys
import os
import json
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import SimpleCDPClient
import urllib.request

def create_hf_token():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode("utf-8"))
    tab = [t for t in tabs if t["id"] == "636DD09A1E829DA3C19E3A431C978642"][0]
    c = SimpleCDPClient(tab["webSocketDebuggerUrl"])
    
    js = """
    (() => {
        const readRadio = document.querySelector('input[type="radio"][value="read"]');
        if (readRadio) {
            readRadio.checked = true;
            readRadio.click();
            readRadio.dispatchEvent(new Event('change', { bubbles: true }));
        }
        const nameInput = document.querySelector('input[name="displayName"]');
        if (nameInput) {
            nameInput.value = 'benchmark-pretest';
            nameInput.dispatchEvent(new Event('input', { bubbles: true }));
            nameInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
        const createBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Create token');
        if (createBtn) {
            createBtn.click();
            return { success: true };
        }
        return { success: false, readRadio: !!readRadio, nameInput: !!nameInput };
    })()
    """
    res = c.send_cmd("Runtime.evaluate", {"expression": js, "returnByValue": True})
    print("Submit result:", res.get("result", {}).get("value"))
    
    time.sleep(3)
    # Check for created token
    js_token = """
    (() => {
        const inputs = Array.from(document.querySelectorAll('input, code, span')).map(e => e.value || e.innerText || '');
        const hfToken = inputs.find(t => t.startsWith('hf_') && t.length > 20);
        return {
            hfToken: hfToken || null,
            bodySnippet: document.body.innerText.slice(0, 1000)
        };
    })()
    """
    res_token = c.send_cmd("Runtime.evaluate", {"expression": js_token, "returnByValue": True})
    val = res_token.get("result", {}).get("value")
    print("Token extraction:", val.get("hfToken") is not None)
    if val.get("hfToken"):
        token_str = val.get("hfToken")
        print(f"Token found: {token_str[:7]}...{token_str[-4:]}")
        # Save to token file locally (strictly ignored by git)
        token_path = os.path.join(PROJECT_ROOT, "data", ".hf_token")
        with open(token_path, "w") as f:
            f.write(token_str.strip())
        print("Saved to", token_path)
    c.close()

if __name__ == "__main__":
    create_hf_token()
