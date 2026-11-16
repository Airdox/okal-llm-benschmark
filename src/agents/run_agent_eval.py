"""
Evaluierungs-Skript für den Vergleich der Agenten-Architekturen (Phase 8).
Vergleicht Variante A, B, C und D auf einer definierten Programmier- und Planungsaufgabe.
"""
import os
import sys
import json
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.agents.architectures import AgentBenchmarkComparator

def main():
    task = {
        "description": "Schreibe eine Python-Funktion `filter_primes(numbers: list) -> list`, die alle Primzahlen aus einer Liste von Ganzzahlen filtert und aufsteigend sortiert zurückgibt. Beachte: Negative Zahlen, 0 und 1 sind keine Primzahlen. Leere Liste ergibt [].",
        "unit_tests": """
assert filter_primes([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == [2, 3, 5, 7]
assert filter_primes([-5, -2, 0, 1]) == []
assert filter_primes([13, 11, 2]) == [2, 11, 13]
assert filter_primes([]) == []
"""
    }

    comparator = AgentBenchmarkComparator(strong_model="qwen3.5:4b", fast_model="gemma4:e2b")
    results = []

    print("\n=======================================================")
    print("Starte empirischen Vergleich der 4 Agenten-Architekturen")
    print("=======================================================")

    # Variante A: Single-Agent
    print("\n--- Teste Variante A (Single-Agent: qwen3.5:4b) ---")
    res_a = comparator.run_variant_a(task)
    print(f"Ergebnis: {'✅' if res_a['passed'] else '❌'} | Zeit: {res_a['total_time_sec']}s | Tokens: {res_a['total_tokens']} | {res_a['feedback']}")
    results.append(res_a)

    # Variante B: Hierarchisch (qwen3.5 plant, gemma4 führt aus)
    print("\n--- Teste Variante B (Planer qwen3.5 -> Executor gemma4) ---")
    res_b = comparator.run_variant_b(task)
    print(f"Ergebnis: {'✅' if res_b['passed'] else '❌'} | Zeit: {res_b['total_time_sec']}s | Tokens: {res_b['total_tokens']} | {res_b['feedback']}")
    results.append(res_b)

    # Variante C: Planer - Executor - Verifier mit Feedback-Loop
    print("\n--- Teste Variante C (Planer -> Exec -> Verifier Loop) ---")
    res_c = comparator.run_variant_c(task)
    print(f"Ergebnis: {'✅' if res_c['passed'] else '❌'} | Zeit: {res_c['total_time_sec']}s | Tokens: {res_c['total_tokens']} | Schleifen: {res_c['loops']}")
    results.append(res_c)

    # Variante D: Dynamische Eskalation (Erst gemma4, bei Fehler qwen3.5)
    print("\n--- Teste Variante D (Dynamische Eskalation) ---")
    res_d = comparator.run_variant_d(task)
    print(f"Ergebnis: {'✅' if res_d['passed'] else '❌'} | Zeit: {res_d['total_time_sec']}s | Tokens: {res_d['total_tokens']} | Eskalationen: {res_d['escalations']}")
    results.append(res_d)

    # Speichern
    out_path = os.path.join(PROJECT_ROOT, "data", "raw_results", "agent_architectures_comparison.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nArchitektur-Vergleich abgeschlossen. Ergebnisse in:\n{out_path}")

if __name__ == "__main__":
    main()
