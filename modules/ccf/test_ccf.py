"""CCF test suite. V-gate naming per rules/python/testing.md convention.

Hermetic: no real network calls, no real API keys, no filesystem writes
outside a pytest tmp_path fixture. Each V-gate follows Arrange/Act/Assert.
"""
from __future__ import annotations

import pytest

from modules.ccf import config_schema, contract_engine, model_adapter, prompt_compiler, trademark_scanner


# --- Contract Engine ---------------------------------------------------

def test_contract_engine_valid_brief_produces_full_spec():
    # Arrange
    brief = (
        "Brand: Aperture Coffee\n"
        "Industry: specialty coffee roasting\n"
        "Audience: urban professionals aged 25-40\n"
        "Values: craftsmanship, sustainability, warmth\n"
        "must: use warm earth tones\n"
        "must_not: use any shade of purple\n"
    )

    # Act
    spec, questions = contract_engine.compile_spec(brief)

    # Assert
    assert questions == []
    assert spec.brand_name == "Aperture Coffee"
    assert spec.industry == "specialty coffee roasting"
    assert spec.constraints["must"] == ["use warm earth tones"]
    assert spec.constraints["must_not"] == ["use any shade of purple"]
    print("V-CONTRACT-ENGINE-VALID")


def test_contract_engine_incomplete_brief_blocks_with_exact_questions():
    # Arrange
    brief = "Brand: Aperture Coffee\nWe want something warm and modern."

    # Act
    spec, questions = contract_engine.compile_spec(brief)

    # Assert
    assert spec is None
    missing = {q["field"] for q in questions}
    assert missing == {"industry", "audience"}
    print("V-CONTRACT-ENGINE-AMBIGUITY")


# --- Config Schema -------------------------------------------------------

def _valid_config():
    return {
        "schema_version": "1.0",
        "theme": "modern", "accent": "#E85D3D", "headFont": "Poppins",
        "labels": ["primary", "icon"],
        "concepts": [{
            "id": "spark", "font": "Poppins Bold", "colours": ["#E85D3D", "#1A1A1A"],
            "bg": "#FFFFFF", "wordmark": "Aperture", "avoid": ["Airbnb", "Uber"],
            "icon": "a four-point coral spark",
        }],
    }


def test_config_schema_valid_config_passes():
    # Arrange / Act
    ok, errors = config_schema.validate_config(_valid_config())

    # Assert
    assert ok
    assert errors == []
    print("V-CONFIG-SCHEMA-VALID")


def test_config_schema_invalid_config_fails_descriptively():
    # Arrange
    bad = {
        "schema_version": "1.0",
        "concepts": [{"id": "thread", "font": "Poppins", "colours": ["#000"],
                       "bg": "#FFF", "avoid": "Airbnb"}],
    }

    # Act
    ok, errors = config_schema.validate_config(bad)

    # Assert
    assert not ok
    assert any("wordmark" in e for e in errors)
    assert any("icon" in e for e in errors)
    assert any("avoid" in e for e in errors)
    print("V-CONFIG-SCHEMA-INVALID")


# --- Prompt Compiler ------------------------------------------------------

_SPEC = contract_engine.CreativeSpecification(
    brand_name="Aperture Coffee", industry="coffee", audience="pros", values=["craft"]
)
_GLOBALS = {"theme": "modern", "accent": "#E85D3D", "headFont": "Poppins", "labels": ["primary"]}
_CONCEPT_CLEAN = {
    "id": "spark", "font": "Poppins Bold", "colours": ["#E85D3D", "#1A1A1A"],
    "bg": "#FFFFFF", "wordmark": "Aperture", "avoid": [], "icon": "a four-point coral spark",
}
_CONCEPT_COLLISION = {
    "id": "thread", "font": "Poppins", "colours": ["#000000"], "bg": "#FFFFFF",
    "wordmark": "Aperture", "avoid": [],
    "icon": "a continuous rounded line that loops back on itself",
}


def test_prompt_compiler_determinism():
    # Arrange / Act
    first = prompt_compiler.compile_prompt(_CONCEPT_CLEAN, _SPEC, _GLOBALS)
    second = prompt_compiler.compile_prompt(_CONCEPT_CLEAN, _SPEC, _GLOBALS)

    # Assert
    assert first["prompt"] == second["prompt"]
    assert first["input_hash"] == second["input_hash"]
    assert "Aperture Coffee" in first["prompt"]
    print("V-PROMPT-COMPILER-DETERMINISM")


# --- Trademark Collision Scanner ------------------------------------------

def test_trademark_scanner_airbnb_belo_case_never_passes():
    # Arrange -- CCF-F01, the founding failure this component exists to catch
    record = prompt_compiler.compile_prompt(_CONCEPT_COLLISION, _SPEC, _GLOBALS)

    # Act
    verdict = trademark_scanner.scan(
        "thread", _CONCEPT_COLLISION["icon"], record["avoid_list"]["semantic"]
    )

    # Assert
    assert verdict["verdict"] in ("WARN", "BLOCK")
    assert verdict["nearest_known_mark"] == "Airbnb"
    print("V-TRADEMARK-SCANNER-F01")


def test_trademark_scanner_clean_concept_passes():
    # Arrange
    record = prompt_compiler.compile_prompt(_CONCEPT_CLEAN, _SPEC, _GLOBALS)

    # Act
    verdict = trademark_scanner.scan(
        "spark", _CONCEPT_CLEAN["icon"], record["avoid_list"]["semantic"]
    )

    # Assert
    assert verdict["verdict"] == "PASS"
    print("V-TRADEMARK-SCANNER-PASS")


# --- Model Adapter Layer ---------------------------------------------------

def test_model_adapter_missing_key_fails_visibly(monkeypatch):
    # Arrange
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    adapter = model_adapter.GPTImage2Adapter(api_key=None)

    # Act
    artifact = adapter.generate("some prompt", {})

    # Assert
    assert artifact.status == "FAILED"
    assert "OPENAI_API_KEY" in artifact.error_detail
    print("V-MODEL-ADAPTER-NOKEY")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
