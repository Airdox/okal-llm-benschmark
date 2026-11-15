"""
Implementierung und Vergleich vollständiger Agenten-Architekturen (Phase 8):
- Variante A: Single-Agent (Ein starkes Modell plant und führt aus)
- Variante B: Hierarchisch (Starkes Modell plant, kleineres Modell führt aus)
- Variante C: Planer - Executor - Unabhängiger Verifier
- Variante D: Dynamische Modellwahl mit automatischer Eskalation
"""
import time
import json
import requests
from typing import Dict, Any, List, Tuple
from src.benchmark.validator import validate_code, clean_markdown_fence

OLLAMA_API_BASE = "http://127.0.0.1:11434"

def call_ollama(model: str, prompt: str, system: str = "", max_tokens: int = 384, temperature: float = 0.0) -> Dict[str, Any]:
    """Führt einen Inferenzaufruf durch und misst Latenz, Token und Duration."""
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }
    t0 = time.perf_counter()
    resp = requests.post(f"{OLLAMA_API_BASE}/api/generate", json=payload, timeout=180)
    dur = time.perf_counter() - t0
    data = resp.json()
    output = data.get("response", "")
    thinking = data.get("thinking", "")
    final_text = output if output.strip() else thinking
    return {
        "text": final_text,
        "thinking": thinking,
        "prompt_tokens": data.get("prompt_eval_count", 0),
        "eval_tokens": data.get("eval_count", 0),
        "wall_time_sec": round(dur, 3),
        "load_duration_sec": round(data.get("load_duration", 0) / 1e9, 3)
    }

class AgentBenchmarkComparator:
    def __init__(self, strong_model: str = "qwen3.5:4b", fast_model: str = "gemma4:e2b"):
        self.strong_model = strong_model
        self.fast_model = fast_model

    def run_variant_a(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Variante A: Single-Agent (Ein starkes Modell bearbeitet die gesamte Aufgabe)."""
        prompt = f"Aufgabe: {task_spec['description']}\nSchreibe den vollständigen, fehlerfreien Python-Codeblock. Keine Prosa."
        res = call_ollama(self.strong_model, prompt, max_tokens=384)
        passed, score, feedback = validate_code(res["text"], task_spec["unit_tests"])
        return {
            "variant": "Variante A (Single-Agent)",
            "passed": passed,
            "score": score,
            "feedback": feedback,
            "total_calls": 1,
            "prompt_tokens": res["prompt_tokens"],
            "eval_tokens": res["eval_tokens"],
            "total_tokens": res["prompt_tokens"] + res["eval_tokens"],
            "total_time_sec": res["wall_time_sec"],
            "loops": 0,
            "escalations": 0
        }

    def run_variant_b(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Variante B: Hierarchischer Planer-Executor (Starkes Modell plant, kleineres führt aus)."""
        # Schritt 1: Planung
        plan_prompt = f"Erstelle einen präzisen, schrittweisen Implementierungsplan für folgende Aufgabe:\n{task_spec['description']}"
        res_plan = call_ollama(self.strong_model, plan_prompt, max_tokens=180)

        # Schritt 2: Ausführung durch schnelles Modell
        exec_prompt = f"Aufgabe: {task_spec['description']}\nFolge diesem Implementierungsplan strikt:\n{res_plan['text']}\nGib ausschließlich den Python-Codeblock aus."
        res_exec = call_ollama(self.fast_model, exec_prompt, max_tokens=384)

        passed, score, feedback = validate_code(res_exec["text"], task_spec["unit_tests"])
        return {
            "variant": "Variante B (Planner-Executor)",
            "passed": passed,
            "score": score,
            "feedback": feedback,
            "total_calls": 2,
            "prompt_tokens": res_plan["prompt_tokens"] + res_exec["prompt_tokens"],
            "eval_tokens": res_plan["eval_tokens"] + res_exec["eval_tokens"],
            "total_tokens": (res_plan["prompt_tokens"] + res_exec["prompt_tokens"]) + (res_plan["eval_tokens"] + res_exec["eval_tokens"]),
            "total_time_sec": round(res_plan["wall_time_sec"] + res_exec["wall_time_sec"], 3),
            "loops": 0,
            "escalations": 0
        }

    def run_variant_c(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Variante C: Planer - Executor - Unabhängiger Verifier mit Korrekturschleife."""
        # 1. Plan
        plan_prompt = f"Plan für: {task_spec['description']}"
        res_plan = call_ollama(self.strong_model, plan_prompt, max_tokens=150)

        # 2. Exec
        exec_prompt = f"Implementiere in Python basierend auf Plan:\n{res_plan['text']}\nCode:"
        res_exec = call_ollama(self.fast_model, exec_prompt, max_tokens=300)

        # 3. Verifier (Automatisch)
        passed, score, feedback = validate_code(res_exec["text"], task_spec["unit_tests"])
        loops = 0
        total_prompt = res_plan["prompt_tokens"] + res_exec["prompt_tokens"]
        total_eval = res_plan["eval_tokens"] + res_exec["eval_tokens"]
        total_time = res_plan["wall_time_sec"] + res_exec["wall_time_sec"]

        # Falls fehlgeschlagen, 1 gezielte Korrekturschleife durch Verifier-Feedback
        if not passed:
            loops += 1
            fix_prompt = f"Der Code hat folgenden Testfehler:\n{feedback}\nVorheriger Code:\n{res_exec['text']}\nKorrigiere den Fehler. Gib nur den gefixten Codeblock aus."
            res_fix = call_ollama(self.strong_model, fix_prompt, max_tokens=300)
            total_prompt += res_fix["prompt_tokens"]
            total_eval += res_fix["eval_tokens"]
            total_time += res_fix["wall_time_sec"]
            passed, score, feedback = validate_code(res_fix["text"], task_spec["unit_tests"])

        return {
            "variant": "Variante C (Planner-Exec-Verifier-Loop)",
            "passed": passed,
            "score": score,
            "feedback": feedback,
            "total_calls": 2 + loops,
            "prompt_tokens": total_prompt,
            "eval_tokens": total_eval,
            "total_tokens": total_prompt + total_eval,
            "total_time_sec": round(total_time, 3),
            "loops": loops,
            "escalations": 0
        }

    def run_variant_d(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Variante D: Dynamische Eskalation (Erst ressourcenschonendes Modell, bei Fehlschlag Eskalation an starkes Modell)."""
        # Versuch 1: Fast Model
        prompt = f"Aufgabe: {task_spec['description']}\nGib nur den Python-Codeblock aus."
        res_fast = call_ollama(self.fast_model, prompt, max_tokens=300)
        passed, score, feedback = validate_code(res_fast["text"], task_spec["unit_tests"])

        total_prompt = res_fast["prompt_tokens"]
        total_eval = res_fast["eval_tokens"]
        total_time = res_fast["wall_time_sec"]
        escalations = 0

        # Wenn Fast Model fehlschlägt: Automatische Eskalation an starkes Modell mit Fehlerdiagnose
        if not passed:
            escalations = 1
            esc_prompt = f"Aufgabe: {task_spec['description']}\nEin Vorversuch scheiterte mit: {feedback}\nCode-Versuch:\n{res_fast['text']}\nErstelle die korrekte Lösung in Python."
            res_esc = call_ollama(self.strong_model, esc_prompt, max_tokens=384)
            total_prompt += res_esc["prompt_tokens"]
            total_eval += res_esc["eval_tokens"]
            total_time += res_esc["wall_time_sec"]
            passed, score, feedback = validate_code(res_esc["text"], task_spec["unit_tests"])

        return {
            "variant": "Variante D (Dynamische Eskalation)",
            "passed": passed,
            "score": score,
            "feedback": feedback,
            "total_calls": 1 + escalations,
            "prompt_tokens": total_prompt,
            "eval_tokens": total_eval,
            "total_tokens": total_prompt + total_eval,
            "total_time_sec": round(total_time, 3),
            "loops": 0,
            "escalations": escalations
        }
