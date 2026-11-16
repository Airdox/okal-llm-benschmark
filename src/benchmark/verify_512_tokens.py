"""
Empirische Verifikation des 512-Token-Limits für Reasoning-Modelle (qwen3.5:4b).
Misst getrennt: Thinking-Tokens, Response-Tokens, done_reason und Validierung.
"""
import requests
import json
import time
import re

OLLAMA_API_BASE = "http://127.0.0.1:11434"

EUROPEAN_CAPITALS = {
    "BERLIN", "PARIS", "ROM", "ROME", "MADRID", "WIEN", "VIENNA", "BERN",
    "LONDON", "DUBLIN", "LISBOA", "LISSABON", "BRUESSEL", "BRUSSELS", "BRÜSSEL",
    "AMSTERDAM", "WARSCHAU", "WARSAW", "PRAG", "PRAGUE", "BUDAPEST", "STOCKHOLM",
    "OSLO", "HELSINKI", "KOPENHAGEN", "COPENHAGEN", "ATHEN", "ATHENS",
    "BRATISLAVA", "LJUBLJANA", "ZAGREB", "SARAJEVO", "BELGRAD", "BELGRADE", "SOFIA",
    "BUKAREST", "BUCHAREST", "TALLINN", "RIGA", "VILNIUS", "REYKJAVIK"
}

def test_prompt(task_id: str, prompt: str, max_tokens: int = 512):
    print(f"\n=======================================================")
    print(f"Test {task_id} mit num_predict = {max_tokens}")
    print(f"=======================================================")
    
    payload = {
        "model": "qwen3.5:4b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 0.95,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "num_predict": max_tokens
        }
    }
    
    t0 = time.perf_counter()
    resp = requests.post(f"{OLLAMA_API_BASE}/api/generate", json=payload, timeout=240)
    wall_dur = round(time.perf_counter() - t0, 3)
    data = resp.json()
    
    raw_response = data.get("response", "")
    thinking = data.get("thinking", "")
    done_reason = data.get("done_reason", "unknown")
    eval_tokens = data.get("eval_count", 0)
    prompt_tokens = data.get("prompt_eval_count", 0)
    eval_dur = round(data.get("eval_duration", 0) / 1e9, 3)
    tps = round(eval_tokens / eval_dur, 2) if eval_dur > 0 else 0.0
    
    print(f"Done Reason:    {done_reason}")
    print(f"Gesamt-Tokens:  {eval_tokens} Tokens in {eval_dur}s ({tps} t/s)")
    print(f"Wall-Time:      {wall_dur}s")
    print(f"Thinking-Länge: {len(thinking)} Zeichen")
    print(f"Response:       {repr(raw_response.strip())}")
    
    return {
        "task_id": task_id,
        "done_reason": done_reason,
        "eval_tokens": eval_tokens,
        "eval_dur_sec": eval_dur,
        "tps": tps,
        "thinking_len": len(thinking),
        "thinking_preview": thinking[:200] + "..." if len(thinking) > 200 else thinking,
        "raw_response": raw_response.strip()
    }

if __name__ == "__main__":
    p_i1 = "Nenne drei europäische Hauptstädte. Bedingung: Schreibe jedes Wort komplett in GROSSBUCHSTABEN und trenne sie nur durch Kommas, absolut ohne Leerzeichen (z.B. ROM,PARIS,MADRID). Keine anderen Wörter oder Erklärungen."
    res_i1 = test_prompt("QS-I1 (Hauptstädte)", p_i1, 512)
    
    tokens = res_i1["raw_response"].split(",")
    valid_format = len(tokens) == 3 and all(t.isupper() for t in tokens)
    valid_content = all(t in EUROPEAN_CAPITALS for t in tokens)
    print(f"QS-I1 Validierung: Format={valid_format}, Content={valid_content} -> {'✅ BESTANDEN' if valid_format and valid_content else '❌ FEHLGESCHLAGEN'}")
    
    p_g1 = "Bilde die 3. Person Singular Präteritum des Verbs 'nachdenken' und setze diese Form in einen vollständigen deutschen Satz. Gib nur diesen Satz aus."
    res_g1 = test_prompt("QS-G1 (Grammatik)", p_g1, 512)
    
    resp_clean = res_g1["raw_response"].lower()
    gram_match = bool(re.search(r"\b(er|sie|es|man)\s+dachte\b.*?\bnach\b", resp_clean) and resp_clean.endswith((".", "!", "?")))
    print(f"QS-G1 Validierung: Muster erfüllt={gram_match} -> {'✅ BESTANDEN' if gram_match else '❌ FEHLGESCHLAGEN'}")
    
    # Unload
    requests.post(f"{OLLAMA_API_BASE}/api/generate", json={"model": "qwen3.5:4b", "keep_alive": 0})
    
    results = [res_i1, res_g1]
    with open("E:/okal llm benschmark/data/raw_results/token_512_verification.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nErgebnisse in E:/okal llm benschmark/data/raw_results/token_512_verification.json gespeichert.")
