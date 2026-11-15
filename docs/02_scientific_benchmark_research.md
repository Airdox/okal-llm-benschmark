# Wissenschaftliche Benchmark-Recherche & Methodik (Phase 2)
**Datum:** 2026-11-16  
**Projekt:** Autonomes LLM-Benchmark- und Modellvergleichssystem  
**Autor:** Wissenschaftlicher Recherche- & Analyse-Agent  
**Status:** Begründet, verifiziert & versioniert (v1.0.0)

---

## 1. Einleitung & Zielsetzung

Die Evaluation von Large Language Models (LLMs) – insbesondere kleinerer Modelle ($\le 7\text{B}$ Parameter) auf ressourcenbeschränkter Hardware (Intel Core i3-7020U, 2 CPU-Kerne, rein CPU-basierte Inferenz via AVX2) – erfordert eine wissenschaftlich fundierte, verzerrungsfreie und reproduzierbare Methodik. 

Rein subjektive Bewertungen ("Vibe Checks") oder ungeprüfte Übernahmen akademischer Standard-Benchmarks sind ungeeignet, da:
1. **Trainingsdaten-Kontamination:** Gängige Benchmarks (wie HumanEval, GSM8K, MBPP) sind fester Bestandteil aktueller Pretraining- und Instruction-Tuning-Korpora. Kleine Modelle schneiden hier oft durch Memorieren unverhältnismäßig gut ab, scheitern jedoch an minimal veränderten Aufgaben.
2. **Inferenzzeit & Energiebedarf:** Bei Inferenzraten von 3–10 Tokens/Sekunde auf der Dual-Core-CPU führen Benchmarks mit tausenden Aufgaben oder ausschweifenden Antworten zu unzumutbaren Laufzeiten (Tage bis Wochen).
3. **Deterministische Messbarkeit:** Die Validierung muss maschinell und deterministisch erfolgen (Unit-Tests, JSON-Schema-Validierung, Regex-Parsen, logische Constraint-Checks).

---

## 2. Analyse etablierter Benchmark-Verfahren

| Benchmark | Ziel-Dimension | Stärken | Bekannte Schwächen & Risiken | Eignung für lokales System |
| :--- | :--- | :--- | :--- | :--- |
| **IFEval** (Google Research) | Instruction Following & Formattreue | Maschinell verifizierbare Regeln (Wortzahl, JSON-Format, Sprache, Satzanzahl, Verbote). 0% Interpretationsspielraum. | Misst primär Regeleinhaltung, weniger tiefes semantisches Reasoning. | **Sehr hoch (Kern-Säule)** |
| **HumanEval / MBPP** | Codegenerierung (Python) | Deterministische Unit-Tests (`assert`). Hohe Reproduzierbarkeit. | Massive Kontamination in praktisch allen 2024–2026 Modellen; misst oft nur Memorierung. | **Modifiziert übernehmen** (Synthetische, unveröffentlichte Unit-Test-Aufgaben) |
| **LiveCodeBench** | Codegenerierung & Problem Solving | Kontaminationsgeschützt durch kontinuierlich neue LeetCode/Codeforces-Aufgaben. | Sehr hohe Aufgabenschwierigkeit; kleine 1B–4B Modelle erzielen fast 0% Pass-Rate, was keine Differenzierung erlaubt. | **Nur für Teilaspekte geeignet** |
| **GSM8K / MATH** | Mathematisches & mehrstufiges Denken | Klare numerische Zielwerte, prüft Schritt-für-Schritt-Reasoning. | Starke Kontamination; Modelle memorieren bekannte Rechenwege. | **Konzept adaptieren** (Paraphrasierte Aufgaben mit veränderten Zahlen) |
| **MMLU / MMLU-Pro** | Wissensbreite & Multiple Choice | Leicht auswertbar (A/B/C/D). | Multiple-Choice korreliert schlecht mit agentischer Praxis (Generierung, Tool Use); stark kontaminiert. | **Geringe Priorität** |
| **BFCL / ToolBench** | Tool Use / Funktionsaufrufe | Bewertet exakte Schema-Treue bei Funktionsaufrufen. | Komplexe Server-Mockups erforderlich. | **Sehr hoch (Agentik-Säule)** (Prüfung auf standardisiertes JSON-Tool-Calling) |

---

## 3. Die 8 verbindlichen Test-Dimensionen

Das Benchmark-Design deckt die 8 im Master-Prompt geforderten Dimensionen über maschinell prüfbare Kriterien ab:

1. **Logisches & Mathematisches Denken (Reasoning):**
   - Mehrstufige Deduktion, veränderte Rechenaufgaben mit eindeutigem numerischem Endwert.
   - *Prüfmethode:* Regex-Extraktion des finalen Werts / exakter Match.
2. **Programmierung (Coding):**
   - Implementierung modularer Python-Funktionen mit Randwertbehandlung.
   - *Prüfmethode:* Ausführung isolierter Unit-Tests mit Timeout (Sandboxing).
3. **Textverständnis & Information Retrieval (Comprehension):**
   - Extraktion spezifischer Fakten aus einem vorgegebenen Kontext (Needle-in-a-Haystack / Key-Fact-Extraction).
   - *Prüfmethode:* String-Inclusion und Abwesenheit von Halluzinationen.
4. **Anweisungsbefolgung (Instruction Following - IFEval-Stil):**
   - Einhaltung negativer Constraints ("Verwende kein 'und'"), Längengrenzen ("Antworte in genau 3 Sätzen"), Strukturvorgaben.
   - *Prüfmethode:* Automatische Validatoren (Länge, Satzzeichen, Wortverbote).
5. **Strukturierte Ausgaben (Structured Output):**
   - Erzeugung syntaktisch validen JSONs, Einhaltung eines geforderten JSON-Schemas mit Datentypen (int, list, enum).
   - *Prüfmethode:* `json.loads()` gefolgt von `jsonschema.validate()`.
6. **Faktische Zuverlässigkeit & Unsicherheitskalibrierung:**
   - Erkennen unlösbarer Fragen ("Wie hieß der Bundeskanzler von Frankreich im Jahr 1820?"), Weigerung zu halluzinieren.
   - *Prüfmethode:* Prüfung auf Zurückweisung ("Diese Information existiert nicht" / "Unbeantwortbar").
7. **Deutschsprachige Leistung:**
   - Grammatikalische Korrektheit, Beibehaltung der deutschen Sprache ohne unzulässiges Umschalten ins Englische ("Language Drift"), Nuancenverständnis.
   - *Prüfmethode:* Spracherkennung (`langdetect` oder Heuristik), morphologische Treffsicherheit.
8. **Agentische Eignung (Planning & Tool Calling):**
   - Zerlegung eines komplexen Ziels in sequenzielle Teilschritte, Ausgabe strukturierter Tool-Calls im JSON-Format (`{"action": "...", "parameters": {...}}`).
   - *Prüfmethode:* Parsing des Tool-Calls, Prüfung der Aktionsauswahl und Parameterkonsistenz.

---

## 4. Statistische Methodik & Versuchsplanung

### 4.1 Stichprobengröße & Laufzeitoptimierung
Auf einem Intel Core i3-7020U erzeugt eine Modellantwort mit 150 Tokens ca. 20–45 Sekunden Rechenzeit.
- **Stufe 1 (Quick Screening):** 6 hocheffiziente Aufgaben (je 1 pro Kernkompetenz), 1 Durchlauf. Ziel: Ausschluss ungeeigneter Modelle in $< 3$ Minuten.
- **Stufe 2 (Haupt-Benchmark):** 16 kuratierte, kontaminationsfreie Aufgaben über alle 8 Dimensionen (2 Aufgaben pro Dimension).
- **Wiederholungen:** Jede Aufgabe wird $K = 3$ Mal ausgeführt.
  - Lauf 1: $T = 0.0$ (Deterministischer Basislauf für Reproduzierbarkeit).
  - Lauf 2 & 3: $T = 0.2$ (Zur Messung stochastischer Stabilität und Varianz).

### 4.2 Statistische Kennzahlen & Unsicherheitsquantifizierung
1. **Erfolgsquote (Pass Rate / Accuracy):**
   $$p = \frac{\sum_{i=1}^N \text{score}_i}{N}$$
2. **Konfidenzintervall (Wilson-Score-Intervall für Binomialdaten):**
   Da der Stichprobenumfang $N$ bei lokalen CPU-Benchmarks realistisch begrenzt ist, liefert das klassische Wald-Intervall ($p \pm z\sqrt{p(1-p)/N}$) irreführende Werte nahe 0 oder 1. Wir verwenden das **Wilson-Score-Intervall**:
   $$w = \frac{p + \frac{z^2}{2N} \pm z \sqrt{\frac{p(1-p)}{N} + \frac{z^2}{4N^2}}}{1 + \frac{z^2}{N}}$$
   (bei 95% Konfidenz: $z = 1.96$).
3. **Leistungs- und Durchsatzmetriken:**
   - *Time-to-First-Token (TTFT):* Prefill-Latenz.
   - *Tokens per Second (TPS):* Generierungsdurchsatz $\text{TPS} = \frac{\text{eval\_count}}{\text{eval\_duration (s)}}$.
   - *Variationskoeffizient (CV):* $CV = \frac{\sigma}{\mu}$ für Latenz und Durchsatz zur Erfassung thermischen Throttlings auf dem Notebook.
4. **Separation von Cold- und Warmstart:**
   Der erste Aufruf misst die Modell-Ladezeit von Festplatte in den RAM (`load_duration`). Nachfolgende Aufrufe messen die reine Inferenzleistung (`eval_duration`, `prompt_eval_duration`).

---

## 5. Trennung der Ranglisten (Master-Prompt Vorgabe)

Zur Vermeidung willkürlicher Gesamtpunktzahlen werden zwei orthogonal ausgerichtete Ranglisten erstellt:

### Rangliste A: Reine Ergebnisqualität (Quality Score $Q$)
$$Q = \sum_{d=1}^8 w_d \cdot S_d$$
wobei $S_d \in [0, 1]$ der normierte Score der Dimension $d$ ist. Gleiche Gewichtung ($w_d = 0.125$) als Basis, ergänzt um Dimensions-Teilrankings (Coding, Reasoning, Deutsch).

### Rangliste B: Gesamteffizienz (Efficiency Index $E$)
$$E = \frac{Q}{\text{Resource Footprint}}$$
$$\text{Resource Footprint} = \alpha \cdot \frac{\overline{\text{Latency}}}{\text{Norm\_Lat}} + \beta \cdot \frac{\text{RAM}}{\text{Norm\_RAM}} + \gamma \cdot \frac{\text{Model\_Size}}{\text{Norm\_Size}}$$
Modelle, die eine hohe Qualität bei minimalem RAM-Bedarf und hohem Durchsatz (t/s) erzielen, führen diese Rangliste an.
