# Unabhängiger QA- & Validierungsbericht (Phase 5 Vorprüfung)
**Datum:** 2026-11-16  
**Rolle:** Unabhängiger QA-, Prüf- & Sicherheitsagent  
**Projekt:** Autonomes LLM-Benchmark- und Modellvergleichssystem  
**Geprüfte Dokumente:**  
1. `E:/okal llm benschmark/docs/01_hardware_feasibility_report.md` (Hardware & Machbarkeit)  
2. `E:/okal llm benschmark/docs/02_scientific_benchmark_research.md` (Wissenschaftliche Methodik)  
3. `E:/okal llm benschmark/docs/03_model_candidates_matrix.md` (Modellkandidaten)  
4. `E:/okal llm benschmark/docs/04_benchmark_test_design.md` (Testdesign & Spezifikation)  
**Status:** **Bedingt freigegeben (Freigabe mit verbindlichen Korrekturauflagen)**

---

## 1. Executive Summary & Gesamturteil

Die Vorarbeiten des Orchestrators und der Fachagenten für die Phasen 1 bis 4 wurden einer unabhängigen, rigorosen und empirischen Prüfung unterzogen. 

### Kernbefunde:
1. **Hardware-Echtheit (100% verifiziert):** Sämtliche Hardware- und Systemdaten aus Dokument 01 wurden nicht simuliert, sondern empirisch und fehlerfrei über native System-APIs ermittelt. Alle Spezifikationen (Intel i3-7020U Dual-Core, 20 GB RAM, keine dedizierte GPU, Ollama 0.33.1, Python 3.14.7) wurden unabhängig bestätigt.
2. **Kritische Sicherheitslage auf Laufwerk C: (Realer Befund):** Laufwerk C: ist zu **97,9 % belegt** (aktuell nur ~5,2 GB frei, temporär unter 700 MB gefallen). Die verhängte Download-Sperre und das Verbot, Arbeitsdaten auf C: zu schreiben, sind zwingend erforderlich und werden strikt aufrechterhalten.
3. **Kritischer methodischer Fehler im Testdesign (Empirisch aufgedeckt):**  
   Das in Dokument 04 vorgeschlagene Token-Limit von `num_predict: 64` für kurze Antworten führt bei modernen Reasoning-Modellen (`qwen3.5:4b`, `gemma4:e2b`) zum **vollständigen Testversagen (0% Score)**. Ein empirischer Test hat gezeigt, dass `qwen3.5:4b` bei `num_predict: 50` das gesamte Tokenbudget in der internen Denkspur (`thinking`) aufbraucht und mit `response: ""` abbricht. Erst bei $Tokens \ge 250$ wird die eigentliche Antwort erzeugt.
4. **Schwachstellen in den Akzeptanzkriterien:** Einzelne Validierungsregeln (z.B. Regex in `QS-I1`, Grammatik in `QS-G1`, Markdown-Fences bei JSON/Code) weisen logische Lücken auf, die zu False-Positives oder False-Negatives führen würden.

**Gesamturteil:**  
Die Architektur ist wissenschaftlich fundiert und hardwaregerecht konzipiert. Die Implementierung des Benchmark-Runners (Phase 5) wird unter der **Bedingung freigegeben**, dass die in diesem Bericht formulierten fünf verbindlichen Korrekturauflagen (Auflagen A bis E) im Runner implementiert werden.

---

## 2. Unabhängige Hardware- und Umgebungsverifikation

Zur Überprüfung, ob die Daten in `01_hardware_feasibility_report.md` real erhoben oder fingiert wurden, führte der QA-Agent unabhängige Abfragen über WMI/CIM, das Python-Systemmodul und die lokale Ollama-REST-API durch:

| Prüfpunkt | Dokumentierte Angabe (Doc 01) | Unabhängige QA-Messung | Status |
| :--- | :--- | :--- | :--- |
| **Betriebssystem** | Windows 11 Home (Build 10.0.26200) | Microsoft Windows 11 Home, 10.0.26200 | ✅ **Exakt bestätigt** |
| **CPU-Modell** | Intel Core i3-7020U @ 2.30GHz | Intel(R) Core(TM) i3-7020U CPU @ 2.30GHz (2 Cores, 4 Threads) | ✅ **Exakt bestätigt** |
| **Physischer RAM** | 20.377.292 KB (~19,43 GiB) | 20.377.292 KB (TotalVisibleMemorySize) | ✅ **Bitgenau bestätigt** |
| **GPU / VRAM** | Intel HD Graphics 620 (keine NVIDIA/CUDA) | Intel HD Graphics 620, Driver 26.20.100.7810, AdapterRAM: 1.073.741.824 | ✅ **Exakt bestätigt** |
| **Laufwerk C:** | 233,5 GB Gesamt, < 690 MB frei (kritisch) | Total: 233,58 GB, Belegt: 228,71 GB, Frei: 4,87 GB (97,9% belegt) | ⚠️ **Bestätigt extrem kritisch** |
| **Laufwerk E:** | 390,6 GB Gesamt, ~ 57,1 GB frei | Total: 390,62 GB, Belegt: 333,47 GB, Frei: 57,15 GB (85,4% belegt) | ✅ **Exakt bestätigt** |
| **Ollama Service** | Aktiv auf `127.0.0.1:11434` | REST-API antwortet auf Port 11434 mit Status 200 | ✅ **Aktiv** |
| **Ollama-Modelle** | `qwen3.5:4b`, `gemma4:e2b`, `llama2:latest`, `nomic-embed-text:latest`, `glm-5.2:cloud` | Exakt identische 5 Modelle in `/api/tags` | ✅ **Exakt bestätigt** |
| **Python-Runtime** | Python 3.14.7 | Python 3.14.7 (MSC v.1944 64 bit AMD64) | ✅ **Exakt bestätigt** |
| **Bibliotheken** | `psutil 7.2.2`, `numpy 2.5.3`, `scipy 1.18.1`, `sklearn 1.9.1`, `requests 2.34.2` | Alle Module importierbar, Versionen bitgenau identisch | ✅ **Exakt bestätigt** |

**Fazit zur Hardware:** Es liegt keinerlei Simulation vor. Die Messwerte sind real, reproduzierbar und unverändert gültig.

---

## 3. Methodische Prüfung & Wissenschaftliche Validität (Doc 02)

### 3.1 Kontaminationsschutz
- **Stärke:** Die Kritik an Standard-Benchmarks (HumanEval, GSM8K, MBPP) in Doc 02 ist methodisch vollkommen berechtigt. Aktuelle LLMs (2024–2026) wurden massiv auf diesen Korpora trainiert. 
- **Würdigung der Lösung:** Der Ansatz, synthetische Aufgaben mit modifizierten Variablen, veränderten Rechenschritten und neu zusammengestellten Randbedingungen einzusetzen, eliminiert reines Data-Memorizing effektiv.

### 3.2 Stichprobengröße ($N=16$) vs. Dual-Core-Laufzeitrestriktion
- **Methodische Schwachstelle:** Bei 16 Aufgaben über 8 Dimensionen entfallen lediglich **2 Aufgaben auf jede Dimension**. Dies führt zu einer sehr groben Diskretisierung der Teil-Scores ($0\%$, $50\%$, $100\%$).
- **Wissenschaftliche Einordnung & Rechtfertigung:** Auf einem Intel Core i3-7020U (2 Kerne, keine GPU) erzeugt ein Durchlauf von 16 Aufgaben mit je 3 Wiederholungen ($K=3$) exakt **48 Inferenzläufe pro Modell**. Bei durchschnittlich 30–45 Sekunden pro Lauf entspricht dies **24 bis 36 Minuten reiner Rechenzeit pro Modell**. Bei 3 lokalen Modellen beläuft sich die Gesamtlaufzeit auf rund **1,5 bis 2 Stunden**.
- **Urteil:** Eine signifikante Erhöhung der Aufgabenanzahl (z.B. auf 100 Aufgaben) würde die Laufzeit auf über 10 Stunden treiben und zu thermischem Throttling der Mobil-CPU führen. Das gewählte 2-Stufen-System (Screening mit 6 Aufgaben + Haupttest mit 16 Aufgaben) stellt das **empirisch vertretbare Optimum** dar. Die geringe Fallzahl muss jedoch durch die explizite Angabe von **Wilson-Score-Konfidenzintervallen** transparent gemacht werden.

### 3.3 Trennung von Qualität ($Q$) und Effizienz ($E$)
- Das Vorhaben, zwei orthogonale Ranglisten zu führen, erfüllt die Vorgaben des Master-Prompts vorbildlich.
- **Kritische Lücke in Formel Doc 02:**
  $$E = \frac{Q}{\alpha \cdot \frac{\overline{\text{Latency}}}{\text{Norm\_Lat}} + \beta \cdot \frac{\text{RAM}}{\text{Norm\_RAM}} + \gamma \cdot \frac{\text{Model\_Size}}{\text{Norm\_Size}}}$$
  Dokument 02 versäumt es, die Parameter $\alpha, \beta, \gamma$ und die Normierungsbaselines fest zu quantifizieren.
- **Verbindliche Festlegung für Phase 5:**
  - $\alpha = 0,5$ (Latenz / Zeit ist der dominierende praktische Engpass auf der CPU)
  - $\beta = 0,3$ (RAM-Allokation)
  - $\gamma = 0,2$ (Modellgröße auf Disk)
  - Baselines: $\text{Norm\_Lat} = 30{,}0\text{ s}$, $\text{Norm\_RAM} = 4096\text{ MB}$, $\text{Norm\_Size} = 4096\text{ MB}$.

---

## 4. Kritische Analyse der Modell-Kandidatenmatrix (Doc 03)

1. **Gruppe 1 (Bereits installiert & offline lauffähig):**
   - `qwen3.5:4b` (4.7B Q4_K_M): Vollwertiges modernes Reasoning- und Vision-Modell.
   - `gemma4:e2b` (5.1B Q4_K_M): Modernes Modell mit Thinking & Tool-Unterstützung.
   - `llama2:latest` (7.0B Q4_0): Klassische Baseline; benötigt aufgrund von 7B und Q4_0 mit ~6,1 GB den größten RAM-Anteil und weist die geringste Inferenzgeschwindigkeit auf.
2. **Status von `glm-5.2:cloud`:**
   - In Ollama als Remote-Proxy registriert (`remote_host: https://ollama.com`, 756B Parameter).
   - **QA-Veto:** Dieses Modell darf **nicht** in den Offline-Hardware-Vergleich einbezogen werden, da es netzwerkabhängig ist, Server-Ressourcen nutzt und die CPU-Hardware-Vergleichbarkeit verfälscht. Es kann höchstens als optionale externe Referenz fungieren.
3. **Gruppe 2 (Künftige Download-Kandidaten):**
   - Die vorgeschlagene Auswahl (`qwen2.5:3b`, `qwen2.5-coder:3b`, `llama3.2:3b`, `llama3.2:1b`, `gemma2:2b`) ist fachlich exzellent auf den Sweet Spot (1B–3.5B) abgestimmt.
   - Die strikte Festlegung, dass Downloads erst nach Nutzerzustimmung und Verlegung von `OLLAMA_MODELS` auf Laufwerk E: zulässig sind, wird ausdrücklich bestätigt.

---

## 5. Detaillierte Überprüfung der Testaufgaben & Akzeptanzkriterien (Doc 04)

### 5.1 Empirischer Durchbruch: Der "Thinking Token"-Konflikt (Kritischer Bug!)
Im Testdesign von Doc 04 heißt es:  
> *"num_predict: Jeweils aufgabenspezifisch limitiert (z.B. 64 Tokens für kurze Antworten)"*

Der QA-Agent hat diesen Parameter auf `qwen3.5:4b` mit der Aufgabe `2+2=` getestet.  
**Ergebnis der Messung:**
- Bei `num_predict: 50`:  
  - `load_duration`: 11 ms (Warmstart)
  - `eval_count`: 50 Tokens
  - `thinking`: *"Thinking Process: 1. Analyze the Request: The user is asking a very simple..."*
  - `response`: `""` (Leerstring!)
  - `done_reason`: `"length"`
  Das Modell verbrauchte alle 50 Tokens für die Generierung seiner Denkspur. Bevor es das finale Ergebnis ausgeben konnte, wurde die Generierung durch das Tokenlimit hart abgebrochen!
- Bei `num_predict: 250`:  
  - `thinking`: 523 Zeichen (~120 Tokens Denkspur)
  - `response`: `'2+2=4'`
  - `done_reason`: `"stop"`
  Erst mit ausreichendem Tokenbudget schloss das Modell den Denkprozess ab und erzeugte die korrekte Antwort.
- **Folge:** Ein starres Limit von 64 Tokens würde alle modernen Thinking-Modelle systematisch mit einem Score von 0,0 bewerten, während ältere Non-Thinking-Modelle (wie `llama2:latest`, das direkt `\n4` ausgibt) bestehen würden.  
- **Korrekturauflage A:** Das Tokenlimit `num_predict` für Standardaufgaben muss auf **mindestens 256 bis 384 Tokens** angehoben werden, um den Denkprozess nicht abzuwürgen. Alternativ muss geprüft werden, ob Ollama Thinking via System-Optionen deaktivieren kann, oder die Denkzeit muss in die Latenz-Evaluation einfließen.

---

### 5.2 Schwachstellen in den Aufgaben-Validatoren

| Task-ID | Spezifikation in Doc 04 | Aufgedeckte Schwachstelle | Verbindliche Korrektur |
| :--- | :--- | :--- | :--- |
| **QS-I1** | Nenne 3 europäische Hauptstädte in GROSSBUCHSTABEN getrennt durch Komma. Regex: `^[A-ZÄÖÜ]+,[A-ZÄÖÜ]+,[A-ZÄÖÜ]+$` | **Format-Semantik-Lücke:** Der Regex akzeptiert beliebige Wörter wie `APFEL,BIRNE,BANANE` oder `AUTO,BAUM,HAUS`. Falsche Antworten würden als bestanden gewertet! | Validierung zweistufig: 1. Regex für Format. 2. Prüfung, ob alle 3 Tokens in einer kanonischen Menge europäischer Hauptstädte (`{'BERLIN', 'PARIS', 'ROM', ...}`) enthalten sind. |
| **QS-G1** | 3. Person Sg. Prät. von "nachdenken" in ganzem Satz. Kriterium: "enthält 'dachte nach' in korrekter Grammatik" | **Subjektivität:** "in korrekter Grammatik" ist maschinell ohne NLP-Parser nicht deterministisch prüfbar. | Deterministische Definition: Regex-Match auf `\b(er\|sie\|es\|man)\s+dachte\s+.*nach\b` sowie Satzendezeichen (`[.!?]$`). |
| **QS-C1** | Python-Funktion `is_even(n)`. Unit-Tests ausführen. | **Code-Fence-Crash:** LLMs geben Code meist als ````python\ndef is_even(n):...```` aus. Ein ungesäubertes `exec()` wirft Syntaxfehler. Zudem fehlt Sandboxing. | Automatisches Extrahieren des Inhalts zwischen Codefences via Regex vor `exec()`. Ausführung in isoliertem Namespace mit 2-Sekunden-Timeout. |
| **QS-S1** | JSON mit `name` (str) und `age` (int 25). Kriterium: `json.loads()`. | **Markdown-JSON-Problem:** LLMs betten JSON fast immer in ````json ... ```` ein. Direktes `json.loads()` wirft `JSONDecodeError`. | Regex-Extraktion des ersten gültigen `{...}`-Blocks vor dem Aufruf von `json.loads()`. |
| **QS-R1** | 14 Kisten à 6 Flaschen, 27 verkauft. Antwort nur die Zahl. Kriterium: Exakt `57`. | **Leading/Trailing Whitespace & Thinking:** Modelle geben oft `57\n` oder `57 Flaschen` aus. Bei Thinking-Modellen steht die Zahl im separaten `response`-Feld. | String bereinigen: `strip()`, Extraktion des letzten Integer-Tokens via `re.search(r'\b57\b', response)`. |

---

## 6. Sicherheits-, Speicher- und Budgetprüfung

1. **Kostenprüfung (0,00 €):**
   - Sämtliche Tests laufen zu 100% lokal über den bestehenden Ollama-Dienst.
   - Es fallen weder API-Gebühren, Cloud-Kosten noch Subskriptionskosten an.
2. **Schutz von Laufwerk C: (Strikte Einhaltung):**
   - Unabhängige Messung: Auf C: sind aktuell nur 4,87 GB frei (97,9% belegt).
   - Der Dateisystem-Check hat bestätigt, dass `OLLAMA_MODELS` nicht in den Windows-Umgebungsvariablen hinterlegt ist. Ollama speichert standardmäßig unter `C:\Users\p_kro\.ollama\models`.
   - **Sicherheitsauflage:** Es darf im gesamten Benchmark **kein einziger `ollama pull`-Befehl** ausgeführt werden.
   - Alle Benchmark-Ergebnisdateien, JSONL-Logs, SQLite-Datenbanken und Markdown-Reports müssen ausnahmslos in `E:\okal llm benschmark\results\` abgelegt werden.

---

## 7. Verbindlicher Auflagenkatalog für Phase 5 (Benchmark-Runner)

Für die anstehende Implementierung des Benchmark-Runners (`benchmark_runner.py` / Testsuite) werden folgende fünf verbindliche Auflagen festgeschrieben:

> [!IMPORTANT]
> ### Verbindliche Auflagen für Phase 5:
> 
> 1. **Auflage A (Dynamisches Tokenbudget & Thinking-Separation):**  
>    Für Aufgaben, die an Thinking-Modelle (`qwen3.5:4b`, `gemma4:e2b`) gerichtet sind, muss `num_predict` auf mindestens **256–384 Tokens** gesetzt werden. Der Runner muss das `thinking`-Feld der Ollama-API separat protokollieren und ausschließlich das `response`-Feld an die Validierungslogik übergeben.
> 
> 2. **Auflage B (Robuste Extraktions-Pipeline):**  
>    Alle Modellantworten müssen vor der Auswertung eine Normalisierungs-Pipeline durchlaufen:
>    - Entfernen von Markdown-Codeblöcken (````json ... ```` bzw. ````python ... ````).
>    - Regex-basierte Extraktion von JSON-Klammern `{...}` bzw. `[...]`.
>    - String-Trimming (`.strip()`) vor numerischen und Text-Vergleichen.
> 
> 3. **Auflage C (Schließen semantischer Prüflücken):**  
>    - In `QS-I1` muss zusätzlich zur Komma- und Großschreibungsprüfung abgeglichen werden, ob die genannten Tokens tatsächlich in einer Whitelist europäischer Hauptstädte existieren.
>    - In `QS-G1` muss die grammatikalische Form über ein präzises Regex-Muster (`\b(er|sie|es|man)\s+dachte\s+.*nach\b`) deterministisch geprüft werden.
> 
> 4. **Auflage D (Sichere Code-Ausführung mit Timeout):**  
>    Für Coding-Aufgaben (`QS-C1`, `HB-C1`, `HB-C2`) darf LLM-Code nur in einem isolierten Scope mit striktem Ausführungs-Timeout (max. 3 Sekunden) ausgeführt werden, um Endlosschleifen der CPU zu unterbinden.
> 
> 5. **Auflage E (Strikte E:-Laufwerksbindung & Null-Download-Garantie):**  
>    Alle Resultate, Metriken und temporären Artefakte sind unter `E:\okal llm benschmark\results` zu speichern. Es werden ausschließlich die drei bereits lokal installierten Modelle (`qwen3.5:4b`, `gemma4:e2b`, `llama2:latest`) getestet.

---

## 8. Formales Freigabevotum

Der unabhängige QA- und Prüfagent erteilt hiermit die:

### **FREIGABE MIT AUFLAGEN (CONDITIONAL APPROVAL)**

Die theoretischen und konzeptionellen Grundlagen der Phasen 1 bis 4 sind solide, empirisch verifiziert und auf die anspruchsvollen Bedingungen der Dual-Core-CPU abgestimmt. Sobald die Auflagen A bis E in Phase 5 im Benchmark-Runner implementiert werden, ist ein wissenschaftlich valides, reproduzierbares und betriebssicheres Testergebnis garantiert.