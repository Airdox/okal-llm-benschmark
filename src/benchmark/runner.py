"""
Autonomer lokaler Benchmark-Runner für Ollama-Modelle.
Protokolliert Latenz, Durchsatz, RAM, CPU und deterministische Testergebnisse.
"""
import os
import sys
import json
import time
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

# Sicherstellen, dass das Projektverzeichnis im sys.path liegt
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.benchmark.metrics import ResourceTracker, compute_llm_metrics
from src.benchmark.suite import STAGE1_TASKS, STAGE2_TASKS

OLLAMA_API_BASE = "http://127.0.0.1:11434"

class BenchmarkRunner:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or os.path.join(PROJECT_ROOT, "data", "raw_results")
        os.makedirs(self.output_dir, exist_ok=True)
        self.tracker = ResourceTracker()

    def unload_model(self, model_name: str):
        """Entlädt ein Modell sofort aus dem RAM (keep_alive: 0)."""
        try:
            requests.post(
                f"{OLLAMA_API_BASE}/api/generate",
                json={"model": model_name, "keep_alive": 0},
                timeout=10
            )
        except Exception as e:
            print(f"[WARNUNG] Konnte Modell {model_name} nicht entladen: {e}")

    def warmup(self, model_name: str) -> Dict[str, Any]:
        """Führt einen Warmstart-Lauf durch und misst die Modell-Ladezeit von Disk in RAM."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starte Kaltstart/Warmup für '{model_name}'...")
        self.tracker.start()
        resp = requests.post(
            f"{OLLAMA_API_BASE}/api/generate",
            json={
                "model": model_name,
                "prompt": "Warmup ping.",
                "stream": False,
                "options": {"num_predict": 5}
            },
            timeout=180
        )
        res_metrics = self.tracker.stop()
        data = resp.json()
        metrics = compute_llm_metrics(data, res_metrics)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] '{model_name}' geladen in {metrics['load_duration_sec']}s (RAM-Peak: {metrics['peak_ram_mb']} MB).")
        return metrics

    def run_task(self, model_name: str, task: Dict[str, Any], temperature: float = 0.0, iteration: int = 1) -> Dict[str, Any]:
        """Führt eine einzelne Benchmark-Aufgabe aus und validiert das Ergebnis."""
        task_id = task["id"]
        prompt = task["prompt"]
        dim = task.get("dimension", "")

        # QA-Auflage: 768 Tokens für Reasoning & Coding, 384 Tokens für Standard-Aufgaben
        if dim in ("Reasoning", "Coding"):
            max_tokens = max(task.get("max_tokens", 768), 768)
            timeout_sec = 180
        else:
            max_tokens = max(task.get("max_tokens", 384), 384)
            timeout_sec = 120

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "repeat_penalty": 1.1,
                "num_predict": max_tokens
            }
        }

        self.tracker.start()
        try:
            res = requests.post(f"{OLLAMA_API_BASE}/api/generate", json=payload, timeout=timeout_sec)
            res.raise_for_status()
            resp_data = res.json()
            err_msg = ""
        except Exception as e:
            resp_data = {}
            err_msg = str(e)

        res_metrics = self.tracker.stop()
        metrics = compute_llm_metrics(resp_data, res_metrics)

        # Trennung von Response und Thinking-Spur (Ollama Chain-of-Thought)
        raw_output = resp_data.get("response", "")
        thinking_output = resp_data.get("thinking", "")
        done_reason = resp_data.get("done_reason", "unknown")

        # 4-Stufen-Fehlerklassifikation
        error_type = "none"
        if done_reason == "length":
            if not raw_output.strip():
                error_type = "truncated_in_reasoning"
            else:
                error_type = "truncated_in_response"
        elif err_msg:
            error_type = "network_or_timeout"

        # QA-Auflage: Hauptbewertung erfolgt verbindlich auf dem Feld 'response'
        eval_target = raw_output
        try:
            if not eval_target.strip():
                passed, score, val_feedback = False, 0.0, f"Keine finale Antwort erzeugt (Fehler: {error_type})."
            else:
                val_res = task["validator"](eval_target)
                if isinstance(val_res, tuple):
                    if len(val_res) == 3:
                        passed, score, val_feedback = val_res
                    elif len(val_res) == 2:
                        passed, score = val_res
                        val_feedback = "Passed" if passed else "Failed"
                else:
                    passed = bool(val_res)
                    score = 1.0 if passed else 0.0
                    val_feedback = "Passed" if passed else "Failed"

                if not passed and error_type == "none":
                    error_type = "content_incorrect"
        except Exception as ve:
            passed, score, val_feedback = False, 0.0, f"Validierungsfehler: {str(ve)}"
            if error_type == "none":
                error_type = "format_error"

        result = {
            "task_id": task_id,
            "dimension": task["dimension"],
            "model_name": model_name,
            "iteration": iteration,
            "temperature": temperature,
            "passed": passed,
            "score": score,
            "feedback": val_feedback,
            "raw_output": raw_output,
            "thinking_output": thinking_output,
            "done_reason": done_reason,
            "error_type": error_type,
            "error": err_msg,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        return result

    def run_stage(self, model_name: str, stage: int = 1, iterations: int = 1) -> str:
        """Führt eine komplette Teststufe für ein Modell aus und speichert die JSONL-Ergebnisse."""
        tasks = STAGE1_TASKS if stage == 1 else STAGE2_TASKS
        stage_name = f"stage_{stage}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_filename = f"{model_name.replace(':', '_')}_{stage_name}_{timestamp}.jsonl"
        out_filepath = os.path.join(self.output_dir, out_filename)

        print(f"\n=======================================================")
        print(f"Starte Stufe {stage} ({len(tasks)} Aufgaben) für '{model_name}'")
        print(f"=======================================================")

        # 1. Warmstart / Kaltstart-Messung
        warmup_metrics = self.warmup(model_name)

        results = []
        with open(out_filepath, "w", encoding="utf-8") as f:
            # Header mit Warmup-Metriken
            header = {
                "type": "run_header",
                "model_name": model_name,
                "stage": stage,
                "warmup_metrics": warmup_metrics,
                "total_tasks": len(tasks),
                "iterations": iterations,
                "timestamp": timestamp
            }
            f.write(json.dumps(header, ensure_ascii=False) + "\n")

            for it in range(1, iterations + 1):
                # Erster Durchlauf immer deterministisch (T=0.0), weitere mit T=0.2
                temp = 0.0 if it == 1 else 0.2
                print(f"\n--- Durchlauf {it}/{iterations} (T={temp}) ---")

                for t in tasks:
                    res = self.run_task(model_name, t, temperature=temp, iteration=it)
                    status_sym = "✅" if res["passed"] else "❌"
                    tps = res["metrics"]["eval_tps"]
                    print(f"[{res['task_id']}] {status_sym} Score: {res['score']:.1f} | TPS: {tps:4.1f} t/s | {res['feedback']}")
                    f.write(json.dumps(res, ensure_ascii=False) + "\n")
                    f.flush()
                    results.append(res)

        # Nach Abschluss Modell entladen zur Schonung von RAM und Systemressourcen
        self.unload_model(model_name)
        print(f"\nStufe {stage} für '{model_name}' abgeschlossen. Ergebnisse in:\n{out_filepath}")
        return out_filepath

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Lokaler LLM Benchmark Runner")
    parser.add_argument("--model", type=str, required=True, help="Ollama Modellname (z.B. qwen3.5:4b)")
    parser.add_argument("--stage", type=int, default=1, choices=[1, 2], help="Teststufe (1=Quick, 2=Main)")
    parser.add_argument("--iterations", type=int, default=1, help="Anzahl der Durchläufe pro Aufgabe")
    args = parser.parse_args()

    runner = BenchmarkRunner()
    runner.run_stage(args.model, stage=args.stage, iterations=args.iterations)
