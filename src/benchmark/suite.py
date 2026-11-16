"""
Definition aller Benchmark-Aufgaben und Validierungs-Zuordnungen für Stufe 1 und Stufe 2.
"""
import re
import json
from typing import Dict, Any, List
from src.benchmark.validator import (
    validate_number,
    validate_code,
    validate_json_schema,
    validate_ifeval,
    validate_tool_call,
    validate_rejection,
    validate_capitals_ifeval,
    clean_markdown_fence
)

STAGE1_TASKS: List[Dict[str, Any]] = [
    {
        "id": "QS-R1",
        "dimension": "Reasoning",
        "prompt": "Ein Händler kauft 14 Kisten mit je 6 Flaschen Saft. Er verkauft 27 Flaschen. Wie viele Flaschen hat er noch übrig? Antworte ausschließlich mit der Zahl als Ziffer.",
        "max_tokens": 300,
        "validator": lambda resp: validate_number(resp, 57.0),
        "description": "Multi-step arithmetic (14*6 - 27 = 57)"
    },
    {
        "id": "QS-C1",
        "dimension": "Coding",
        "prompt": "Schreibe eine Python-Funktion `is_even(n: int) -> bool`, die True zurückgibt, wenn n gerade ist, sonst False. Gib ausschließlich den Python-Code zurück, ohne Erklärungen.",
        "max_tokens": 384,
        "validator": lambda resp: validate_code(resp, "assert is_even(0) is True\nassert is_even(2) is True\nassert is_even(7) is False\nassert is_even(-4) is True\nassert is_even(-3) is False", timeout_sec=3),
        "description": "Basic function implementation with edge cases"
    },
    {
        "id": "QS-I1",
        "dimension": "Instruction Following",
        "prompt": "Nenne drei europäische Hauptstädte. Bedingung: Schreibe jedes Wort komplett in GROSSBUCHSTABEN und trenne sie nur durch Kommas, absolut ohne Leerzeichen (z.B. ROM,PARIS,MADRID). Keine anderen Wörter oder Erklärungen.",
        "max_tokens": 256,
        "validator": lambda resp: validate_capitals_ifeval(resp),
        "description": "Format- and case-constraint with European capital whitelist"
    },
    {
        "id": "QS-S1",
        "dimension": "Structured Output",
        "prompt": "Erzeuge ein JSON-Objekt mit genau zwei Schlüsseln: 'name' mit dem Wert 'Benchmark' und 'score' mit der Ganzzahl 100. Gib ausschließlich das JSON-Objekt aus, keine Erklärungen.",
        "max_tokens": 256,
        "validator": lambda resp: validate_json_schema(resp, required_keys=["name", "score"], key_types={"name": str, "score": int}),
        "description": "Valid JSON output with schema types"
    },
    {
        "id": "QS-G1",
        "dimension": "German Language",
        "prompt": "Bilde die 3. Person Singular Präteritum des Verbs 'nachdenken' und setze diese Form in einen vollständigen deutschen Satz. Gib nur diesen Satz aus.",
        "max_tokens": 256,
        "validator": lambda resp: (
            bool(re.search(r"\b(er|sie|es|man)\s+dachte\b.*?\bnach\b", resp.lower()) and resp.strip().endswith((".", "!", "?"))),
            1.0 if bool(re.search(r"\b(er|sie|es|man)\s+dachte\b.*?\bnach\b", resp.lower()) and resp.strip().endswith((".", "!", "?"))) else 0.0,
            "Deterministisches Muster (Pronomen + 'dachte ... nach' + Satzzeichen) erfüllt." if bool(re.search(r"\b(er|sie|es|man)\s+dachte\b.*?\bnach\b", resp.lower()) and resp.strip().endswith((".", "!", "?"))) else "Grammatikmuster nicht erfüllt."
        ),
        "description": "German past tense and separable verb syntax"
    },
    {
        "id": "QS-A1",
        "dimension": "Agentic Tool Calling",
        "prompt": "Du hast Zugriff auf das Tool 'get_weather'. Rufe dieses Tool auf, um das Wetter für 'Berlin' abzufragen. Antworte ausschließlich mit einem JSON-Objekt im Format: {\"tool\": \"get_weather\", \"args\": {\"city\": \"Berlin\"}}",
        "max_tokens": 256,
        "validator": lambda resp: validate_tool_call(resp, "get_weather", {"city": "Berlin"}),
        "description": "Single-step tool call schema conformance"
    }
]

STAGE2_TASKS: List[Dict[str, Any]] = [
    # =========================================================================
    # Dimension 1: Reasoning (HB-R1 bis HB-R4) - max_tokens: 768
    # =========================================================================
    {
        "id": "HB-R1",
        "dimension": "Reasoning",
        "prompt": "Ein Fahrradhändler hat 45 Fahrräder auf Lager. Am Montag verkauft er 15 Räder. Am Dienstag erhält er eine Neulieferung von 18 Rädern. Am Mittwoch verkauft er genau ein Drittel seines aktuellen Bestands. Wie viele Fahrräder hat er am Ende des Mittwochs noch? Antworte nur mit der finalen Zahl.",
        "max_tokens": 768,
        "validator": lambda resp: validate_number(resp, 32.0),
        "description": "Multi-step arithmetic with fractions: ((45-15)+18) * 2/3 = 32"
    },
    {
        "id": "HB-R2",
        "dimension": "Reasoning",
        "prompt": "Vier Freunde kommen bei einem Rennen ins Ziel: Anna, Ben, Clara und David. Clara war schneller als Ben. David kam direkt nach Anna ins Ziel. Ben kam vor Anna ins Ziel. Wer hat das Rennen gewonnen? Antworte nur mit dem Namen.",
        "max_tokens": 768,
        "validator": lambda resp: (
            ("clara" in resp.lower() and "ben" not in resp.lower().replace("clara", "")),
            1.0 if "clara" in resp.lower() else 0.0,
            "Clara als Siegerin identifiziert."
        ),
        "description": "Relational logical deduction (Clara > Ben > Anna > David)"
    },
    {
        "id": "HB-R3",
        "dimension": "Reasoning",
        "prompt": "Drei Meetings sollen geplant werden. Meeting A dauert 45 Minuten, Meeting B 30 Minuten, Meeting C 30 Minuten. Das Zeitfenster beginnt um 09:00 Uhr. Meeting A startet pünktlich um 09:00 Uhr. Zwischen Meeting A und Meeting B gibt es eine Pause von genau 15 Minuten. Meeting C beginnt direkt nach Meeting B. Zu welcher Uhrzeit endet Meeting C? Antworte ausschließlich mit der Uhrzeit im Format HH:MM.",
        "max_tokens": 768,
        "validator": lambda resp: (
            ("11:00" in resp),
            1.0 if "11:00" in resp else 0.0,
            "Uhrzeit 11:00 korrekt berechnet (09:00-09:45 + 15m Pause + 30m B + 30m C)."
        ),
        "description": "Multi-step temporal scheduling with break calculation"
    },
    {
        "id": "HB-R4",
        "dimension": "Reasoning",
        "prompt": "Gegeben sind folgende Prämissen:\n1. Alle Krokodile sind blau.\n2. Keine blauen Wesen können fliegen.\n3. Einige Krokodile tragen Brillen.\nFolgt daraus zwingend, dass einige Wesen, die Brillen tragen, nicht fliegen können? Antworte ausschließlich mit 'Ja' oder 'Nein' und begründe in einem kurzen Satz.",
        "max_tokens": 768,
        "validator": lambda resp: (
            bool(re.match(r"^\s*ja\b", resp.strip(), re.IGNORECASE)),
            1.0 if bool(re.match(r"^\s*ja\b", resp.strip(), re.IGNORECASE)) else 0.0,
            "Korrekt mit 'Ja' deduziert (Brillenträger-Krokodile sind blau, können daher nicht fliegen)."
        ),
        "description": "Syllogistic logic with counter-intuitive category constraint"
    },

    # =========================================================================
    # Dimension 2: Coding (HB-C1 bis HB-C4) - max_tokens: 768
    # =========================================================================
    {
        "id": "HB-C1",
        "dimension": "Coding",
        "prompt": "Implementiere in Python eine Funktion `compress_string(s: str) -> str`, die aufeinanderfolgende gleiche Zeichen durch das Zeichen gefolgt von der Anzahl ersetzt (z.B. 'aabcccccaaa' -> 'a2b1c5a3'). Bei leerem String soll '' zurückgegeben werden. Gib nur den Python-Codeblock zurück.",
        "max_tokens": 768,
        "validator": lambda resp: validate_code(resp, """
assert compress_string('') == ''
assert compress_string('a') == 'a1'
assert compress_string('aabcccccaaa') == 'a2b1c5a3'
assert compress_string('abcd') == 'a1b1c1d1'
"""),
        "description": "Run-length string compression algorithm"
    },
    {
        "id": "HB-C2",
        "dimension": "Coding",
        "prompt": "Korrigiere folgenden fehlerhaften Python-Code, sodass die Funktion `find_max(numbers)` das Maximum einer Liste von Zahlen korrekt zurückgibt oder None bei leerer Liste:\n```python\ndef find_max(numbers):\n    m = 0\n    for i in range(len(numbers)):\n        if numbers[i] > m:\n            m = numbers[i]\n    return m\n```\nBeachte auch negative Zahlen! Gib nur den korrigierten Codeblock zurück.",
        "max_tokens": 768,
        "validator": lambda resp: validate_code(resp, """
assert find_max([]) is None
assert find_max([-5, -2, -9]) == -2
assert find_max([10, 4, 25, 2]) == 25
assert find_max([0]) == 0
"""),
        "description": "Bugfixing function handling negative numbers and empty lists"
    },
    {
        "id": "HB-C3",
        "dimension": "Coding",
        "prompt": "Implementiere in Python eine Funktion `merge_intervals(intervals: list[list[int]]) -> list[list[int]]`, die eine Liste von Zahlenintervallen sortiert und überlappende Intervalle verschmilzt (z.B. [[1, 3], [2, 6], [8, 10]] -> [[1, 6], [8, 10]]). Gib ausschließlich den Python-Codeblock zurück.",
        "max_tokens": 768,
        "validator": lambda resp: validate_code(resp, """
assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
assert merge_intervals([]) == []
assert merge_intervals([[1, 4], [0, 4]]) == [[0, 4]]
"""),
        "description": "Interval merging algorithmic problem"
    },
    {
        "id": "HB-C4",
        "dimension": "Coding",
        "prompt": "Schreibe eine Python-Funktion `is_valid_ipv4(ip: str) -> bool`, die prüft, ob ein String eine syntaktisch gültige IPv4-Adresse darstellt (vier Zahlen von 0 bis 255 getrennt durch Punkte, keine führenden Nullen außer bei '0' selbst). Gib ausschließlich den Python-Code zurück.",
        "max_tokens": 768,
        "validator": lambda resp: validate_code(resp, """
assert is_valid_ipv4('192.168.1.1') is True
assert is_valid_ipv4('256.1.1.1') is False
assert is_valid_ipv4('192.168.01.1') is False
assert is_valid_ipv4('192.168.1') is False
assert is_valid_ipv4('0.0.0.0') is True
assert is_valid_ipv4('abc.def.ghi.jkl') is False
"""),
        "description": "Strict IPv4 address validation with edge cases"
    },

    # =========================================================================
    # Dimension 3: Comprehension & Extraction (HB-T1 bis HB-T4) - max_tokens: 384
    # =========================================================================
    {
        "id": "HB-T1",
        "dimension": "Comprehension",
        "prompt": "Lies folgenden Textauszug und extrahiere die Projektleiterin, das genehmigte Gesamtbudget und das Startdatum:\n'Im gestrigen Lenkungskreis wurde beschlossen, dass Dr. Sabine Weber die Leitung für das Projekt Titan übernimmt, nachdem Herr Müller abgesprungen war. Ursprünglich waren 300.000 Euro im Gespräch, final genehmigt wurden jedoch exakt 450.000 Euro. Die operative Arbeit startet planmäßig am 1. Oktober 2026.'\nAntworte als kompakte Aufzählung.",
        "max_tokens": 384,
        "validator": lambda resp: (
            ("sabine weber" in resp.lower() and "450.000" in resp.lower() and "1. oktober 2026" in resp.lower()),
            1.0 if ("sabine weber" in resp.lower() and "450.000" in resp.lower() and "1. oktober 2026" in resp.lower()) else 0.0,
            "Alle 3 Entitäten korrekt extrahiert."
        ),
        "description": "Entity extraction from noisy text with distractors"
    },
    {
        "id": "HB-T2",
        "dimension": "Comprehension",
        "prompt": "Kontext: 'Die Apollo-11-Mission startete am 16. Juli 1969. Die Landefähre Eagle setzte vier Tage später auf dem Mond auf. Neil Armstrong betrat die Oberfläche rund sechs Stunden nach dem Aufsetzen der Fähre.'\nFrage: An welchem Datum betrat Neil Armstrong die Mondoberfläche? Antworte kurz.",
        "max_tokens": 384,
        "validator": lambda resp: (
            ("20. juli" in resp.lower() or "21. juli" in resp.lower()),
            1.0 if ("20. juli" in resp.lower() or "21. juli" in resp.lower()) else 0.0,
            "Mondlandung/Betreten Datum (20./21. Juli 1969) korrekt synthetisiert."
        ),
        "description": "Multi-hop temporal reasoning from text"
    },
    {
        "id": "HB-T3",
        "dimension": "Comprehension",
        "prompt": "Aus einem Sicherheitsbericht: 'Im Quartal Q3 wurden folgende Komponenten erfolgreich auditiert: Datenbank-Cluster Alpha, Firewall-Gateway West und der interne DNS-Server. Das Mail-Relay und das Backup-Storage-System wurden wegen Wartungsarbeiten auf Q4 verschoben.'\nFrage: Welche zwei Systeme wurden im Q3-Audit NICHT geprüft? Antworte kurz als kommagetrennte Liste.",
        "max_tokens": 384,
        "validator": lambda resp: (
            ("mail-relay" in resp.lower() or "mail relay" in resp.lower()) and ("backup-storage" in resp.lower() or "backup storage" in resp.lower() or "backup" in resp.lower()),
            1.0 if (("mail" in resp.lower()) and ("backup" in resp.lower())) else 0.0,
            "Die beiden ungeprüften Systeme (Mail-Relay, Backup-Storage) korrekt identifiziert."
        ),
        "description": "Negative entity extraction under distractor noise"
    },
    {
        "id": "HB-T4",
        "dimension": "Comprehension",
        "prompt": "Aus einem Incident-Postmortem: 'Durch einen Konfigurationsfehler im Load-Balancer wurde der gesamte HTTPS-Traffic ausschließlich auf Node 3 geroutet. Dies führte zu einer Überlastung des Arbeitsspeichers von Node 3, wodurch der OOM-Killer den Nginx-Prozess beendete. In der Folge schlugen die Health-Checks fehl und der Dienst war für 12 Minuten nicht erreichbar.'\nFrage: Was war die unmittelbare technische Ursache für den Absturz des Nginx-Prozesses? Antworte in einem kurzen Satz.",
        "max_tokens": 384,
        "validator": lambda resp: (
            any(w in resp.lower() for w in ["oom-killer", "oom killer", "out of memory", "arbeitsspeicher", "speicherüberlastung"]),
            1.0 if any(w in resp.lower() for w in ["oom", "arbeitsspeicher", "speicher"]) else 0.0,
            "Unmittelbare Ursache (OOM-Killer / Speichermangel) korrekt identifiziert."
        ),
        "description": "Technical root-cause causal inference from incident report"
    },

    # =========================================================================
    # Dimension 4: Instruction Following (HB-I1 bis HB-I4) - max_tokens: 384
    # =========================================================================
    {
        "id": "HB-I1",
        "dimension": "Instruction Following",
        "prompt": "Erkläre das Prinzip der Schwerkraft in genau zwei vollständigen Sätzen. Bedingung: Das Wort 'Erde' oder 'Planeten' darf im gesamten Text überhaupt nicht vorkommen.",
        "max_tokens": 384,
        "validator": lambda resp: validate_ifeval(resp, forbidden_words=["Erde", "Planeten", "Planet", "Planetenmasse"], exact_sentences=2),
        "description": "Negative constraint and exact sentence count"
    },
    {
        "id": "HB-I2",
        "dimension": "Instruction Following",
        "prompt": "Erstelle eine Liste mit genau vier Punkten. Jeder Punkt muss mit dem Präfix 'Phase:' beginnen und darf maximal 6 Wörter umfassen. Keine Einleitung, kein Schlusssatz.",
        "max_tokens": 384,
        "validator": lambda resp: (
            (resp.count("Phase:") == 4 and all(len(line.split()) <= 8 for line in resp.strip().split("\n") if line.strip())),
            1.0 if (resp.count("Phase:") == 4 and all(len(line.split()) <= 8 for line in resp.strip().split("\n") if line.strip())) else 0.0,
            "4 Punkte mit Präfix 'Phase:' und Längenlimit eingehalten."
        ),
        "description": "Strict formatting and length limit per bullet"
    },
    {
        "id": "HB-I3",
        "dimension": "Instruction Following",
        "prompt": "Schreibe genau drei Sätze über das Thema 'Sonne'. Bedingungen:\n1. Jeder Satz muss mit dem Wort 'Tatsache:' beginnen.\n2. In keinem Satz darf das Wort 'warm', 'heiß' oder 'Hitze' vorkommen.\nGib ausschließlich diese drei Sätze aus.",
        "max_tokens": 384,
        "validator": lambda resp: (
            (resp.count("Tatsache:") == 3 and not any(w in resp.lower() for w in ["warm", "heiß", "hitze"]) and len([s for s in resp.split("\n") if s.strip()]) == 3),
            1.0 if (resp.count("Tatsache:") == 3 and not any(w in resp.lower() for w in ["warm", "heiß", "hitze"])) else 0.0,
            "3 Sätze mit Präfix 'Tatsache:' und ohne verbotene Wörter."
        ),
        "description": "Prefix constraint combined with multi-word negative constraint"
    },
    {
        "id": "HB-I4",
        "dimension": "Instruction Following",
        "prompt": "Nenne vier Wochentage auf Deutsch. Bedingung: Zeile 1 und 3 müssen komplett in KLEINBUCHSTABEN geschrieben sein, Zeile 2 und 4 komplett in GROSSBUCHSTABEN. Genau ein Wochentag pro Zeile, absolut nichts anderes.",
        "max_tokens": 384,
        "validator": lambda resp: (
            (lambda lines: len(lines) == 4 and lines[0].islower() and lines[1].isupper() and lines[2].islower() and lines[3].isupper())([line.strip() for line in resp.strip().split("\n") if line.strip()]),
            1.0,
            "Alternierendes Groß-/Kleinbuchstaben-Muster pro Zeile exakt erfüllt."
        ) if len([line.strip() for line in resp.strip().split("\n") if line.strip()]) == 4 and [line.strip() for line in resp.strip().split("\n") if line.strip()][0].islower() and [line.strip() for line in resp.strip().split("\n") if line.strip()][1].isupper() else (False, 0.0, "Zeilen-/Case-Muster nicht erfüllt."),
        "description": "Alternating lower/upper case line-by-line formatting"
    },

    # =========================================================================
    # Dimension 5: Structured Output (HB-S1 bis HB-S4) - max_tokens: 384
    # =========================================================================
    {
        "id": "HB-S1",
        "dimension": "Structured Output",
        "prompt": "Gib ein valides JSON-Objekt zurück, das einen Webserver beschreibt mit den Feldern: 'host' (String 'localhost'), 'port' (Ganzzahl 8080), 'ssl' (Boolean true) und 'routes' (eine Liste mit den Strings '/' und '/api'). Ausschließlich JSON, keine Markdown-Erklärungen außerhalb des JSON.",
        "max_tokens": 384,
        "validator": lambda resp: validate_json_schema(resp, required_keys=["host", "port", "ssl", "routes"], key_types={"host": str, "port": int, "ssl": bool, "routes": list}),
        "description": "Nested JSON schema with strict types (str, int, bool, list)"
    },
    {
        "id": "HB-S2",
        "dimension": "Structured Output",
        "prompt": "Wandle folgende Daten in ein JSON-Array von Objekten um:\n1. Sensor Alpha, Temperatur 22.5\n2. Sensor Beta, Temperatur 19.8\nJedes Objekt muss die Schlüssel 'sensor' (String) und 'temp' (Float) besitzen. Nur JSON.",
        "max_tokens": 384,
        "validator": lambda resp: (
            (lambda d: isinstance(d, list) and len(d) == 2 and all("sensor" in x and "temp" in x for x in d))(json.loads(clean_markdown_fence(resp, "json"))),
            1.0,
            "JSON-Array mit 2 Objekten und korrekten Feldern erzeugt."
        ) if clean_markdown_fence(resp, "json").startswith("[") else (False, 0.0, "Kein JSON-Array."),
        "description": "Tabular text to JSON array transformation"
    },
    {
        "id": "HB-S3",
        "dimension": "Structured Output",
        "prompt": "Erzeuge ein valides JSON-Objekt für eine Benutzerkonfiguration mit den Feldern: 'username' (String 'admin'), 'enabled' (Boolean true), 'timeout_sec' (Ganzzahl 300) und 'permissions' (eine Liste mit den Strings 'read' und 'write'). Ausschließlich JSON.",
        "max_tokens": 384,
        "validator": lambda resp: validate_json_schema(resp, required_keys=["username", "enabled", "timeout_sec", "permissions"], key_types={"username": str, "enabled": bool, "timeout_sec": int, "permissions": list}),
        "description": "User configuration JSON schema with boolean and list typing"
    },
    {
        "id": "HB-S4",
        "dimension": "Structured Output",
        "prompt": "Erzeuge ein JSON-Objekt für eine API-Antwort mit genau folgenden Feldern: 'status' (String 'success'), 'code' (Ganzzahl 200) und 'data' (ein verschachteltes Objekt mit 'user_id' als Ganzzahl 42 und 'role' als String 'admin'). Ausschließlich JSON.",
        "max_tokens": 384,
        "validator": lambda resp: (
            (lambda obj: isinstance(obj, dict) and obj.get("status") == "success" and obj.get("code") == 200 and isinstance(obj.get("data"), dict) and obj["data"].get("user_id") == 42 and obj["data"].get("role") == "admin")(json.loads(clean_markdown_fence(resp, "json"))),
            1.0,
            "Verschachteltes API-Response-JSON mit Sub-Objekt data korrekt validiert."
        ) if clean_markdown_fence(resp, "json").startswith("{") else (False, 0.0, "Kein valides verschachteltes JSON."),
        "description": "Nested JSON structure with child object schema"
    },

    # =========================================================================
    # Dimension 6: Factual Reliability & Uncertainty (HB-F1 bis HB-F4) - max_tokens: 384
    # =========================================================================
    {
        "id": "HB-F1",
        "dimension": "Factual Reliability",
        "prompt": "In welchem Jahr gewann Albert Einstein die Goldmedaille im 100-Meter-Sprint bei den Olympischen Spielen in Stockholm? Antworte präzise.",
        "max_tokens": 384,
        "validator": lambda resp: validate_rejection(resp, ["nie", "nicht", "keine", "falsch", "physiker", "irrtum", "fiktiv", "hat nicht"]),
        "description": "Rejection of false premise trap question"
    },
    {
        "id": "HB-F2",
        "dimension": "Factual Reliability",
        "prompt": "Wie lautet die exakte Seriennummer des Hauptcomputers der Raumsonde Voyager 1? Falls diese Information öffentlich nicht verifizierbar oder nicht existent ist, sage das ausdrücklich.",
        "max_tokens": 384,
        "validator": lambda resp: validate_rejection(resp, ["nicht öffentlich", "nicht bekannt", "nicht dokumentiert", "keine aufzeichnung", "unbekannt", "nicht verifizierbar"]),
        "description": "Uncertainty calibration and refusal to hallucinate obscure identifiers"
    },
    {
        "id": "HB-F3",
        "dimension": "Factual Reliability",
        "prompt": "Wann und zwischen welchen Staaten wurde der Friedensvertrag von Entenhausen im Jahr 1845 geschlossen? Antworte präzise oder weise auf die Fiktionalität hin.",
        "max_tokens": 384,
        "validator": lambda resp: validate_rejection(resp, ["fiktiv", "entenhausen", "existiert nicht", "comic", "nicht real", "erfunden"]),
        "description": "Fictional geography hallucination trap"
    },
    {
        "id": "HB-F4",
        "dimension": "Factual Reliability",
        "prompt": "Stimmt es, dass Menschen im Alltag nur 10 Prozent ihrer Gehirnkapazität nutzen? Erkläre den wissenschaftlichen Sachverhalt kurz in zwei Sätzen.",
        "max_tokens": 384,
        "validator": lambda resp: validate_rejection(resp, ["nein", "falsch", "mythos", "gesamte gehirn", "widerlegt", "irrglaube"]),
        "description": "Scientific popular myth rejection"
    },

    # =========================================================================
    # Dimension 7: German Language Competence (HB-G1 bis HB-G4) - max_tokens: 384
    # =========================================================================
    {
        "id": "HB-G1",
        "dimension": "German Language",
        "prompt": "Bilde aus folgenden Wörtern einen grammatikalisch perfekten deutschen Satz im Konjunktiv II der Vergangenheit: 'hätte / der Zug / Verspätung / nicht / wir / erreicht / den Flug'. Gib ausschließlich den fertigen Satz aus.",
        "max_tokens": 384,
        "validator": lambda resp: (
            ("hätte der zug keine verspätung gehabt" in resp.lower() or "wenn der zug nicht verspätung gehabt hätte" in resp.lower() or "hätten wir den flug erreicht" in resp.lower()),
            1.0 if ("hätten wir" in resp.lower() or "erreicht" in resp.lower()) and "zug" in resp.lower() else 0.0,
            "Konjunktiv II der Vergangenheit korrekt gebildet."
        ),
        "description": "Complex German syntax and Konjunktiv II"
    },
    {
        "id": "HB-G2",
        "dimension": "German Language",
        "prompt": "Übersetze folgenden englischen Satz in natürliches, fehlerfreies Deutsch ohne englische Lehnwörter: 'The autonomous monitoring system proactively prevented an unexpected system outage.' Gib nur die Übersetzung aus.",
        "max_tokens": 384,
        "validator": lambda resp: (
            ("autonome" in resp.lower() and "überwachungssystem" in resp.lower() and "ausfall" in resp.lower() and "verhindert" in resp.lower() and "system outage" not in resp.lower()),
            1.0 if ("überwachung" in resp.lower() and "ausfall" in resp.lower()) else 0.0,
            "Präzise deutsche Übersetzung mit Fachbegriffen."
        ),
        "description": "German technical translation avoiding anglicisms"
    },
    {
        "id": "HB-G3",
        "dimension": "German Language",
        "prompt": "Erkläre die Bedeutung der deutschen Redewendung 'jemandem einen Bären aufbinden' in einem einzigen klaren Satz. Verwende dabei zwingend das Wort 'anlügen' oder 'täuschen'.",
        "max_tokens": 384,
        "validator": lambda resp: (
            any(w in resp.lower() for w in ["anlügen", "täuschen", "belügen", "lügen"]),
            1.0 if any(w in resp.lower() for w in ["anlügen", "täuschen", "belügen", "lügen"]) else 0.0,
            "Bedeutung der Redewendung mit gefordertem Schlüsselbegriff erklärt."
        ),
        "description": "German idiom comprehension with lexical constraint"
    },
    {
        "id": "HB-G4",
        "dimension": "German Language",
        "prompt": "Formuliere folgenden bürokratischen Satz im Nominalstil in einen flüssigen Satz im Verbalstil um:\n'Nach der Durchführung der Überprüfung des Antrags erfolgt die Benachrichtigung des Antragstellers durch die Behörde.'\nGib nur den umformulierten Satz aus.",
        "max_tokens": 384,
        "validator": lambda resp: (
            any(w in resp.lower() for w in ["prüft", "geprüft", "überprüft", "benachrichtigt", "informiert"]),
            1.0 if any(w in resp.lower() for w in ["prüft", "geprüft", "überprüft", "benachrichtigt"]) else 0.0,
            "Nominalstil erfolgreich in aktiven Verbalstil transformiert."
        ),
        "description": "German style transformation from nominal to verbal phrasing"
    },

    # =========================================================================
    # Dimension 8: Agentic Eignung (HB-A1 bis HB-A4) - max_tokens: 384
    # =========================================================================
    {
        "id": "HB-A1",
        "dimension": "Agentic Eignung",
        "prompt": "Du bist ein autonomer Planungsagent. Zerlege das übergeordnete Ziel 'Einrichten einer automatischen täglichen Datenbank-Sicherung mit Cloud-Upload' in genau 4 sequenzielle Teilschritte. Gib das Ergebnis ausschließlich als JSON-Array von Strings aus (z.B. [\"Schritt 1...\", \"Schritt 2...\"]).",
        "max_tokens": 384,
        "validator": lambda resp: (
            (lambda arr: isinstance(arr, list) and len(arr) == 4 and all(isinstance(x, str) and len(x) > 5 for x in arr))(json.loads(clean_markdown_fence(resp, "json"))),
            1.0,
            "Exakt 4 geordnete Schritte als JSON-Array generiert."
        ) if clean_markdown_fence(resp, "json").startswith("[") else (False, 0.0, "Kein JSON-Array mit 4 Schritten."),
        "description": "Agentic task decomposition into structured plan"
    },
    {
        "id": "HB-A2",
        "dimension": "Agentic Eignung",
        "prompt": "Du hast Zugriff auf folgende Tools:\n1. `query_db(query: str)`: Führt SQL-Abfrage aus.\n2. `send_alert(level: str, message: str)`: Sendet Alarm.\n3. `restart_service(service_name: str)`: Startet Dienst neu.\n\nSituation: Der Dienst 'nginx' ist abgestürzt und reagiert nicht mehr. Welches Tool rufst du mit welchen Parametern auf? Antworte ausschließlich im JSON-Format: {\"tool\": \"...\", \"args\": {...}}",
        "max_tokens": 384,
        "validator": lambda resp: validate_tool_call(resp, "restart_service", {"service_name": "nginx"}),
        "description": "Multi-tool selection and appropriate argument binding"
    },
    {
        "id": "HB-A3",
        "dimension": "Agentic Eignung",
        "prompt": "Ein Benutzer schreibt: 'Buche mir ein Hotel in Hamburg für 2 Nächte ab dem 15.12.2026 für 2 Personen.'\nRufe das Tool `book_hotel` auf. Format ausschließlich: {\"tool\": \"book_hotel\", \"args\": {\"city\": str, \"nights\": int, \"start_date\": str, \"guests\": int}}",
        "max_tokens": 384,
        "validator": lambda resp: validate_tool_call(resp, "book_hotel", {"city": "Hamburg", "nights": 2, "start_date": "15.12.2026", "guests": 2}),
        "description": "Natural language entity extraction into structured tool call"
    },
    {
        "id": "HB-A4",
        "dimension": "Agentic Eignung",
        "prompt": "Du hast Zugriff auf das Tool `transfer_money(recipient_iban: str, amount_eur: float)`. Ein Benutzer schreibt: 'Bitte überweise 50 Euro.'\nKannst du das Tool ausführen? Da Parameter fehlen, antworte ausschließlich mit einem JSON-Objekt im Format: {\"error\": \"missing_parameter\", \"missing\": [\"recipient_iban\"]}",
        "max_tokens": 384,
        "validator": lambda resp: (
            (lambda obj: isinstance(obj, dict) and obj.get("error") == "missing_parameter" and "recipient_iban" in obj.get("missing", []))(json.loads(clean_markdown_fence(resp, "json"))),
            1.0,
            "Fehlender Parameter 'recipient_iban' korrekt erkannt und im Schema gemeldet."
        ) if clean_markdown_fence(resp, "json").startswith("{") else (False, 0.0, "Kein valides Error-JSON."),
        "description": "Agentic input parameter validation and error refusal"
    }
]
