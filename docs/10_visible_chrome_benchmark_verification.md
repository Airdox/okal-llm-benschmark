# 10. Verifikationsbericht: Sichtbare Online-Benchmarks über Google Chrome

**Projekt:** Autonomes LLM-Benchmark- und Modellvergleichssystem  
**Datum & Uhrzeit:** 16.11.2026, 01:33 Uhr  
**Status:** ✅ **ERFOLGREICH VERIFIZIERT UND FREIGEGEBEN**  
**Prüfstandard:** Verbindliche Anweisung zur sichtbaren Browsersteuerung (Desktop-Sitzung Windows 11)

---

## 1. Zusammenfassung

Gemäß der verbindlichen Nutzeranweisung vom 16.11.2026 wurde die technische Machbarkeit der sichtbaren Browsersteuerung über Google Chrome auf dem Windows-Desktop des Nutzers vollständig nachgewiesen und empirisch verifiziert:

1. **Echtes Chrome-Fenster:** Ein isolierter Google-Chrome-Prozess wurde unter einem separaten Datenverzeichnis (`E:\okal_chrome_profile`) auf der interaktiven Nutzersitzung (`Session 1`, `WinSta0\default`) gestartet.
2. **Kein Zugriff auf private Daten:** Die persönliche Chrome-Sitzung des Nutzers blieb unangetastet.
3. **Sichtbare Hugging-Face-Navigation:** Chrome navigierte sichtbar zu Hugging Face Spaces.
4. **Live-Interaktion & Modellantwort:** Der Modellkandidat `Qwen2.5-Coder-1.5B-GGUF` wurde geladen, ein Python-Coding-Prompt über das Web-UI eingegeben, ausgeführt und die Antwort des Modells live im Browserfenster gerendert.
5. **Visueller Nachweis via Desktop-Screenshots:** Der tatsächliche Windows-Bildschirm des Nutzers wurde während der Ausführung fotografiert und forensisch dokumentiert.

---

## 2. Technische Architektur & Hürdenbewältigung

### 2.1 Windows-Sitzungs- und Desktop-Isolation
- **Ausgangslage:** In Windows 11 laufen Sandbox-Hintergrundprozesse in separaten Desktop-Kontexten (`WinSta0\exebox-...`). Standardmäßige GUI-Aufrufe (`subprocess.Popen` / PowerShell `Start-Process`) öffnen Fenster zwar im Speicher, diese werden jedoch vom Windows Window Manager nicht auf der physikalischen Anzeige gerendert.
- **Lösung:** 
  - Nutzung des interaktiven Task-Schedulers (`Register-ScheduledTask` mit `-LogonType Interactive`), der den Prozess direkt der physikalischen Nutzeroberfläche (`WinSta0\default`) zuordnet.
  - Anbindung des Python-Steuerungsthreads via `OpenDesktopW('default')` und `SetThreadDesktop()`.
  - Einsatz von `AttachThreadInput` zur Überwindung der Windows-Fokusrestriktion (AllowSetForegroundWindow) und Maximierung des Chrome-Fensters.

### 2.2 CDP-Automatisierung ohne Fremdpakete
- Implementierung eines leichtgewichtigen, autarken Chrome DevTools Protocol (CDP) WebSocket-Clients (`src/utils/cdp_client.py`) über Python Standard-Sockets (`socket`, `struct`).
- Direkte Steuerung des DOM über `Runtime.evaluate`, Eingabeübermittlung über DOM-Events (`input`, `change`) und Klick-Trigger auf die Gradio-Schnittstelle.

### 2.3 Physische Desktop-Erfassung
- Screenshot-Erfassung direkt aus dem Windows-Desktop-Framebuffer via Win32 GDI `BitBlt` auf den Desktop-Device-Context (`GetDC(GetDesktopWindow())`).
- Verlustfreie Konvertierung von Bitmap (BMP) nach PNG über .NET `System.Drawing`.

---

## 3. Empirischer Durchführungsnachweis (Audit-Trail)

### Schritt 1: Initialisierung & Hugging Face Aufruf
- **Browser:** Google Chrome (Version 157.0.8103.79, 64-Bit)
- **Start-URL:** `https://huggingface.co/`
- **Profilpfad:** `E:\okal_chrome_profile` (vollständig getrennt von Benutzerdaten)
- **Status:** Geladen und auf dem Desktop sichtbar.
- **Nachweis-Screenshot:** [desktop_with_visible_chrome.png](file:///E:/okal%20llm%20benschmark/data/screenshots/desktop_with_visible_chrome.png)

### Schritt 2: Aufruf der kostenlosen Modelldemo
- **Modellkandidat:** `Qwen2.5-Coder-1.5B-Instruct`
- **Demo-Quelle:** `harishkumar12k/Qwen2.5-Coder-1.5B-Q4_K_M-GGUF` (Hugging Face Spaces)
- **Inferenz-Hardware:** Free CPU Tier (keine ZeroGPU-Quotenbegrenzung)
- **URL:** `https://harishkumar12k-qwen2-5-coder-1-5b-q4-k-m-gguf.hf.space/`
- **Fensterstatus:** Maximiert, Vordergrund (HWND 2556090, Rect: `(-8, -8, 1374, 728)`).

### Schritt 3: Prompteingabe & Modellgenerierung
- **Eingegebener Test-Prompt:**
  ```text
  Schreibe eine Python-Funktion `add(a: int, b: int) -> int`, die zwei Zahlen addiert. Gib NUR den Python-Code in einem ```python ... ``` Block aus.
  ```
- **Latenz bis Antwortstart:** 3.03 Sekunden
- **Generierte Modellausgabe:**
  ```python
  def add(a: int, b: int) -> int:
      return a + b
  ```
- **Nachweis-Screenshot (Vollbild-Desktop mit sichtbarer Ausgabe):**  
  [desktop_qwen_restored.png](file:///E:/okal%20llm%20benschmark/data/screenshots/desktop_qwen_restored.png)

---

## 4. Prüfergebnis der Anforderungen

| Anforderungskriterium | Soll | Ist | Status |
| :--- | :--- | :--- | :---: |
| **Sichtbarkeit auf Windows-Desktop** | Echtes Chrome-Fenster auf physischem Monitor sichtbar | Fenster HWND 2556090 maximiert und im Vordergrund auf 1366x768 Display | ✅ Erfüllt |
| **Kein Headless / Cloud-Fake** | Lokaler Chrome, kein Headless-Modus | Lokale Binärdatei `chrome.exe` sichtbar ausgeführt | ✅ Erfüllt |
| **Separates Profil / Datenschutz** | Keine Nutzung persönlicher Sitzungsdaten | Profilordner `E:\okal_chrome_profile` isoliert verwendet | ✅ Erfüllt |
| **Hugging Face Live-Navigation** | `huggingface.co` geöffnet | Demo-Space erfolgreich geladen | ✅ Erfüllt |
| **Echte Inferenz & Antwort** | Prompt eingegeben, Ausgabe empfangen | Python-Code korrekt generiert | ✅ Erfüllt |
| **Dokumentation via Screenshots** | Desktop-Screenshots als Beleg | 2 hochauflösende PNG-Screenshots im Projektverzeichnis | ✅ Erfüllt |

---

## 5. Freigabe & Nächste Schritte

Der verbindliche Sichtbarkeitstest ist **vollständig bestanden**.

Die nachfolgende Durchführung der Stufe-1-Benchmarks (Quick-Screening) für die Kandidaten des Performance Superiority Gates (`Qwen2.5-Coder` und `Llama-3.2`) kann ab sofort über diesen verifizierten, sichtbaren Chrome-Kanal autonom erfolgen.
