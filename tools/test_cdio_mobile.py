#!/usr/bin/env python3
"""test_cdio_mobile.py -- done-gate for the CDIO-08 absorption (V-CDIO-MOBILE-*).

Spec: vault/specs/cdio-08-mobile-app-surface.md. Hermetic, read-only: it reads
the dataset, the agents, the skill and their live mirrors, and drives the real
scorer. It writes nothing.

  V-CDIO-MOBILE-DATASET     CDIO-08 sealed, governed by CDIO-00, source recorded
  V-CDIO-MOBILE-CRITERIA    every section-3 criterion names a scorable dimension
                            and a severity (floor on the population + red drill)
  V-CDIO-MOBILE-SCORABLE    each criterion, as a failing verdict, is accepted by
                            the real scorer and lowers the score
  V-CDIO-MOBILE-REJECTED    the five rejected source claims stay recorded
  V-CDIO-MOBILE-WIRED       kernel, Lens 6, CDIO-07 sec.11, agents, skill, CLAUDE.md
  V-CDIO-MOBILE-MIRRORS     repo copies == live copies (red drill on drift)
"""
from __future__ import annotations

import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

HOME_CLAUDE = os.path.join(os.path.expanduser("~"), ".claude")
CDIO = os.path.join(ROOT, "vault", "knowledge_base", "cdio")
DATASET = os.path.join(CDIO, "CDIO-08-mobile-app-surface.md")
SKILL = os.path.join(ROOT, "skills", "mobile-app-ui-design", "SKILL.md")
SKILL_LIVE = os.path.join(HOME_CLAUDE, "skills", "mobile-app-ui-design", "SKILL.md")
AGENTS = ("cdio-core.md", "cdio-reviewer.md", "cdio-standards-librarian.md")

DIMENSIONS = {"visual", "ux", "trust", "conversion"}
SEVERITIES = {"critical", "major", "minor"}
# Population floor: the criteria section 3 was sealed with. A parser that
# silently stops matching must not read as "every criterion is well-formed".
EXPECTED_CRITERIA = {
    "thumb-zone-primary-action", "value-over-label", "search-zero-state",
    "selection-over-typing", "input-method-fit", "status-as-timeline",
    "bottom-nav-destinations", "first-run-differs", "tabular-figures",
    "shadow-tint-on-colour",
}
CRITERION_RE = re.compile(
    r"^\*\*`(?P<name>[a-z0-9-]+)`\*\*\s*\((?P<meta>[^)]*)\)", re.M)

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


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _section(text, number):
    m = re.search(rf"^## {number}\..*?(?=^## \d+\.|\Z)", text, flags=re.M | re.S)
    return m.group(0) if m else ""


def parse_criteria(section_text):
    """Return ({name: (dimension, severity)}, [malformed names]).

    A criterion is malformed when its parenthetical names no known dimension
    or no known severity -- the two fields the scorer and CDIO-05 sec.3 need.
    """
    found, malformed = {}, []
    for m in CRITERION_RE.finditer(section_text):
        meta = m.group("meta")
        dim = re.search(r"dimension\s+`(\w+)`", meta)
        sev = re.search(r"severity\s+(\w+)", meta)
        if not dim or dim.group(1) not in DIMENSIONS or not sev \
                or sev.group(1) not in SEVERITIES:
            malformed.append(m.group("name"))
            continue
        found[m.group("name")] = (dim.group(1), sev.group(1))
    return found, malformed


def mirror_drift(pairs):
    """Return the pairs whose two files differ or are missing."""
    bad = []
    for a, b in pairs:
        if not (os.path.isfile(a) and os.path.isfile(b)) or _sha(a) != _sha(b):
            bad.append(os.path.basename(a))
    return bad


def v_dataset():
    if not os.path.isfile(DATASET):
        _fail("V-CDIO-MOBILE-DATASET", "CDIO-08 missing")
        return
    fm = re.match(r"^---(.*?)---", _read(DATASET), flags=re.S)
    fm = fm.group(1) if fm else ""
    need = ("id: CDIO-08", "status: sealed", "governed_by: CDIO-00",
            "github.com/ceorkm/mobile-app-ui-design")
    missing = [n for n in need if n not in fm]
    if missing:
        _fail("V-CDIO-MOBILE-DATASET", f"front matter lacks {missing}")
    else:
        _ok("V-CDIO-MOBILE-DATASET", "sealed, governed by CDIO-00, source recorded")


def v_criteria():
    found, malformed = parse_criteria(_section(_read(DATASET), 3))
    missing = sorted(EXPECTED_CRITERIA - set(found))
    # Red drill: a synthetic criterion with no dimension must be caught, and a
    # well-formed one must not -- otherwise the parser proves nothing.
    _, drill_bad = parse_criteria(
        "**`synthetic-no-dimension`** (severity major). text\n"
        "**`synthetic-ok`** (dimension `ux`, severity minor). text\n")
    drill_ok = drill_bad == ["synthetic-no-dimension"]
    if malformed or missing or not drill_ok:
        _fail("V-CDIO-MOBILE-CRITERIA",
              f"malformed={malformed} missing={missing} drill_ok={drill_ok}")
    else:
        _ok("V-CDIO-MOBILE-CRITERIA",
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
        _fail("V-CDIO-MOBILE-SCORABLE", f"found={len(found)} bad={bad}")
    else:
        _ok("V-CDIO-MOBILE-SCORABLE",
            f"{len(found)} criteria accepted by the real scorer, each lowers it")


def v_rejected():
    sec = _section(_read(DATASET), 7).lower()
    markers = {"celebrate": "celebrate small wins",
               "backdrop blur": "glow / blur polish",
               "80 to 96px": "desktop section padding",
               "two font weights": "2-vs-3 weights contradiction",
               "monospace": "monospace numbers"}
    absent = [label for key, label in markers.items() if key not in sec]
    if absent:
        _fail("V-CDIO-MOBILE-REJECTED", f"no longer recorded: {absent}")
    else:
        _ok("V-CDIO-MOBILE-REJECTED", f"{len(markers)} rejected claims recorded")


def v_wired():
    k = _read(os.path.join(CDIO, "CDIO-00-design-intelligence-kernel.md"))
    l6 = _section(_read(os.path.join(CDIO, "CDIO-05-design-review-pipeline.md")), 1)
    c7 = _read(os.path.join(CDIO, "CDIO-07-experience-contract.md"))
    agents = {n: _read(os.path.join(ROOT, "vault", "agents", n)) for n in AGENTS}
    claude_md = _read(os.path.join(ROOT, "CLAUDE.md"))
    skill = _read(SKILL) if os.path.isfile(SKILL) else ""
    checks = {
        "kernel-governs": re.search(r"^governs:.*CDIO-08", k, flags=re.M) is not None,
        "lens6-pointer": "CDIO-08" in l6,
        "cdio07-sec11": re.search(r"^## 11\. Peak-End", c7, flags=re.M) is not None,
        "agents": all("CDIO-08" in t for t in agents.values()),
        "skill-cites": "CDIO-08" in skill and "name: mobile-app-ui-design" in skill,
        "claude-md-row": "mobile-app-ui-design" in claude_md,
    }
    off = [c for c, ok in checks.items() if not ok]
    if off:
        _fail("V-CDIO-MOBILE-WIRED", f"not wired: {off}")
    else:
        _ok("V-CDIO-MOBILE-WIRED", f"{len(checks)} wiring points present")


def v_mirrors():
    pairs = [(SKILL, SKILL_LIVE)] + [
        (os.path.join(ROOT, "vault", "agents", n), os.path.join(HOME_CLAUDE, "agents", n))
        for n in AGENTS]
    drift = mirror_drift(pairs)
    # Red drill: two files known to differ must be reported as drift.
    drill = mirror_drift([(DATASET, SKILL)]) == [os.path.basename(DATASET)]
    if drift or not drill:
        _fail("V-CDIO-MOBILE-MIRRORS", f"drift={drift} drill_ok={drill}")
    else:
        _ok("V-CDIO-MOBILE-MIRRORS", f"{len(pairs)} live copies identical; drill caught drift")


def main():
    v_dataset()
    if not os.path.isfile(DATASET):
        print(f"CDIO_MOBILE_PASS={_passes}/{_passes + _fails}")
        return 1
    found = v_criteria()
    v_scorable(found)
    v_rejected()
    v_wired()
    v_mirrors()
    total = _passes + _fails
    print(f"CDIO_MOBILE_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
