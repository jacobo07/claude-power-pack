#!/usr/bin/env python3
"""Intent-fidelity gate -- does the output satisfy the intent that started it?

Standing scope (Owner decision 2026-08-14): resolve every spec statically,
observe only the spec bound to the current task. Cost stays flat as the spec
corpus grows, which is what keeps the row on every push.

  python tools/intent_verify.py                       # standing gate
  python tools/intent_verify.py --task "<description>" # + observe the bound spec
  python tools/intent_verify.py --spec vault/specs/x.md --observe
  python tools/intent_verify.py --baseline            # record the ratchet

Exit 0 iff no critical criterion of the task under verification is unobserved
or failing, AND the named ratchet did not regress. The exit condition is an
absolute count -- never a ratio, which is satisfied by deleting criteria.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.intent_verified import (  # noqa: E402
    Observed, Reach, Verdict, blocking_count, decide, emitters, iter_specs,
    observe, read_criteria, resolve, spec_label, standing_gate_targets,
    verify_task,
)
from modules.intent_verified.ratchet import (  # noqa: E402
    DEFAULT_BASELINE, check as ratchet_check, save as ratchet_save,
)

REPORT = PP_ROOT / "vault" / "intent_verified" / "intent_verification_report.md"
DEBT = PP_ROOT / "vault" / "intent_verified" / "intent_not_captured.jsonl"


def _collect(root: Path) -> tuple[list, list[str], list[str]]:
    """Resolve every spec in the repo. Returns (results, unreadable, silent).

    `silent` = a spec whose acceptance section names no V-gate criterion, kept
    separate from one that names criteria nothing can reach.
    """
    index, reached = emitters(root), standing_gate_targets(root)
    results, unreadable, silent = [], [], []
    for spec in iter_specs(root):
        label = spec_label(spec, root)
        try:
            criteria = read_criteria(spec, root)
        except OSError as exc:
            unreadable.append(f"{label} ({type(exc).__name__})")
            continue
        if not criteria:
            silent.append(label)
            continue
        results.extend(resolve(criteria, root, index, reached))
    return results, unreadable, silent


def _write_report(root: Path, results: list, unreadable: list[str],
                  silent: list[str], ratchet, task_v=None) -> Path:
    by_reach = {r: [x for x in results if x.reach is r] for r in Reach}
    lines = [
        "# Intent verification report",
        "",
        f"Specs with mechanical criteria: "
        f"{len({r.criterion.spec for r in results})}",
        f"Criteria declared: {len(results)}",
        "",
        "| Reach | Count |",
        "|---|---:|",
    ]
    lines += [f"| {r.value} | {len(v)} |" for r, v in by_reach.items()]
    if silent:
        lines += ["", "## Criteria not mechanical", ""]
        lines += [f"- {s}" for s in silent]
    if unreadable:
        lines += ["", "## Unreadable specs", ""]
        lines += [f"- {s}" for s in unreadable]

    lines += ["", "## Unjoined -- declared, emitted, no standing gate runs it",
              ""]
    unjoined = by_reach[Reach.UNJOINED]
    if unjoined:
        lines += ["| Criterion | Owner | Spec |", "|---|---|---|"]
        lines += [f"| `{r.criterion.id}` | `{r.owners[0]}` | {r.criterion.spec} |"
                  for r in unjoined]
    else:
        lines.append("None.")

    lines += ["", "## Unverifiable -- declared, emitted by no executable file",
              ""]
    unver = by_reach[Reach.UNVERIFIABLE]
    lines += ([f"- `{r.criterion.id}` ({r.criterion.spec})" for r in unver]
              or ["None."])

    lines += ["", "## Ratchet", "", f"- withdrawn: {ratchet.withdrawn or 'none'}",
              f"- reachable-then-unjoined: {ratchet.unjoined_back or 'none'}",
              f"- added: {len(ratchet.added)}",
              f"- repaired: {ratchet.repaired or 'none'}"]

    if task_v is not None:
        lines += ["", "## Task under verification", "",
                  f"- verdict: **{task_v.verdict.value}**",
                  f"- spec: {task_v.spec or '(none bound)'}",
                  f"- reason: {task_v.reason}"]
        for r in task_v.results:
            mark = "PASS" if r.satisfied else r.observed.value
            lines.append(f"  - `{r.criterion.id}` {mark} -- {r.evidence or r.reach.value}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return REPORT


def _record_debt(task: str, v) -> None:
    """INTENT_NOT_CAPTURED accumulates by name. Visible, never blocking."""
    DEBT.parent.mkdir(parents=True, exist_ok=True)
    entry = {"task": task, "verdict": v.verdict.value, "reason": v.reason}
    with DEBT.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--task", default="",
                    help="task description; its bound spec gets the observe tier")
    ap.add_argument("--spec", default="",
                    help="verify one spec directly, bypassing task binding")
    ap.add_argument("--observe", action="store_true",
                    help="force the observe tier for --spec")
    ap.add_argument("--baseline", action="store_true",
                    help="record the current criterion set as the ratchet floor")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    root = PP_ROOT
    results, unreadable, silent = _collect(root)
    report, current = ratchet_check(results, root / DEFAULT_BASELINE)

    task_v = None
    if a.spec:
        spec = Path(a.spec) if Path(a.spec).is_absolute() else root / a.spec
        criteria = read_criteria(spec, root)
        res = resolve(criteria, root)
        if a.observe:
            res = observe(res, root)
        task_v = decide(res, spec_label(spec, root),
                        "verified directly by --spec")
    elif a.task:
        task_v = verify_task(a.task, root, observe_tier=True)
        if task_v.verdict is Verdict.INTENT_NOT_CAPTURED:
            _record_debt(a.task, task_v)

    if a.baseline:
        ratchet_save(root / DEFAULT_BASELINE, current)

    path = _write_report(root, results, unreadable, silent, report, task_v)

    if a.json:
        print(json.dumps({
            "criteria": len(results),
            "reach": {r.value: sum(1 for x in results if x.reach is r)
                      for r in Reach},
            "ratchet": report.as_dict(),
            "task": task_v.as_dict() if task_v else None,
        }, indent=1))
    else:
        print("=== INTENT FIDELITY ===")
        print(f"  criteria declared : {len(results)}")
        for r in Reach:
            print(f"  {r.value:<14s}: "
                  f"{sum(1 for x in results if x.reach is r)}")
        if silent:
            print(f"  not mechanical    : {len(silent)} spec(s)")
        if unreadable:
            print(f"  unreadable        : {unreadable}")
        print(f"  ratchet           : withdrawn={report.withdrawn or 'none'} "
              f"unjoined_back={report.unjoined_back or 'none'} "
              f"repaired={len(report.repaired)}")
        if task_v is not None:
            print(f"\n  TASK VERDICT      : {task_v.verdict.value}")
            print(f"  spec              : {task_v.spec or '(none bound)'}")
            print(f"  {task_v.reason}")
            for r in task_v.results:
                mark = "PASS" if r.satisfied else r.observed.value
                print(f"    [{mark:<12s}] {r.criterion.id} "
                      f"{r.evidence or r.reach.value}")
        print(f"\n  report            : {path}")

    blocking = blocking_count(task_v) if task_v is not None else 0
    if task_v is not None and task_v.verdict is Verdict.INTENT_NOT_CAPTURED:
        blocking = 0  # Owner decision: visible debt, never a block.
    if report.regressed:
        print(f"\nRATCHET REGRESSION -- withdrawn={report.withdrawn} "
              f"unjoined_back={report.unjoined_back}")
        return 1
    if blocking:
        print(f"\nNOT DONE -- {blocking} critical criterion/criteria not "
              f"observed satisfied.")
        return 1
    print("\nOK -- no critical criterion of the verified task is unobserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
