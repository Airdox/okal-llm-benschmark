import sys
import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.cdp_client import get_page_client

def inspect_dom():
    client = get_page_client(url_filter="openbmb-minicpm5-2b-demo")
    js = """
    (() => {
        const tas = Array.from(document.querySelectorAll('textarea')).map(t => ({ placeholder: t.placeholder, class: t.className, tag: t.tagName }));
        const btns = Array.from(document.querySelectorAll('button')).map(b => ({ text: b.innerText, class: b.className, label: b.getAttribute('aria-label') }));
        const checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"]')).map(c => ({ id: c.id, checked: c.checked, label: c.parentElement ? c.parentElement.innerText : '' }));
        return {
            title: document.title,
            textareas: tas,
            buttons: btns,
            checkboxes: checkboxes
        };
    })()
    """
    res = client.send_cmd("Runtime.evaluate", {"expression": js, "returnByValue": True})
    val = res.get("result", {}).get("value")
    print(json.dumps(val, indent=2))
    client.close()

if __name__ == "__main__":
    inspect_dom()
