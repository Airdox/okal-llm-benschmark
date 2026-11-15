"""
Definition aller Benchmark-Aufgaben und Validierungs-Zuordnungen für Stufe 1 und Stufe 2.
"""
import re
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
    # Dimension 1: Reasoning
    {
        "id": "HB-R1",
        "dimension": "Reasoning",
        "prompt": "Ein Fahrradhändler hat 45 Fahrräder auf Lager. Am Montag verkauft er 12 Räder. Am Dienstag erhält er eine Neulieferung von 20 Rädern. Am Mittwoch verkauft er ein Drittel seines gesamten aktuellen Bestands. Wie viele Fahrräder hat er am Ende des Mittwochs? Antworte ausschließlich mit der Zahl.",
        "max_tokens": 128,
        # Berechnung: 45 - 12 = 33; 33 + 20 = 53; 53 ist nicht glatt durch 3 teilbar, warte: 
        # Nehmen wir glatte Zahlen: 45 - 15 = 30; + 18 = 48; 48 - (48/3 = 16) = 32!
        # Lass uns den Prompt glatt anpassen:
        "prompt": "Ein Fahrradhändler hat 45 Fahrräder auf Lager. Am Montag verkauft er 15 Räder. Am Dienstag erhält er eine Neulieferung von 18 Rädern. Am Mittwoch verkauft er genau ein Drittel seines aktuellen Bestands. Wie viele Fahrräder hat er am Ende des Mittwochs noch? Antworte nur mit der finalen Zahl.",
        "validator": lambda resp: validate_number(resp, 32.0),
        "description": "Multi-step arithmetic with fractions: ((45-15)+18) * 2/3 = 32"
    },
    {
        "id": "HB-R2",
        "dimension": "Reasoning",
        "prompt": "Vier Freunde kommen bei einem Rennen ins Ziel: Anna, Ben, Clara und David. Clara war schneller als Ben. David kam direkt nach Anna ins Ziel. Ben kam vor Anna ins Ziel. Wer hat das Rennen gewonnen? Antworte nur mit dem Namen.",
        "max_tokens": 64,
        # Logik: Clara > Ben; Ben > Anna; Anna > David. Reihenfolge: Clara, Ben, Anna, David. Gewinnerin: Clara.
        "validator": lambda resp: ("clara" in resp.lower() and "ben" not in resp.lower().replace("clara", ""), 1.0 if "clara" in resp.lower() else 0.0, "Clara als Siegerin identifiziert."),
        "description": "Relational logical deduction"
    },
    # Dimension 2: Coding
    {
        "id": "HB-C1",
        "dimension": "Coding",
        "prompt": "Implementiere in Python eine Funktion `compress_string(s: str) -> str`, die aufeinanderfolgende gleiche Zeichen durch das Zeichen gefolgt von der Anzahl ersetzt (z.B. 'aabcccccaaa' -> 'a2b1c5a3'). Bei leerem String soll '' zurückgegeben werden. Gib nur den Python-Codeblock zurück.",
        "max_tokens": 384,
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
        "max_tokens": 256,
        "validator": lambda resp: validate_code(resp, """
assert find_max([]) is None
assert find_max([-5, -2, -9]) == -2
assert find_max([10, 4, 25, 2]) == 25
assert find_max([0]) == 0
"""),
        "description": "Bugfixing function handling negative numbers and empty lists"
    },
    # Dimension 3: Comprehension & Extraction
    {
        "id": "HB-T1",
        "dimension": "Comprehension",
        "prompt": "Lies folgenden Textauszug und extrahiere die Projektleiterin, das genehmigte Gesamtbudget und das Startdatum:\n'Im gestrigen Lenkungskreis wurde beschlossen, dass Dr. Sabine Weber die Leitung für das Projekt Titan übernimmt, nachdem Herr Müller abgesprungen war. Ursprünglich waren 300.000 Euro im Gespräch, final genehmigt wurden jedoch exakt 450.000 Euro. Die operative Arbeit startet planmäßig am 1. Oktober 2026.'\nAntworte als kompakte Aufzählung.",
        "max_tokens": 150,
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
        "max_tokens": 80,
        "validator": lambda resp: (
            ("20. juli" in resp.lower() or "21. juli" in resp.lower()),
            1.0 if ("20. juli" in resp.lower() or "21. juli" in resp.lower()) else 0.0,
            "Mondlandung/Betreten Datum (20./21. Juli 1969) korrekt synthetisiert."
        ),
        "description": "Multi-hop temporal reasoning from text"
    },
    # Dimension 4: Instruction Following (IFEval)
    {
        "id": "HB-I1",
        "dimension": "Instruction Following",
        "prompt": "Erkläre das Prinzip der Schwerkraft in genau zwei vollständigen Sätzen. Bedingung: Das Wort 'Erde' oder 'Planeten' darf im gesamten Text überhaupt nicht vorkommen.",
        "max_tokens": 128,
        "validator": lambda resp: validate_ifeval(resp, forbidden_words=["Erde", "Planeten", "Planet", "Planetenmasse"], exact_sentences=2),
        "description": "Negative constraint and exact sentence count"
    },
    {
        "id": "HB-I2",
        "dimension": "Instruction Following",
        "prompt": "Erstelle eine Liste mit genau vier Punkten. Jeder Punkt muss mit dem Präfix 'Phase:' beginnen und darf maximal 6 Wörter umfassen. Keine Einleitung, kein Schlusssatz.",
        "max_tokens": 150,
        "validator": lambda resp: (
            (resp.count("Phase:") == 4 and all(len(line.split()) <= 8 for line in resp.strip().split("\n") if line.strip())),
            1.0 if (resp.count("Phase:") == 4 and all(len(line.split()) <= 8 for line in resp.strip().split("\n") if line.strip())) else 0.0,
            "4 Punkte mit Präfix 'Phase:' und Längenlimit eingehalten."
        ),
        "description": "Strict formatting and length limit per bullet"
    },
    # Dimension 5: Structured Outputs
    {
        "id": "HB-S1",
        "dimension": "Structured Output",
        "prompt": "Gib ein valides JSON-Objekt zurück, das einen Webserver beschreibt mit den Feldern: 'host' (String 'localhost'), 'port' (Ganzzahl 8080), 'ssl' (Boolean true) und 'routes' (eine Liste mit den Strings '/' und '/api'). Ausschließlich JSON, keine Markdown-Erklärungen außerhalb des JSON.",
        "max_tokens": 180,
        "validator": lambda resp: validate_json_schema(resp, required_keys=["host", "port", "ssl", "routes"], key_types={"host": str, "port": int, "ssl": bool, "routes": list}),
        "description": "Nested JSON schema with strict types (str, int, bool, list)"
    },
    {
        "id": "HB-S2",
        "dimension": "Structured Output",
        "prompt": "Wandle folgende Daten in ein JSON-Array von Objekten um:\n1. Sensor Alpha, Temperatur 22.5\n2. Sensor Beta, Temperatur 19.8\nJedes Objekt muss die Schlüssel 'sensor' (String) und 'temp' (Float) besitzen. Nur JSON.",
        "max_tokens": 150,
        "validator": lambda resp: (
            (lambda d: isinstance(d, list) and len(d) == 2 and all("sensor" in x and "temp" in x for x in d))(json.loads(clean_markdown_fence(resp, "json"))),
            1.0,
            "JSON-Array mit 2 Objekten und korrekten Feldern erzeugt."
        ) if clean_markdown_fence(resp, "json").startswith("[") else (False, 0.0, "Kein JSON-Array."),
        "description": "Tabular text to JSON array transformation"
    },
    # Dimension 6: Factual Reliability & Uncertainty
    {
        "id": "HB-F1",
        "dimension": "Factual Reliability",
        "prompt": "In welchem Jahr gewann Albert Einstein die Goldmedaille im 100-Meter-Sprint bei den Olympischen Spielen in Stockholm? Antworte präzise.",
        "max_tokens": 100,
        "validator": lambda resp: validate_rejection(resp, ["nie", "nicht", "keine", "falsch", "physiker", "irrtum", "fiktiv", "hat nicht"]),
        "description": "Rejection of false premise trap question"
    },
    {
        "id": "HB-F2",
        "dimension": "Factual Reliability",
        "prompt": "Wie lautet die exakte Seriennummer des Hauptcomputers der Raumsonde Voyager 1? Falls diese Information öffentlich nicht verifizierbar oder nicht existent ist, sage das ausdrücklich.",
        "max_tokens": 100,
        "validator": lambda resp: validate_rejection(resp, ["nicht öffentlich", "nicht bekannt", "nicht dokumentiert", "keine aufzeichnung", "unbekannt", "nicht verifizierbar"]),
        "description": "Uncertainty calibration and refusal to hallucinate obscure identifiers"
    },
    # Dimension 7: German Language Competence
    {
        "id": "HB-G1",
        "dimension": "German Language",
        "prompt": "Bilde aus folgenden Wörtern einen grammatikalisch perfekten deutschen Satz im Konjunktiv II der Vergangenheit: 'hätte / der Zug / Verspätung / nicht / wir / erreicht / den Flug'. Gib ausschließlich den fertigen Satz aus.",
        "max_tokens": 80,
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
        "max_tokens": 90,
        "validator": lambda resp: (
            ("autonome" in resp.lower() and "überwachungssystem" in resp.lower() and "ausfall" in resp.lower() and "verhindert" in resp.lower() and "system outage" not in resp.lower()),
            1.0 if ("überwachung" in resp.lower() and "ausfall" in resp.lower()) else 0.0,
            "Präzise deutsche Übersetzung mit Fachbegriffen."
        ),
        "description": "German technical translation avoiding anglicisms"
    },
    # Dimension 8: Agentic Eignung (Planning & Tool Calling)
    {
        "id": "HB-A1",
        "dimension": "Agentic Eignung",
        "prompt": "Du bist ein autonomer Planungsagent. Zerlege das übergeordnete Ziel 'Einrichten einer automatischen täglichen Datenbank-Sicherung mit Cloud-Upload' in genau 4 sequenzielle Teilschritte. Gib das Ergebnis ausschließlich als JSON-Array von Strings aus (z.B. [\"Schritt 1...\", \"Schritt 2...\"]).",
        "max_tokens": 200,
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
        "max_tokens": 128,
        "validator": lambda resp: validate_tool_call(resp, "restart_service", {"service_name": "nginx"}),
        "description": "Multi-tool selection and appropriate argument binding"
    }
]
