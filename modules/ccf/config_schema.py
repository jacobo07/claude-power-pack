"""Config Schema and Loader (CCF component #2 -- Config-Driven Pipeline).

Adopts the config.json shape observed in the reference implementation
(brendanjowett/logo-concept-generator, per REVERSE_ENGINEERING_REPORT.md):
per-concept font/colours/bg/wordmark/avoid/icon, global theme/accent/headFont/
labels. Schema-versioned so future specializations (UI/Presentation compilers)
extend the concept-axis fields without touching this loader.
"""
from __future__ import annotations

import json

SCHEMA_VERSION = "1.0"

CONCEPT_REQUIRED_FIELDS = ("id", "font", "colours", "bg", "wordmark", "avoid", "icon")
GLOBAL_OPTIONAL_FIELDS = ("theme", "accent", "headFont", "labels")


def default_config() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "theme": None,
        "accent": None,
        "headFont": None,
        "labels": [],
        "concepts": [],
    }


def validate_config(config: dict) -> tuple:
    """Validate a config dict against the CCF config schema.

    Returns (is_valid, errors). errors is a list of human-readable strings,
    each naming the exact concept/field at fault -- never a bare "invalid".
    """
    errors = []
    if not isinstance(config, dict):
        return False, ["config must be a JSON object"]

    if config.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"schema_version must be '{SCHEMA_VERSION}', got {config.get('schema_version')!r}"
        )

    concepts = config.get("concepts")
    if not isinstance(concepts, list) or not concepts:
        errors.append("concepts must be a non-empty list")
        concepts = []

    seen_ids = set()
    for index, concept in enumerate(concepts):
        label = f"concepts[{index}]"
        if not isinstance(concept, dict):
            errors.append(f"{label} must be an object")
            continue
        for req_field in CONCEPT_REQUIRED_FIELDS:
            value = concept.get(req_field)
            if req_field == "avoid":
                if not isinstance(value, list):
                    errors.append(f"{label}.avoid must be a list (may be empty)")
                continue
            if value is None or (isinstance(value, str) and not value.strip()):
                concept_id = concept.get("id", f"#{index}")
                errors.append(f"{label} (id={concept_id!r}) is missing required field '{req_field}'")
        concept_id = concept.get("id")
        if concept_id is not None:
            if concept_id in seen_ids:
                errors.append(f"{label} has duplicate id {concept_id!r}")
            seen_ids.add(concept_id)

    return (len(errors) == 0), errors


def load_config(path: str) -> tuple:
    """Load and validate a config.json file.

    Returns (config_or_none, errors). Never raises on malformed JSON or a
    missing file -- both surface as a descriptive entry in errors, per the
    fail-visible-never-fail-silent constraint.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except OSError as exc:
        return None, [f"cannot read config file {path!r}: {exc}"]

    try:
        config = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [f"config file {path!r} is not valid JSON: {exc}"]

    is_valid, errors = validate_config(config)
    if not is_valid:
        return None, errors
    return config, []
