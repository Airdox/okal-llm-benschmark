# Performance Superiority Gate: Modellfilterung & Kandidatenbereinigung
**Datum:** 2026-11-16  
**Projekt:** Autonomes LLM-Benchmark- und Modellvergleichssystem  
**Regel:** Verbindliche Ergänzung zum Master-Prompt (Performance Superiority Gate)  
**Status:** Audit abgeschlossen – Kandidatenliste bereinigt

---

## 1. Ausgangslage & Referenz-Baseline

Als primäre Vergleichsbasis dienen die empirisch erhobenen Leistungsdaten der vorhandenen Modelle auf der Zielhardware (Intel Core i3-7020U, 2 Kerne, 20 GB RAM):

| Modell | Parameter | Quantisierung | Empirische Baseline (Stufe 1) | Reale Stärken & Schwächen |
| :--- | :--- | :--- | :--- | :--- |
| **`gemma4:e2b`** | 5.1B | Q4_K_M | **66,7 % Score**, 4,94 t/s TPS, 16,3 GB RAM, 40,8s Warmup | Hohe Tokens/s-Rate für 5B, exzellente Tool-Nutzung (QS-A1), solide Codegenerierung. Schwäche: 256-Token-Limit bei Denkschleifen. |
| **`qwen3.5:4b`** | 4.7B | Q4_K_M | **50,0 % Score**, 3,35 t/s TPS, 12,8 GB RAM, 23,5s Warmup | Tiefe mathematische Deduktion (QS-R1), validierter Python-Code (QS-C1), 262k Kontext. Schwäche: Extremer Chain-of-Thought-Overhead (250+ Tokens Monolog pro Task). |
| **`llama2:latest`** | 7.0B | Q4_0 | **33,3 % Score**, 2,78 t/s TPS, 14,8 GB RAM, 23,5s Warmup | Historische Baseline; mathematische Halluzinationen, scheitert an Code- und Grammatikaufgaben. |

---

## 2. Prüfung der 7 Neumodell-Kandidaten am Performance Superiority Gate

Gemäß den verbindlichen Kriterien (Erwartete Verbesserung gegenüber Baseline in Qualität, Coding/Reasoning, Geschwindigkeit oder Agentik) ergibt sich folgende wissenschaftliche Neubewertung:

| Kandidat | Parameter | Generation / Datum | Erwartete Leistung vs. Baseline | Gate-Entscheidung | Begründung |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`smollm2:1.7b`** | 1.71B | Ende 2024 | Signifikant schwächer in Reasoning (MMLU ~52%) und Coding (HumanEval ~28%). | ❌ **AUSGESCHLOSSEN** | Keine plausible Überlegenheit. Auf 20 GB RAM bringt die Einsparung von 1 GB RAM keinen Vorteil, der einen 30–40% Qualitätsabfall rechtfertigt. |
| **`llama3.2:1b`** | 1.23B | Ende 2024 | 1B-Modelle scheitern reproduzierbar an komplexer deutscher Syntax, Multi-Step-Logik und Tool-Calling. | ❌ **AUSGESCHLOSSEN** | Unterdimensioniert für anspruchsvolle Agentik- und Planungsaufgaben. |
| **`gemma2:2b`** | 2.61B | Mitte 2024 | Vorgänger-Generation von `gemma4:e2b`. | ❌ **AUSGESCHLOSSEN** | Älteres Modell derselben Familie. Die vorhandene `gemma4:e2b` deckt die Domäne mit modernerer Architektur und besserem Tool-Support ab. |
| **`phi3.5:3.8b`** | 3.82B | Mitte 2024 | Stark bei englischem synthetischem Math, jedoch notorisch schwach in deutscher Sprache und strukturierter JSON-Formatierung. | ❌ **AUSGESCHLOSSEN** | Deutlicher Nachteil bei deutschen Aufgaben und Agentik gegenüber `qwen3.5:4b`. |
| **`qwen2.5:3b`** | 3.09B | Herbst 2024 | Vorgänger von `qwen3.5:4b`. | ⏸️ **ZURÜCKGESTELLT** | Solider Allrounder, aber `qwen3.5:4b` ist der direkte Nachfolger. Nur als Notfall-Fallback relevant. |
| **`qwen2.5-coder:3b`** | 3.09B | Ende 2024 | **Spezialisierter Code-Experte** (5.5T Tokens Pretraining). Übertrifft Generalisten-Modelle (wie Gemma und Llama) bei Coding-Benchmarks (HumanEval >80%) deutlich. | ✅ **ZUGELASSEN (Kandidat #1)** | **Erfüllt Bedingung 2 & 3:** Deutlich höhere Coding- und Bugfixing-Präzision bei höherer Latenz-Effizienz (~6–8 t/s auf CPU) durch schlanke 3B-Architektur. |
| **`llama3.2:3b`** | 3.21B | Ende 2024 | 128k Kontext, **direkte Anweisungsbefolgung ohne Reasoning-Token-Overhead**. Im Online-Vorabtest: 100% Pass auf QS-R1 & QS-C1 in <2,9s. | ✅ **ZUGELASSEN (Kandidat #2)** | **Erfüllt Bedingung 3:** Vergleichbare Ergebnisqualität bei deutlich höherer effektiver Antwortgeschwindigkeit (kein 250-Token-Denkmonolog). |

---

## 3. Bereinigte Testplanung

1. **Ausgeschlossene Modelle:** `smollm2:1.7b`, `llama3.2:1b`, `gemma2:2b`, `phi3.5:3.8b`.  
   *Konsequenz:* Keine Online-Tests, keine Downloads, keine Rechenzeitverschwendung.
2. **Zugelassene Neumodelle für die weitere Evaluation:**
   - **Kandidat #1:** `qwen2.5-coder:3b` (Fokus: Coding, Agentic Tool-Execution)
   - **Kandidat #2:** `llama3.2:3b` (Fokus: Schneller Executor, IFEval, Dialog ohne Token-Verschwendung)
3. **Qualitätssicherung:**
   Dieser Bereinigungsbericht wird dem unabhängigen QA-Agenten zur formellen Prüfung vorgelegt.
