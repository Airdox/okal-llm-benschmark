"""
Metriken- und Ressourcenerfassung für das LLM-Benchmark-System.
"""
import time
import psutil
from typing import Dict, Any, Optional

class ResourceTracker:
    def __init__(self):
        self.process = psutil.Process()
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.start_ram_mb: float = 0.0
        self.peak_ram_mb: float = 0.0
        self.cpu_samples = []

    def start(self):
        self.start_time = time.perf_counter()
        self.start_ram_mb = psutil.virtual_memory().used / (1024 * 1024)
        self.peak_ram_mb = self.start_ram_mb
        self.cpu_samples = []
        # Non-blocking CPU sample init
        psutil.cpu_percent(interval=None)

    def sample(self):
        current_ram = psutil.virtual_memory().used / (1024 * 1024)
        if current_ram > self.peak_ram_mb:
            self.peak_ram_mb = current_ram
        cpu = psutil.cpu_percent(interval=None)
        if cpu > 0:
            self.cpu_samples.append(cpu)

    def stop(self) -> Dict[str, Any]:
        self.end_time = time.perf_counter()
        self.sample()
        avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0.0
        return {
            "wall_time_sec": round(self.end_time - self.start_time, 3),
            "start_ram_mb": round(self.start_ram_mb, 1),
            "peak_ram_mb": round(self.peak_ram_mb, 1),
            "ram_delta_mb": round(self.peak_ram_mb - self.start_ram_mb, 1),
            "avg_cpu_percent": round(avg_cpu, 1),
        }

def compute_llm_metrics(ollama_resp: Dict[str, Any], resource_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Berechnet standardisierte Durchsatz- und Latenzkennzahlen aus Ollama-Metriken."""
    total_dur_ns = ollama_resp.get("total_duration", 0)
    load_dur_ns = ollama_resp.get("load_duration", 0)
    prompt_dur_ns = ollama_resp.get("prompt_eval_duration", 0)
    eval_dur_ns = ollama_resp.get("eval_duration", 0)

    prompt_tokens = ollama_resp.get("prompt_eval_count", 0)
    eval_tokens = ollama_resp.get("eval_count", 0)

    tps_eval = (eval_tokens / (eval_dur_ns / 1e9)) if eval_dur_ns > 0 else 0.0
    tps_prompt = (prompt_tokens / (prompt_dur_ns / 1e9)) if prompt_dur_ns > 0 else 0.0

    return {
        "total_duration_sec": round(total_dur_ns / 1e9, 3),
        "load_duration_sec": round(load_dur_ns / 1e9, 3),
        "prompt_eval_sec": round(prompt_dur_ns / 1e9, 3),
        "eval_duration_sec": round(eval_dur_ns / 1e9, 3),
        "prompt_tokens": prompt_tokens,
        "eval_tokens": eval_tokens,
        "eval_tps": round(tps_eval, 2),
        "prompt_tps": round(tps_prompt, 2),
        **resource_metrics
    }
