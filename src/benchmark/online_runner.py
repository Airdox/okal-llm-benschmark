"""
Automatisierter Online-Benchmark-Runner für kostenlose Hugging Face Spaces (Phase 5).
Ermöglicht verifizierte, legale und kostenfreie Vorabtests ohne lokale Downloads oder API-Keys.
"""
import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.benchmark.suite import STAGE1_TASKS
from src.benchmark.validator import clean_markdown_fence

class HuggingFaceSpaceRunner:
    def __init__(self, space_url: str = "https://huggingface-projects-llama-3-2-3b-instruct.hf.space"):
        self.space_url = space_url.rstrip("/")
        self.output_dir = os.path.join(PROJECT_ROOT, "data", "raw_results")
        os.makedirs(self.output_dir, exist_ok=True)

    def query(self, prompt: str, max_tokens: int = 256, temperature: float = 0.1) -> Dict[str, Any]:
        """Führt eine echte Online-Inferenz über den Gradio-Stream-Endpunkt aus."""
        call_url = f"{self.space_url}/gradio_api/call/generate"
        payload = {
            "data": [
                prompt,
                [], # History
                max_tokens,
                temperature,
                0.95, # top_p
                40,   # top_k
                1.1   # repetition penalty
            ]
        }
        
        t0 = time.perf_counter()
        resp = requests.post(call_url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
        resp.raise_for_status()
        event_id = resp.json().get("event_id")
        
        # SSE Stream abholen
        stream_url = f"{self.space_url}/gradio_api/call/generate/{event_id}"
        r_stream = requests.get(stream_url, stream=True, timeout=60)
        
        final_text = ""
        error_msg = ""
        for line in r_stream.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8")
            if decoded.startswith("event: error"):
                error_msg = "ZeroGPU/Provider Quota Exceeded"
            elif decoded.startswith("data: "):
                try:
                    raw_data = decoded[6:]
                    data_payload = json.loads(raw_data)
                    if isinstance(data_payload, dict) and "error" in data_payload:
                        error_msg = str(data_payload["error"])
                    elif isinstance(data_payload, list) and len(data_payload) > 0:
                        final_text = data_payload[0]
                except Exception:
                    pass
                    
        dur = round(time.perf_counter() - t0, 3)
        if error_msg and not final_text:
            raise RuntimeError(f"Online-Inferenz-Quota/Fehler: {error_msg}")
        return {
            "response": final_text,
            "latency_sec": dur,
            "provider": "Hugging Face Spaces (Free Cloud Tier)",
            "space_url": self.space_url
        }

    def run_stage1_online(self, model_name: str = "meta-llama/Llama-3.2-3B-Instruct") -> str:
        """Führt den kompletten Stufe-1-Benchmark online aus."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_filename = f"online_{model_name.replace('/', '_').replace(':', '_')}_stage_1_{timestamp}.jsonl"
        out_filepath = os.path.join(self.output_dir, out_filename)

        print(f"\n=======================================================")
        print(f"Starte kostenlosen Online-Vorabtest für '{model_name}'")
        print(f"Ziel: {self.space_url}")
        print(f"=======================================================")

        with open(out_filepath, "w", encoding="utf-8") as f:
            header = {
                "type": "online_run_header",
                "model_name": model_name,
                "provider": "Hugging Face Spaces",
                "space_url": self.space_url,
                "timestamp": timestamp,
                "stage": 1
            }
            f.write(json.dumps(header, ensure_ascii=False) + "\n")

            for t in STAGE1_TASKS:
                task_id = t["id"]
                prompt = t["prompt"]
                print(f"[{task_id}] Sende Online-Anfrage...")
                
                try:
                    infer_res = self.query(prompt, max_tokens=256, temperature=0.1)
                    raw_output = infer_res["response"]
                    latency = infer_res["latency_sec"]
                    passed, score, feedback = t["validator"](raw_output)
                    err_msg = ""
                except Exception as e:
                    raw_output = ""
                    latency = 0.0
                    passed, score, feedback = False, 0.0, f"Online-Verbindungsfehler: {str(e)}"
                    err_msg = str(e)

                status_sym = "✅" if passed else "❌"
                print(f"[{task_id}] {status_sym} Score: {score:.1f} | Latenz: {latency:4.2f}s | {feedback}")
                
                record = {
                    "task_id": task_id,
                    "dimension": t["dimension"],
                    "model_name": model_name,
                    "passed": passed,
                    "score": score,
                    "feedback": feedback,
                    "raw_output": raw_output,
                    "latency_sec": latency,
                    "provider": "Hugging Face Spaces",
                    "error": err_msg,
                    "timestamp": datetime.now().isoformat()
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()

        print(f"\nOnline-Vorabtest abgeschlossen. Ergebnisse in:\n{out_filepath}")
        return out_filepath

if __name__ == "__main__":
    runner = HuggingFaceSpaceRunner()
    runner.run_stage1_online()
