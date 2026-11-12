#!/usr/bin/env python3
"""test_cdio_build.py -- done-gate for CDIO-12, the website build workflow (V-CDIO-BUILD-*).

Spec: vault/specs/cdio-12-website-build-workflow.md. Hermetic, read-only: it
reads the dataset, the CDIO wiring points and the agents' live mirrors, and
drives the real scorer. It writes nothing.

  V-CDIO-BUILD-DATASET     CDIO-12 sealed, governed by CDIO-00, source + evidence recorded
  V-CDIO-BUILD-FIDELITY    all nine steps of the video present, in order, each with its
                           timestamp range (red drill: a removed step is caught)
  V-CDIO-BUILD-CRITERIA    every sec.5 criterion names a scorable dimension and a
                           severity (population floor + red drill)
  V-CDIO-BUILD-SCORABLE    each criterion, as a failing verdict, is accepted by the
                           real scorer and lowers the score
  V-CDIO-BUILD-HONEST      the four floor collisions, the not-adopted host and the
                           PLANNED end-to-end run stay recorded
  V-CDIO-BUILD-WIRED       kernel governs CDIO-12; the three agents name it
  V-CDIO-BUILD-MIRRORS     repo agents == live agents (red drill on drift)
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

# One parser for one grammar: CDIO-08's criterion reader, section reader and
# mirror comparison, so this gate cannot disagree with the others about form.
from test_cdio_mobile import (  # noqa: E402
    AGENTS, CDIO, HOME_CLAUDE, _read, _section, mirror_drift, parse_criteria)

DATASET = os.path.join(CDIO, "CDIO-12-website-build-workflow.md")

# Population floor: the criteria sec. 5 was sealed with.
EXPECTED_CRITERIA = {
    "brand-from-owner-assets", "reference-is-direction-not-copy",
    "sections-declared-match-built", "no-empty-section", "claims-have-source",
    "hero-fits-first-viewport", "primary-cta-resolves", "real-contact-data",
    "image-fit-and-placement", "motion-has-still-equivalent", "hero-media-weight",
    "publish-root-is-site-root",
}
# The two criteria the dataset declares critical (floors). A silent downgrade
# would let invented proof or motion without a still pass APPROVE.
EXPECTED_CRITICAL = {"claims-have-source", "motion-has-still-equivalent"}

# The video's nine steps, with the timestamp each starts at (chapters of
# fDTwHIKltpc). The anchor is "### Step N —" + the start time.
VIDEO_STEPS = [(1, "01:09"), (2, "02:58"), (3, "05:02"), (4, "07:34"), (5, "09:45"),
               (6, "11:00"), (7, "13:00"), (8, "14:00"), (9, "19:55")]

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


def step_gaps(text):
    """Return the step numbers whose heading is absent or out of order."""
    positions, gaps = [], []
    for n, start in VIDEO_STEPS:
        m = re.search(rf"^### Step {n} \u2014 .*\({re.escape(start)}-\d\d:\d\d\)", text, flags=re.M)
        if not m:
            gaps.append(n)
        else:
            positions.append(m.start())
    if positions != sorted(positions):
        gaps.append("order")
    return gaps


def wiring_gaps(texts):
    """Return the names of wiring points absent from the given texts."""
    checks = {
        "kernel-governs": re.search(r"^governs:.*CDIO-12", texts["kernel"],
                                    flags=re.M) is not None,
        "agents": all("CDIO-12" in t for t in texts["agents"].values()),
    }
    return [c for c, ok in checks.items() if not ok]


def v_dataset():
    if not os.path.isfile(DATASET):
        _fail("V-CDIO-BUILD-DATASET", "CDIO-12 missing")
        return
    fm = re.match(r"^---(.*?)---", _read(DATASET), flags=re.S)
    fm = fm.group(1) if fm else ""
    need = ("id: CDIO-12", "status: sealed", "governed_by: CDIO-00",
            "source: video fDTwHIKltpc", "evidence:")
    missing = [n for n in need if n not in fm]
    if missing:
        _fail("V-CDIO-BUILD-DATASET", f"front matter lacks {missing}")
    else:
        _ok("V-CDIO-BUILD-DATASET", "sealed, governed by CDIO-00, source + evidence recorded")


def v_fidelity():
    text = _read(DATASET)
    gaps = step_gaps(text)
    drilled = re.sub(r"^### Step 6 \u2014.*$", "### Step six removed", text, flags=re.M)
    drill_ok = step_gaps(drilled) == [6]
    if gaps or not drill_ok:
        _fail("V-CDIO-BUILD-FIDELITY", f"missing/out of order={gaps} drill_ok={drill_ok}")
    else:
        _ok("V-CDIO-BUILD-FIDELITY",
            f"{len(VIDEO_STEPS)} video steps present in order; drill caught a removed step")


def v_criteria():
    found, malformed = parse_criteria(_section(_read(DATASET), 5))
    missing = sorted(EXPECTED_CRITERIA - set(found))
    critical = {n for n, (_, sev) in found.items() if sev == "critical"}
    _, drill_bad = parse_criteria(
        "**`synthetic-no-severity`** (dimension `ux`). text\n"
        "**`synthetic-ok`** (dimension `trust`, severity major). text\n")
    drill_ok = drill_bad == ["synthetic-no-severity"]
    if malformed or missing or critical != EXPECTED_CRITICAL or not drill_ok:
        _fail("V-CDIO-BUILD-CRITERIA",
              f"malformed={malformed} missing={missing} critical={sorted(critical)} "
              f"drill_ok={drill_ok}")
    else:
        _ok("V-CDIO-BUILD-CRITERIA",
            f"{len(found)} criteria well-formed, {len(critical)} critical; "
            "red drill caught the synthetic one")
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
        _fail("V-CDIO-BUILD-SCORABLE", f"found={len(found)} bad={bad}")
    else:
        _ok("V-CDIO-BUILD-SCORABLE",
            f"{len(found)} criteria accepted by the real scorer, each lowers it")


def v_honest():
    text = _read(DATASET)
    collisions = _section(text, 6)
    publishing = _section(text, 7)
    evidence = _section(text, 8)
    markers = {
        "collision 6.1 reference": "### 6.1" in collisions,
        "collision 6.2 motion": "### 6.2" in collisions,
        "collision 6.3 empty section": "### 6.3" in collisions,
        "collision 6.4 invented proof": "### 6.4" in collisions,
        "host not adopted": "not adopted" in publishing,
        "deploy governance": "DEPLOY_GOVERNANCE" in publishing,
        "auto-dub provenance": "auto-dub" in evidence,
        "frames not viewed": re.search(r"\|\s*Frames\s*\|\s*not viewed", evidence) is not None,
        "end-to-end run PLANNED": "**PLANNED**" in evidence,
    }
    absent = [k for k, ok in markers.items() if not ok]
    if absent:
        _fail("V-CDIO-BUILD-HONEST", f"no longer recorded: {absent}")
    else:
        _ok("V-CDIO-BUILD-HONEST", f"{len(markers)} limits and collisions recorded")


def v_wired():
    texts = {
        "kernel": _read(os.path.join(CDIO, "CDIO-00-design-intelligence-kernel.md")),
        "agents": {n: _read(os.path.join(ROOT, "vault", "agents", n)) for n in AGENTS},
    }
    gaps = wiring_gaps(texts)
    drilled = dict(texts, kernel=texts["kernel"].replace("CDIO-12", "CDIO-1X"))
    drill_ok = wiring_gaps(drilled) == ["kernel-governs"]
    if gaps or not drill_ok:
        _fail("V-CDIO-BUILD-WIRED", f"not wired: {gaps} drill_ok={drill_ok}")
    else:
        _ok("V-CDIO-BUILD-WIRED", "kernel + 3 agents wired; drill caught a removed pointer")


def v_mirrors():
    pairs = [(os.path.join(ROOT, "vault", "agents", n), os.path.join(HOME_CLAUDE, "agents", n))
             for n in AGENTS]
    drift = mirror_drift(pairs)
    drill = mirror_drift([(DATASET, pairs[0][0])]) == [os.path.basename(DATASET)]
    if drift or not drill:
        _fail("V-CDIO-BUILD-MIRRORS", f"drift={drift} drill_ok={drill}")
    else:
        _ok("V-CDIO-BUILD-MIRRORS", f"{len(pairs)} live copies identical; drill caught drift")


def main():
    v_dataset()
    if not os.path.isfile(DATASET):
        print(f"CDIO_BUILD_PASS={_passes}/{_passes + _fails}")
        return 1
    v_fidelity()
    found = v_criteria()
    v_scorable(found)
    v_honest()
    v_wired()
    v_mirrors()
    total = _passes + _fails
    print(f"CDIO_BUILD_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
