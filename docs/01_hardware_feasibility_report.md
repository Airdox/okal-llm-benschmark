# Technischer Bestandsaufnahme- und Machbarkeitsbericht (Phase 1)
**Datum:** 2026-11-16  
**Projekt:** Autonomes LLM-Benchmark- und Modellvergleichssystem  
**Status:** Verifiziert & Abgeschlossen

---

## 1. Zusammenfassung

Die empirische Bestandsaufnahme der tatsächlichen Ausführungsumgebung wurde vollständig und automatisiert durchgeführt. Der Coding-Agent besitzt über die lokale Befehlsschnittstelle direkten, autorisierten Zugriff auf das lokale Windows-System des Nutzers. Alle nachfolgenden Hardware-, Speicher- und Modellkennwerte wurden über native Windows-CIM/WMI-Schnittstellen, Dateisystemabfragen und direkte Abfragen der Ollama-REST-API (`http://127.0.0.1:11434`) erhoben und verifiziert.

---

## 2. Verifizierte Hardware-Spezifikationen

| Komponente | Tatsächlicher Wert / Messung | Relevanz für LLM-Inferenz |
| :--- | :--- | :--- |
| **Betriebssystem** | Microsoft Windows 11 Home (64-Bit, Version 10.0.26200) | Unterstützt moderne Windows-APIs, Ollama-Daemon, Python 3.14.7 |
| **CPU-Modell** | **Intel(R) Core(TM) i3-7020U CPU @ 2.30 GHz** | 2 physische Kerne, 4 logische Threads (Kaby Lake, 15W TDP). AVX2 unterstützt, kein AVX-512. |
| **Installierter RAM** | **20.377.292 KB (~19,43 GiB / 20 GB)** | Ausreichend Kapazität für Modelle bis ~7B/8B (Q4_K_M benötigt ca. 4–6 GB RAM), freier RAM bei Ruhezustand ca. 7,1 GB. |
| **Grafikkarte (GPU)** | **Intel(R) HD Graphics 620** (integrierte GPU) | Treiber: 26.20.100.7810. Kein dedizierter VRAM (nur shared Host-RAM). |
| **NVIDIA-GPU / CUDA** | **Nicht vorhanden** (`nvidia-smi not found`) | **Keine CUDA-/TensorRT-Beschleunigung.** |
| **Tatsächliches Inferenz-Backend** | **100% CPU (llama.cpp via AVX2)** | Verifiziert durch `ollama ps`: `PROCESSOR: 100% CPU`. |

---

## 3. Speicherplatz- und Sicherheitsanalyse (Kritischer Befund)

| Laufwerk | Gesamtkapazität | Belegter Speicher | Freier Speicher | Sicherheitsstatus |
| :--- | :--- | :--- | :--- | :--- |
| **C:** | 233,5 GB | 232,9 GB | **< 690 MB** | ⚠️ **KRITISCH VOLL** |
| **E:** (Arbeitsverzeichnis) | 390,6 GB | 333,5 GB | **~ 57,1 GB** | ✅ **Ausreichend Speicher frei** |

> [!CAUTION]
> **Extremes Speicherrisiko auf Laufwerk C:**  
> Auf Laufwerk C: sind weniger als 700 MB frei! Standardmäßig speichert Ollama Modelle im Benutzerverzeichnis (`C:\Users\p_kro\.ollama\models`). Ein unkontrollierter Download oder Temp-Dateien auf C: würden das System sofort zum Absturz bringen oder den Betriebssystembetrieb blockieren.  
> **Verbindliche Schutzmaßnahme:**
> 1. Sämtliche Projektdateien, temporären Dateien, Logs und Benchmark-Datensätze verbleiben strikt auf **`E:\okal llm benschmark`**.
> 2. Neue Modelldownloads dürfen **ausschließlich nach ausdrücklicher Nutzerfreigabe** und nach möglicher Umleitung von `OLLAMA_MODELS` auf Laufwerk E: (z.B. `E:\.ollama\models`) erwogen werden.

---

## 4. Verifizierter Ollama-Status & Modellbestand

**Ollama-Daemon:** Aktiv (PID 5096 lauscht auf `127.0.0.1:11434`), Version 0.33.1.  
Python-Umgebung: **Python 3.14.7** mit vorinstallierten Bibliotheken `psutil 7.2.2`, `numpy 2.5.3`, `scipy 1.18.1`, `scikit-learn 1.9.1`, `requests 2.34.2`.

### Installierte Modelle (Soll-Ist-Abgleich):

| Modell-ID in Ollama | Format / Familie | Exakte Parameter | Quantisierung | Dateigröße | Verifizierte Fähigkeiten |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`qwen3.5:4b`** | GGUF / qwen35 | 4.7B | **Q4_K_M** | 3,39 GB | `vision`, `completion`, `tools`, `thinking` |
| **`gemma4:e2b`** | GGUF / gemma4 | 5.1B | **Q4_K_M** | 7,16 GB | `completion`, `tools`, `thinking` |
| **`llama2:latest`** | GGUF / llama | 7.0B | **Q4_0** | 3,83 GB | `completion` |
| **`nomic-embed-text:latest`** | GGUF / nomic-bert | 137M | F16 | 274 MB | `embedding` |
| **`glm-5.2:cloud`** | Cloud-Proxy | 756B | - | Remote | Remote via ollama.com (nicht lokal offline) |

---

## 5. Empirische Performance-Basismessung (Intel i3-7020U, 100% CPU)

Die ersten realen Inferenzmessungen für `qwen3.5:4b` lieferten folgende verifizierte Metriken:
- **Kaltstart (Laden von Disk in RAM):** 25,46 Sekunden.
- **Prompt-Evaluierung (Prefill):** ca. 8,5 – 10 Tokens/Sekunde.
- **Token-Generierung (Warm):** ca. 3,2 – 3,8 Tokens/Sekunde.
- **RAM-Footprint:** ca. 3,1 GB.
- **Architektonische Besonderheit:** Das Modell erzeugt eine separate Denkspur (`thinking`-Token / Chain of Thought).

---

## 6. Fazit & Akzeptanzkriterium Phase 1

- Das Akzeptanzkriterium für Phase 1 ist **vollständig erfüllt**: Alle Hardware- und Modellinformationen stammen nachweislich direkt von der lokalen Maschine.
- Die CPU-Grenzen (2 Kerne, Inferenzrate ca. 3–4 t/s) erfordern ein hocheffizientes Testdesign mit fokussierten, prägnanten Prompts und token-sparenden Sampling-Limits.
- Phase 1 ist hiermit abgeschlossen.
