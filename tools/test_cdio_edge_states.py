#!/usr/bin/env python3
"""test_cdio_edge_states.py -- done-gate for the edge-state amendments (V-CDIO-EDGE-*).

Spec: vault/specs/cdio-edge-states.md. Hermetic, read-only: it reads the three
amended datasets and drives the real scorer. It writes nothing.

  V-CDIO-EDGE-CRITERIA   each criterion lives in its OWNING section, with a
                         dimension and a severity (population floor + red drill)
  V-CDIO-EDGE-SEVERITY   severities follow CDIO-05 sec.3: a dead end or a status
                         collapse is critical, the other two are major
  V-CDIO-EDGE-SCORABLE   each criterion, as a failing verdict, is accepted by the
                         real scorer and lowers the score
  V-CDIO-EDGE-CONTRAST   review profiles: a recovery page that really recovers is
                         APPROVE; a dead link on it, a 401 shown as 404, wrong-brand
                         metadata or an unobserved layout state each score lower,
                         and the two criticals block "done"
  V-CDIO-EDGE-SCOPE      the amendments carry the abstraction, never one
                         product's trivia (brand, illustration, colour); drilled
  V-CDIO-EDGE-SENTENCE   the old CDIO-03 sentence that passed any 404 offering a
                         link home is gone; the qualified one is present
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CDIO = os.path.join(ROOT, "vault", "knowledge_base", "cdio")
DATASETS = {
    "CDIO-02": os.path.join(CDIO, "CDIO-02-ux-intelligence-engine.md"),
    "CDIO-03": os.path.join(CDIO, "CDIO-03-trust-premium-intelligence.md"),
    "CDIO-05": os.path.join(CDIO, "CDIO-05-design-review-pipeline.md"),
}
# criterion -> (dataset, owning section, dimension, severity). The owning
# section is part of the contract: a criterion that drifts to another section,
# or exists only in a changelog, is not where a reviewer reads for it.
EXPECTED = {
    "dead-affordance": ("CDIO-02", 5, "ux", "critical"),
    "edge-state-host-ownership": ("CDIO-03", 7, "trust", "major"),
    "error-status-collapse": ("CDIO-03", 7, "trust", "critical"),
    "unobserved-layout-state": ("CDIO-05", 8, "visual", "major"),
}
DIMENSIONS = {"visual", "ux", "trust", "conversion"}
SEVERITIES = {"critical", "major", "minor"}
CRITERION_RE = re.compile(
    r"^\*\*`(?P<name>[a-z0-9-]+)`\*\*\s*\((?P<meta>[^)]*)\)", re.M)
# One product's details must never become a design-intelligence rule. Fragments
# of the campaign that produced these amendments; drilled below.
TRIVIA_RE = re.compile(
    r"quick\s*lease|infinity\s*ops|costaluz|\bwoman\b|\bdog\b|golden retriever|"
    r"#28cbd3|signpost|oops", re.I)

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


def _section(text, number):
    m = re.search(rf"^## {number}\..*?(?=^## \d+\.|\Z)", text, flags=re.M | re.S)
    return m.group(0) if m else ""


def parse_criteria(section_text):
    """Return ({name: (dimension, severity)}, [malformed names])."""
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


def owned_criteria():
    """Criteria as found in their owning sections: {name: (dim, sev)}."""
    texts = {k: _read(p) for k, p in DATASETS.items()}
    found, malformed = {}, []
    for name, (ds, sec, _, _) in EXPECTED.items():
        got, bad = parse_criteria(_section(texts[ds], sec))
        malformed += bad
        if name in got:
            found[name] = got[name]
    return found, sorted(set(malformed))


def v_criteria():
    found, malformed = owned_criteria()
    missing = sorted(set(EXPECTED) - set(found))
    _, drill_bad = parse_criteria(
        "**`synthetic-no-dimension`** (severity critical). text\n"
        "**`synthetic-ok`** (dimension `trust`, severity major). text\n")
    drill_ok = drill_bad == ["synthetic-no-dimension"]
    if malformed or missing or not drill_ok:
        _fail("V-CDIO-EDGE-CRITERIA",
              f"malformed={malformed} missing_from_owning_section={missing} drill_ok={drill_ok}")
    else:
        _ok("V-CDIO-EDGE-CRITERIA",
            f"{len(found)} criteria in their owning sections; red drill caught the synthetic one")
    return found


def v_severity(found):
    wrong = {n: found[n] for n, (_, _, dim, sev) in EXPECTED.items()
             if n in found and found[n] != (dim, sev)}
    if wrong or not found:
        _fail("V-CDIO-EDGE-SEVERITY", f"dimension/severity drift: {wrong}")
    else:
        _ok("V-CDIO-EDGE-SEVERITY", "dead end + status collapse critical, the other two major")


def _profile(failing):
    """A review of a recovery page: the shared passes plus the given failures."""
    from modules.cdio.scorer import Verdict
    base = [Verdict("contrast-body", "visual", "pass", observed="6.1:1"),
            Verdict("dead-end-error", "ux", "pass", observed="home + product + contact"),
            Verdict("value-3s", "trust", "pass", observed="what happened, in words")]
    return base + [Verdict(n, d, "fail", s, observed=f"observed {n}") for n, (d, s) in failing]


def v_scorable(found):
    from modules.cdio.scorer import score_review
    baseline = score_review(_profile([])).score
    bad = []
    for name, (dim, sev) in sorted(found.items()):
        r = score_review(_profile([(name, (dim, sev))]))
        if r.dropped or r.score is None or r.score >= baseline:
            bad.append((name, r.score, len(r.dropped)))
    if not found or bad:
        _fail("V-CDIO-EDGE-SCORABLE", f"found={len(found)} bad={bad} baseline={baseline}")
    else:
        _ok("V-CDIO-EDGE-SCORABLE", f"{len(found)} criteria accepted by the real scorer, each lowers it")


def v_contrast(found):
    from modules.cdio.scorer import score_review
    good = score_review(_profile([]))
    rows, wrong = [], []
    for name, (dim, sev) in sorted(found.items()):
        r = score_review(_profile([(name, (dim, sev))]))
        rows.append(f"{name}={r.verdict}/{r.score}")
        blocks = r.verdict != "APPROVE"
        if r.score >= good.score or (sev == "critical") != blocks:
            wrong.append(name)
    # The known anti-pattern the amendments target: a generic dead-end 404.
    from modules.cdio.scorer import Verdict
    generic = score_review([Verdict("dead-end-error", "ux", "fail", "critical",
                                    observed="framework 404, no way back")])
    if good.verdict != "APPROVE" or generic.verdict == "APPROVE" or wrong or not found:
        _fail("V-CDIO-EDGE-CONTRAST",
              f"good={good.verdict}/{good.score} generic={generic.verdict} wrong={wrong} {rows}")
    else:
        _ok("V-CDIO-EDGE-CONTRAST",
            f"good={good.verdict}/{good.score}; generic dead-end={generic.verdict}; " + ", ".join(rows))


def _amended_text():
    texts = {k: _read(p) for k, p in DATASETS.items()}
    return (_section(texts["CDIO-02"], 5) + _section(texts["CDIO-03"], 7)
            + _section(texts["CDIO-05"], 8))


def v_scope():
    hits = sorted({m.group(0).lower() for m in TRIVIA_RE.finditer(_amended_text())})
    drill = TRIVIA_RE.search("a woman with a map and her dog on a QuickLease page") is not None
    if hits or not drill:
        _fail("V-CDIO-EDGE-SCOPE", f"product trivia in CDIO: {hits} drill_ok={drill}")
    else:
        _ok("V-CDIO-EDGE-SCOPE", "no product trivia in the amended sections; drill caught a planted one")


def v_sentence():
    sec = re.sub(r"\s+", " ", _section(_read(DATASETS["CDIO-03"]), 7))
    old = "one that offers search or a link home is not."
    new = "provided every link it offers resolves on the host that renders it"
    if old in sec or new not in sec:
        _fail("V-CDIO-EDGE-SENTENCE", f"old_present={old in sec} qualified_present={new in sec}")
    else:
        _ok("V-CDIO-EDGE-SENTENCE", "a 404 passes on links that resolve, not on links that exist")


def main():
    missing = [k for k, p in DATASETS.items() if not os.path.isfile(p)]
    if missing:
        _fail("V-CDIO-EDGE-CRITERIA", f"datasets missing: {missing}")
        print(f"CDIO_EDGE_PASS={_passes}/{_passes + _fails}")
        return 1
    found = v_criteria()
    v_severity(found)
    v_scorable(found)
    v_contrast(found)
    v_scope()
    v_sentence()
    total = _passes + _fails
    print(f"CDIO_EDGE_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
