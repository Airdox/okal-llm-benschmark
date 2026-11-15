"""
Unit-Tests für die Validierungsfunktionen des Benchmark-Systems.
"""
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.benchmark.validator import (
    clean_markdown_fence,
    extract_json_block,
    validate_number,
    validate_code,
    validate_json_schema,
    validate_ifeval,
    validate_capitals_ifeval,
    validate_tool_call,
    validate_rejection
)

def test_clean_markdown_fence():
    assert clean_markdown_fence("```json\n{\"a\": 1}\n```", "json") == "{\"a\": 1}"
    assert clean_markdown_fence("```python\nprint(1)\n```") == "print(1)"
    assert clean_markdown_fence("Plain text") == "Plain text"

def test_validate_number():
    passed, score, _ = validate_number("Das Ergebnis ist 57 Flaschen.", 57.0)
    assert passed and score == 1.0

    passed, score, _ = validate_number("Es sind 32,0 Fahrräder.", 32.0)
    assert passed and score == 1.0

    passed, score, _ = validate_number("Keine Zahl hier.", 57.0)
    assert not passed and score == 0.0

def test_validate_code():
    valid_code = "def is_even(n):\n    return n % 2 == 0"
    test_cases = "assert is_even(2) is True\nassert is_even(3) is False"
    passed, score, _ = validate_code(valid_code, test_cases)
    assert passed and score == 1.0

    invalid_code = "def is_even(n):\n    return False"
    passed, score, _ = validate_code(invalid_code, test_cases)
    assert not passed and score == 0.0

def test_validate_json_schema():
    valid_json = '{"name": "Benchmark", "score": 100}'
    passed, score, _ = validate_json_schema(valid_json, required_keys=["name", "score"], key_types={"name": str, "score": int})
    assert passed and score == 1.0

    invalid_type = '{"name": "Benchmark", "score": "100"}'
    passed, score, _ = validate_json_schema(invalid_type, key_types={"score": int})
    assert not passed

def test_validate_ifeval():
    # Regex format check
    passed, score, _ = validate_ifeval("BERLIN,PARIS,MADRID", regex_pattern=r"^[A-ZÄÖÜ]+,[A-ZÄÖÜ]+,[A-ZÄÖÜ]+$")
    assert passed and score == 1.0

    # Capital whitelist check (Auflage C)
    passed, score, _ = validate_capitals_ifeval("BERLIN,PARIS,MADRID")
    assert passed and score == 1.0

    # Negative test with non-capitals
    passed, score, _ = validate_capitals_ifeval("APFEL,BIRNE,BANANE")
    assert not passed and score == 0.0

    # Forbidden word check
    passed, score, _ = validate_ifeval("Die Erde ist rund.", forbidden_words=["Erde"])
    assert not passed

def test_validate_tool_call():
    call_json = '{"tool": "get_weather", "args": {"city": "Berlin"}}'
    passed, score, _ = validate_tool_call(call_json, "get_weather", {"city": "Berlin"})
    assert passed and score == 1.0

    wrong_tool = '{"tool": "get_news", "args": {"city": "Berlin"}}'
    passed, score, _ = validate_tool_call(wrong_tool, "get_weather", {"city": "Berlin"})
    assert not passed

def test_validate_rejection():
    passed, score, _ = validate_rejection("Albert Einstein hat nie an Olympischen Spielen teilgenommen.")
    assert passed and score == 1.0

    passed, score, _ = validate_rejection("Er gewann die Medaille 1912 mit einer Zeit von 10,2 Sekunden.")
    assert not passed and score == 0.0

if __name__ == "__main__":
    print("Führe Unit-Tests aus...")
    test_clean_markdown_fence()
    test_validate_number()
    test_validate_code()
    test_validate_json_schema()
    test_validate_ifeval()
    test_validate_tool_call()
    test_validate_rejection()
    print("Alle Validierungstests erfolgreich bestanden! ✅")
