"""V-E1R-* gates for the E1 report renderer (plan 04-01). Synthetic records come from test_e1_runner's own
`simulate` / `pair` helpers (its no-model guard is installed on import), so the report is tested against the
records the contract code produces, each gate with its red branch.

    python3 vault/programs/cognitive-economy/e1/test_e1_report.py

Ends `E1R_PASS=<passes>/<total>`; exit 0 only when every gate passed.
"""
import sys

sys.dont_write_bytecode = True

import json  # noqa: E402
import tempfile  # noqa: E402
import traceback  # noqa: E402
from pathlib import Path  # noqa: E402

E1 = Path(__file__).resolve().parent
sys.path.insert(0, str(E1))
import test_e1_runner as T  # noqa: E402  (installs the no-model guard first)
import e1_contract as K  # noqa: E402
import e1_report as P  # noqa: E402

ORDER = T.mk_order()
R2 = T.R2_RULES


def campaign(outcome):
    """outcome(task, arm, attempt) -> run kwargs for T.mk_run; returns the simulated records with their stop."""
    recs, act = T.simulate(ORDER, lambda task, arm, att: T.mk_run(task, arm, att, **outcome(task, arm, att)))
    return recs, act


def all_pass(*_):
    return {}


def refused(records):
    try:
        P.checked(ORDER, records, R2)
        return None
    except P.ReportRefused as e:
        return str(e)


def rendered(records):
    return P.render(ORDER, records, r2_rules=R2)


def g_all_decided():
    recs, act = campaign(all_pass)
    text = rendered(recs)
    rows = [l for l in text.splitlines() if l.startswith("| `rules/")]
    cited = all(f"| {i}-A-a1 | {i}-B-a1 |" in text for i in T.ORDER_IDS)
    r2 = all(f"| `{r}` | {K.R2_CARRIED} |" in text for r in R2)
    moves = text.split("## Proposed move list")[1].split("## Known limits")[0]
    ok = (act == ("STOP", K.ALL_DECIDED) and len(rows) == 13 and cited and r2
          and moves.count("- `rules/") == 13 and "HR-001" in moves)
    return ok, f"act={act} rows={len(rows)} cited={cited} r2={r2} moves={moves.count('- `rules/')}"


def g_not_finished():
    recs, _ = campaign(all_pass)
    open_ = [r for r in recs if r.get("kind") != "stop"]
    why = refused(open_)
    control = refused(recs)
    ok = why is not None and "no stop record" in why and control is None
    return ok, f"open={why!r} control={control!r}"


def g_tampered():
    recs, _ = campaign(all_pass)
    stop = json.loads(json.dumps(recs[-1]))
    rule = T.E1_RULES[3]
    stop["final_decisions"][rule]["decision"] = K.STAYS
    why = refused(recs[:-1] + [stop])
    spent = json.loads(json.dumps(recs[-1]))
    spent["spent"] = 1
    why2 = refused(recs[:-1] + [spent])
    ok = why is not None and rule in why and why2 is not None and "spent" in why2
    return ok, f"decision={why!r} spent={why2!r}"


def g_replay_refused():
    recs, _ = campaign(all_pass)
    dup = recs[:1] + recs  # the same run twice
    why = refused(dup)
    return why is not None and "replay refused" in why, f"{why!r}"


def g_harm():
    recs, act = campaign(lambda task, arm, att: {"passed": arm == "A"})
    text = rendered(recs)
    moves = text.split("## Proposed move list")[1]
    ok = (act == ("STOP", K.HARM_STOP) and "None: `HARM_STOP`" in moves and "- `rules/" not in moves.split("##")[0]
          and text.count("harm stop: group exclusion falsified") == 13)
    return ok, f"act={act} harm_rows={text.count('harm stop: group exclusion falsified')}"


def g_posctl():
    recs, act = campaign(lambda task, arm, att: {"first": 100_000 if arm == "A" else 90_000})
    text = rendered(recs)
    ok = (act == ("STOP", K.POSITIVE_CONTROL_STOP) and "FAILED -- arms did not differ" in text
          and "None: `POSITIVE_CONTROL_STOP`" in text and P.CEILING not in text)
    return ok, f"act={act}"


def g_ceiling():
    recs, _ = campaign(all_pass)
    text = rendered(recs).lower()
    one_loss, _ = campaign(lambda task, arm, att: {"passed": not (task == T.ORDER_IDS[2] and arm == "B")})
    lossy = rendered(one_loss)
    ok = (P.CEILING in text and "no effect" not in text.replace("not a measured absence of effect", "")
          and P.CEILING not in lossy and f"| `{T.E1_RULES[2]}` | {K.STAYS} |" in lossy)
    return ok, f"ceiling={P.CEILING in text} lossy_has_ceiling={P.CEILING in lossy}"


def g_tokens_no_tiebreak():
    a, _ = campaign(all_pass)
    b, _ = campaign(lambda task, arm, att: {"total": 650_000 if arm == "B" else 750_000})
    da = a[-1]["final_decisions"]
    db = b[-1]["final_decisions"]
    return da == db, f"same decisions under different tokens: {da == db}"


def g_bank_access():
    recs, _ = campaign(all_pass)
    hit_id, none_id = f"{T.ORDER_IDS[1]}-B-a1", f"{T.ORDER_IDS[4]}-A-a1"
    for r in recs:
        if r.get("run_id") == hit_id:
            r["bank_access"] = [["d68871742a", "git show d68871742a:bank/x.py"]]
        elif r.get("run_id") == none_id:
            r["bank_access"], r["bank_access_error"] = None, "OSError: gone"
        elif r.get("kind") == "run":
            r["bank_access"] = []
    text = rendered(recs)
    clean, _ = campaign(all_pass)
    for r in clean:
        if r.get("kind") == "run":
            r["bank_access"] = []
    ctext = rendered(clean)
    ok = (f"Hit: {hit_id} (pair {T.ORDER_IDS[1]})" in text and f"NOT AUDITED: {none_id} (OSError: gone)" in text
          and "No marker hit" in ctext and "NOT AUDITED" not in ctext)
    return ok, f"hit={hit_id in text} unaudited={'NOT AUDITED' in text} clean={'No marker hit' in ctext}"


def g_weak_loss():
    lose = T.ORDER_IDS[1]
    recs, _ = campaign(lambda task, arm, att: {"passed": not (task == lose and arm == "B")})
    plain = rendered(recs)
    for r in recs:
        if r.get("run_id") == f"{lose}-B-a1":
            r["grade_fails"] = ["control first_request_starts 'refused'"]
    weak = rendered(recs)
    ok = "also failed control checks" in weak and lose in weak.split("also failed control")[1].split("\n")[0] \
        and "also failed control checks" not in plain
    return ok, f"weak={'also failed control' in weak} plain={'also failed control' in plain}"


def g_spend_stop_undecided():
    recs, act = campaign(lambda task, arm, att: {"total": 2_000_000})
    text = rendered(recs)
    und = text.count(f"| {K.UNDECIDED_STAYS} |")
    moves = text.split("## Proposed move list")[1].split("## Known limits")[0]
    ok = act == ("STOP", K.SPEND_STOP) and und > 0 and und + moves.count("- `rules/") - 2 == 11
    return ok, f"act={act} undecided={und} moves={moves.count('- `rules/')}"


def g_limits_verbatim():
    real = P.limits_section()
    text = Path(P.ADDENDUM).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as d:
        bad = Path(d) / "a.md"
        bad.write_text("# no limits here\n", encoding="utf-8")
        try:
            P.limits_section(bad)
            red = None
        except P.ReportRefused as e:
            red = str(e)
    ok = real and real in text and "n = 1 pair per rule" in real and red is not None
    return ok, f"len={len(real)} red={red!r}"


def g_home_refused():
    try:
        P._out_ok(P.HOME_CLAUDE / "rules" / "x.md")
        red = None
    except P.ReportRefused as e:
        red = str(e)
    with tempfile.TemporaryDirectory() as d:
        green = P._out_ok(Path(d) / "REPORT.md")
    return red is not None and green.name == "REPORT.md", f"red={red!r}"


def g_cli():
    recs, _ = campaign(all_pass)
    with tempfile.TemporaryDirectory() as d:
        res, out = Path(d) / "r.jsonl", Path(d) / "REPORT.md"
        res.write_text("".join(json.dumps(r) + "\n" for r in recs[:-1]), encoding="utf-8")
        rc_open = P.main(["render", "--results", str(res), "--out", str(out)], order=ORDER)
        wrote_open = out.exists()
        res.write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
        rc_check = P.main(["check", "--results", str(res)], order=ORDER)
        rc = P.main(["render", "--results", str(res), "--out", str(out)], order=ORDER)
        body = out.read_text(encoding="utf-8") if out.exists() else ""
        rc_home = P.main(["render", "--results", str(res), "--out", str(P.HOME_CLAUDE / "E1-REPORT.md")], order=ORDER)
        rc_usage = P.main(["bogus"], order=ORDER)
    ok = (rc_open == 1 and not wrote_open and rc_check == 0 and rc == 0 and body.startswith("# E1 report")
          and rc_home == 1 and not (P.HOME_CLAUDE / "E1-REPORT.md").exists() and rc_usage == 2)
    return ok, f"open={rc_open}/{wrote_open} check={rc_check} render={rc} home={rc_home} usage={rc_usage}"


GATES = [
    ("V-E1R-ALL-DECIDED", g_all_decided), ("V-E1R-NOT-FINISHED", g_not_finished), ("V-E1R-TAMPERED", g_tampered),
    ("V-E1R-REPLAY-REFUSED", g_replay_refused), ("V-E1R-HARM", g_harm), ("V-E1R-POSCTL", g_posctl),
    ("V-E1R-CEILING", g_ceiling), ("V-E1R-TOKENS-NO-TIEBREAK", g_tokens_no_tiebreak),
    ("V-E1R-BANK-ACCESS", g_bank_access), ("V-E1R-WEAK-LOSS", g_weak_loss),
    ("V-E1R-SPEND-UNDECIDED", g_spend_stop_undecided),
    ("V-E1R-LIMITS", g_limits_verbatim), ("V-E1R-HOME-REFUSED", g_home_refused), ("V-E1R-CLI", g_cli),
]


def main():
    passes = 0
    for name, fn in GATES:
        try:
            ok, ev = fn()
        except Exception as e:  # a crashing gate is a FAIL, never a silent skip
            ok, ev = False, f"crashed: {type(e).__name__}: {e} | {traceback.format_exc().splitlines()[-3:]}"
        passes += bool(ok)
        print(f"{'PASS' if ok else 'FAIL'} {name} {str(ev)[:300]}")
    no_model = not T.BLOCKED
    print(f"{'PASS' if no_model else 'FAIL'} V-E1R-NO-MODEL blocked={len(T.BLOCKED)}")
    passes += no_model
    total = len(GATES) + 1
    print(f"E1R_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
