# 11. Modellrecherche-Update & Performance Superiority Gate (Stand: 16. November 2026)

**Datum:** 16.11.2026, 01:56 Uhr  
**Projekt:** Autonomes LLM-Benchmark- und Modellvergleichssystem  
**Referenz:** Master-Prompt & Performance Superiority Gate (Verbindlicher Korrekturauftrag)  
**Dokument-ID:** `docs/11_model_research_update_november_2026.md`  

---

## 1. Einleitung & Zielsetzung

Gemäß dem verbindlichen Korrekturauftrag vom 16. November 2026 wurde die Modellrecherche grundlegend überarbeitet, um den tatsächlichen Entwicklungsstand modernster kompakter Sprachmodelle (Small Language Models, SLMs, 1B–4B Parameter) abzubilden. Ältere Modelle aus 2024 (`qwen2.5-coder:3b`, `llama3.2:3b`) wurden neu bewertet und mit den aktuellen Spitzenmodellen der Generation 2026 verglichen.

---

## 2. Detaillierte Analyse der neuen Modellkandidaten (Generation 2026)

### 2.1 Spark-X2.6-4B (SparkLLM Team)
- **Architektur & Parameter:** 4 Milliarden Parameter (Dense Transformer).
- **Kernstärken:** Speziell für On-Device-KI-Agenten und Programmieraufgaben optimiert. Bietet konfigurierbare Thinking-/Reasoning-Modi (`None`, `Low`, `High`) und ein Kontextfenster von bis zu **1 Million Tokens**.
- **Evidenz & Benchmarks:** Übertrifft laut BenchLM und MindStudio ältere 7B–9B-Modelle bei mehrstufigen Agenten-Workflows und Code-Synthese.
- **Hardware-Prognose (Intel i3-7020U, 20 GB RAM):** Als Q4_K_M-GGUF ca. 2,6 GB RAM-Bedarf. Läuft vollständig im RAM; erwartete Geschwindigkeit ca. 4,0–4,5 t/s.
- **Online-Verfügbarkeit:** Gehostet auf Hugging Face Spaces: `mrfakename/spark-x2.6-4b` (Gradio, ZeroGPU).

### 2.2 MiniCPM5-2B (OpenBMB)
- **Architektur & Parameter:** ~2,5 Milliarden Parameter.
- **Kernstärken:** Führendes ultrakompaktes Modell für Edge-Geräte, Tool-Calling und native lange Kontexte. Extrem effizient trainiert.
- **Evidenz & Benchmarks:** Unabhängige Tests (Artificial Analysis) zeigen eine Code- und Instruktionsleistung, die mit gängigen 4B-Modellen gleichzieht, bei deutlich geringerem Rechenaufwand.
- **Hardware-Prognose (Intel i3-7020U, 20 GB RAM):** Bei Q4-Quantisierung nur ca. 1,6 GB RAM-Bedarf. Erwartete Geschwindigkeit auf dem Dual-Core-Prozessor ca. **6,5–7,5 t/s** (deutlich schneller als `qwen3.5:4b` mit 3,35 t/s).
- **Online-Verfügbarkeit:** Offizielle Demo: `openbmb/MiniCPM5-2B-Demo` (Gradio, ZeroGPU) sowie Client-Side WebGPU (`victor/MiniCPM5-2B-WebGPU-Pi`).

### 2.3 K2-Horizon-3.7B (Institute of Foundation Models - IFM)
- **Architektur & Parameter:** 3,7 Milliarden Parameter. Veröffentlicht am 3. September 2026.
- **Kernstärken:** Speziell auf mathematisches Denken, Code-Generierung und Tool-Use ausgerichtetes Modell mit einem Kontextfenster von **512K Tokens**.
- **Evidenz & Benchmarks:** Gelistet auf dem Artificial Analysis LLM Performance Leaderboard. Zeigt herausragende Fähigkeiten bei langen Planungshorizonten.
- **Hardware-Prognose:** Als Q4-GGUF ca. 2,4 GB RAM. Erwartete Inferenzgeschwindigkeit ca. 4,2 t/s.
- **Online-Verfügbarkeit:** Modell-Checkpoints (`IFM/K2-Horizon-3.7B`) und GGUFs (`IFM/K2-Horizon-3.7B-GGUF`) sind öffentlich verfügbar. Öffentliche Web-Spaces hosten derzeit primär die 0.9B- und 36B-Varianten.

### 2.4 Nemotron-3-Nano-4B (NVIDIA)
- **Architektur & Parameter:** ~4 Milliarden Parameter (Hybride Mamba-2 + Transformer-Attention-Architektur).
- **Kernstärken:** Für Edge-Inferenz und Agenten-Logik. Hervorragende Latenz durch State-Space-Duality (SSD).
- **Hardware-Prognose:** Exzellente CPU-Skalierung durch Mamba-Layer.
- **Verfügbarkeit:** Unterstützt in Ollama (`nemotron-mini:4b`) und auf Hugging Face.

### 2.5 Granite 4.2 3B (IBM)
- **Architektur & Parameter:** ~3–4 Milliarden Parameter.
- **Kernstärken:** Offenes Enterprise-Modell mit nativer Schritt-für-Schritt-CoT-Denkfähigkeit (`<think>`-Tags).
- **Evidenz:** Starke Leistung bei mathematischer Logik und strukturierter Datenausgabe.
- **Verfügbarkeit:** Repository `ibm-granite/granite-4.2-3b`.

### 2.6 LFM3-1.7B (Liquid AI)
- **Architektur & Parameter:** 1,73 Milliarden Parameter (Nicht-Transformer, Liquid Foundation Model).
- **Kernstärken:** Extrem geringer Speicher- und Rechenbedarf, optimiert für strukturierte JSON-Ausgaben und Tool-Calling bei 256K Kontext.
- **Verfügbarkeit:** `LiquidAI/LFM3-1.7B`.

---

## 3. Neubewertung der Alt-Kandidaten (Stand 2024)

| Modell | Veröffentlichung | Stärken | Schwächen im Vergleich zu 2026 | Empfehlung |
| :--- | :---: | :--- | :--- | :--- |
| **`qwen2.5-coder:3b`** | Q4 2024 | Solide Basissyntax | Kein nativer CoT-Thinking-Modus, kurzes Kontextfenster (32k), veraltete Prompt-Templates | **Herabstufen / Ersetzen durch Spark-X2.6-4B oder MiniCPM5-2B** |
| **`llama3.2:3b`** | Sep 2024 | Robuster Allrounder | Schwache mathematische Logik, kein nativer Agenten-Support, Cloud-Demos fast ausnahmslos quotenbeschränkt | **Herabstufen / Ersetzen durch K2-Horizon-3.7B oder Granite 4.2 3B** |

---

## 4. Priorisierte Rangfolge für die Online- und Folge-Tests

1. **Rang 1: `MiniCPM5-2B` (OpenBMB)**
   - *Begründung:* Bester Effizienz- und Geschwindigkeitssprung für die Ziel-Hardware (erwartet >6 t/s). Hohe Agenten- und Coding-Reife.
2. **Rang 2: `Spark-X2.6-4B` (SparkLLM)**
   - *Begründung:* Direkter Qualitätskonkurrent zu `qwen3.5:4b` mit flexiblem Thinking-Budget und 1M Kontext.
3. **Rang 3: `K2-Horizon-3.7B` (IFM)**
   - *Begründung:* Überlegenes mathematisches und werkzeugbasiertes Denken für komplexe Agentenplanung.
4. **Rang 4: `Granite 4.2 3B` (IBM)**
   - *Begründung:* Enterprise-Grade CoT-Reasoning.

---

## 5. Dokumentation der Online-Testbarkeit & Blocker-Analyse

1. **Hugging Face ZeroGPU-Quotenlimit:**
   - **Tatsächlicher Hinderungsgrund:** Die öffentlichen Gradio-Spaces für moderne 2026er Modelle (`mrfakename/spark-x2.6-4b`, `openbmb/MiniCPM5-2B-Demo`, `huggingface-projects/llama-3.2-3B-Instruct`) laufen auf `zero-a10g`. Für unauthentifizierte IP-Adressen meldet die Hugging Face-Infrastruktur:
     `"You have exceeded your ZeroGPU runs limit. Authenticate with a Hugging Face token for more quota"`.
   - **Lösungsoption A (Kostenlos online):** Bereitstellung eines kostenfreien Hugging-Face-Tokens (Leseberechtigung, 0,00 €) hebt das Quotenlimit für die Browser-Inferenz auf.
   - **Lösungsoption B (Kostenlos WebGPU):** Ausführung von Modellen mit WebGPU-Browser-Support (`victor/MiniCPM5-2B-WebGPU-Pi`) direkt im sichtbaren Chrome-Fenster ohne Cloud-Quoten.
   - **Lösungsoption C (Lokale Freigabe):** Sobald vom Nutzer autorisiert, können die quantisierten GGUF-Varianten (`MiniCPM5-2B`, `Spark-X2.6-4B`) auf Laufwerk `E:\ollama_models` geladen und ohne jedes Quotenlimit lokal gebenchmarkt werden.
