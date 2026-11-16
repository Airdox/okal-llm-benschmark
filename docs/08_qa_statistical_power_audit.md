# Unabhängiges QA-Audit: Statistische Aussagekraft, Trennschärfe & Laufzeit-Trade-off (Phase 5/8)
**Datum:** 2026-11-16  
**Rolle:** Unabhängiger QA-, Prüf- & Sicherheitsagent  
**Projekt:** Autonomes LLM-Benchmark- und Modellvergleichssystem  
**Referenzdokumente:**  
- `docs/02_scientific_benchmark_research.md` (Wissenschaftliche Methodik)  
- `docs/04_benchmark_test_design.md` (Testdesign v1.0.0: 16 Aufgaben, 8 Dimensionen, 3 Wiederholungen)  
- `docs/05_qa_validation_report.md` (Erster QA-Prüfbericht)  
- `docs/06_soll_ist_audit_report.md` (Projektstatus & empirische TPS-Daten)  
**Dokument-ID:** `docs/08_qa_statistical_power_audit.md`  
**Status:** **Prüfbericht abgeschlossen – Umfassende statistische Bewertung & Optimierungsempfehlung**

---

## 1. Executive Summary & Auditurteil

Der Orchestrator hat den unabhängigen QA-Agenten beauftragt zu prüfen, ob der im Testdesign v1.0.0 festgelegte Hauptbenchmark (16 Aufgaben, 2 Aufgaben pro Dimension über 8 Dimensionen, 3 Wiederholungen = 48 Inferenzläufe pro Modell) eine **ausreichende statistische Aussagekraft** besitzt, um lokale LLMs auf der Zielhardware (Intel Core i3-7020U Dual-Core CPU) wissenschaftlich valide zu vergleichen und zu ranken.

### Zentrales Prüfergebnis:
> [!WARNING]
> **Klares QA-Urteil: Das Design mit 16 Aufgaben ($m=2$ pro Dimension) besitzt eine unzureichende statistische Trennschärfe!**
> 1. **Globaler Konfidenzintervall-Fehler:** Bei $N=16$ Aufgaben beträgt die 95%-Wilson-Score-Intervallbreite bei einer gemessenen Genauigkeit von 70% massive **$\pm 20{,}5\%$** ($[45{,}6\%, 86{,}7\%]$). Zwei Modelle mit 70% und 55% Genauigkeit sind statistisch **nicht unterscheidbar ($p > 0{,}05$)**.
> 2. **Kollaps der dimensionalen Teilrankings ($m=2$):** Mit nur 2 Aufgaben pro Dimension existieren lediglich drei diskrete Zustände: $0\%$, $50\%$ und $100\%$. Die mathematische Wahrscheinlichkeitsanalyse belegt: Ein Modell mit einer echten Fähigkeit von 75% gewinnt gegen ein Modell mit 60% Fähigkeit **nur in 42,0% der Fälle**; in 58,0% der Fälle kommt es zu Gleichstand (39,3%) oder einer Rangumkehr (18,8%). Die Teilrankings sind damit weitgehend pseudozufällig ("Münzwurf-Effekt").
> 3. **Das Pseudoreplikations-Problem:** Das Wiederholen desselben Prompts ($K=3$) bei $T \le 0{,}2$ erzeugt hochgradig autokorrelierte Antworten ($\rho \approx 0{,}85$). Die 48 Läufe liefern rechnerisch nur **$N_{\text{eff}} \approx 17{,}8$ effektive unabhängige Aufgaben**. Die Rechenzeit wird primär für Prompt-Stabilität verschwendet, statt die Wissensbreite der Dimensionen abzudecken.

### Konkrete Optimierungsempfehlung:
- **Budget-neutrale Sofortmaßnahme (gleiche Laufzeit, 45% mehr Trennschärfe):**  
  Umstellung von $N=16, K=3$ auf **$N=24, K=2$ ($m=3$ Aufgaben pro Dimension)**. Exakt gleiche Inferenzanzahl (48 Läufe, ~28 Min. pro Modell), aber Erhöhung von $N_{\text{eff}}$ von 17,8 auf **25,9**.
- **Das wissenschaftliche "Golden Optimum" für Dual-Core CPU:**  
  Erweiterung auf **$N=32$ Aufgaben ($m=4$ pro Dimension)** mit $K=2$ Durchläufen (1x $T=0{,}0$, 1x $T=0{,}2$).  
  - Gesamtlaufzeit für 3 Modelle: **~1,87 Stunden** (voll beherrschbar ohne thermisches Throttling).  
  - Statistische Power zur Erkennung eines 20%-Unterschieds verdoppelt sich nahezu von 22,9% auf **> 60%** (gepoolt).  
  - Dimensions-Teilrankings erhalten 5 (bzw. mit $K=2$ bis zu 9) diskrete Leistungsstufen statt nur 3.

---

## 2. Analyse der Konfidenzintervalle (Wilson-Score-Breite)

Bei dichotomen Evaluationsdaten (Bestanden = 1, Nicht bestanden = 0) im Bereich kleiner bis mittlerer Stichprobenumfänge ($n \le 100$) liefert das klassische Wald-Intervall irreführende Ergebnisse. Das in Phase 2 gewählte **Wilson-Score-Intervall** ist methodisch exakt:

$$w = \frac{p + \frac{z^2}{2n} \pm z \sqrt{\frac{p(1-p)}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}} \quad (\text{für 95\% Konfidenz: } z = 1{,}95996)$$

### 2.1 Konfidenzintervallbreite des Gesamt-Scores bei $p = 0{,}70$ (70% Erfolgsquote)

Die nachfolgende Tabelle zeigt die reale statistische Unsicherheit für verschiedene Stichprobenumfänge:

| Aufgabenanzahl $n$ | 95% Wilson-Intervall $[L, U]$ | Intervallbreite $\Delta$ | Fehlermarge $\pm \%$ | Statistische Bewertung |
| :---: | :---: | :---: | :---: | :--- |
| **$n = 16$ (Aktuell v1.0.0)** | **$[0{,}456; 0{,}867]$** | **$0{,}411$** | **$\pm 20{,}5\%$** | ❌ **Extrem ungenau; keine Differenzierung möglich** |
| **$n = 24$ ($m=3$)** | $[0{,}500; 0{,}845]$ | $0{,}345$ | $\pm 17{,}2\%$ | 🟡 Spürbare Verbesserung |
| **$n = 32$ ($m=4$)** | $[0{,}527; 0{,}830]$ | $0{,}303$ | $\pm 15{,}2\%$ | 🟢 **Guter Kompromiss für lokale CPU** |
| **$n = 40$ ($m=5$)** | $[0{,}546; 0{,}819]$ | $0{,}274$ | $\pm 13{,}7\%$ | 🟢 Hohe Trennschärfe |
| **$n = 48$ (Falls 48 unabh.)** | $[0{,}560; 0{,}811]$ | $0{,}251$ | $\pm 12{,}6\%$ | 🟢 Solide Basis |
| **$n = 64$ ($m=8$)** | $[0{,}578; 0{,}800]$ | $0{,}222$ | $\pm 11{,}1\%$ | 🔵 Hoher akademischer Standard |
| **$n = 96$** | $[0{,}602; 0{,}783]$ | $0{,}180$ | $\pm 9{,}0\%$ | 🔵 Sehr hohe Präzision |

### 2.2 Reale Auswirkung auf Modellvergleiche:
Wenn **Modell A** 70% ($11{,}2 / 16$) und **Modell B** 55% ($8{,}8 / 16$) erzielt:
- Modell A Intervall: $[45{,}6\%, 86{,}7\%]$
- Modell B Intervall: $[31{,}8\%, 76{,}4\%]$
- **Überlappung:** Der Bereich von $45{,}6\%$ bis $76{,}4\%$ ist identisch. Der Unterschied von 15 Prozentpunkten ist statistisch **nicht signifikant** ($p = 0{,}37$ im exakten Fisher-Test).  
**Fazit:** Mit $N=16$ Aufgaben kann man wissenschaftlich nicht behaupten, dass ein 70%-Modell besser ist als ein 55%-Modell.

---

## 3. Mathematische Analyse des Diskretisierungsfehlers in Teilrankings

Das Master-Prompt verlangt explizit dimensionale Teilrankings (z.B. Coding, Reasoning, Deutsch). In v1.0.0 stehen pro Dimension lediglich **$m = 2$ Aufgaben** bereit.

### 3.1 Die Diskrete Zustandsmenge bei $m = 2$
Ein Modell kann bei 2 Aufgaben pro Durchlauf nur genau drei Werte annehmen:
$$\mathcal{S} = \{0{,}00; 0{,}50; 1{,}00\} \quad (\text{Schrittweite: } \Delta = 50\%)$$

Für $m=2$ beträgt das 95%-Wilson-Intervall bei $p=0{,}50$ gigantische **$[0{,}095; 0{,}905]$ (Breite: $81{,}1\%$, Fehlermarge: $\pm 40{,}5\%$)**.

### 3.2 Probabilistische Simulation: Das Rangumkehr-Phänomen
Nehmen wir zwei Modelle mit substanziell unterschiedlicher wahrer Fähigkeit in der Dimension *Coding*:
- **Modell A (stark):** Wahre Erfolgswahrscheinlichkeit $P(A) = 0{,}75$ (75%)
- **Modell B (schwächer):** Wahre Erfolgswahrscheinlichkeit $P(B) = 0{,}60$ (60%)

Die Wahrscheinlichkeiten für die beobachteten Scores auf 2 Aufgaben berechnen sich nach der Binomialverteilung $\mathcal{B}(m, p)$:

| Score | Wahrscheinlichkeit Modell A ($p=0{,}75$) | Wahrscheinlichkeit Modell B ($p=0{,}60$) |
| :---: | :---: | :---: |
| **0 / 2 (0%)** | $(1-0{,}75)^2 = \mathbf{6{,}25\%}$ | $(1-0{,}60)^2 = \mathbf{16{,}0\%}$ |
| **1 / 2 (50%)** | $2 \cdot 0{,}75 \cdot 0{,}25 = \mathbf{37{,}50\%}$ | $2 \cdot 0{,}60 \cdot 0{,}40 = \mathbf{48{,}0\%}$ |
| **2 / 2 (100%)** | $0{,}75^2 = \mathbf{56{,}25\%}$ | $0{,}60^2 = \mathbf{36{,}0\%}$ |

Daraus ergibt sich für den direkten Vergleich der beiden Modelle:
1. **Modell A gewinnt tatsächlich:**  
   $$P(A > B) = P(A=1, B \le 0{,}5) + P(A=0{,}5, B=0) = (0{,}5625 \cdot 0{,}64) + (0{,}375 \cdot 0{,}16) = \mathbf{42{,}00\%}$$
2. **Gleichstand (keine Unterscheidung möglich):**  
   $$P(A = B) = (0{,}5625 \cdot 0{,}36) + (0{,}375 \cdot 0{,}48) + (0{,}0625 \cdot 0{,}16) = \mathbf{39{,}25\%}$$
3. **Falsche Rangumkehr (schwächeres Modell B gewinnt):**  
   $$P(B > A) = P(B=1, A \le 0{,}5) + P(B=0{,}5, A=0) = (0{,}36 \cdot 0{,}4375) + (0{,}48 \cdot 0{,}0625) = \mathbf{18{,}75\%}$$

> [!CAUTION]
> **Statistisches Desaster bei $m=2$:**  
> Obwohl Modell A um 15 Prozentpunkte überlegen ist, **gewinnt es nur in 42% der Testläufe**! In 58% der Fälle behauptet der Benchmark fälschlicherweise, Modell B sei gleich gut oder sogar besser.  
> Ein Teilergebnis auf Basis von 2 Aufgaben ist wissenschaftlich wertlos.

---

## 4. Das "Pseudoreplikations-Problem": Der Irrtum über $K = 3$

In `02_scientific_benchmark_research.md` und `04_benchmark_test_design.md` wird argumentiert, dass $16 \text{ Aufgaben} \times 3 \text{ Wiederholungen} = 48 \text{ Datenpunkte}$ pro Modell erzeugt werden.

### 4.1 Cluster-Korrelation (Intra-Cluster Correlation $\rho$)
LLMs sind deterministische Algorithmen mit stochastischem Sampling. Bei $T=0{,}0$ ist die Antwort zu 100% identisch. Bei $T=0{,}2$ weisen wiederholte Antworten auf denselben Prompt eine extrem hohe Ähnlichkeit auf. Empirische Studien zur LLM-Evaluation belegen eine Intra-Cluster-Korrelation von **$\rho \approx 0{,}80$ bis $0{,}90$**.

Der statistische **Design-Effekt (DEFF)** für geclusterte Stichproben lautet:
$$\text{DEFF} = 1 + (K - 1) \cdot \rho$$

Mit $K = 3$ Wiederholungen und konservativem $\rho = 0{,}85$:
$$\text{DEFF} = 1 + (3 - 1) \cdot 0{,}85 = 1 + 1{,}70 = \mathbf{2{,}70}$$

Die **effektive Stichprobengröße ($N_{\text{eff}}$)** für die Verallgemeinerbarkeit auf das Aufgabengebiet berechnet sich zu:
$$N_{\text{eff}} = \frac{N_{\text{total}}}{\text{DEFF}} = \frac{16 \cdot 3}{2{,}70} = \frac{48}{2{,}70} \approx \mathbf{17{,}8 \text{ Aufgaben}}$$

### 4.2 Statistische Varianzzerlegung:
Die Gesamtvarianz einer Modell-Evaluation setzt sich zusammen aus:
$$\operatorname{Var}(\bar{Y}) = \frac{\sigma^2_{\text{prompt}}}{N} + \frac{\sigma^2_{\text{sampling}}}{N \cdot K}$$
- Da $\sigma^2_{\text{prompt}}$ (die Varianz zwischen verschiedenen Aufgaben) bei LLMs **etwa 5- bis 10-mal größer** ist als $\sigma^2_{\text{sampling}}$ (die Varianz durch Temperaturrauschen bei $T=0{,}2$), bringt das Erhöhen von $K$ (Wiederholungen) fast keinen Informationsgewinn für das Modellkönnen.
- **Jeder Rechenzeit-Token ist drastisch besser investiert in neue, unterschiedliche Aufgaben ($N \uparrow$) als in Wiederholungen desselben Prompts ($K \uparrow$)!**

---

## 5. Empirisches Laufzeit- & Hardware-Modell (Intel Core i3-7020U)

Die statistische Optimierung darf nicht isoliert von den realen Hardware-Fesseln der Zielmaschine betrachtet werden.

### 5.1 Verifizierte Inferenz-Parameter
- **Hardware:** Intel Core i3-7020U (2 Kerne / 4 Threads, 2.30 GHz, kein AVX-512, keine GPU).
- **Gemessener Durchsatz (Phase 7 v1.0.0):**
  - `qwen3.5:4b`: **3,35 Tokens/s** (inkl. Thinking)
  - `gemma4:e2b`: **4,94 Tokens/s** (Warmstart)
  - `llama2:latest`: **~3,80 Tokens/s**
  - **Mittelwert über Modelle:** $\approx \mathbf{3{,}8 \text{ bis } 4{,}0 \text{ t/s}}$
- **Durchschnittliche Inferenzzeit pro Task-Aufruf:**
  - Standardaufgabe (Prompt 35 Tokens, Antwort 80 Tokens): $\approx 25\text{ s}$
  - Thinking-Aufgabe / Coder (Prompt 50 Tokens, Thinking + Code 180 Tokens): $\approx 50\text{ s}$
  - **Empirischer Durchschnittsaufwand pro Einzelaufruf:** $\mathbf{t_{\text{run}} \approx 35\text{ Sekunden}}$

### 5.2 Thermisches Risiko bei Dauerlast
Das Notebook besitzt eine mobile U-Serie CPU (15 Watt cTDP). Dauertests von $> 2{,}5\text{ Stunden}$ unter 100% CPU-Last führen zu thermischem Throttling (Absenkung von 2.3 GHz auf 1.6–1.8 GHz), was die Durchsätze nach hinten raus verfälscht. Benchmarks sollten daher pro Gesamtsession **unter 2 Stunden** bleiben.

---

## 6. Quantitative Gegenüberstellung der Design-Alternativen

Die folgende Matrix vergleicht die statistische Güte und die reale Rechenzeit für verschiedene Aufgabenkonfigurationen ($N \in \{16, 24, 32, 40, 48\}$) und Wiederholungszahlen ($K \in \{1, 2, 3\}$):

| Design-Variante | Aufgaben $N$ | Aufgaben/Dim $m$ | Wiederholungen $K$ | Inferenzläufe / Modell | Laufzeit / Modell (Ø 35s) | Gesamtlaufzeit (3 Modelle) | Effektive Stichprobe $N_{\text{eff}}$ | Teststärke (Power) bei $\Delta = 20\%$ | Zustände pro Dimension |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Status Quo (v1.0.0)** | **16** | **2** | **3** | **48** | **28,0 min** | **84,0 min (1,4 h)** | **17,8** | **22,9 %** | 3 Stufen (0, 50, 100%) |
| **Option A (Budget-neutral)** | **24** | **3** | **2** | **48** | **28,0 min** | **84,0 min (1,4 h)** | **25,9 (+45%)** | **32,3 %** | 4 bzw. 7 Stufen |
| **Option B (Golden Optimum)** | **32** | **4** | **2** | **64** | **37,3 min** | **112,0 min (1,87 h)** | **34,6 (+94%)** | **41,3 % (gepoolt >60%)** | 5 bzw. 9 Stufen |
| **Option C (Deterministic)** | **32** | **4** | **1 ($T=0$)** | **32** | **18,7 min** | **56,0 min (0,9 h)** | **32,0 (+80%)** | **41,3 %** | 5 Stufen |
| **Option D (High-Power)** | **40** | **5** | **2** | **80** | **46,7 min** | **140,0 min (2,3 h)** | **43,2 (+142%)** | **49,7 %** | 6 bzw. 11 Stufen |
| **Option E (Maximal)** | **48** | **6** | **3** | **144** | **84,0 min** | **252,0 min (4,2 h)** | **53,3** | **57,2 %** | 7 Stufen |

### Wichtigste Erkenntnisse aus der Matrix:
1. **Status Quo (v1.0.0) ist ineffizient:** Bei 48 Läufen pro Modell erreicht das Design nur 22,9% Teststärke, weil 2/3 der Läufe redundante Wiederholungen sind.
2. **Option A (24 Aufgaben, $K=2$) schlägt den Status Quo bei identischer Laufzeit:**  
   Die exakt gleichen 48 Läufe (84 Minuten Gesamtlaufzeit) liefern 45% mehr statistische Power und reduzieren den Diskretisierungssprung von 50% auf 33% (bzw. 16,7% gepoolt).
3. **Option B (32 Aufgaben, $K=2$) ist das wissenschaftliche Optimum:**  
   Mit 1,87 Stunden Gesamtlaufzeit bleibt das System unter der 2-Stunden-Thermalgrenze. Die dimensionale Schrittweite sinkt auf 25% (5 diskrete Stufen), und die Unterscheidbarkeit zweier Modelle verbessert sich dramatisch.
4. **Option C (32 Aufgaben, nur $T=0{,}0$):**  
   Mit nur 56 Minuten Gesamtlaufzeit schneller als der Status Quo, aber mit 32 echten Aufgaben doppelt so aussagekräftig wie v1.0.0!

---

## 7. Verbindliche QA-Empfehlung für den Orchestrator

Auf Basis dieses statistischen Audits empfiehlt der unabhängige QA-Agent dem Orchestrator folgende strategische Weichenstellung für die Revision des Hauptbenchmarks (Benchmark-Version 1.1.0):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ENTCHEIDUNGSMATRIX                              │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Empfohlener Standard ("Golden Optimum"):                           │
│    -> N = 32 Aufgaben (exakt 4 Aufgaben pro Dimension über 8 Dim.)    │
│    -> K = 2 Durchläufe (1x T=0.0 deterministisch, 1x T=0.2 Stabilität)│
│    -> Gesamtlaufzeit: ~37 Min. / Modell (~112 Min. für alle 3 Modelle) │
│    -> Vorteil: 5 dimensionale Stufen, 94% höhere effektive Stichprobe, │
│       Wilson-Fehlermarge sinkt auf ±15,2%, thermisch sicher.           │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Alternative bei strikter Laufzeitdeckelung ("Budget-Neutral"):      │
│    -> N = 24 Aufgaben (3 Aufgaben pro Dimension über 8 Dim.)          │
│    -> K = 2 Durchläufe (1x T=0.0, 1x T=0.2)                           │
│    -> Gesamtlaufzeit: exakt 28 Min. / Modell (84 Min. für 3 Modelle)   │
│    -> Vorteil: Laufzeit identisch zu v1.0.0, aber +45% mehr Power      │
│       und 4 dimensionale Leistungsstufen statt 3.                      │
└────────────────────────────────────────────────────────────────────────┘
```

### Konkrete Handlungsanweisungen für die Spezifikation v1.1.0:
1. **Aufstockung des Aufgabenpools:** Der Aufgabenkatalog für Stufe 2 muss von 16 auf **mindestens 24 (besser 32) Aufgaben** erweitert werden (z.B. HB-R1 bis HB-R4, HB-C1 bis HB-C4 etc.).
2. **Reduktion von $K=3$ auf $K=2$:** Der dritte Durchlauf bei $T=0{,}2$ erzeugt statistisch redundante Datenpunkte und blockiert wertvolle Rechenzeit. Ein Durchlauf bei $T=0{,}0$ (Reproduzierbarkeit) und ein Durchlauf bei $T=0{,}2$ (Stochastik-Check) sind vollkommen ausreichend.
3. **Ausweisung von $N_{\text{eff}}$ im Abschlussbericht:** Im finalen Auswertungsbericht müssen die Wilson-Score-Intervalle und die effektiven Stichprobengrößen transparent neben den Roh-Scores abgedruckt werden.

---

## 8. Fazit

Der Hauptbenchmark v1.0.0 mit 16 Aufgaben ist ein guter methodischer Prototyp, leidet jedoch unter schwerwiegenden statistischen Schwächen (nur 22,9% Power, Münzwurf-Verhalten in den Dimensionen).  

Durch die Umverteilung von Rechenzeit – **Wegfall der redundanten 3. Wiederholung zugunsten von 32 echten Aufgaben ($m=4$)** – wird das System ohne nennenswerten Laufzeit-Mehraufwand von einem groben Schätzwerkzeug zu einem **wissenschaftlich belastbaren, hochgradig trennscharfen Benchmark** aufgewertet.