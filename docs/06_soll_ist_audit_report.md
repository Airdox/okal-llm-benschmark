# Umfassender Soll-Ist-Projektprüfbericht & Qualitätsaudit
**Datum:** 2026-11-16  
**Projekt:** Autonomes LLM-Benchmark- und Modellvergleichssystem  
**Referenz:** Master-Prompt Anforderungen vs. Bisheriger Projektverlauf  
**Status:** Audit abgeschlossen – Korrekturbedarf identifiziert & priorisiert

---

## 1. Abgleich: Master-Prompt Soll-Anforderungen vs. Ist-Stand

| Phase / Anforderung | Status im Projekt | Dokumentation / Nachweis | Bewertung & Abweichungen |
| :--- | :--- | :--- | :--- |
| **Phase 1: Technische Bestandsaufnahme** | ✅ **Abgeschlossen** | `docs/01_hardware_feasibility_report.md` | Real erhoben: Intel i3-7020U (2 Kerne, 2.3 GHz), 20 GB RAM, keine CUDA-GPU, Ollama 0.33.1. Kritischer C:-Speicherplatz (<700 MB / 4,87 GB frei) identifiziert. |
| **Phase 2: Wissenschaftliche Benchmark-Recherche** | ✅ **Abgeschlossen** | `docs/02_scientific_benchmark_research.md` | Analyse von IFEval, HumanEval, MBPP, GSM8K, LiveCodeBench; Begründung von Kontaminationsschutz, Wilson-Score-CI, 8 Dimensionen. |
| **Phase 3: Modellrecherche geeigneter LLMs** | ✅ **Abgeschlossen** | `docs/03_model_candidates_matrix.md` | Sweet-Spot (1B–4B) identifiziert; Matrix für 7 neue Kandidaten + 3 vorhandene Modelle. |
| **Phase 4: Entwicklung Testsystem (Design)** | ✅ **Abgeschlossen** | `docs/04_benchmark_test_design.md` | Version 1.0.0 spezifiziert: 2-Stufen-Modell (Quick Screening 6 Tasks, Haupttest 16 Tasks). |
| **Phase 5: Kostenlose Online-Vorabtests** | ⚠️ **Ausstehend / Verzögert** | Offen | **Wesentliche Abweichung:** Wurde zugunsten der lokalen Initialisierung zurückgestellt. Muss nun vor weiteren Modellentscheidungen vorrangig durchgeführt werden. |
| **Phase 6: Individuelle Downloadfreigabe** | ✅ **Eingehalten** | Keine Downloads ausgeführt | Keine Downloads erfolgt; strikte Null-Download-Garantie und C:-Laufwerksschutz gewahrt. |
| **Phase 7: Automatische lokale Benchmarks** | 🔄 **Teilweise (Stufe 1 v1.0.0)** | `data/raw_results/*.jsonl` | Stufe 1 für `qwen3.5:4b` und `gemma4:e2b` durchgeführt. Zeigt deutliche Methodenlimitationen auf (Thinking-Token-Limit). |
| **Phase 8: Agentensystem-Vergleich** | 🟡 **Vorbereitet** | `src/agents/architectures.py` | Architekturmodule implementiert; Ausführung steht nach Stufe 2 an. |
| **Phase 9: Unabhängige Qualitätsprüfung** | ✅ **Abgeschlossen** | `docs/05_qa_validation_report.md` | Unabhängiger QA-Subagent (`af91f909-...`) führte reale Gegenprüfungen durch und formulierte verbindliche Auflagen. |
| **Phase 10: Statistische Auswertung** | 🟡 **Vorbereitet** | `src/analysis/ranker.py` | Ranking-Engine für Rangliste A (Qualität) und B (Effizienz) implementiert. |

---

## 2. Ursachenanalyse der Phasenabweichung (Lokale Benchmarks vor Online-Vorabtests)

### Der Befund:
Gemäß Master-Prompt sollte Phase 5 (Online-Vorabtests) als erste praktische Modellvergleichsphase dienen, um externe Kandidaten ohne lokalen Download vorab zu filtern. Der Orchestrator hat jedoch bereits lokale Stufe-1-Benchmarks auf den *bereits installierten* Modellen gestartet.

### Die Ursachen:
1. **Verwechslung von Bestands-Kalibrierung und Neumodell-Vorauswahl:** Der Orchestrator priorisierte die sofortige Feststellung der hardwareseitigen Leistungsbasis (Baseline auf 2 CPU-Kernen) anhand der bereits vorhandenen Modelle (`qwen3.5:4b`, `gemma4:e2b`), um Referenzdurchsätze (Tokens/s) für die spätere Effizienzformel zu ermitteln.
2. **Priorisierung lokaler Systemintegrität:** Da Laufwerk C: extrem voll ist und keine neuen Downloads erfolgen durften, wurde die lokale Runner-Infrastruktur primär an den existierenden Modellen verifiziert.
3. **Korrektur:** Neue Kandidaten (z.B. Qwen2.5-Coder-3B, Llama-3.2-3B, Gemma-2-2B) dürfen keinesfalls lokal gezogen werden, bevor nicht die Online-Vorabtests (Phase 5) planmäßig durchgeführt und dokumentiert wurden.

---

## 3. Analyse der empirischen Testergebnisse & Differenzierte Fehlerursachen

Die beiden ersten realen Testläufe der Stufe 1 (v1.0.0) liefern wertvolle wissenschaftliche Erkenntnisse:

### 3.1 Zusammenfassung der Rohdaten (Stufe 1, v1.0.0)

| Modell | Getestete Aufgaben | Erfolgsquote | Avg. TPS (CPU) | RAM-Peak | Kaltstart / Warmup |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`qwen3.5:4b`** | 6 | **3 / 6 (50,0 %)** | 3,35 t/s | 12,8 GB | 23,5 s |
| **`gemma4:e2b`** | 6 | **4 / 6 (66,7 %)** | 4,94 t/s | 16,3 GB | 40,8 s |

### 3.2 Differenzierung der Fehlerursachen

Die wissenschaftliche Differenzierung zwischen echten Modellschwächen und methodischen Testartefakten ist essenziell:

1. **Konfigurations- und Benchmark-Artefakte (Token-Limit bei Reasoning-Modellen):**
   - **Aufgabe QS-I1 (Europäische Hauptstädte):**
     - Sowohl `qwen3.5:4b` als auch `gemma4:e2b` erreichten bei 256 Tokens `done_reason: "length"` mit leerem `raw_output`.
     - Bei `qwen3.5:4b` belegt die protokollierte Denkspur (`thinking_output`), dass das Modell die Aufgabe intern vollkommen korrekt analysiert, validiert und die Lösung `BERLIN,PARIS,LONDON` explizit formuliert hatte. Da jedoch die Denkspur 256 Tokens beanspruchte, brach der Inferenzprozess exakt vor der Ausgabe der eigentlichen Antwort ab.
     - **Urteil:** Dies ist **kein Wissens- oder Anweisungsfehler des Modells**, sondern ein **klares Konfigurationsdefizit des Benchmark-Setups** (unzureichendes Tokenbudget für Reasoning-Modelle).
   - **Aufgabe QS-G1 (Deutsche Grammatik):**
     - Identisches Phänomen: `qwen3.5:4b` verbrauchte 256 Tokens für linguistische Vorüberlegungen über trennbare Verben im Präteritum. Die Generierung wurde abgeschnitten.
     - **Urteil:** Testbedingungs-Artefakt.

2. **Echte Modell- und Formatierungsfehler:**
   - **Aufgabe QS-A1 (Agentic Tool Call) bei `qwen3.5:4b`:**
     - Das Modell gab den Tool-Call nicht als reines JSON aus, sondern verharrte im internen Denkmodus (`done_reason: 'length'`).
   - Im Gegensatz dazu meisterte **`gemma4:e2b`** dieselbe Aufgabe (`QS-A1`) exzellent mit einem perfekten JSON-Tool-Call: `{"tool": "get_weather", "args": {"city": "Berlin"}}` bei 4,7 t/s.

3. **Integritäts-Garantie:**
   - Gemäß der verbindlichen Vorgabe werden diese Ergebnisse **nicht rückwirkend modifiziert oder gelöscht**. Sie verbleiben als authentischer Datenbestand von **Benchmark-Version 1.0.0**.

---

## 4. Konkrete Nachweise der unabhängigen Qualitätsprüfung

Die vom Master-Prompt geforderte unabhängige Prüfung durch einen separaten Prüfagenten wurde real vollzogen:
1. **Subagenten-Audit:** Der QA-Agent (`conversationId: af91f909-6c46-4b48-8453-ffcd4ffc287c`, Typ: `self`) führte eigenständige, unbeeinflusste System- und REST-API-Abfragen durch.
2. **Prüfbericht:** Vollständig niedergelegt in `E:/okal llm benschmark/docs/05_qa_validation_report.md`.
3. **Aufgedeckte Befunde des QA-Agenten:**
   - Bestätigung der echten Hardware und des C:-Laufwerksnotstands (97,9% belegt).
   - Unabhängige Entdeckung des "Thinking Token"-Budgetdefizits bei Reasoning-Modellen.
   - Aufdeckung semantischer Prüflücken (Regex-Validierung ohne Sachprüfung bei Hauptstädten).
   - Formulierung der 5 verbindlichen Auflagen (A bis E) zur Erteilung der "Freigabe mit Auflagen".

---

## 5. Korrekturplan & Priorisierung der nächsten Schritte

Um den Projektverlauf strikt mit dem Master-Prompt zu harmonisieren, gilt ab sofort folgende Arbeitsreihenfolge:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Priorität: Phase 5 – Kostenlose Online-Vorabtests                   │
│    - Prüfung kostenloser Hugging Face Spaces / Gradio-Endpunkte        │
│    - Durchführung dokumentierter Vorabtests für Recherche-Kandidaten   │
│    - Keine Kosten, keine CAPTCHA-Umgehung, vollständige Transparenz    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. Priorität: Definition Benchmark-Version 1.1.0                       │
│    - Erhöhung des Tokenbudgets auf 512 Tokens für Reasoning-Modelle    │
│    - Erprobung von System-Prompts zur Dämpfung unnötiger Denkmonologe  │
│    - Saubere Versionierung (v1.0.0 vs. v1.1.0)                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. Priorität: Phase 6 – Strukturierte Download-Freigabeanfrage         │
│    - Vorlage der Ergebnisse aus Phase 3 & 5 an den Nutzer              │
│    - Klare Freigabeanfrage für maximal 1-2 Favoriten mit E:-Routing    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. Priorität: Lokale Haupt-Benchmarks (Phase 7) & Agentik (Phase 8)    │
│    - Systematischer Vergleich aller autorisierten Modelle              │
│    - Ranglisten A & B sowie Abschlussbericht                           │
└────────────────────────────────────────────────────────────────────────┘
```
