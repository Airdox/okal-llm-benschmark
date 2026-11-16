import requests

queries = ['coder-3b', 'qwen-3b', 'qwen2.5-3b', 'qwen2.5 coder 3b', 'qwen2.5-coder']
found_spaces = []

for q in queries:
    r = requests.get(f'https://huggingface.co/api/spaces?search={q}&limit=25').json()
    print(f"=== Query: {q} ({len(r)} found) ===")
    for s in r:
        sid = s['id']
        try:
            info = requests.get(f'https://huggingface.co/api/spaces/{sid}', timeout=2).json()
            stage = info.get('runtime', {}).get('stage')
            if stage in ['RUNNING', 'SLEEPING']:
                sdk = info.get('sdk')
                hw = info.get('runtime', {}).get('hardware', {}).get('current')
                print(f"  {sid} | stage: {stage} | sdk: {sdk} | hw: {hw}")
                found_spaces.append((sid, stage, sdk, hw))
        except Exception:
            pass

print(f"\nTotal active/sleeping spaces found: {len(found_spaces)}")
