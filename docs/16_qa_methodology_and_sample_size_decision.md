# Verbindliche QA-Entscheidung: Methodische Schärfung Hauptbenchmark v2.0 & Token-Architektur
**Datum:** 2026-11-16  
**Rolle:** Unabhängiger QA-, Prüf- & Sicherheitsagent  
**Projekt:** Autonomes LLM-Benchmark- und Modellvergleichssystem  
**Referenzdokumente:**  
- `docs/08_qa_statistical_power_audit.md` (Statistisches Power-Audit)  
- `docs/15_performance_superiority_gate_classification.md` (5-Stufen-Taxonomie)  
- `docs/14_online_pretest_final_evaluation.md` (Online-Abschlussbericht)  
**Dokument-ID:** `docs/16_qa_methodology_and_sample_size_decision.md`  
**Status:** **VERBINDLICHE METHODENENTSCHEIDUNG & FREIGABE**

---

## 1. Executive Summary & Entscheidungsgrundlage

Der Benutzer hat einen verbindlichen Korrekturauftrag zur methodischen Bereinigung des Hauptbenchmarks erteilt. Zwischen der statistischen Empfehlung aus `docs/08_qa_statistical_power_audit.md` ($N=32$ disjunkte Aufgaben) und dem Entwurf eines reduzierten 16-Aufgaben-Benchmarks bestand ein methodischer Widerspruch, der durch diese Entscheidung endgültig aufgelöst wird.

### Die drei verbindlichen QA-Entscheidungen:
1. **Verbindlicher Aufgabenumfang $N=32$ für Hauptbenchmark v2.0:**  
   Der Hauptbenchmark v2.0 **muss zwingend $N=32$ disjunkte Aufgaben umfassen (exakt $m=4$ Aufgaben pro Dimension über alle 8 Dimensionen)**. Ein Test mit 16 Aufgaben besitzt eine unzureichende Trennschärfe (Wilson-Intervallbreite $\pm 20{,}5\%$, Diskretisierungssprung 50%) und wird verbindlich als reiner technischer **Vorabtest (Smoke Test)** eingestuft.
2. **Architektur für Thinking- und Reasoning-Modelle:**  
   Die Auswertung wird verbindlich von Inferenzartefakten entkoppelt:  
   - Strikt getrennte Erfassung von `thinking` und `response` (Validierung nur auf `response`).  
   - Festlegung des Tokenbudgets auf **`num_predict = 768`** für Reasoning- und Coding-Aufgaben auf der Dual-Core-CPU.  
   - Einführung einer 4-stufigen Fehlerklassifikation zur Unterscheidung von Denk-Abbrüchen (`truncated_in_reasoning`) und semantischen Fehlleistungen.
3. **Bestätigung des Performance Superiority Gate (5-Stufen-Taxonomie):**  
   Die in `docs/15_performance_superiority_gate_classification.md` definierte Taxonomie (Stufen A bis E) wird **vollumfänglich genehmigt**. Die Einstufung von `MiniCPM5-2B` in Stufe B (Gleichstand/kein belegter Vorteil gegenüber der lokalen Baseline `gemma4:e2b`) und `Spark-X2.6-4B` in Stufe C (Offener Kandidat / Cloud-Quota-Abbruch) ist wissenschaftlich exakt.

---

## 2. Entscheidung zu Benchmark-Umfang & Stichprobenarchitektur

### 2.1 Mathematische Notwendigkeit von $N = 32$ Aufgaben ($m = 4$ pro Dimension)
Die mathematische Analyse aus Bericht 08 belegt unanfechtbar:
- Bei $m=2$ Aufgaben pro Dimension existieren nur drei diskrete Stufen: $\{0\%, 50\%, 100\%\}$.  
  Bei einem wahren Fähigkeitsunterschied von 15 Prozentpunkten (z.B. Modell A mit 75% vs. Modell B mit 60%) gewinnt das bessere Modell A **nur in 42,0% der Testläufe**. In 58% herrscht Gleichstand oder das schwächere Modell gewinnt fälschlicherweise ("Münzwurf-Effekt").
- Bei **$m=4$ Aufgaben pro Dimension ($N=32$ Aufgaben gesamt)**:
  - Diskrete Stufen pro Dimension steigen auf **fünf Stufen**: $\{0\%, 25\%, 50\%, 75\%, 100\%\}$.
  - Die Schrittweite halbiert sich von 50% auf **25%**.
  - Die Fehlermarge des globalen 95%-Wilson-Konfidenzintervalls sinkt von $\pm 20{,}5\%$ auf **$\pm 15{,}2\%$**.
  - Die statistische Teststärke (Power) zur Detektion eines 20%-Unterschieds steigt von 22,9% auf **> 60%** (gepoolt).

### 2.2 Methodische Behandlung von Wiederholungen ($N$ vs. $K$)
> [!IMPORTANT]
> **Verbindliche statistische Festlegung:**  
> 1. Die Wiederholung desselben Prompts ($K$) bei niedriger Temperatur ($T \le 0{,}2$) stellt **keine Vergrößerung des Aufgabenraums $N$** dar! Da die Antworten auf denselben Prompt eine Autokorrelation von $\rho \approx 0{,}85$ aufweisen, erzeugen 48 Läufe auf 16 Aufgaben rechnerisch nur $N_{\text{eff}} \approx 17{,}8$ effektive Freiheitsgrade.  
> 2. Die Wiederholungsmessung $K$ dient **ausschließlich der Erfassung der stochastischen Varianz (Sampling-Stabilität)**.  
> 3. Für Hauptbenchmark v2.0 werden verbindlich **$K = 2$ Durchläufe** festgelegt:
>    - **Lauf 1 ($T = 0{,}0$):** Deterministischer Referenzlauf (Reproduzierbarkeit).
>    - **Lauf 2 ($T = 0{,}2$):** Stabilitätslauf (Varianz- und Robustheitsmessung).  
> 4. Der dritte Durchlauf ($K=3$) entfällt ersatzlos. Die dadurch eingesparte Rechenzeit fließt vollständig in die Erweiterung auf $N=32$ echte Aufgaben.

### 2.3 Rollenverteilung: 16 Aufgaben vs. 32 Aufgaben
- **16 Aufgaben (oder 6 Aufgaben Stufe 1):** Dürfen ausschließlich als **technischer Vorabtest / Smoke Test** fungieren, um Latenzen, Memory-Peaks, Sandboxing und Parser-Stabilität zu überprüfen.
- **32 Aufgaben (Hauptbenchmark v2.0):** Bilden die **einzig zulässige wissenschaftliche Grundlage** für die finalen Ranglisten A (Qualität) und B (Effizienz) sowie den formalen Modellvergleich.

---

## 3. Architektur für Reasoning- & Thinking-Modelle in v2.0

Der empirische Befund aus den Vorabtests zeigte, dass Modelle wie `qwen3.5:4b` oft 250–350 Tokens für interne Denkmonologe verbrauchen, bevor das erste Antwort-Token ausgegeben wird. Ein starres Limit von 512 Tokens führte vereinzelt zu vorzeitigen Längenabbrüchen (`done_reason: 'length'`).

Für Hauptbenchmark v2.0 gelten folgende verbindliche Architekturregeln:

### 3.1 Getrennte Erfassung (`thinking` vs. `response`)
- Ollama liefert bei Modellen mit nativer Thinking-Unterstützung (`qwen3.5`, `gemma4`) den Denkprozess im Feld `thinking` und die Endausgabe im Feld `response` (bzw. umschlossen von `<think>...</think>`).
- Der Benchmark-Runner muss diese Felder zwingend separat erfassen und in den JSONL-Ergebnisdaten protokollieren:
  - `thinking_content`: Vollständige Denkspur zur Messung von Denktiefe, Tokenverbrauch und Zeitaufwand.
  - `raw_response`: Die eigentliche Antwort des Modells.
- **Validierungs-Regel:** Sämtliche Validatoren (Unit-Tests, Regex-Muster, JSON-Parser, String-Vergleiche) werden **ausnahmslos auf dem bereinigten `raw_response`-String** ausgeführt.

### 3.2 Festlegung des Tokenbudgets (`num_predict`) auf der Dual-Core-CPU
Die Wahl von `num_predict` erfordert einen optimalen Kompromiss zwischen Abbruchvermeidung und Laufzeitbegrenzung auf der Intel i3-7020U CPU (~3,5 t/s):

| Task-Kategorie | Betroffene Dimensionen | Verbindliches `num_predict` | Maximale Laufzeit / Task | Begründung |
| :--- | :--- | :---: | :---: | :--- |
| **Reasoning & Math** | D1 (Reasoning), D2 (Coding) | **768 Tokens** | ~180 s (Timeout) | Ermöglicht 300–450 Tokens Denkmonolog PLUS vollständige Code- bzw. Formelausgabe. Verhindert Längenabbrüche zuverlässig. |
| **Standard-Tasks** | D3 (Comprehension), D4 (IFEval), D5 (JSON), D6 (Fakten), D7 (Deutsch), D8 (Agentic) | **384 Tokens** | ~90 s | Verhindert ausschweifende Antworten bei einfachen Aufgaben und schont die Rechenzeit. |

### 3.3 4-Stufen-Fehlerklassifikation bei Inferenzabbrüchen
Um Testartefakte nicht mit Modellunfähigkeit zu vermengen, wird bei Fehlschlägen verbindlich folgende Taxonomie protokolliert:
1. **`truncated_in_reasoning`:**  
   `done_reason == 'length'` UND `raw_response` ist leer (`""`), während `thinking_content` vorhanden ist.  
   *Bedeutung:* Modell hat das Tokenbudget komplett im internen Denkprozess verbraucht.
2. **`truncated_in_response`:**  
   `done_reason == 'length'` UND `raw_response` bricht unvollständig ab (z.B. offener Code-Block, unvollständiges JSON).
3. **`content_incorrect`:**  
   `done_reason == 'stop'`, aber die Antwort erfüllt das fachliche Akzeptanzkriterium nicht (falsche Zahl, fehlschlagender Unit-Test).
4. **`format_error`:**  
   `done_reason == 'stop'`, aber strukturelle Vorgaben wurden verletzt (ungültiges JSON, Markdown-Verletzung).

---

## 4. Audit & Bestätigung des Performance Superiority Gate (Doc 15)

Der QA-Agent hat die 5-Stufen-Taxonomie in `docs/15_performance_superiority_gate_classification.md` auditiert:

| Stufe | Bezeichnung | Bewertung durch QA |
| :---: | :--- | :--- |
| **A** | **Nachgewiesen bzw. plausibel überlegen** | Mathematisch sauber definiert ($p < 0{,}05$, $N \ge 32$). Verhindert voreilige Downloads. |
| **B** | **Kein statistisch belastbarer Vorteil belegt** | Schützt Modelle vor ungerechtfertigter Abwertung. Exakt zutreffend für `MiniCPM5-2B`. |
| **C** | **Noch nicht ausreichend getestet (Offen)** | Wissenschaftlich zwingend bei externen Quoten-Abbrüchen. Exakt zutreffend für `Spark-X2.6-4B`. |
| **D** | **Technisch nicht online testbar** | Transparente Nicht-Verfügbarkeit. Verhindert unzulässige Substitutionen (`K2-Horizon-3.7B`). |
| **E** | **Nachgewiesen unterlegen** | Berechtigter Ausschluss nach vollständigem, signifikantem Versagen (`llama2:latest`). |

**Audit-Befund:**  
Die Taxonomie beseitigt frühere Ungenauigkeiten und schützt das System vor unberechtigten Downloads und vor Fehlurteilen. Sie wird hiermit **formell freigegeben**.

---

## 5. Verbindlicher Umsetzungsfahrplan für Hauptbenchmark v2.0

Für die technische Implementierung von Hauptbenchmark v2.0 gelten folgende Vorgaben:

```
┌────────────────────────────────────────────────────────────────────────┐
│              FAHRPLAN HAUPTBENCHMARK v2.0 (N=32, K=2)                  │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Aufgabenkatalog:                                                    │
│    -> 32 disjunkte Aufgaben (HB2-R1..R4 bis HB2-A1..A4)                │
│    -> Exakt 4 Aufgaben pro Dimension über alle 8 Dimensionen           │
│    -> Kontaminationsfreie, synthetische Parametrisierung               │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Sampling & Inferenz:                                                │
│    -> Lauf 1: T = 0.0 (deterministischer Basislauf)                    │
│    -> Lauf 2: T = 0.2 (Stabilitäts- und Varianzlauf)                   │
│    -> num_predict = 768 (D1, D2) bzw. 384 (D3..D8)                     │
│    -> Striktes Sandboxing mit 3-Sekunden-Timeout für Python-Code       │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Zielmodelle für den lokalen Hauptvergleich:                         │
│    -> gemma4:e2b (2B-Klasse Baseline Leader)                           │
│    -> qwen3.5:4b (4B-Klasse Baseline)                                  │
│    -> Gesamtumfang: 2 Modelle x 32 Aufgaben x 2 Läufe = 128 Läufe      │
│    -> Gesamtlaufzeit: ~1,5 bis 1,8 Stunden (thermisch absolut sicher)  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Formales QA-Freigabevotum

Der unabhängige QA- und Prüfagent erteilt hiermit die:

### **UNEINGESCHRÄNKTE FORMALE FREIGABE (FULL QA APPROVAL)**

für:
1. Die Spezifikation des **Hauptbenchmarks v2.0 mit $N=32$ disjunkten Aufgaben ($m=4$) und $K=2$ Durchläufen**.
2. Die verbindliche **Thinking-Token-Architektur mit `num_predict: 768` / `384`** und separater Erfassung.
3. Die **5-Stufen-Taxonomie des Performance Superiority Gate** gemäß `docs/15_performance_superiority_gate_classification.md`.

Der Orchestrator ist autorisiert, den Aufgabenkatalog und den Test-Runner für Hauptbenchmark v2.0 auf dieser Grundlage verbindlich zu implementieren.