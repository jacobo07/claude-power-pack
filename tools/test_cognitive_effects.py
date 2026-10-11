#!/usr/bin/env python
"""V-CE-* gates for cognitive_effects + route_admission REFUSED_EFFECT. CE_DRILL_DIR holds a mutated copy."""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if os.environ.get("CE_DRILL_DIR"):
    sys.path.insert(0, os.environ["CE_DRILL_DIR"])
sys.path.insert(1 if os.environ.get("CE_DRILL_DIR") else 0, str(HERE))
import cognitive_effects as ce  # noqa: E402
import route_admission as ra  # noqa: E402
import tier_routing as tr  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


floors = ra.load_floors(HERE.parent / "vault" / "config" / "route-floors.json")
base = {"envelope": {"target": 7000000, "warn": 8000000, "stop": 9000000, "calls": 30},
        "workers": [{"name": "w", "profile": "slim-t2", "calls": 5, "packet": 1000}]}
os.environ.pop("CDC_EFFECT_GATE", None)
check("V-CE-01 aliases", [ce.normalize(a) for a in ("satisfied", "deterministic", "known_transform", "novel", "owner_reality")]
      == [ce.ZERO_COGNITION, ce.DETERMINISTIC, ce.BOUNDED_COGNITION, ce.NOVEL_COGNITION, ce.OWNER_COGNITION]
      and ce.normalize("x") is None)
v = ce.validate_route(base)
check("V-CE-02 absent effect = BOUNDED, defaulted", v["ok"] and v["effect"] == ce.BOUNDED_COGNITION and v["defaulted"])
r = ra.admit({**base, "effect": "deterministic"}, floors)
check("V-CE-03 deterministic + worker + no deopt REFUSED", r["verdict"] == ra.REFUSED_EFFECT, r["verdict"])
r = ra.admit({**base, "effect": "ZERO_COGNITION", "deopt": []}, floors)
check("V-CE-04 empty deopt REFUSED", r["verdict"] == ra.REFUSED_EFFECT)
r = ra.admit({**base, "effect": "DETERMINISTIC", "deopt": ["input hash changed"]}, floors)
check("V-CE-05 with deopt admitted", r["verdict"] == ra.ADMISSIBLE, r["verdict"])
r = ra.admit({**base, "effect": "BOUNDED_COGNITION"}, floors)
check("V-CE-06 bounded no deopt admitted", r["verdict"] == ra.ADMISSIBLE)
check("V-CE-07 REFUSED_EFFECT is not launchable and is known",
      ra.REFUSED_EFFECT not in ra.LAUNCHABLE_VERDICTS and ra.REFUSED_EFFECT in ra.KNOWN_VERDICTS)
os.environ["CDC_EFFECT_GATE"] = "off"
r = ra.admit({**base, "effect": "deterministic"}, floors)
check("V-CE-08 kill switch", r["verdict"] == ra.ADMISSIBLE)
os.environ.pop("CDC_EFFECT_GATE")
check("V-CE-09 bad effect / bad ABI field refused",
      not ce.validate_route({**base, "effect": "bogus"})["ok"] and not ce.validate_route({**base, "invalidators": "x"})["ok"])
check("V-CE-10 tier_for reads enum",
      [tr.tier_for(e) for e in ce.EFFECTS] == [tr.ZERO_MODEL, tr.ZERO_MODEL, tr.SLIM, tr.DEFAULT, tr.DEFAULT]
      and tr.tier_for("deterministic") == tr.ZERO_MODEL)
print(f"{passes} pass, {fails} fail")
sys.exit(1 if fails else 0)
