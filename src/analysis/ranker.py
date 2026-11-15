"""
Auswertungs- und Ranking-Engine für das LLM-Benchmark-System.
Berechnet Wilson-Score-Konfidenzintervalle, Dimensions-Teilrankings sowie
Rangliste A (Qualität) und Rangliste B (Gesamteffizienz).
"""
import os
import sys
import json
import math
import glob
from collections import defaultdict
from typing import Dict, Any, List, Tuple

def wilson_score_interval(successes: int, total: int, z: float = 1.96) -> Tuple[float, float]:
    """Berechnet das Wilson-Score-Intervall für binomiale Konfidenz (95% bei z=1.96)."""
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denominator = 1 + (z ** 2) / total
    centre_adjusted_probability = p + (z ** 2) / (2 * total)
    adjusted_std_dev = math.sqrt((p * (1 - p) + (z ** 2) / (4 * total)) / total)
    
    lower_bound = (centre_adjusted_probability - z * adjusted_std_dev) / denominator
    upper_bound = (centre_adjusted_probability + z * adjusted_std_dev) / denominator
    return max(0.0, round(lower_bound, 3)), min(1.0, round(upper_bound, 3))

class BenchmarkAnalyzer:
    def __init__(self, results_dir: str):
        self.results_dir = results_dir

    def load_stage_results(self, stage: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """Lädt alle JSONL-Ergebnisse für eine gegebene Teststufe."""
        pattern = os.path.join(self.results_dir, f"*_stage_{stage}_*.jsonl")
        files = glob.glob(pattern)
        model_results = defaultdict(list)

        for fpath in files:
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    if item.get("type") == "run_header":
                        continue
                    model_name = item.get("model_name")
                    if model_name:
                        model_results[model_name].append(item)
                        
        return dict(model_results)

    def analyze_model(self, model_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Berechnet umfassende statistische Kennzahlen für ein Modell."""
        total_tasks = len(records)
        if total_tasks == 0:
            return {}

        successes = sum(1 for r in records if r.get("passed", False))
        raw_accuracy = successes / total_tasks
        ci_lower, ci_upper = wilson_score_interval(successes, total_tasks)

        # Dimensionen aufschlüsseln
        dim_scores = defaultdict(list)
        for r in records:
            dim = r.get("dimension", "Unknown")
            dim_scores[dim].append(1.0 if r.get("passed", False) else 0.0)

        dim_accuracies = {
            dim: round(sum(scores) / len(scores), 3)
            for dim, scores in dim_scores.items()
        }

        # Performanz-Metriken (TPS, Latenz, RAM)
        tps_list = [r["metrics"]["eval_tps"] for r in records if "metrics" in r and r["metrics"].get("eval_tps", 0) > 0]
        ttft_list = [r["metrics"]["prompt_eval_sec"] for r in records if "metrics" in r]
        ram_peaks = [r["metrics"]["peak_ram_mb"] for r in records if "metrics" in r]

        avg_tps = round(sum(tps_list) / len(tps_list), 2) if tps_list else 0.0
        avg_ttft = round(sum(ttft_list) / len(ttft_list), 3) if ttft_list else 0.0
        max_ram = round(max(ram_peaks), 1) if ram_peaks else 0.0

        # Quality Score Q (0 bis 100)
        quality_score = round(raw_accuracy * 100, 1)

        # Efficiency Index E:
        # Belohnt hohe Qualität und hohen Durchsatz (TPS), bestraft hohen RAM-Bedarf
        # Formel: E = (Quality_Score * avg_tps) / (max_ram_gb * 10)
        ram_gb = max(1.0, max_ram / 1024.0)
        efficiency_index = round((quality_score * avg_tps) / (ram_gb * 10.0), 2)

        return {
            "model_name": model_name,
            "total_tasks": total_tasks,
            "successes": successes,
            "accuracy": round(raw_accuracy, 3),
            "quality_score": quality_score,
            "ci_95": [ci_lower, ci_upper],
            "avg_tps": avg_tps,
            "avg_ttft_sec": avg_ttft,
            "peak_ram_mb": max_ram,
            "efficiency_index": efficiency_index,
            "dimension_scores": dim_accuracies
        }

    def generate_rankings(self, stage: int = 1) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Erzeugt Rangliste A (Qualität) und Rangliste B (Effizienz)."""
        data = self.load_stage_results(stage)
        model_stats = [self.analyze_model(m, recs) for m, recs in data.items() if recs]

        # Rangliste A: Sortiert nach Quality Score (absteigend)
        rank_a = sorted(model_stats, key=lambda x: x.get("quality_score", 0), reverse=True)

        # Rangliste B: Sortiert nach Efficiency Index (absteigend)
        rank_b = sorted(model_stats, key=lambda x: x.get("efficiency_index", 0), reverse=True)

        return rank_a, rank_b

    def export_markdown_report(self, stage: int = 1) -> str:
        """Erzeugt einen formatgeschützten Markdown-Bericht der Ranglisten."""
        rank_a, rank_b = self.generate_rankings(stage)
        lines = []
        lines.append(f"## Benchmark-Ranglisten (Stufe {stage})\n")
        
        lines.append("### Rangliste A: Ergebnisqualität (Quality Score)")
        lines.append("| Rang | Modell | Quality Score | Erfolgsquote (95% CI) | Gelöste Aufgaben |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for i, m in enumerate(rank_a, 1):
            ci = f"[{m['ci_95'][0]:.2f} – {m['ci_95'][1]:.2f}]"
            lines.append(f"| **#{i}** | `{m['model_name']}` | **{m['quality_score']:.1f}%** | {m['accuracy']*100:.1f}% {ci} | {m['successes']}/{m['total_tasks']} |")

        lines.append("\n### Rangliste B: Gesamteffizienz (Hardware-Ressourcenbezug)")
        lines.append("| Rang | Modell | Efficiency Index | Durchsatz (t/s) | Latenz (TTFT) | Peak RAM |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for i, m in enumerate(rank_b, 1):
            lines.append(f"| **#{i}** | `{m['model_name']}` | **{m['efficiency_index']:.2f}** | {m['avg_tps']} t/s | {m['avg_ttft_sec']}s | {m['peak_ram_mb']} MB |")

        return "\n".join(lines)
