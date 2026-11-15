# Recherche & Kandidatenmatrix geeigneter LLMs (Phase 3)
**Datum:** 2026-11-16  
**Projekt:** Autonomes LLM-Benchmark- und Modellvergleichssystem  
**Hardware-Profil:** Intel Core i3-7020U (2 Kerne / 4 Threads, 2.3 GHz), 20 GB RAM, reine CPU-Inferenz (100% CPU via AVX2), freier Speicherplatz C: <700 MB, E: 57 GB.  
**Status:** Verifiziert & Klassifiziert

---

## 1. Auswahlkriterien für die Zielhardware

Aufgrund der Dual-Core-CPU ohne dedizierte GPU sind Modelle mit $>7\text{B}$ Parametern für interaktive oder agentische Anwendungen zu langsam (Latenzen $> 500\text{ms}$ pro Token, Inferenzraten $< 2\text{ t/s}$). 
Der optimale Sweet Spot für diese Maschine liegt im Bereich **1B bis 4B Parameter** in **Q4_K_M**-Quantisierung:
- **Downloadgröße:** 0,9 GB bis 2,5 GB
- **RAM-Footprint:** ca. 1,5 GB bis 3,5 GB (problemlos im verfügbaren 20 GB RAM)
- **Erwartete Generierungsrate:** 8 bis 15 Tokens/Sekunde auf 2 CPU-Kernen.

---

## 2. Kandidatenmatrix

### Gruppe 1: Bereits lokal installierte Modelle (Sofort testbar ohne Download)

| Modellkennung | Entwickler | Reale Parameter | Quantisierung | Disk-Größe | RAM (verifiziert) | Kontext | Stärken & Fähigkeiten |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`qwen3.5:4b`** | Alibaba Cloud | 4.7B | Q4_K_M | 3.39 GB | 3.1 GB | 262K | Vision, Tools, Thinking-Spur (Chain of Thought), hohe Reasoning-Dichte |
| **`gemma4:e2b`** | Google DeepMind | 5.1B | Q4_K_M | 7.16 GB | ~4.5 GB | 8K | Tools, Thinking, hohe Tokens/s-Rate (empirisch ~10.8 t/s im Warmstart) |
| **`llama2:latest`** | Meta AI | 7.0B | Q4_0 | 3.83 GB | 6.1 GB | 4K | Historische Baseline; solide Allgemeinsprache, jedoch ältere Architektur |

---

### Gruppe 2: Hochgradig empfehlenswerte Kandidaten (Erfordern Freigabe vor Download)

| Modellkennung | Entwickler | Parameter | Quant. (Ollama) | Downloadgröße | Geschätzter RAM | Empfohlene Rolle im Agentensystem | Primäre Eignung |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`qwen2.5:3b`** | Alibaba Cloud | 3.09B | Q4_K_M | ~1.9 GB | ~2.2 GB | Allrounder / Planer / Extraktor | Exzellente deutsche Sprachleistung, strukturierte JSON-Ausgabe, Tool-Calling |
| **`qwen2.5-coder:3b`** | Alibaba Cloud | 3.09B | Q4_K_M | ~1.9 GB | ~2.2 GB | Spezialisierter Coder / Executor | Führend in Code-Generierung, Bugfixing und Syntax-Validierung in der <4B-Klasse |
| **`llama3.2:3b`** | Meta AI | 3.21B | Q4_K_M | ~2.0 GB | ~2.4 GB | Planer / Dialog-Agent | 128k Kontext, starkes Instruction Following, geringe Latenz |
| **`llama3.2:1b`** | Meta AI | 1.23B | Q4_K_M | ~1.3 GB | ~1.5 GB | Ultra-Fast Executor / Worker | Extrem schnell auf Dual-Core CPU (>15 t/s), ideal für einfache Worker-Tasks |
| **`gemma2:2b`** | Google DeepMind | 2.61B | Q4_K_M | ~1.6 GB | ~2.0 GB | Reasoning / Textverständnis | Hohe Wissensdichte und Reasoning bei sehr geringer Modellgröße |
| **`smollm2:1.7b`** | Hugging Face | 1.71B | Q4_K_M | ~1.0 GB | ~1.3 GB | Ressourcenschonender Filter | Extrem geringer Footprint, On-Device optimiert |
| **`phi3.5:3.8b`** | Microsoft | 3.82B | Q4_K_M | ~2.2 GB | ~2.7 GB | Deep Reasoning | Hohe mathematische und logische Problemlösungskompetenz |

---

## 3. Risikobewertung & Speicherplatz-Vorgabe

> [!IMPORTANT]
> **Kritische Download-Restriktion:**
> Da Laufwerk C: weniger als 700 MB freien Speicher aufweist, darf **kein Modell** über das Standardverzeichnis (`C:\Users\p_kro\.ollama\models`) heruntergeladen werden.
> Ein Download ist erst zulässig, wenn:
> 1. Der Nutzer eine individuelle Einzelfreigabe für das konkrete Modell erteilt hat.
> 2. Die Umgebungsvariable `OLLAMA_MODELS` auf ein Verzeichnis auf Laufwerk E: (z.B. `E:\ollama_models`) gesetzt ist, wo 57 GB frei sind.
