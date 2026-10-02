#!/usr/bin/env python3
"""test_cdio_focus.py -- done-gate for CDIO-09, the focused decision surface (V-CDIO-FOCUS-*).

Spec: vault/specs/cdio-09-focused-decision-surface.md. Hermetic, read-only: it
reads the dataset, the CDIO wiring points and the agents' live mirrors, and
drives the real scorer. It writes nothing.

  V-CDIO-FOCUS-DATASET     CDIO-09 sealed, governed by CDIO-00, source + evidence recorded
  V-CDIO-FOCUS-CRITERIA    every sec.3 criterion names a scorable dimension and a
                           severity (floor on the population + red drill)
  V-CDIO-FOCUS-SCORABLE    each criterion, as a failing verdict, is accepted by the
                           real scorer and lowers the score
  V-CDIO-FOCUS-HONEST      the not-universalised list and the PLANNED gate stay
                           recorded, so the dataset cannot drift into overclaiming
  V-CDIO-FOCUS-WIRED       kernel, Lens 5, CDIO-06 F1 variant, three agents
  V-CDIO-FOCUS-MIRRORS     repo agents == live agents (red drill on drift)
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

# The grammar, the section reader and the mirror comparison are CDIO-08's; one
# parser for one grammar, so the two gates cannot disagree about what a
# well-formed criterion is.
from test_cdio_mobile import (  # noqa: E402
    AGENTS, CDIO, HOME_CLAUDE, _read, _section, mirror_drift, parse_criteria)

DATASET = os.path.join(CDIO, "CDIO-09-focused-decision-surface.md")
# Population floor: the criteria section 3 was sealed with.
EXPECTED_CRITERIA = {
    "focus-applicability", "one-filled-action", "backdrop-inert",
    "initial-focus-intent", "focus-restored", "single-effect-in-flight",
    "retry-only-if-nothing-changed", "selected-state-non-color",
    "progress-is-announced", "backdrop-not-privacy",
}

_passes = 0
_fails = 0


def _ok(name, detail):
    global _passes
    _passes += 1
    print(f"[PASS] {name}: {detail}")


def _fail(name, detail):
    global _fails
    _fails += 1
    print(f"[FAIL] {name}: {detail}")


def wiring_gaps(texts):
    """Return the names of wiring points absent from the given texts.

    texts: {"kernel", "lens5", "cdio06", "agents": {name: text}}.
    """
    checks = {
        "kernel-governs": re.search(r"^governs:.*CDIO-09", texts["kernel"],
                                    flags=re.M) is not None,
        "lens5-pointer": "CDIO-09" in texts["lens5"],
        "cdio06-f1-variant": "Zero-accent variant" in texts["cdio06"]
                             and "CDIO-09" in texts["cdio06"],
        "agents": all("CDIO-09" in t for t in texts["agents"].values()),
    }
    return [c for c, ok in checks.items() if not ok]


def v_dataset():
    if not os.path.isfile(DATASET):
        _fail("V-CDIO-FOCUS-DATASET", "CDIO-09 missing")
        return
    fm = re.match(r"^---(.*?)---", _read(DATASET), flags=re.S)
    fm = fm.group(1) if fm else ""
    need = ("id: CDIO-09", "status: sealed", "governed_by: CDIO-00",
            "source: InfinityOps", "evidence:")
    missing = [n for n in need if n not in fm]
    if missing:
        _fail("V-CDIO-FOCUS-DATASET", f"front matter lacks {missing}")
    else:
        _ok("V-CDIO-FOCUS-DATASET", "sealed, governed by CDIO-00, source + evidence recorded")


def v_criteria():
    found, malformed = parse_criteria(_section(_read(DATASET), 3))
    missing = sorted(EXPECTED_CRITERIA - set(found))
    _, drill_bad = parse_criteria(
        "**`synthetic-no-severity`** (dimension `ux`). text\n"
        "**`synthetic-ok`** (dimension `trust`, severity major). text\n")
    drill_ok = drill_bad == ["synthetic-no-severity"]
    if malformed or missing or not drill_ok:
        _fail("V-CDIO-FOCUS-CRITERIA",
              f"malformed={malformed} missing={missing} drill_ok={drill_ok}")
    else:
        _ok("V-CDIO-FOCUS-CRITERIA",
            f"{len(found)} criteria well-formed; red drill caught the synthetic one")
    return found


def v_scorable(found):
    from modules.cdio.scorer import Verdict, score_review
    baseline = score_review([Verdict("value-3s", "trust", "pass",
                                     observed="value stated")]).score
    bad = []
    for name, (dim, sev) in sorted(found.items()):
        r = score_review([Verdict(name, dim, "fail", sev,
                                  observed=f"synthetic observation for {name}")])
        if r.dropped or r.score is None or r.score >= baseline:
            bad.append((name, r.score, len(r.dropped)))
    if not found or bad:
        _fail("V-CDIO-FOCUS-SCORABLE", f"found={len(found)} bad={bad}")
    else:
        _ok("V-CDIO-FOCUS-SCORABLE",
            f"{len(found)} criteria accepted by the real scorer, each lowers it")


def v_honest():
    text = _read(DATASET)
    not_universal = _section(text, 6).lower()
    evidence = _section(text, 8)
    markers = {
        "exact hex values": "hex values" in not_universal,
        "blur radius": "blur radius" in not_universal,
        "step count": "five steps" in not_universal,
        "transport rule owned by B1": "web_surface" in not_universal,
        "transfer not reached": re.search(r"\|\s*transfer\s*\|\s*not reached",
                                          evidence) is not None,
        "design_gate check PLANNED": "**PLANNED**" in evidence,
    }
    absent = [k for k, ok in markers.items() if not ok]
    if absent:
        _fail("V-CDIO-FOCUS-HONEST", f"no longer recorded: {absent}")
    else:
        _ok("V-CDIO-FOCUS-HONEST", f"{len(markers)} scope limits recorded")


def v_wired():
    texts = {
        "kernel": _read(os.path.join(CDIO, "CDIO-00-design-intelligence-kernel.md")),
        "lens5": _section(_read(os.path.join(CDIO, "CDIO-05-design-review-pipeline.md")), 1),
        "cdio06": _read(os.path.join(CDIO, "CDIO-06-aesthetic-families.md")),
        "agents": {n: _read(os.path.join(ROOT, "vault", "agents", n)) for n in AGENTS},
    }
    gaps = wiring_gaps(texts)
    # Red drill: the same texts with the kernel pointer removed must be reported.
    drilled = dict(texts, kernel=texts["kernel"].replace("CDIO-09", "CDIO-0X"))
    drill_ok = wiring_gaps(drilled) == ["kernel-governs"]
    if gaps or not drill_ok:
        _fail("V-CDIO-FOCUS-WIRED", f"not wired: {gaps} drill_ok={drill_ok}")
    else:
        _ok("V-CDIO-FOCUS-WIRED", "4 wiring points present; drill caught a removed pointer")


def v_mirrors():
    pairs = [(os.path.join(ROOT, "vault", "agents", n), os.path.join(HOME_CLAUDE, "agents", n))
             for n in AGENTS]
    drift = mirror_drift(pairs)
    drill = mirror_drift([(DATASET, pairs[0][0])]) == [os.path.basename(DATASET)]
    if drift or not drill:
        _fail("V-CDIO-FOCUS-MIRRORS", f"drift={drift} drill_ok={drill}")
    else:
        _ok("V-CDIO-FOCUS-MIRRORS", f"{len(pairs)} live copies identical; drill caught drift")


def main():
    v_dataset()
    if not os.path.isfile(DATASET):
        print(f"CDIO_FOCUS_PASS={_passes}/{_passes + _fails}")
        return 1
    found = v_criteria()
    v_scorable(found)
    v_honest()
    v_wired()
    v_mirrors()
    total = _passes + _fails
    print(f"CDIO_FOCUS_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
