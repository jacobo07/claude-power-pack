"""E1 report: renders e1/REPORT.md from e1/results.jsonl (plan 04-01). Nothing in the report is hand-written that
the records can say.

The decisions are the stop record's `final_decisions`, re-derived independently by e1_contract.replay +
final_decisions over the same records; a missing stop record, a record set replay refuses, or any disagreement is
a refusal (no file written, exit 1). Tokens are reported and never read by the decision path (clause 4).

    python3 vault/programs/cognitive-economy/e1/e1_report.py check  [--results PATH]
    python3 vault/programs/cognitive-economy/e1/e1_report.py render [--results PATH] [--out PATH]

check: the refusal gate alone, printing `REPORT OK <condition>` or `REPORT REFUSED <why>`.
render: check, then write the report (default e1/REPORT.md). An --out under ~/.claude is refused: the report
proposes the move list and changes nothing there (HR-001)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e1_contract as K  # noqa: E402
import e1_runner as R  # noqa: E402

ADDENDUM = HERE / "ADDENDUM-E1.md"
REPORT = HERE / "REPORT.md"
LIMITS_HEADING = "## Known limits, stated before the numbers"
CEILING = "no loss observed at n=1 per rule"
HOME_CLAUDE = Path.home() / ".claude"


class ReportRefused(Exception):
    pass


def limits_section(addendum=ADDENDUM):
    """The ADDENDUM-E1 'Known limits' section, verbatim (heading excluded)."""
    text = Path(addendum).read_text(encoding="utf-8")
    i = text.find(LIMITS_HEADING)
    if i < 0:
        raise ReportRefused(f"{addendum}: no '{LIMITS_HEADING}' section")
    body = text[i + len(LIMITS_HEADING):]
    j = body.find("\n## ")
    return (body if j < 0 else body[:j]).strip("\n")


def checked(order, records, r2_rules=R.EXCLUDED_BY_R2):
    """-> (state, stop). Raises ReportRefused unless the campaign ended on a stop record whose decisions the
    contract re-derives exactly from the same records."""
    try:
        state = K.replay(order, records)
    except K.ContractError as e:
        raise ReportRefused(f"replay refused the records: {e}")
    stop = state["stop"]
    if stop is None:
        last = records[-1].get("kind") if records else None
        raise ReportRefused(f"no stop record (last record kind {last!r}): the campaign has not ended")
    cond = stop.get("condition")
    if cond not in K.STOP_CONDITIONS:
        raise ReportRefused(f"stop record names unknown condition {cond!r}")
    try:
        want = K.final_decisions(state, cond, r2_rules)
    except K.ContractError as e:
        raise ReportRefused(f"final decisions refused: {e}")
    if stop.get("final_decisions") != want:
        bad = sorted(r for r in set(want) | set(stop.get("final_decisions") or {})
                     if (stop.get("final_decisions") or {}).get(r) != want.get(r))
        raise ReportRefused(f"stop record decisions differ from the replay for {bad}")
    if stop.get("spent") != state["spent"] or stop.get("runs_counted") != state["runs_counted"]:
        raise ReportRefused(f"stop record spent/runs {stop.get('spent')}/{stop.get('runs_counted')} != replay "
                            f"{state['spent']}/{state['runs_counted']}")
    return state, stop


def _n(v):
    return "-" if v is None else (f"{v:,}" if isinstance(v, int) and not isinstance(v, bool) else str(v))


def _runs(records):
    return [r for r in records if r.get("kind") == "run"]


def _pair_of(state):
    return {rid: t["id"] for t in state["tasks"] for rid in t["runs"]}


def move_list(stop):
    """Rules proposed for relocation: E1 relocation candidates + R2 carried. Empty on a harm or control stop."""
    if stop["condition"] in (K.HARM_STOP, K.POSITIVE_CONTROL_STOP):
        return []
    return sorted(r for r, d in stop["final_decisions"].items()
                  if d["decision"] in (K.RELOCATION_CANDIDATE, K.R2_CARRIED))


def is_ceiling(state):
    """Every task has a valid pair and every pair passed in both arms."""
    return (bool(state["tasks"]) and all(t["status"] == K.PAIR_VALID for t in state["tasks"])
            and all(t["decision"] == K.RELOCATION_CANDIDATE for t in state["tasks"]))


def render(order, records, *, addendum=ADDENDUM, r2_rules=R.EXCLUDED_BY_R2):
    state, stop = checked(order, records, r2_rules)
    cond, fd = stop["condition"], stop["final_decisions"]
    runs = _runs(records)
    pair_of = _pair_of(state)
    first = runs[0] if runs else {}
    L = []
    L += ["# E1 report", "",
          f"Rendered by `e1_report.py` from `results.jsonl` ({len(records)} records). Contract: `ADDENDUM-E1.md`.",
          "", f"**Stop condition: `{cond}`** (stop record at {stop.get('at', '-')}).", "",
          f"- Runs counted: {stop['runs_counted']}; valid pairs: {stop['valid_pairs']}; "
          f"losses in the first {K.HARM_WINDOW} valid pairs: {stop['losses_in_window']}",
          f"- Model `{first.get('model', '-')}`, CLI `{first.get('cli_version', '-')}`, BASE `{first.get('base', '-')}`",
          ""]
    if cond == K.ALL_DECIDED and is_ceiling(state):
        L += [f"Every pair passed in both arms: {CEILING}. This is a ceiling, not a measured absence of effect.", ""]

    L += ["## Decisions", "",
          "| rule | decision | basis | task | A run | B run | A pass | B pass |", "|---|---|---|---|---|---|---|---|"]
    tasks = {t["id"]: t for t in state["tasks"]}
    for rule in [t["rule"] for t in state["tasks"]] + sorted(r for r in fd if r not in {t["rule"] for t in state["tasks"]}):
        d = fd[rule]
        t = tasks.get(d.get("task"), {})
        L.append(f"| `{rule}` | {d['decision']} | {d['basis']} | {d.get('task') or '-'} | {d.get('a_run') or '-'} "
                 f"| {d.get('b_run') or '-'} | {_n(t.get('a_pass'))} | {_n(t.get('b_pass'))} |")
    flagged = [t["id"] for t in state["tasks"] if t.get("b_pass_where_a_fails")]
    L += ["", "Decisions are the contract's (clause 4); no token count breaks a tie. "
          + (f"B passed where A failed (reported, never used): {', '.join(flagged)}." if flagged
             else "No task where B passed and A failed."), ""]
    by_id = {r["run_id"]: r for r in runs}
    weak = [f"{t['id']} ({by_id[t['b_run']].get('grade_summary')})" for t in state["tasks"]
            if t["decision"] == K.STAYS and t["b_run"] in by_id
            and any(str(f).startswith("control ") for f in by_id[t["b_run"]].get("grade_fails") or [])]
    if weak:
        L += ["Losses whose B run also failed control checks (the solution broke the task's plain behaviour, not only "
              "its judgement; the decision stands, attribution to the rule is weaker): " + ", ".join(weak) + ".", ""]

    pc = stop.get("positive_control")
    L += ["## Positive control (gate 1, first valid pair)", ""]
    if pc:
        L += [f"Task {pc['task']}: A first-call context {_n(pc['a_first'])}, B {_n(pc['b_first'])}, "
              f"delta {_n(pc['delta'])} (needs >= {K.PC_DELTA:,}): {'OK' if pc['ok'] else 'FAILED -- arms did not differ'}.", ""]
    else:
        L += ["No valid pair: the positive control was never evaluated.", ""]

    deltas = [t["a_first"] - t["b_first"] for t in state["tasks"] if t["status"] == K.PAIR_VALID
              and isinstance(t["a_first"], int) and isinstance(t["b_first"], int)]
    L += ["## Spend", "",
          f"- Counted context summed over all runs (valid and invalid): {_n(stop['spent'])} of the "
          f"{K.CAP:,} cap; over the cap by {_n(stop.get('over_cap_by'))}; largest run {_n(stop.get('max_seen'))}",
          f"- First-call delta A - B over {len(deltas)} valid pairs: "
          + (f"mean {sum(deltas) // len(deltas):,}, min {min(deltas):,}, max {max(deltas):,}" if deltas else "none measured"),
          "- Logical transcript tokens only; the account meter's weighting is not derived from them.", ""]

    L += ["## Runs", "",
          "| run | valid | invalid reasons | grade | first-call ctx | total ctx | output tokens |",
          "|---|---|---|---|---|---|---|"]
    for r in runs:
        m = r.get("metrics") if isinstance(r.get("metrics"), dict) else {}
        L.append(f"| {r['run_id']} | {r.get('valid')} | {'; '.join(r.get('invalid_reasons') or []) or '-'} "
                 f"| {r.get('grade_summary') or '-'} | {_n(m.get('first_call_context'))} "
                 f"| {_n(m.get('total_context'))} | {_n(m.get('output_tokens'))} |")
    L.append("")

    L += ["## Bank-access audit", "",
          "Each run's transcript tool calls were searched for the bank's markers (Phase 1 limit: the shared object "
          "store makes the bank reachable by git from a run tree). A hit is reported against its pair; it changes "
          "no decision.", ""]
    hits, unaudited = [], []
    for r in runs:
        ba = r.get("bank_access")
        if not r.get("session_launched"):
            continue
        if ba is None:
            unaudited.append(f"{r['run_id']} ({r.get('bank_access_error') or 'no transcript'})")
        elif ba:
            hits.append(f"{r['run_id']} (pair {pair_of.get(r['run_id'], '-')}): {len(ba)} hit(s), first "
                        f"`{ba[0][0]}` in `{ba[0][1]!r}`")
    L += [f"- Hit: {h}" for h in hits] or ["- No marker hit in any audited run."]
    L += [f"- NOT AUDITED: {u}" for u in unaudited]
    L.append("")

    moves = move_list(stop)
    L += ["## Proposed move list (for the Owner)", ""]
    if moves:
        L += [f"- `{m}`" for m in moves]
        L += ["", "Each move is a global config write under `~/.claude/rules` (rule -> skill + one-line pointer) and "
              "needs the Owner's yes on this exact list (HR-001). This report changed nothing under `~/.claude`.",
              "After a move, a one-call gate-1 probe confirms the billed floor fell by the relocated rules' share."]
    else:
        L += [f"None: `{cond}` keeps every rule resident. This report changed nothing under `~/.claude`."]
    L += ["", "## Known limits (ADDENDUM-E1, verbatim)", "", limits_section(addendum), ""]
    return "\n".join(L)


def _out_ok(out):
    p = Path(out).resolve()
    home = HOME_CLAUDE.resolve()
    if p == home or home in p.parents:
        raise ReportRefused(f"output {p} is under {home}: the report changes nothing there")
    return p


def main(argv, *, order=None):
    cmd, rest = (argv[0], argv[1:]) if argv else (None, [])
    opts = {}
    while rest:
        if rest[0] in ("--results", "--out") and len(rest) > 1:
            opts[rest[0]], rest = rest[1], rest[2:]
        else:
            print(__doc__)
            return 2
    if cmd not in ("check", "render"):
        print(__doc__)
        return 2
    results = opts.get("--results", R.RESULTS)
    try:
        out = _out_ok(opts.get("--out", REPORT)) if cmd == "render" else None
        if order is None:
            order = R.ordered_tasks(R.load_bank(R.BANK_DIR))
        records = R.read_records(results)
        state, stop = checked(order, records)
        if cmd == "check":
            print(f"REPORT OK {stop['condition']} runs={stop['runs_counted']} spent={stop['spent']}")
            return 0
        text = render(order, records)
    except (ReportRefused, K.ContractError) as e:
        print(f"REPORT REFUSED {e}")
        return 1
    out.write_text(text, encoding="utf-8")
    print(f"REPORT WRITTEN {out} {stop['condition']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
