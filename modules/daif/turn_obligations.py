"""Evaluation -> obligation compiler (EWC M4).

Takes the last assistant turn's TEXT and returns the open obligations it admits to:
FAIL/RED/WARN/AMBER table rows, missing evidence, uncommitted work, a stated next step,
and items the turn hands to the Owner. Sentences that only describe, wish or count zero
are refused: the wish clause and commitment frame are the SAME objects obligation_extractor
uses (imported, not copied). Trigger patterns live in ONE JSON shared with the Node Stop
hook: modules/autonomy_gate/obligation_patterns.json.

Pure function, fail-open on malformed input (returns []): the Stop hook that calls it
decides what to do with an empty result, this layer never raises.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from modules.autonomy_gate.obligations import classify_obligation
from modules.daif.obligation_extractor import COMMITMENT_FRAME_RE, MIN_SUBJECT_WORDS, WISH_RE
from modules.gsd_x.goal.session_scope import obligation_id

PATTERNS_FILE = Path(__file__).resolve().parent.parent / "autonomy_gate" / "obligation_patterns.json"
_MAX_LEN = 600


def _load():
    spec = json.loads(PATTERNS_FILE.read_text(encoding="utf-8"))
    out = []
    for p in spec["patterns"]:
        fl = re.I if "i" in p.get("flags", "") else 0
        out.append((p, re.compile(p["regex"], fl), re.compile(p["exclude"], fl) if p.get("exclude") else None))
    return out, re.compile(spec["sentence_split"])


_PATTERNS, _SPLIT = _load()
_ACTION = {"NOW": "NOW", "APPROVAL": "APPROVAL", "RESOURCE": "RESOURCE", "HUMAN_PREF": "HUMAN_PREF",
           "INFO": "INFO", "gate-error": "APPROVAL"}


def _units(text: str):
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("|"):
            if re.fullmatch(r"[|\s:\-]+", s):
                continue                      # table separator
            yield "table_row", s
        else:
            for sent in _SPLIT.split(s):
                if sent.strip():
                    yield "sentence", sent.strip()


def compile_turn(text) -> list[dict]:
    try:
        if not isinstance(text, str) or not text.strip():
            return []
        found: dict[str, dict] = {}
        for scope, unit in _units(text):
            if len(unit) > _MAX_LEN or WISH_RE.search(unit):
                continue
            for p, rx, ex in _PATTERNS:
                if p["scope"] != scope or not rx.search(unit) or (ex and ex.search(unit)):
                    continue
                if p.get("frame") and not COMMITMENT_FRAME_RE.search(unit):
                    break
                if scope == "sentence" and len(unit.split()) < MIN_SUBJECT_WORDS:
                    break
                cell_text = " ".join(c.strip() for c in unit.strip("|").split("|") if c.strip()) \
                    if scope == "table_row" else unit
                nxt = p["next_action"].format(text=cell_text)
                ob = {"id": obligation_id(cell_text), "text": cell_text, "source": p["source"],
                      "severity": p["severity"], "next_action": nxt,
                      "actionability": p.get("declared_actionability", "NOW")}
                v = classify_obligation(ob)
                ob["actionability"] = _ACTION.get(v["category"], "APPROVAL")
                ob["owner_class"] = v["owner"]
                found.setdefault(ob["id"], ob)
                break
        return list(found.values())
    except Exception:  # noqa: BLE001 -- fail-open: no obligations compiled, never a crash
        return []
