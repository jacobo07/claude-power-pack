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
import json
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
    c = dict(opportunities=0, pass_after_card=0, no_opportunity=0, judgement_unknown=0, ignored_non_commit=0)
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
        if dec == "deny-card":
            state = "card"
        elif invoked is True:
            state = "invocation"
        elif invoked is False:
            state = "none"
        else:
            state = "UNMEASURED"
            why = "no judgement ts" if until is None else (
                "no transcript read" if not paths else "only untimed candidate rows")
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
        "unlabelled_delivered": len(delivered) - len(labelled),
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


# --------------------------------------------------------------------------- evidence render


def _frozen_rule() -> str:
    with open(REPO / LEDGER_REL, encoding="utf-8") as fh:
        led = json.load(fh)
    for p in led["frozen"]["pillars"]:
        if p["id"] == "C":
            return p["rule"]
    return "(frozen C rule not found)"


def render(fx: dict | None = None) -> str:
    fx = fx if fx is not None else load_fixture(REPO / FIXTURE_REL)
    rep = fixture_window(fx)
    L = ["# [C] opportunity / delivery / recall / precision -- evidence", "",
         "Frozen C rule (ledger.json, never edited here):", "", f"> {_frozen_rule()}", "",
         "## Definitions", ""]
    L += [f"- {d}" for d in DEFINITIONS]
    L += ["", "## Planes", "",
          "- Window F is the fixture plane: synthetic rows authored for a known answer, host-independent.",
          "- No figure in this file sums across windows. Each figure line carries its window prefix and its n.", "",
          f"## Window {rep['window']}", "",
          f"- [F] plane: {rep['plane']}",
          f"- [F] selection: {rep['selection']}",
          f"- [F] opportunities: {rep['opportunities']}",
          f"- [F] delivery measured: {rep['delivery_measured']}",
          f"- [F] delivery UNMEASURED: {rep['delivery_unmeasured']} (outside the recall n): "
          + "; ".join(rep["unmeasured"]),
          f"- [F] delivered: {rep['delivered']} (card {rep['by_card']}, invocation-only "
          f"{rep['by_invocation_only']}, card and invocation {rep['card_and_invocation']})",
          f"- [F] recall: {rep['recall_line']}",
          f"- [F] precision: {rep['precision_line']}",
          f"- [F] pass-after-card rows (not opportunities): {rep['pass_after_card']}",
          f"- [F] no_opportunity rows: {rep['no_opportunity']}",
          f"- [F] judgement unknown or timeout rows: {rep['judgement_unknown']}",
          f"- [F] non-commit rows ignored: {rep['ignored_non_commit']}", "",
          "## Commands", "",
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
    text = render(fx)
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fixture", help="evaluate the window-F clauses on this fixture only")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write-evidence", action="store_true")
    a = ap.parse_args(argv)
    fpath = Path(a.fixture) if a.fixture else REPO / FIXTURE_REL
    try:
        fx = load_fixture(fpath)
        rep = fixture_window(fx)
    except (OSError, ValueError, KeyError) as exc:
        print(f"cannot run: {fpath}: {exc}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps([rep], indent=1))
        return 0
    if a.write_evidence:
        with open(REPO / EVIDENCE_REL, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render(fx))
        print(f"wrote {EVIDENCE_REL}")
        return 0
    results = f_clauses(rep, fx)
    if not a.fixture:
        results.append(evidence_current())
        results += drills(fx)
        results.append(red_subprocess(fx))
    return _print(results)


if __name__ == "__main__":
    sys.exit(main())
