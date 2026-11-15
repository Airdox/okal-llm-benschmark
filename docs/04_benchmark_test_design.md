# Spezifikation des Benchmark-Testsystems (Phase 4)
**Datum:** 2026-11-16  
**Version:** 1.0.0 (Versioniert & festgeschrieben)  
**Projekt:** Autonomes LLM-Benchmark- und Modellvergleichssystem  
**Status:** Festgelegt & Bereit zur Prüfung

---

## 1. Architektur des zweistufigen Testsystems

Um Rechenzeit und Energie auf der Dual-Core-CPU optimal zu schonen und gleichzeitig maximale wissenschaftliche Aussagekraft zu garantieren, ist das Testsystem in zwei fest definierte Stufen unterteilt:

```
┌────────────────────────────────────────────────────────┐
│               Modell-Kandidat (Lokal)                  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│     Stufe 1: Quick Screening Benchmark (Vorabtest)     │
│  - 6 Kern-Aufgaben                                     │
│  - Deterministisch (T=0.0)                             │
│  - Laufzeit: < 2 Minuten                               │
│  - Kriterium: Mind. 50% Erfolgsquote für Stufe 2       │
└──────────────────────────┬─────────────────────────────┘
                           │ Besteht Stufe 1
                           ▼
┌────────────────────────────────────────────────────────┐
│         Stufe 2: Vollständiger Haupt-Benchmark          │
│  - 16 kuratierte, kontaminationsfreie Aufgaben         │
│  - 8 Dimensionen (je 2 Aufgaben)                       │
│  - 3 Durchläufe (1x T=0.0, 2x T=0.2)                   │
│  - Ressourcen-Logging (RAM, TTFT, TPS, CPU, Thermals)   │
│  - Automatische Soll-Ist-Prüfung                       │
└────────────────────────────────────────────────────────┘
```

---

## 2. Kontaminationsschutz & Deterministische Parameter

1. **Synthetische Parametrisierung:** Alle numerischen Aufgaben, Programmier-Prompts und Entitäts-Namen sind gezielt variiert, sodass auswendig gelernte Standardantworten aus dem Pretraining (z.B. HumanEval #0 oder Standard-GSM8K) fehlschlagen.
2. **Feste Sampling-Parameter:**
   - `temperature`: 0.0 (Basislauf) / 0.2 (Stabilitätsläufe)
   - `top_p`: 0.95
   - `top_k`: 40
   - `repeat_penalty`: 1.1
   - `num_predict`: Jeweils aufgabenspezifisch limitiert (z.B. 64 Tokens für kurze Antworten, 256 Tokens für Code/JSON), um unkontrollierte Endlosgenerierungen zu verhindern.
3. **Template-Konsistenz:** Verwendung des nativen Ollama Chat-API-Formats (`/api/chat` bzw. `/api/generate`), um das jeweilige Modelfile-Chat-Template (ChatML, Llama-3-Header, etc.) nativ und unverfälscht anzusprechen.

---

## 3. Aufgabenkatalog: Stufe 1 (Quick Screening)

| Task-ID | Dimension | Prompt (Auszug) | Maschinelles Akzeptanzkriterium |
| :--- | :--- | :--- | :--- |
| **QS-R1** | Reasoning | Ein Händler kauft 14 Kisten mit je 6 Flaschen Saft. Er verkauft 27 Flaschen. Wie viele Flaschen hat er noch? Antworte nur mit der Zahl. | Exakter numerischer Match: `57` |
| **QS-C1** | Coding | Schreibe eine Python-Funktion `is_even(n)`, die True zurückgibt, wenn n gerade ist, sonst False. Gib nur den Codeblock zurück. | Unit-Test: `is_even(4)==True`, `is_even(7)==False`, `is_even(0)==True` |
| **QS-I1** | Instruction | Nenne drei europäische Hauptstädte. Bedingung: Schreibe jedes Wort in GROSSBUCHSTABEN und trenne sie nur durch Kommas, ohne Leerzeichen. | Regex-Prüfung: `^[A-ZÄÖÜ]+,[A-ZÄÖÜ]+,[A-ZÄÖÜ]+$` |
| **QS-S1** | Structured | Gib ein JSON-Objekt mit den Schlüsseln "name" (String) und "age" (Integer 25) aus. Keine weiteren Erklärungen. | Validierung: `json.loads()`, `d["name"]` ist str, `d["age"] == 25` |
| **QS-G1** | Deutsch | Bilde die 3. Person Singular Präteritum von "nachdenken" und setze sie in einen vollständigen deutschen Satz. | Satz enthält "dachte nach" in korrekter Grammatik |
| **QS-A1** | Agentic Tool | Rufe das Tool `get_weather` mit dem Parameter `{"city": "Berlin"}` im JSON-Format `{"tool": "...", "args": {...}}` auf. | `json.loads()`, `tool == "get_weather"`, `args["city"] == "Berlin"` |

---

## 4. Aufgabenkatalog: Stufe 2 (Haupt-Benchmark: 16 Aufgaben)

### D1: Logisches & Mathematisches Denken (Reasoning)
- **HB-R1:** Dreistufige Rechenaufgabe mit prozentualem Rabatt und Restwert. Eindeutiger Integer-Wert.
- **HB-R2:** Logik-Rätsel: Reihenfolge von vier Personen (A ist vor B, C ist hinter D, etc.). Eindeutige Reihenfolge.

### D2: Programmierung (Coding)
- **HB-C1:** Algorithmus: String-Kompression (Run-Length-Encoding). Automatisierte Unit-Tests mit Standard- und Randfällen (leerer String, Einzelzeichen).
- **HB-C2:** Bugfixing: Gegebener Python-Code enthält einen Off-by-one-Fehler und fehlende Typenkonvertierung. Automatische Testsuite muss nach Korrektur `pass` melden.

### D3: Textverständnis & Extraktion (Comprehension)
- **HB-T1:** Extraktion von Datum, Projektbudget und Projektleiter aus einem unübersichtlichen E-Mail-Absatz mit Distraktoren.
- **HB-T2:** Frage zu einem Text, die durch zwei voneinander getrennte Sätze beantwortet werden muss (Synthese).

### D4: Anweisungsbefolgung (Instruction Following - IFEval-Stil)
- **HB-I1:** Negatives Constraint: Erkläre kurz das Phänomen Photosynthese in genau zwei Sätzen, ohne das Wort "Pflanze" oder "Pflanzen" zu verwenden.
- **HB-I2:** Format-Constraint: Erstelle eine nummerierte Liste mit genau 4 Punkten. Jeder Punkt muss mit dem Wort "Schritt" beginnen und darf maximal 8 Wörter lang sein.

### D5: Strukturierte Ausgaben (Structured Output)
- **HB-S1:** Strenges JSON-Schema mit verschachtelten Daten (Server-Konfiguration: Host, Port als int, Flags als bool, Tags als Liste von Strings).
- **HB-S2:** Parsing einer tabellarischen Textpassage in eine JSON-Liste von Objekten mit Typprüfung.

### D6: Faktische Zuverlässigkeit & Unsicherheitskalibrierung
- **HB-F1:** Falle: "In welchem Jahr gewann Albert Einstein die Goldmedaille im 100-Meter-Lauf bei den Olympischen Spielen?" Akzeptanz: Erkennen der falschen Prämisse / Zurückweisung.
- **HB-F2:** Grenzen des Wissens: Frage nach fiktiven Ereignissen aus der Zukunft. Akzeptanz: Deklaration als unbekannt/spekulativ statt freier Erfindung.

### D7: Deutschsprachige Leistung
- **HB-G1:** Korrektur eines komplexen deutschen Satzes mit Konjunktiv II und Passivkonstruktion.
- **HB-G2:** Präzise Übersetzung eines englischen technischen Fachtexts ins Deutsche unter Vermeidung von Anglizismen und falschem Satzbau.

### D8: Agentische Eignung (Planning & Tool Calling)
- **HB-A1:** Zerlege das Ziel "Erstelle ein tägliches Datenbank-Backup und versende einen Statusbericht" in genau 4 geordnete Arbeitsschritte im JSON-Array-Format.
- **HB-A2:** Multi-Parameter Tool-Call: Auswählen des richtigen Tools aus 3 bereitgestellten Tool-Definitionen (`send_email`, `query_database`, `create_ticket`) mit korrekten Argumenten.

---

## 5. Vollständige Metrikerfassung pro Task-Ausführung

Für jeden einzelnen Aufruf protokolliert der Benchmark-Runner im JSONL-Format:
- `task_id`, `model_name`, `iteration`, `temperature`
- `success` (Boolean: 0 oder 1)
- `score` (Float: 0.0 bis 1.0)
- `error_message` (bei Exceptions oder Schema-Verletzung)
- `raw_output` (vollständiger Modelltext)
- `thinking_output` (separat extrahierte Chain of Thought, falls vorhanden)
- `ttft_ms` (Time to First Token)
- `eval_duration_ms` (Reine Generierungszeit)
- `prompt_eval_count` (Input-Tokens)
- `eval_count` (Output-Tokens)
- `tokens_per_second` (TPS)
- `ram_usage_mb` (Host-RAM vor/nach Inferenz via `psutil`)
- `cpu_percent` (CPU-Auslastung während des Laufs)
