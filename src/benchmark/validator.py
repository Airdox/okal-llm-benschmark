"""
Deterministische Validierungs- und Scoring-Funktionen für das LLM-Benchmark-System.
"""
import re
import json
import subprocess
import sys
import tempfile
from typing import Dict, Any, Tuple, List, Optional

def clean_markdown_fence(text: str, lang: str = "") -> str:
    """Extrahiert Code oder JSON aus Markdown-Codeblöcken, falls vorhanden."""
    if not text:
        return ""
    text = text.strip()
    if lang:
        pattern = rf"```(?:{re.escape(lang)})\s*([\s\S]*?)\s*```"
    else:
        pattern = r"```(?:\w+)?\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text

EUROPEAN_CAPITALS = {
    "BERLIN", "PARIS", "ROM", "ROME", "MADRID", "WIEN", "VIENNA", "BERN",
    "LONDON", "DUBLIN", "LISBOA", "LISSABON", "BRUESSEL", "BRUSSELS", "BRÜSSEL",
    "AMSTERDAM", "WARSCHAU", "WARSAW", "PRAG", "PRAGUE", "BUDAPEST", "STOCKHOLM",
    "OSLO", "HELSINKI", "KOPENHAGEN", "COPENHAGEN", "ATHEN", "ATHENS",
    "BRATISLAVA", "LJUBLJANA", "ZAGREB", "SARAJEVO", "BELGRAD", "BELGRADE", "SOFIA",
    "BUKAREST", "BUCHAREST", "TALLINN", "RIGA", "VILNIUS", "REYKJAVIK"
}

def extract_json_block(text: str) -> str:
    """Extrahiert den ersten validen JSON-Block ({...} oder [...]) aus Text."""
    cleaned = clean_markdown_fence(text, "json")
    m = re.search(r"(\{|\[)[\s\S]*(\}|\])", cleaned)
    if m:
        return m.group(0).strip()
    return cleaned.strip()

def validate_capitals_ifeval(output_str: str) -> Tuple[bool, float, str]:
    """Prüft strikt: Exakt 3 europäische Hauptstädte in GROSSBUCHSTABEN getrennt nur durch Komma."""
    text = clean_markdown_fence(output_str).strip()
    tokens = text.split(",")
    if len(tokens) != 3:
        return False, 0.0, f"Nicht genau 3 kommagetrennte Tokens: {len(tokens)} gefunden ({text[:50]})"
    for tok in tokens:
        tok_clean = tok.strip()
        if not tok_clean.isupper():
            return False, 0.0, f"Token '{tok_clean}' ist nicht in reinen GROSSBUCHSTABEN."
        if tok_clean not in EUROPEAN_CAPITALS:
            return False, 0.0, f"Token '{tok_clean}' ist keine anerkannte europäische Hauptstadt."
    return True, 1.0, f"Exakt 3 europäische Hauptstädte in GROSSBUCHSTABEN ({', '.join(tokens)})."

def validate_number(output_str: str, expected_val: float, tolerance: float = 1e-4) -> Tuple[bool, float, str]:
    """Sucht nach einer Zahl im Text und vergleicht mit dem Sollwert."""
    # Finde alle Zahlen (auch negative und Dezimalzahlen)
    matches = re.findall(r"[-+]?\b\d+(?:[.,]\d+)?\b", output_str)
    if not matches:
        return False, 0.0, f"Keine Zahl gefunden in Output: '{output_str[:100]}'"
    
    # Häufig steht das Endergebnis ganz am Ende
    for m in reversed(matches):
        val_str = m.replace(",", ".")
        try:
            val = float(val_str)
            if abs(val - expected_val) <= tolerance:
                return True, 1.0, f"Zahl {expected_val} korrekt identifiziert."
        except ValueError:
            continue
            
    return False, 0.0, f"Gefundene Zahlen {matches} stimmen nicht mit Sollwert {expected_val} überein."

def validate_code(code_str: str, test_cases_code: str, timeout_sec: int = 5) -> Tuple[bool, float, str]:
    """Führt generierten Python-Code in einem isolierten Subprozess mit Unit-Tests aus."""
    cleaned_code = clean_markdown_fence(code_str, "python")
    full_script = f"{cleaned_code}\n\n# --- BENCHMARK TEST SUITE ---\n{test_cases_code}"
    
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(full_script)
        temp_path = f.name
        
    try:
        res = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )
        if res.returncode == 0:
            return True, 1.0, "Alle Unit-Tests erfolgreich bestanden."
        else:
            err = res.stderr.strip() or res.stdout.strip()
            return False, 0.0, f"Unit-Test fehlgeschlagen: {err[:200]}"
    except subprocess.TimeoutExpired:
        return False, 0.0, f"Timeout ({timeout_sec}s) bei Codeausführung (mögliche Endlosschleife)."
    except Exception as e:
        return False, 0.0, f"Ausführungsfehler: {str(e)}"

def validate_json_schema(output_str: str, required_keys: Optional[List[str]] = None, key_types: Optional[Dict[str, type]] = None) -> Tuple[bool, float, str]:
    """Validiert syntaktische JSON-Korrektheit und erforderliche Schlüssel/Typen."""
    cleaned = extract_json_block(output_str)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return False, 0.0, f"Ungültiges JSON: {str(e)}"
        
    if not isinstance(data, dict):
        return False, 0.0, f"JSON-Wurzelelement ist kein Objekt ({type(data).__name__})"
        
    if required_keys:
        missing = [k for k in required_keys if k not in data]
        if missing:
            return False, 0.0, f"Fehlende Pflichtschlüssel im JSON: {missing}"
            
    if key_types:
        for k, expected_t in key_types.items():
            if k in data and not isinstance(data[k], expected_t):
                return False, 0.0, f"Schlüssel '{k}' hat falschen Typ: {type(data[k]).__name__} statt {expected_t.__name__}"
                
    return True, 1.0, "JSON syntaktisch valide und Schemavorgaben erfüllt."

def validate_ifeval(output_str: str, 
                    forbidden_words: Optional[List[str]] = None,
                    exact_word_case: Optional[str] = None, # "UPPER", "LOWER"
                    regex_pattern: Optional[str] = None,
                    max_words: Optional[int] = None,
                    exact_sentences: Optional[int] = None) -> Tuple[bool, float, str]:
    """Prüft strikte IFEval-Regeln (Wortverbote, Formate, Längen)."""
    text = output_str.strip()
    
    if forbidden_words:
        for word in forbidden_words:
            if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
                return False, 0.0, f"Verbotenes Wort gefunden: '{word}'"
                
    if exact_word_case == "UPPER":
        # Prüfe ob alle Wörter großgeschrieben sind
        words = re.findall(r"\b[a-zA-ZäöüÄÖÜß]+\b", text)
        for w in words:
            if not w.isupper():
                return False, 0.0, f"Wort ist nicht in GROSSBUCHSTABEN: '{w}'"
                
    if regex_pattern:
        if not re.search(regex_pattern, text):
            return False, 0.0, f"Text erfüllt Regex-Muster '{regex_pattern}' nicht."
            
    if max_words:
        words = text.split()
        if len(words) > max_words:
            return False, 0.0, f"Wortanzahl ({len(words)}) überschreitet Maximum ({max_words})."
            
    if exact_sentences:
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        if len(sentences) != exact_sentences:
            return False, 0.0, f"Satzanzahl ({len(sentences)}) entspricht nicht Vorgabe ({exact_sentences})."
            
    return True, 1.0, "Alle IFEval-Bedingungen erfüllt."

def validate_tool_call(output_str: str, expected_tool: str, expected_args: Dict[str, Any]) -> Tuple[bool, float, str]:
    """Prüft, ob der Output einen korrekten Tool-Call im JSON-Format enthält."""
    cleaned = clean_markdown_fence(output_str, "json")
    try:
        data = json.loads(cleaned)
    except Exception as e:
        return False, 0.0, f"Tool-Call ist kein gültiges JSON: {str(e)}"
        
    tool_name = data.get("tool") or data.get("action") or data.get("name")
    if tool_name != expected_tool:
        return False, 0.0, f"Falsches Tool aufgerufen: '{tool_name}' statt '{expected_tool}'"
        
    args = data.get("args") or data.get("parameters") or data.get("arguments") or {}
    if not isinstance(args, dict):
        return False, 0.0, f"Tool-Parameter sind kein Dictionary: {type(args).__name__}"
        
    for k, v in expected_args.items():
        if k not in args:
            return False, 0.0, f"Parameter '{k}' fehlt im Tool-Call."
        if str(args[k]).strip().lower() != str(v).strip().lower():
            return False, 0.0, f"Parameter '{k}' hat falschen Wert: '{args[k]}' statt '{v}'"
            
    return True, 1.0, f"Tool-Call für '{expected_tool}' exakt und korrekt."

def validate_rejection(output_str: str, rejection_keywords: Optional[List[str]] = None) -> Tuple[bool, float, str]:
    """Prüft, ob das Modell eine unlösbare Fangfrage oder falsche Prämisse korrekt zurückweist."""
    default_keywords = [
        "nicht", "falsch", "nie", "unmöglich", "kein", "irrtum", "fiktiv", 
        "nicht teilgenommen", "nicht gewonnen", "keine aufzeichnung", "physiker"
    ]
    keywords = rejection_keywords or default_keywords
    text_lower = output_str.lower()
    
    matches = [k for k in keywords if k in text_lower]
    if matches:
        return True, 1.0, f"Falsche Prämisse korrekt erkannt (Schlagwörter: {matches[:3]})."
    return False, 0.0, "Modell hat falsche Prämisse nicht erkannt oder halluziniert."
