#!/usr/bin/env python
"""test_skill_delivery.py -- pillar C gate (skill-capability, SC-C, decisions D-01 and D-03).

    python3 tools/test_skill_delivery.py                  # check (default mode, every clause)
    python3 tools/test_skill_delivery.py --fixture PATH   # window-F clauses on one fixture only (red-drill entrance)
    python3 tools/test_skill_delivery.py --json           # the per-window report list as JSON
    python3 tools/test_skill_delivery.py --write-evidence # render vault/programs/skill-capability/evidence/C-delivery.md

(`python` on the laptop, `python3` on gex44.) One gate computes opportunity, delivery, recall and
precision from commit-card rows plus transcripts over a named window (D-01). Every transcript read
goes through tools/skill_invocations.py (`count_file`, `session_of`, `row_epoch`); this file has no
transcript-row parse of its own, so a mention can never read as delivery.

Default mode reads only committed files (the fixture, the ledger, the evidence file) plus a
TemporaryDirectory it writes itself. It does not read ~/.claude, does not call installed_names(),
does not use the network and does not call git, because the CE verifier re-runs it on two hosts.
Every read states encoding="utf-8" and every write states newline="\\n" (the laptop re-runs it too).

UNMEASURED and INCONCLUSIVE are never a pass: an opportunity whose delivery could not be observed (no
transcript, or only untimed candidate rows) is excluded from the recall n and reported beside it.

p3_delivery (cognitive-resource-os, phase 06) defines per-run delivery as "a Skill tool_use came
BEFORE the first commit command", by tool-use index. This gate uses the same predicate keyed by
timestamp against the card judgement's `ts`. It does NOT import p3_delivery: that imports p3_runner,
which binds Windows constants at import time and lives in another workstream's phase directory.

Output lines: `  ok   V-SD-X <evidence>`, `  FAIL V-SD-X <diagnostic>`, `  INCONCLUSIVE V-SD-X <why>`, last
line `SD_PASS=<passed>/<total>`. Exit codes: 0 all clauses ok, 1 any FAIL or INCONCLUSIVE, 2 could not run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_invocations as si  # noqa: E402

FIXTURE_REL = "vault/programs/skill-capability/delivery_fixture.json"
LEDGER_REL = "vault/programs/skill-capability/ledger.json"
EVIDENCE_REL = "vault/programs/skill-capability/evidence/C-delivery.md"
SELF_REL = "tools/test_skill_delivery.py"
PACK_REL = "vault/programs/skill-capability/card_evidence_pack.json"
G_RECORD_REL = "vault/programs/skill-capability/evidence/C-window-G.json"
# D-02: window L is this committed laptop pack, pinned by its LF sha256 (the value ledger state.A already cites).
PACK_SHA256 = "dacfdf5aa8afb0a5e6221ebf98fcf1b70866c7de3931083e210e7e948a6c0c05"
# The builder rule, copied from /home/kobii/missions/skill-capability-data/card_evidence_pack.py lines 81-82
# (outside the repo, so not read here): the builder picks NO `opportunity` rows.
PACK_SELECTION_RULE = ('decision in ("deny-card", "pass-after-card") or "exit 128" in str(reason)  '
                       '(card_evidence_pack.py lines 81-82)')
WINDOW_RECORD_SCHEMA = "skill-delivery-window/1"
TS_FORMAT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")  # the pack's exact ts shape (24 chars)

FIXTURE_SCHEMA = "skill-delivery-fixture/1"
CAPABILITY = "concurrent-writers-shared-tree"  # mirrors tools/skill_opportunity_signals.py:CAPABILITY
MIN_N = 5
# mirrors tools/skill_opportunity_signals.py:DECISIONS; that module is not imported (it pulls
# modules.cognitive_os.co_12_telemetry at import time)
OPPORTUNITY_DECISIONS = ("opportunity", "deny-card")
UNKNOWN_DECISIONS = ("unknown", "timeout")
FRESH_SESSIONS_THIS_PHASE = 0  # D-SESSIONS: a statement about this phase, not a measurement

DEFINITIONS = (
    "opportunity: a commit-card judgement row with decision `opportunity` or `deny-card` that lists at "
    "least one foreign file (the capability was needed or shown at a commit).",
    "delivered: the capability reached the model at or before the judgement `ts` in the same session, by "
    "the card (decision `deny-card`) OR by an invocation (a Skill tool_use or a typed command counted by "
    "tools/skill_invocations.py); a mention, listing or hook body is never delivery.",
    "recall: delivered / opportunities whose delivery is measured. An opportunity with no transcript read "
    "or only untimed candidate rows is UNMEASURED and sits outside n, never counted as not delivered.",
    "precision: (delivered AND needed) / delivered with a needed label; needed = frozen D-CARD ground "
    "truth or the window fixture's per-row label.",
    "small n: a rate is printed with its n, and with n < 5 no ratio is printed or estimated.",
    "a skill with no opportunity detector reports opportunity UNMEASURED, never 0.",
)


# --------------------------------------------------------------------------- pure derivation


def is_commit_row(row) -> bool:
    """`card` == `commit`, or `card` absent and a `foreign` key present (the 03-02 pack drops `card`)."""
    if not isinstance(row, dict):
        return False
    if "card" in row:
        return row.get("card") == "commit"
    return "foreign" in row


def is_opportunity(row) -> bool:
    return (is_commit_row(row) and row.get("decision") in OPPORTUNITY_DECISIONS
            and len(row.get("foreign") or []) >= 1)


def transcript_index(root: Path) -> dict:
    """session id -> sorted list of jsonl paths under root (subagent files join by si.session_of)."""
    out: dict = {}
    for p in sorted(Path(root).rglob("*.jsonl")):
        out.setdefault(si.session_of(p), []).append(p)
    return out


def invoked_before(paths, capability, installed, until):
    """True / False / None. None = UNMEASURED (no transcript, or only untimed candidate rows)."""
    if not paths:
        return None
    untimed = 0
    for p in paths:
        r = si.count_file(p, installed, set(), until=until)
        if r["model"][capability] + r["typed"][capability] >= 1:
            return True
        untimed += r["untimed_rows"]
    return None if untimed else False


def judged_at(row):
    """Epoch seconds of the card judgement `ts` (ISO string or number), or None."""
    ts = row.get("ts")
    if isinstance(ts, bool):
        return None
    if isinstance(ts, (int, float)):
        return float(ts)
    return si.row_epoch({"timestamp": ts})


def rate(num: int, n: int) -> dict:
    return {"num": num, "n": n, "value": round(num / n, 3) if n >= MIN_N else None}


def fmt_rate(r: dict) -> str:
    if r["value"] is None:
        return f"n={r['n']} (< {MIN_N}, not estimated)"
    return f"{r['num']}/{r['n']} = {r['value']:.3f} (n={r['n']})"


def compute_window(card_rows, index, installed, needed_of, *, window="?", plane="?", selection="?",
                   capability=CAPABILITY, detector=invoked_before, opportunity=is_opportunity,
                   absent_policy="unmeasured", fmt=fmt_rate) -> dict:
    rows_out, unmeasured = [], []
    c = dict(opportunities=0, pass_after_card=0, no_opportunity=0, judgement_unknown=0, ignored_non_commit=0,
             unparseable_ts=0)
    for row in card_rows:
        if not is_commit_row(row):
            c["ignored_non_commit"] += 1
            continue
        dec = row.get("decision")
        if dec == "pass-after-card":
            c["pass_after_card"] += 1
        elif dec == "no_opportunity":
            c["no_opportunity"] += 1
        elif dec in UNKNOWN_DECISIONS:
            c["judgement_unknown"] += 1
        if not opportunity(row):
            continue
        c["opportunities"] += 1
        sess = row.get("session")
        paths = index.get(sess, [])
        until = judged_at(row)
        if until is None:
            invoked = None
        elif not paths and absent_policy == "none":
            invoked = False
        else:
            invoked = detector(paths, capability, installed, until)
        if until is None:
            c["unparseable_ts"] += 1  # A-1: delivery UNMEASURED for any decision, counted, never a crash or a drop
            state = "UNMEASURED"
            why = "no judgement ts"
            unmeasured.append(f"{sess} {dec} {row.get('ts')}: {why}")
        elif dec == "deny-card":
            state = "card"
        elif invoked is True:
            state = "invocation"
        elif invoked is False:
            state = "none"
        else:
            state = "UNMEASURED"
            why = "no transcript read" if not paths else "only untimed candidate rows"
            unmeasured.append(f"{sess} {dec} {row.get('ts')}: {why}")
        rows_out.append({"session": sess, "decision": dec, "ts": row.get("ts"), "delivery": state,
                         "invoked": invoked, "needed": needed_of(row)})
    delivered = [r for r in rows_out if r["delivery"] in ("card", "invocation")]
    by_card = [r for r in delivered if r["delivery"] == "card"]
    measured = [r for r in rows_out if r["delivery"] != "UNMEASURED"]
    card_inv_unmeasured = sum(1 for r in by_card if r["invoked"] is None)
    labelled = [r for r in delivered if r["needed"] is not None]
    rec = rate(len(delivered), len(measured))
    prec = rate(sum(1 for r in labelled if r["needed"] is True), len(labelled))
    return {
        "window": window, "plane": plane, "selection": selection,
        "opportunities": c["opportunities"], "delivery_measured": len(measured),
        "delivery_unmeasured": len(rows_out) - len(measured), "delivered": len(delivered),
        "by_card": len(by_card), "by_invocation_only": len(delivered) - len(by_card),
        "card_and_invocation": ("UNMEASURED" if card_inv_unmeasured
                                else sum(1 for r in by_card if r["invoked"] is True)),
        "card_invocation_unmeasured": card_inv_unmeasured,
        "recall": rec, "precision": prec,
        "recall_line": fmt(rec), "precision_line": fmt(prec),
        "pass_after_card": c["pass_after_card"], "no_opportunity": c["no_opportunity"],
        "judgement_unknown": c["judgement_unknown"], "ignored_non_commit": c["ignored_non_commit"],
        "unlabelled_delivered": len(delivered) - len(labelled), "unparseable_ts": c["unparseable_ts"],
        "unmeasured": unmeasured, "rows": rows_out,
    }


# --------------------------------------------------------------------------- fixture window F


def load_fixture(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def fixture_window(fx: dict, **mutants) -> dict:
    """Write the fixture transcripts to a TemporaryDirectory, then derive window F from them."""
    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / "projects" / "fixture-window-F"
        base.mkdir(parents=True)
        for session, rows in fx["transcripts"].items():
            with open(base / f"{session}.jsonl", "w", encoding="utf-8", newline="\n") as fh:
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
        index = transcript_index(Path(td) / "projects")
        w = fx["window"]
        return compute_window(fx["card_rows"], index, set(fx["installed"]), lambda row: row.get("needed"),
                              window=w["name"], plane=w["plane"], selection=w["selection"],
                              capability=fx.get("capability", CAPABILITY), **mutants)


def _state(rep: dict, session_n: int) -> str:
    sid = f"f0000000-0000-4000-8000-00000000000{session_n}"
    hits = [r["delivery"] for r in rep["rows"] if r["session"] == sid and r["decision"] in OPPORTUNITY_DECISIONS]
    return ",".join(hits) or "absent"


def _cmp(rep: dict, exp: dict, keys) -> list:
    return [f"{k}: measured {rep[k]!r}, expected {exp[k]!r}" for k in keys if rep[k] != exp[k]]


def f_clauses(rep: dict, fx: dict) -> list:
    """Window-F clauses. Returns [(name, status, text)] with status in ok / FAIL / INCONCLUSIVE."""
    exp = fx["expected"]
    out = []

    def add(name, bad, good):
        out.append((name, "FAIL" if bad else "ok", "; ".join(bad) if bad else good))

    bad = []
    if fx.get("schema") != FIXTURE_SCHEMA:
        bad.append(f"schema {fx.get('schema')!r}")
    if rep["by_invocation_only"] + (rep["card_and_invocation"] if isinstance(rep["card_and_invocation"], int) else 0) < 1:
        bad.append("detector found 0 invocations (positive control)")
    add("V-SD-F-SOURCES", bad,
        f"schema {FIXTURE_SCHEMA}, {len(fx['card_rows'])} card rows, {len(fx['transcripts'])} transcripts, "
        f"invocations found {rep['by_invocation_only']} invocation-only")
    keys = ("opportunities", "pass_after_card", "no_opportunity", "judgement_unknown", "ignored_non_commit")
    add("V-SD-OPPORTUNITY", _cmp(rep, exp, keys), ", ".join(f"{k} {rep[k]}" for k in keys))
    keys = ("delivered", "by_card", "by_invocation_only", "card_and_invocation")
    add("V-SD-DELIVERY", _cmp(rep, exp, keys), ", ".join(f"{k} {rep[k]}" for k in keys))
    bad = _cmp(rep, exp, ("delivery_unmeasured", "delivery_measured"))
    for n in (6, 8):
        if _state(rep, n) != "UNMEASURED":
            bad.append(f"S{n} delivery is {_state(rep, n)!r}, expected 'UNMEASURED'")
    add("V-SD-UNMEASURED-NOT-ZERO", bad,
        f"measured {rep['delivery_measured']}, UNMEASURED {rep['delivery_unmeasured']} "
        f"(S6 no transcript, S8 untimed row only): {rep['unmeasured']}")
    bad = []
    if (rep["recall"]["num"], rep["recall"]["n"]) != (exp["recall"]["num"], exp["recall"]["n"]):
        bad.append(f"recall {rep['recall']['num']}/{rep['recall']['n']}, expected {exp['recall']['num']}/{exp['recall']['n']}")
    bad += _cmp(rep, exp, ("recall_line",))
    add("V-SD-RECALL", bad, rep["recall_line"])
    bad = []
    if (rep["precision"]["num"], rep["precision"]["n"]) != (exp["precision"]["num"], exp["precision"]["n"]):
        bad.append(f"precision {rep['precision']['num']}/{rep['precision']['n']}, expected "
                   f"{exp['precision']['num']}/{exp['precision']['n']}")
    if rep["precision"]["value"] is not None:
        bad.append(f"precision value {rep['precision']['value']!r} printed at n={rep['precision']['n']}")
    add("V-SD-PRECISION", bad, f"num {rep['precision']['num']}, n {rep['precision']['n']}, value None")
    bad = []
    if rep["precision_line"] != exp["precision_line"]:
        bad.append(f"precision_line {rep['precision_line']!r}, expected {exp['precision_line']!r}")
    if "/" in rep["precision_line"]:
        bad.append("a ratio is printed at n < 5")
    add("V-SD-SMALL-N", bad, rep["precision_line"])
    return out


# --------------------------------------------------------------------------- window L (the laptop pack)


def pack_sha256(path: Path) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def load_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def frozen_dcard() -> dict:
    return load_json(REPO / LEDGER_REL)["frozen"]["denominators"]["D-CARD"]


def pack_selected(row) -> bool:
    return row.get("decision") in ("deny-card", "pass-after-card") or "exit 128" in str(row.get("reason"))


def dcard_labels(rows, dcard):
    """(needed_of, beside, unconsumed, refusal). The frozen D-CARD is an aggregate (live_denies, true_positives,
    deny_shas). With true_positives != 0 no row can be labelled from it, so every row is None. Otherwise walk the
    deny-card rows in ts order against a consumable multiset of deny_shas: a match is labelled False (not needed,
    TP 0); every other delivered row is None and its session prefix goes to `beside`."""
    left = list(dcard["deny_shas"])
    if dcard.get("true_positives") != 0:
        return (lambda row: None), [], left, (f"true_positives {dcard.get('true_positives')!r} != 0: "
                                              "no row can be labelled from an aggregate")
    labels, beside = {}, []
    deny = [r for r in rows if r.get("decision") == "deny-card"]
    for row in sorted(deny, key=lambda r: judged_at(r) or 0.0):
        pre = str(row.get("session", ""))[:8]
        if pre in left:
            left.remove(pre)
            labels[id(row)] = False
        else:
            beside.append(pre)
    return (lambda row: labels.get(id(row))), beside, left, None


def pack_window(pack: dict, dcard: dict, *, wrap_labeller=None, **kw) -> dict:
    rows = pack["rows"]
    needed_of, beside, unconsumed, refusal = dcard_labels(rows, dcard)
    if wrap_labeller is not None:
        needed_of = wrap_labeller(needed_of)
    by_dec: dict = {}
    for r in rows:
        by_dec[r.get("decision")] = by_dec.get(r.get("decision"), 0) + 1
    rep = compute_window(rows, {}, {CAPABILITY}, needed_of, window="L", plane="laptop",
                         selection=f"the laptop evidence pack: {len(rows)} of {pack.get('source_ledger_rows')} "
                                   "ledger rows, picked by the builder rule", **kw)
    nameless = sum(1 for s in pack.get("sessions", {}).values() if isinstance(s, dict)
                   for t in (s.get("tool_calls") or []) if isinstance(t, dict) and t.get("tool") == "Skill")
    rep.update({
        "selection_detail": {"rule": PACK_SELECTION_RULE, "source_ledger_rows": pack.get("source_ledger_rows"),
                             "rows": len(rows), "by_decision": dict(sorted(by_dec.items()))},
        "skill_calls_without_name": nameless, "invocation_channel": "UNMEASURED",
        "recall_label": ("selection-bound: the builder picks no undelivered opportunity rows, so this is 1 by "
                         "construction and is not a population recall"),
        "population_recall": "UNMEASURED on host gex44",
        "beside_dcard": beside, "dcard_unconsumed": unconsumed, "dcard_refusal": refusal,
    })
    return rep


def l_clauses(rep: dict, pack: dict, dcard: dict, pack_path: Path | None = None) -> list:
    """Window-L clauses. Every expectation derives from the pack or from frozen D-CARD."""
    out = []

    def add(name, bad, good):
        out.append((name, "FAIL" if bad else "ok", "; ".join(bad) if bad else good))

    path = pack_path or REPO / PACK_REL
    try:
        got = pack_sha256(path)
    except OSError as exc:
        got = f"unreadable: {exc}"
    add("V-SD-L-PINNED", [] if got == PACK_SHA256 else [f"LF sha256 {got}, pinned {PACK_SHA256}"],
        f"{PACK_REL} LF sha256 {PACK_SHA256[:16]}...")
    off = [str(r.get("session"))[:8] for r in pack["rows"] if not pack_selected(r)]
    sel = rep["selection_detail"]
    add("V-SD-L-SELECTION", [f"rows outside the builder rule: {off}"] if off else [],
        f"all {sel['rows']} rows satisfy the builder rule; source_ledger_rows {sel['source_ledger_rows']}; "
        f"by_decision {sel['by_decision']}")
    add("V-SD-L-FLOOR", [] if rep["opportunities"] >= 1 else ["opportunities 0 on the real window: the detector "
                                                           "found nothing (positive control)"],
        f"opportunities {rep['opportunities']} (floor >= 1)")
    bad = [f"deny_sha {s} never matched a pack deny-card row" for s in rep["dcard_unconsumed"]]
    if rep["dcard_refusal"]:
        bad.append(rep["dcard_refusal"])
    add("V-SD-L-DCARD-MATCH", bad, f"all {len(dcard['deny_shas'])} frozen deny_shas consumed; beside D-CARD: "
        + ", ".join(rep["beside_dcard"]))
    bad = []
    pr = rep["precision"]
    if pr["n"] != dcard["live_denies"]:
        bad.append(f"precision n {pr['n']}, D-CARD live_denies {dcard['live_denies']}")
    if pr["num"] != dcard["true_positives"]:
        bad.append(f"precision num {pr['num']}, D-CARD true_positives {dcard['true_positives']}")
    if rep["unlabelled_delivered"] != len(rep["beside_dcard"]):
        bad.append(f"unlabelled_delivered {rep['unlabelled_delivered']}, beside {len(rep['beside_dcard'])}")
    if rep["precision_line"] != fmt_rate(rate(pr["num"], pr["n"])):
        bad.append(f"precision_line {rep['precision_line']!r}")
    add("V-SD-L-PRECISION", bad, f"{rep['precision_line']} derived from frozen D-CARD; unlabelled "
        f"{rep['unlabelled_delivered']}")
    bad = []
    rc = rep["recall"]
    if rc["n"] < 1 or rep["recall_line"] != fmt_rate(rate(rc["num"], rc["n"])):
        bad.append(f"recall_line {rep['recall_line']!r}")
    if not str(rep.get("recall_label", "")).startswith("selection-bound"):
        bad.append(f"recall_label {rep.get('recall_label')!r}")
    if rep.get("population_recall") != "UNMEASURED on host gex44":
        bad.append(f"population_recall {rep.get('population_recall')!r}")
    add("V-SD-L-RECALL-LABEL", bad, f"{rep['recall_line']} labelled selection-bound; population recall "
        f"{rep['population_recall']}")
    bad = [f"{k} is {rep.get(k)!r}, expected the string 'UNMEASURED'" for k in ("invocation_channel", "card_and_invocation")
           if rep.get(k) != "UNMEASURED"]
    add("V-SD-L-INVOCATION-UNMEASURED", bad, f"invocation channel UNMEASURED, card_and_invocation UNMEASURED; "
        f"{rep['skill_calls_without_name']} nameless Skill calls in the pack")
    return out


def _unlabelled_false(inner):
    """Mutant: an unlabelled delivered row is read as 'not needed'."""
    return lambda row: False if inner(row) is None else inner(row)


def _invocation_zero(rep):
    rep = dict(rep)
    rep["invocation_channel"] = 0
    return rep


def _dcard_tp(d):
    d = dict(d)
    d["true_positives"] = 1
    return d


def _empty_pack(p):
    p = dict(p)
    p["rows"] = []
    return p


def _same(x):
    return x


# (name, pack transform, D-CARD transform, labeller wrap, report transform, clause that must go red)
L_MUTANTS = (
    ("UNLABELLED-AS-FALSE", _same, _same, _unlabelled_false, _same, "V-SD-L-PRECISION"),
    ("INVOCATION-ZERO", _same, _same, None, _invocation_zero, "V-SD-L-INVOCATION-UNMEASURED"),
    ("DCARD-TP", _same, _dcard_tp, None, _same, "V-SD-L-PRECISION"),
    ("EMPTY-WINDOW", _empty_pack, _same, None, _same, "V-SD-L-FLOOR"),
)


def l_drills(pack: dict, dcard: dict) -> list:
    out = []
    clean = l_clauses(pack_window(pack, dcard), pack, dcard)
    bad = [n for n, st, _ in clean if st != "ok"]
    out.append(("V-SD-DRILL-L-CLEAN", "FAIL" if bad else "ok",
                f"clean pack window red on {bad}" if bad else f"clean pack window: all {len(clean)} L clauses ok"))
    for name, ptf, dtf, wrap, rtf, kill in L_MUTANTS:
        mp, md = ptf(pack), dtf(dcard)
        rep = rtf(pack_window(mp, md, wrap_labeller=wrap))
        res = {n: st for n, st, _ in l_clauses(rep, pack, dcard)}  # expectations stay the REAL pack and D-CARD
        survived = res.get(kill) == "ok"
        pinned = res.get("V-SD-L-PINNED") == "ok"
        if survived or not pinned:
            why = f"{kill} stayed ok (mutant survived)" if survived else "V-SD-L-PINNED went red (mutant touched the file)"
            out.append((f"V-SD-DRILL-L-{name}", "FAIL", why))
        else:
            out.append((f"V-SD-DRILL-L-{name}", "ok", f"killed by {kill}; V-SD-L-PINNED stays ok"))
    return out


def ts_clause(fx: dict, **mutants) -> tuple:
    """A-1: an unparseable card ts makes that row's delivery UNMEASURED, counted in unparseable_ts; never a crash,
    never a silent drop. Also pins the fixture card ts to the pack's 24-char ISO shape."""
    name = "V-SD-TS-UNPARSEABLE"
    clean = fixture_window(fx, **mutants)
    mut = json.loads(json.dumps(fx))
    row = next(r for r in mut["card_rows"] if r.get("decision") == "deny-card")
    row["ts"] = "not-a-time"
    try:
        rep = fixture_window(mut, **mutants)
    except Exception as exc:  # noqa: BLE001 -- a crash is the failure being tested for
        return (name, "FAIL", f"crash on an unparseable ts: {exc!r}")
    bad = []
    shape = [r["ts"] for r in fx["card_rows"] if not (isinstance(r.get("ts"), str) and TS_FORMAT.match(r["ts"]))]
    if shape:
        bad.append(f"fixture card ts not in the pack shape: {shape}")
    if rep["unparseable_ts"] != 1:
        bad.append(f"unparseable_ts {rep['unparseable_ts']}, expected 1")
    if rep["opportunities"] != clean["opportunities"]:
        bad.append(f"opportunities {rep['opportunities']}, clean {clean['opportunities']} (a silent drop)")
    if rep["delivery_unmeasured"] != clean["delivery_unmeasured"] + 1:
        bad.append(f"delivery_unmeasured {rep['delivery_unmeasured']}, expected {clean['delivery_unmeasured'] + 1}")
    if rep["delivered"] != clean["delivered"] - 1:
        bad.append(f"delivered {rep['delivered']}, expected {clean['delivered'] - 1}")
    return (name, "FAIL" if bad else "ok",
            "; ".join(bad) if bad else "unparseable ts -> UNMEASURED, counted (unparseable_ts 1), opportunity kept; "
            "fixture ts all 24-char ISO")


def _drop_unparseable(row):
    return is_opportunity(row) and judged_at(row) is not None


def ts_drill(fx: dict) -> tuple:
    """M-TS-DROP: a window that silently drops unparseable-ts rows from the opportunities is killed by
    V-SD-TS-UNPARSEABLE; the real window stays ok."""
    killed = ts_clause(fx, opportunity=_drop_unparseable)[1] == "FAIL"
    control = ts_clause(fx)[1] == "ok"
    return ("V-SD-DRILL-TS-DROP", "ok" if (killed and control) else "FAIL",
            "killed by V-SD-TS-UNPARSEABLE (a silent drop moves the opportunity count); the real window stays ok"
            if (killed and control) else f"killed={killed}, control ok={control}")


# --------------------------------------------------------------------------- live measurement (--measure-live)


def _utc(ep: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ep, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_card_ledger() -> Path:
    """Mirrors tools/skill_opportunity_signals.py card_state_dir(): env override, else ~/.claude/state/doctrine-cards."""
    d = os.environ.get("DOCTRINE_CARDS_STATE_DIR")
    base = Path(d) if d else Path.home() / ".claude" / "state" / "doctrine-cards"
    return base / "ledger.jsonl"


def measure_live(root, days, end_iso, *, root_label=None, card_ledger=None, installed=None, host=None,
                 window="live", command=None) -> dict:
    """One named live window, content-free (counts and skill names only). The defaults for installed, host and
    card_ledger are read only here, never in the gate's default mode."""
    end = si.row_epoch({"timestamp": end_iso})
    if end is None:
        raise ValueError(f"--end {end_iso!r} is not an ISO timestamp")
    start = end - days * 86400
    installed = set(installed) if installed is not None else si.installed_names()
    host = host or socket.gethostname()
    ledger = Path(card_ledger) if card_ledger is not None else default_card_ledger()
    rootp = Path(os.path.expanduser(str(root)))
    inv = si.scan(rootp, days, installed, now=end, bound_rows=True)
    names = sorted(set(inv["model"]) | set(inv["typed"]))
    rec = {
        "schema": WINDOW_RECORD_SCHEMA, "window": window, "host": host,
        "root": root_label if root_label is not None else str(root), "days": days,
        "start": _utc(start), "end": _utc(end),
        "selection": ("transcript files with mtime >= start under root; transcript rows with timestamp in "
                      "[start, end]; card rows with ts in [start, end]"),
        "installed_count": len(installed),
        "opportunity_detectors": {CAPABILITY: "commit card ledger"},
        "capability": CAPABILITY,
        "capability_invocations": {"model": inv["model"][CAPABILITY], "typed": inv["typed"][CAPABILITY]},
        "skills": {n: {"model": inv["model"][n], "typed": inv["typed"][n]} for n in names},
        "totals": {"model": sum(inv["model"].values()), "typed": sum(inv["typed"].values()),
                   "unknown_rows": inv["unknown_rows"], "untimed_rows": inv["untimed_rows"],
                   "sessions_with_calls": inv["sessions_with_calls"], "files_scanned": inv["files"]},
        "other_skills_opportunity": "UNMEASURED (no detector)",
        "command": command or "",
    }
    if not ledger.is_file():
        rec.update({"card_ledger": "ABSENT", "opportunities": "UNMEASURED", "recall": None, "precision": None,
                    "delivery": None})
        return rec
    rows = []
    with open(ledger, encoding="utf-8") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not is_commit_row(row):
                continue
            ep = judged_at(row)
            if ep is None or start <= ep <= end:  # an unparseable ts is kept: it prints UNMEASURED, never dropped
                rows.append(row)
    d_needed = dcard_labels(rows, frozen_dcard())[0]
    rep = compute_window(rows, transcript_index(rootp), installed,
                         lambda row: row["needed"] if "needed" in row else d_needed(row),
                         window=window, plane=host, selection=rec["selection"])
    keep = ("opportunities", "delivery_measured", "delivery_unmeasured", "delivered", "by_card",
            "by_invocation_only", "card_and_invocation", "pass_after_card", "no_opportunity", "judgement_unknown",
            "unlabelled_delivered", "unparseable_ts", "recall_line", "precision_line")
    rec.update({"card_ledger": "PRESENT", "opportunities": rep["opportunities"], "recall": rep["recall"],
                "precision": rep["precision"], "delivery": {k: rep[k] for k in keep}})
    return rec


def compare_records(a: dict, b: dict) -> list:
    """Every field except totals.files_scanned and command (new files appear after `end`)."""
    def strip(r):
        r = json.loads(json.dumps(r))
        r.get("totals", {}).pop("files_scanned", None)
        r.pop("command", None)
        return r
    a, b = strip(a), strip(b)
    return [f"{k}: recorded {a.get(k)!r}, re-measured {b.get(k)!r}" for k in sorted(set(a) | set(b))
            if a.get(k) != b.get(k)]


def write_record(rec: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, sort_keys=True, indent=1) + "\n")


def live_path_clause(fx: dict) -> tuple:
    """V-SD-LIVE-PATH: measure_live over the fixture materialised as a fake root plus a card ledger reproduces
    window F's expected figures, so the laptop `[C]` run executes tested code."""
    name = "V-SD-LIVE-PATH"
    exp = fx["expected"]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "projects"
        base = root / "fixture-window-F"
        base.mkdir(parents=True)
        for session, rows in fx["transcripts"].items():
            with open(base / f"{session}.jsonl", "w", encoding="utf-8", newline="\n") as fh:
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
        ledger = Path(td) / "ledger.jsonl"
        with open(ledger, "w", encoding="utf-8", newline="\n") as fh:
            for r in fx["card_rows"]:
                fh.write(json.dumps(r) + "\n")
        rec = measure_live(root, 2, "2026-10-02T00:00:00Z", card_ledger=ledger, installed=set(fx["installed"]),
                           host="fixture-host", window="F-live")
    d = rec.get("delivery") or {}
    bad = [f"{k}: live {d.get(k)!r}, window F {exp[k]!r}" for k in
           ("opportunities", "delivery_measured", "delivery_unmeasured", "delivered", "by_card",
            "by_invocation_only", "card_and_invocation", "pass_after_card", "no_opportunity",
            "judgement_unknown", "recall_line", "precision_line") if d.get(k) != exp[k]]
    if (rec.get("recall") or {}).get("num") != exp["recall"]["num"] or (rec.get("recall") or {}).get("n") != exp["recall"]["n"]:
        bad.append(f"recall {rec.get('recall')!r}, window F {exp['recall']!r}")
    if (rec.get("precision") or {}).get("num") != exp["precision"]["num"] or (rec.get("precision") or {}).get("n") != exp["precision"]["n"]:
        bad.append(f"precision {rec.get('precision')!r}, window F {exp['precision']!r}")
    return (name, "FAIL" if bad else "ok",
            "; ".join(bad) if bad else f"live path on the fixture reproduces window F: recall {d['recall_line']}, "
            f"precision {d['precision_line']}, opportunities {d['opportunities']}")


def g_record_clause(rec: dict | None) -> tuple:
    name = "V-SD-G-RECORD"
    if rec is None:
        return (name, "INCONCLUSIVE", f"{G_RECORD_REL} absent: window G was not recorded")
    bad = []
    if rec.get("schema") != WINDOW_RECORD_SCHEMA:
        bad.append(f"schema {rec.get('schema')!r}")
    if "gex44" not in str(rec.get("host")):
        bad.append(f"host {rec.get('host')!r} does not name gex44")
    if rec.get("card_ledger") != "ABSENT":
        bad.append(f"card_ledger {rec.get('card_ledger')!r}, expected ABSENT on gex44")
    if rec.get("opportunities") != "UNMEASURED":
        bad.append(f"opportunities {rec.get('opportunities')!r}, expected the string 'UNMEASURED' (never 0)")
    if rec.get("recall") is not None or rec.get("precision") is not None:
        bad.append("recall/precision must be null with no opportunity source")
    tot = rec.get("totals") or {}
    for k in ("model", "typed", "unknown_rows", "untimed_rows", "sessions_with_calls", "files_scanned"):
        if not (isinstance(tot.get(k), int) and not isinstance(tot.get(k), bool) and tot[k] >= 0):
            bad.append(f"totals.{k} {tot.get(k)!r} is not a non-negative int")
    cmd = str(rec.get("command"))
    if "--end" not in cmd or "--days" not in cmd:
        bad.append("command carries no --end/--days")
    if str(rec.get("root")).startswith("/"):
        bad.append(f"root {rec.get('root')!r} is an expanded path (A-2: store the literal ~/.claude/projects)")
    return (name, "FAIL" if bad else "ok",
            "; ".join(bad) if bad else f"host {rec['host']}, {rec['start']} .. {rec['end']}, card ledger ABSENT, "
            f"opportunities UNMEASURED, model {tot['model']} typed {tot['typed']}")


def planes_clause(text: str) -> tuple:
    """V-SD-PLANES: every non-empty line of a `## Window X` section starts with `[X] `; no line carries two tags."""
    name = "V-SD-PLANES"
    bad, cur = [], None
    for i, line in enumerate(text.split("\n"), 1):
        if line.startswith("## "):
            m = re.match(r"## Window (\w+)", line)
            cur = m.group(1) if m else None
            continue
        if cur and line.strip() and not line.startswith(f"[{cur}] "):
            bad.append(f"line {i} in Window {cur} lacks the [{cur}] prefix")
        tags = {t for t in ("[F]", "[L]", "[G]") if t in line}
        if len(tags) > 1:
            bad.append(f"line {i} carries two window tags {sorted(tags)}")
    return (name, "FAIL" if bad else "ok", "; ".join(bad[:3]) if bad else "every window line carries exactly its own tag")


def g_record_load():
    path = REPO / G_RECORD_REL
    return load_json(path) if path.is_file() else None


def _g_opportunity_zero(rec):
    rec = json.loads(json.dumps(rec))
    rec["opportunities"] = 0
    return rec


def g_drills(rec, text: str) -> list:
    out = []
    if rec is not None:
        killed = g_record_clause(_g_opportunity_zero(rec))[1] == "FAIL"
        control = g_record_clause(rec)[1] == "ok"
        out.append(("V-SD-DRILL-G-OPPORTUNITY-ZERO", "ok" if (killed and control) else "FAIL",
                    "killed by V-SD-G-RECORD (opportunities 0 with the card ledger ABSENT); the real record stays ok"
                    if (killed and control) else f"killed={killed}, control ok={control}"))
    else:
        out.append(("V-SD-DRILL-G-OPPORTUNITY-ZERO", "INCONCLUSIVE", "no window G record to mutate"))
    summed = text.rstrip("\n") + "\n[L] 6 delivered plus [G] 3 invoked = 9 total\n"
    killed = planes_clause(summed)[1] == "FAIL"
    control = planes_clause(text)[1] == "ok"
    out.append(("V-SD-DRILL-PLANE-SUM", "ok" if (killed and control) else "FAIL",
                "killed by V-SD-PLANES (a line summing two planes); the real render stays ok"
                if (killed and control) else f"killed={killed}, control ok={control}"))
    return out


# --------------------------------------------------------------------------- evidence render


def _frozen_rule() -> str:
    with open(REPO / LEDGER_REL, encoding="utf-8") as fh:
        led = json.load(fh)
    for p in led["frozen"]["pillars"]:
        if p["id"] == "C":
            return p["rule"]
    return "(frozen C rule not found)"


def _render_l() -> list:
    pack, dcard = load_json(REPO / PACK_REL), frozen_dcard()
    r = pack_window(pack, dcard)
    sel = r["selection_detail"]
    return [f"## Window L (plane: {r['plane']}, selection: {len(pack['rows'])} of {sel['source_ledger_rows']} "
            "ledger rows picked by the builder rule)", "",
            f"[L] pack: {PACK_REL}, LF sha256 {PACK_SHA256}",
            f"[L] selection rule: {sel['rule']}",
            f"[L] selection: {sel['rows']} of {sel['source_ledger_rows']} ledger rows; by decision {sel['by_decision']}",
            f"[L] opportunities: {r['opportunities']} (n={r['opportunities']})",
            f"[L] delivery measured: {r['delivery_measured']}, UNMEASURED: {r['delivery_unmeasured']}",
            f"[L] delivered: {r['delivered']} (by card {r['by_card']}, invocation-only {r['by_invocation_only']})",
            f"[L] card and invocation: {r['card_and_invocation']} (the pack ships {r['skill_calls_without_name']} "
            "Skill tool calls with no skill name, so the invocation channel is UNMEASURED, never 0 and never "
            f"{r['skill_calls_without_name']})",
            f"[L] recall: {r['recall_line']} -- {r['recall_label']}",
            f"[L] population recall: {r['population_recall']}",
            f"[L] precision (card channel): {r['precision_line']}, labels from frozen D-CARD "
            f"(live_denies {dcard['live_denies']}, true_positives {dcard['true_positives']})",
            f"[L] unlabelled delivered beside D-CARD, never folded in: {r['unlabelled_delivered']} "
            f"({', '.join(r['beside_dcard'])})",
            f"[L] pass-after-card rows (not opportunities): {r['pass_after_card']}",
            f"[L] judgement unknown (git exit 128), beside and never counted: {r['judgement_unknown']}", ""]


def _render_g() -> list:
    rec = g_record_load()
    if rec is None:
        return []
    t, cap = rec["totals"], rec["capability_invocations"]
    redo = (f"python3 tools/test_skill_delivery.py --measure-live --window {rec['window']} --root {rec['root']} "
            f"--days {rec['days']:g} --end {rec['end']} --compare {G_RECORD_REL}")
    L = [f"## Window G (plane: {rec['host']}, recorded measurement)", "",
         f"[G] host: {rec['host']}; root {rec['root']}; days {rec['days']:g}; start {rec['start']}; end {rec['end']}",
         f"[G] selection: {rec['selection']}",
         f"[G] {rec['capability']} invocations: model {cap['model']}, typed {cap['typed']} (measured); "
         f"opportunity UNMEASURED (card ledger {rec['card_ledger']} on this host)",
         "[G] recall and precision: UNMEASURED (no opportunity source on this plane)",
         f"[G] totals: model {t['model']}, typed {t['typed']}, unknown_rows {t['unknown_rows']}, "
         f"untimed_rows {t['untimed_rows']}, sessions with calls {t['sessions_with_calls']}",
         f"[G] files scanned (informational, excluded from --compare): {t['files_scanned']}",
         f"[G] installed names: {rec['installed_count']}; other skills: {rec['other_skills_opportunity']}"]
    for n, v in rec["skills"].items():
        L.append(f"[G] skill {n}: model {v['model']}, typed {v['typed']}, opportunity UNMEASURED")
    L += [f"[G] command: {rec['command']}", f"[G] command: {redo}", ""]
    return L


def render(fx: dict | None = None) -> str:
    fx = fx if fx is not None else load_fixture(REPO / FIXTURE_REL)
    rep = fixture_window(fx)
    L = ["# [C] opportunity / delivery / recall / precision -- evidence", "",
         "Frozen C rule (ledger.json, never edited here):", "", f"> {_frozen_rule()}", "",
         "## Definitions", ""]
    L += [f"- {d}" for d in DEFINITIONS]
    L += ["", "## Planes", "",
          "- Window F is the fixture plane: synthetic rows authored for a known answer, host-independent.",
          "- Window L is the laptop plane: the committed content-free evidence pack (a selection of the laptop's "
          "card ledger), pinned by its LF sha256.",
          "- Window G is this host's own transcripts (plane: the host named in its record), a recorded measurement: "
          "invocation delivery is measured there, opportunity is UNMEASURED because the host has no card ledger.",
          "- Window G is a recorded measurement, not an L5 input: the gate's default mode reads only committed files, "
          "because `--final` re-runs it on the laptop where this host's transcripts do not exist. This host's "
          "transcripts also keep growing while the run writes them, and Claude Code prunes old ones, so a fixed "
          "window can vanish.",
          "- Re-measuring on gex44 stays pinned: the window is named by --root + --days + --end, rows are bounded "
          "by their own timestamps, and --compare shows that a re-run reproduces the record.",
          "- Laptop owner command shape: python tools/test_skill_delivery.py --measure-live --window laptop --root "
          "~/.claude/projects --days 7 --end <ISO> --out vault/programs/skill-capability/evidence/C-window-laptop.json",
          "- No figure in this file sums across windows. Each figure line carries its window prefix and its n.", "",
          f"## Window {rep['window']}", "",
          f"[F] plane: {rep['plane']}",
          f"[F] selection: {rep['selection']}",
          f"[F] opportunities: {rep['opportunities']}",
          f"[F] delivery measured: {rep['delivery_measured']}",
          f"[F] delivery UNMEASURED: {rep['delivery_unmeasured']} (outside the recall n): "
          + "; ".join(rep["unmeasured"]),
          f"[F] delivered: {rep['delivered']} (card {rep['by_card']}, invocation-only "
          f"{rep['by_invocation_only']}, card and invocation {rep['card_and_invocation']})",
          f"[F] recall: {rep['recall_line']}",
          f"[F] precision: {rep['precision_line']}",
          f"[F] pass-after-card rows (not opportunities): {rep['pass_after_card']}",
          f"[F] no_opportunity rows: {rep['no_opportunity']}",
          f"[F] judgement unknown or timeout rows: {rep['judgement_unknown']}",
          f"[F] non-commit rows ignored: {rep['ignored_non_commit']}",
          f"[F] unparseable card ts (UNMEASURED, counted): {rep['unparseable_ts']}", ""]
    L += _render_l()
    L += _render_g()
    L += ["## Commands", "",
          "- command: python3 tools/test_skill_delivery.py",
          "- command: python3 tools/test_skill_delivery.py --write-evidence", "",
          "## D-SESSIONS", "",
          f"- {FRESH_SESSIONS_THIS_PHASE} fresh sessions were consumed in this phase (frozen D-SESSIONS: "
          "new_benchmark_cap 10).", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------- evidence + subprocess clauses


def evidence_current(text: str | None = None) -> tuple:
    """V-SD-EVIDENCE-CURRENT: the committed evidence file (LF-normalised) equals a fresh render()."""
    name = "V-SD-EVIDENCE-CURRENT"
    if text is None:
        try:
            with open(REPO / EVIDENCE_REL, encoding="utf-8", newline="") as fh:
                text = fh.read()
        except OSError as exc:
            return (name, "FAIL", f"{EVIDENCE_REL} unreadable ({exc}); re-render with --write-evidence")
    text = text.replace("\r\n", "\n")
    if text != render():
        return (name, "FAIL", f"{EVIDENCE_REL} differs from a fresh render; re-render with --write-evidence")
    return (name, "ok", f"{EVIDENCE_REL} equals a fresh render ({len(text)} chars, LF)")


def red_subprocess(fx: dict) -> tuple:
    """V-SD-RED-SUBPROCESS: move S4's Skill call after its judgement in a temp copy; the gate, run in a
    subprocess on that copy, must exit 1 and print `FAIL V-SD-DELIVERY` (ROADMAP Phase 3 criterion 1)."""
    name = "V-SD-RED-SUBPROCESS"
    mut = json.loads(json.dumps(fx))
    moved = 0
    for row in mut["transcripts"].get("f0000000-0000-4000-8000-000000000004", []):
        if row.get("timestamp") == "2026-10-01T10:59:00.000Z":
            row["timestamp"] = "2026-10-01T11:00:30.000Z"
            moved += 1
    if moved != 1:
        return (name, "FAIL", f"could not position the S4 Skill row (moved {moved})")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "mutated_fixture.json"
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(mut, fh)
        try:
            r = subprocess.run([sys.executable, str(REPO / SELF_REL), "--fixture", str(tmp)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        except subprocess.TimeoutExpired:
            return (name, "FAIL", "subprocess timed out after 60 s")
    if r.returncode == 1 and "FAIL V-SD-DELIVERY" in r.stdout:
        return (name, "ok", "mutated copy exited 1 and printed `FAIL V-SD-DELIVERY`")
    return (name, "FAIL", f"rc={r.returncode}, FAIL V-SD-DELIVERY in output: {'FAIL V-SD-DELIVERY' in r.stdout}")


# --------------------------------------------------------------------------- red drills


def _mention_detector(paths, capability, installed, until):
    """Mutant: a mention counter. Promotes a measured 'no' to 'yes' when the name appears in the text."""
    r = invoked_before(paths, capability, installed, until)
    if r is False:
        for p in paths:
            with open(p, encoding="utf-8", errors="replace") as fh:
                if capability in fh.read():
                    return True
    return r


def _no_until_detector(paths, capability, installed, until):
    """Mutant: the join without the judgement-time bound (an effectively infinite `until`)."""
    return invoked_before(paths, capability, installed, 1e12)


def _untimed_as_none_detector(paths, capability, installed, until):
    """Mutant (A-1): a session that has transcripts but no timed hit is 'not delivered', untimed or not."""
    r = invoked_before(paths, capability, installed, until)
    return False if (r is None and paths) else r


def _pass_after_opportunity(row):
    """Mutant: the re-issued commit after a deny-card counts as a second opportunity."""
    return is_opportunity(row) or (is_commit_row(row) and row.get("decision") == "pass-after-card"
                                   and len(row.get("foreign") or []) >= 1)


def _always_ratio(r):
    return f"{r['num']}/{r['n']} = {r['num'] / r['n']:.3f} (n={r['n']})"


# (name, compute_window kwargs, clause that must go red, clauses that must stay ok)
MUTANTS = (
    ("MENTION", {"detector": _mention_detector}, "V-SD-DELIVERY", ("V-SD-OPPORTUNITY", "V-SD-UNMEASURED-NOT-ZERO")),
    ("NO-UNTIL", {"detector": _no_until_detector}, "V-SD-DELIVERY", ("V-SD-OPPORTUNITY",)),
    ("ABSENT-AS-NONE", {"absent_policy": "none"}, "V-SD-UNMEASURED-NOT-ZERO", ("V-SD-OPPORTUNITY", "V-SD-DELIVERY")),
    ("UNTIMED-AS-NONE", {"detector": _untimed_as_none_detector}, "V-SD-UNMEASURED-NOT-ZERO",
     ("V-SD-OPPORTUNITY", "V-SD-DELIVERY")),
    ("PASS-AFTER", {"opportunity": _pass_after_opportunity}, "V-SD-OPPORTUNITY", ("V-SD-DELIVERY",)),
    ("SMALL-N-RATIO", {"fmt": _always_ratio}, "V-SD-SMALL-N", ("V-SD-RECALL",)),
)


def drills(fx: dict) -> list:
    """Each mutant must die on its named clause while its control clauses stay ok; the clean fixture is
    all ok (positive control, so a drill that cannot pass the clean case proves nothing)."""
    out = []
    clean = f_clauses(fixture_window(fx), fx)
    bad = [n for n, st, _ in clean if st != "ok"]
    out.append(("V-SD-DRILL-CLEAN", "FAIL" if bad else "ok",
                f"clean fixture red on {bad}" if bad else f"clean fixture: all {len(clean)} F clauses ok"))
    for name, kw, kill, controls in MUTANTS:
        res = {n: st for n, st, _ in f_clauses(fixture_window(fx, **kw), fx)}
        survived = res.get(kill) == "ok"
        broken = [c for c in controls if res.get(c) != "ok"]
        if survived or broken:
            why = f"{kill} stayed ok (mutant survived)" if survived else f"control clauses went red: {broken}"
            out.append((f"V-SD-DRILL-{name}", "FAIL", why))
        else:
            out.append((f"V-SD-DRILL-{name}", "ok", f"killed by {kill}; controls ok: {', '.join(controls)}"))
    out.append(ts_clause(fx))
    out.append(ts_drill(fx))
    pack, dcard = load_json(REPO / PACK_REL), frozen_dcard()
    out += l_drills(pack, dcard)
    text = render(fx)
    out += g_drills(g_record_load(), text)
    digit = next(i for i, ch in enumerate(text) if ch.isdigit())
    stale = text[:digit] + str((int(text[digit]) + 1) % 10) + text[digit + 1:]
    killed, control = evidence_current(stale)[1] != "ok", evidence_current(text)[1] == "ok"
    out.append(("V-SD-DRILL-STALE-EVIDENCE", "ok" if (killed and control) else "FAIL",
                "killed by V-SD-EVIDENCE-CURRENT; a fresh render stays ok" if (killed and control)
                else f"stale text killed={killed}, fresh render ok={control}"))
    return out


# --------------------------------------------------------------------------- CLI


def _print(results) -> int:
    ok = 0
    for name, status, text in results:
        label = {"ok": "  ok   ", "FAIL": "  FAIL ", "INCONCLUSIVE": "  INCONCLUSIVE "}[status]
        print(f"{label}{name} {text}")
        ok += status == "ok"
    print(f"SD_PASS={ok}/{len(results)}")
    return 0 if ok == len(results) else 1


def _cli_measure(a) -> int:
    if not a.end:
        print("REFUSED --end is required: a live window is named by its end", file=sys.stderr)
        return 2
    cmd = (f"{Path(sys.executable).name} tools/test_skill_delivery.py --measure-live --window {a.window} "
           f"--root {a.root} --days {a.days:g} --end {a.end}")
    try:
        rec = measure_live(a.root, a.days, a.end, root_label=a.root, card_ledger=a.card_ledger, window=a.window,
                           command=cmd)
    except (ValueError, OSError) as exc:
        print(f"cannot measure: {exc}", file=sys.stderr)
        return 2
    if a.compare:
        diff = compare_records(load_json(Path(a.compare)), rec)
        for d in diff:
            print(f"DIFF {d}")
        print("compare: identical" if not diff else f"compare: {len(diff)} field(s) differ")
        return 1 if diff else 0
    if a.out:
        write_record(rec, Path(a.out))
        print(f"wrote {a.out}")
    else:
        print(json.dumps(rec, sort_keys=True, indent=1))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fixture", help="evaluate the window-F clauses on this fixture only")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write-evidence", action="store_true")
    ap.add_argument("--measure-live", action="store_true", help="measure one named live window (see --root/--days/--end)")
    ap.add_argument("--root", default="~/.claude/projects")
    ap.add_argument("--days", type=float, default=7)
    ap.add_argument("--end", help="ISO end of the window (required with --measure-live)")
    ap.add_argument("--window", default="live")
    ap.add_argument("--card-ledger")
    ap.add_argument("--out")
    ap.add_argument("--compare")
    a = ap.parse_args(argv)
    if a.measure_live:
        return _cli_measure(a)
    fpath = Path(a.fixture) if a.fixture else REPO / FIXTURE_REL
    try:
        fx = load_fixture(fpath)
        rep = fixture_window(fx)
    except (OSError, ValueError, KeyError) as exc:
        print(f"cannot run: {fpath}: {exc}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps([rep, pack_window(load_json(REPO / PACK_REL), frozen_dcard())], indent=1))
        return 0
    if a.write_evidence:
        with open(REPO / EVIDENCE_REL, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render(fx))
        print(f"wrote {EVIDENCE_REL}")
        return 0
    results = f_clauses(rep, fx)
    if not a.fixture:
        pack, dcard = load_json(REPO / PACK_REL), frozen_dcard()
        results += l_clauses(pack_window(pack, dcard), pack, dcard)
        results.append(live_path_clause(fx))
        results.append(g_record_clause(g_record_load()))
        results.append(planes_clause(render(fx)))
        results.append(evidence_current())
        results += drills(fx)
        results.append(red_subprocess(fx))
    return _print(results)


if __name__ == "__main__":
    sys.exit(main())
