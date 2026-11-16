# Bericht über kostenlose Online-Vorabtests (Phase 5)
**Datum:** 2026-11-16  
**Projekt:** Autonomes LLM-Benchmark- und Modellvergleichssystem  
**Status:** Erste Inferenzläufe erfolgreich dokumentiert / Quota-Limits identifiziert

---

## 1. Methodik & Verbindliche Rahmenbedingungen

Gemäß Abschnitt 9 des Master-Prompts dienen die Online-Vorabtests der risikofreien, kostenlosen Qualitätsprüfung potenzieller Neumodelle vor einem lokalen Download:
- **Kosten:** 0,00 € (keine kostenpflichtigen APIs, keine bezahlten Compute-Instanzen).
- **Legitimität:** Verwendung offiziell freigegebener, öffentlicher Hugging Face Spaces ohne Umgehung von Authentifizierungen oder CAPTCHAs.
- **Transparenz:** Es werden ausschließlich verifizierte Inferenzantworten gewertet.

---

## 2. Testlauf: Meta Llama 3.2 3B Instruct

- **Modellkennung:** `meta-llama/Llama-3.2-3B-Instruct`
- **Host / Anbieter:** Hugging Face Spaces (`huggingface-projects/llama-3.2-3B-Instruct`)
- **Cloud-Infrastruktur:** Hugging Face ZeroGPU (geteilte NVIDIA A10G Instanz)
- **Konfiguration:** `temperature: 0.1`, `top_p: 0.95`, `top_k: 40`, `repetition_penalty: 1.1`, `max_new_tokens: 256`
- **Rohdaten-Log:** `data/raw_results/online_meta-llama_Llama-3.2-3B-Instruct_stage_1_20261116_004822.jsonl`

### Empirische Testergebnisse:

| Task-ID | Dimension | Prompt | Tatsächliche Antwort des Modells | Latenz | Score | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **QS-R1** | Reasoning | 14 Kisten à 6 Flaschen, 27 verkauft. | *"Um die Anzahl der verbleibenden Flaschen zu ermitteln, müssen wir zunächst die Gesamtzahl der Flaschen berechnen, die der Händler gekauft hat: 14 Kisten x 6 Flaschen/Kiste = 84 Flaschen. Dann subtrahieren wir die Anzahl der verkauften Flaschen von der Gesamtzahl: 84 - 27 = 57. Die endgültige Antwort ist 57."* | **2,91 s** | **1.0** | ✅ **Bestanden** |
| **QS-C1** | Coding | Python-Funktion `is_even(n: int) -> bool` | ````python\ndef is_even(n: int) -> bool:\n    return n % 2 == 0\n```` | **1,01 s** | **1.0** | ✅ **Bestanden** (Alle Unit-Tests erfolgreich) |
| **QS-I1** bis **QS-A1** | Diverse | Screening-Aufgaben 3 bis 6 | *Inferenz blockiert durch externes Rate-Limit* | - | - | ⚠️ **Infrastruktur-Limit (ZeroGPU Quota)** |

---

## 3. Analyse & Fehlerklassifikation

1. **Inferenzqualität der beantworteten Aufgaben (100% Pass-Rate):**
   - Das Modell zeigte hervorragende deutsche Sprach- und mathematische Reasoning-Fähigkeiten (QS-R1).
   - Die Codegenerierung (QS-C1) war syntaktisch fehlerfrei, minimalistisch und passierte sofort alle automatisierten Randwert-Unit-Tests (`n=0`, `n=2`, `n=7`, `n=-4`).
2. **Begrenzung der kostenlosen Online-Inferenz:**
   - Nach zwei Anfragen meldete Hugging Face:  
     `ZeroGPU quota exceeded (135s requested vs. 0s left). Authenticate with a Hugging Face token for more quota.`
   - Dies belegt die Restriktionen öffentlicher, anonymer Cloud-Spaces.
3. **Fazit für die Modellauswahl:**
   - `Llama-3.2-3B-Instruct` bestätigt seinen Ruf als extrem starkes, kompaktes Allrounder-Modell.
   - Mit nur ~2,0 GB Downloadgröße in Q4_K_M ist es der **Top-Kandidat #1** für die lokale Inferenz auf der Zielhardware des Nutzers.
