#!/usr/bin/env python3
"""Rule Compiler CLI (P1) -- replaces the seal path of bug_to_hardrule.py.

  --compile   validate the corpus, write the 3 artifacts (db, digest,
              rejection report)
  --check     validate and report WITHOUT writing (CI / pre-commit)
  --show ID*  print the full body of one or more rules (the drill-down
              the digest points at)
  --list      list every valid rule id + title
  --rejects   print the rejection report to stdout
  --binding   which rules declare WHERE they bind (advisory / block-build
              / block-deploy / ...) and which declare nothing -- the
              named drill-down the digest's binding section points at
  --reconcile which rules this estate ENFORCES but never compiles, and how
              CLAUDE.md's block differs from the archive's. Exits 1 only on
              a rule that fires from a hook and is absent from the corpus.
              Add --singletons to list one-file ids.

Sealed by the AKOS macro audit (2026-07-12).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.rule_compiler import (  # noqa: E402
    DIGEST_MAX_BYTES,
    REASON_HELP,
    compile_rules,
    show,
    write_artifacts,
)
from modules.rule_compiler.digest import classify  # noqa: E402


def _summary(res) -> None:
    total = len(res.valid) + len(res.rejected)
    print(f"corpus        : {total} rules")
    print(f"  valid       : {len(res.valid)}")
    print(f"  rejected    : {len(res.rejected)}")
    print(f"digest        : {res.digest_bytes} bytes "
          f"(cap {DIGEST_MAX_BYTES}) -> "
          f"{'OK' if res.within_budget else 'OVER BUDGET'}")
    if res.omitted:
        print(f"  omitted     : {len(res.omitted)} ids did not fit "
              f"(named inside the digest)")


def cmd_compile() -> int:
    res = compile_rules()
    paths = write_artifacts(res)
    _summary(res)
    print()
    for name, p in paths.items():
        print(f"{name:<11}: {p}")
    if not res.within_budget:
        print("\n[FAIL] digest exceeds the tool read budget -- the kill "
              "switch would be unreadable again.", file=sys.stderr)
        return 1
    return 0


def cmd_check() -> int:
    res = compile_rules()
    _summary(res)
    print()
    for r in res.rejected:
        reasons = ", ".join(x.value for x in r.rejections)
        print(f"REJECTED {r.rule_id:<32} {reasons}")
    return 0 if res.within_budget else 1


def cmd_show(ids: list[str]) -> int:
    rules = show(ids)
    if not rules:
        print(f"[FAIL] no rule matched {ids}", file=sys.stderr)
        return 2
    for r in rules:
        status = "ACTIVE" if r.valid else "REJECTED (cannot fire)"
        print("=" * 68)
        print(f"{r.rule_id} -- {r.title}")
        print(f"  status  : {status}")
        print(f"  form    : {r.form.value}")
        print(f"  source  : {r.source}")
        print(f"  classes : {', '.join(classify(r))}")
        if r.trigger:
            print(f"  TRIGGER : {r.trigger}")
        if r.stop:
            print(f"  ACTION  : {r.stop}")
        if r.evidence:
            print(f"  EVIDENCE: {r.evidence}")
        if r.exception:
            print(f"  EXCEPT  : {r.exception}")
        if not r.valid:
            for reason in r.rejections:
                print(f"  ! {reason.value}: {REASON_HELP[reason]}")
        if r.form.value == "IMPERATIVE" and r.body:
            print(f"\n{r.body}")
    return 0


def cmd_class(name: str) -> int:
    from modules.rule_compiler.compiler import rules_in_class
    from modules.rule_compiler.digest import (
        RETIRED_CLASSES,
        ROUTER_CONTRACTED,
        TRIGGER_CLASSES,
        UNCLASSIFIED,
    )
    known = [c[0] for c in TRIGGER_CLASSES] + [UNCLASSIFIED]
    cls = name.upper()
    if cls not in known:
        print(f"[FAIL] unknown class '{name}'. Known: "
              f"{', '.join(known)}", file=sys.stderr)
        return 2
    rules = rules_in_class(cls)
    if cls in RETIRED_CLASSES:
        print(f"=== {cls} -- RETIRED_NO_CORPUS ===")
        print(RETIRED_CLASSES[cls])
        if not rules:
            return 0
        print(f"\n[REOPEN] {len(rules)} rule(s) now classify here -- the "
              "reopen condition is met. Restore this class to "
              "ROUTER_CONTRACTED; the rules below are NOT yet contracted.",
              file=sys.stderr)
    if not rules and cls in ROUTER_CONTRACTED:
        print(f"=== {cls} -- COVERAGE DEFECT: 0 binding rules ===")
        print("The global router fires on this trigger and finds nothing "
              "to enforce. An empty contracted class is an unenforced "
              "trigger point, not a clean pass -- do not read it as "
              "compliance.", file=sys.stderr)
        return 3
    print(f"=== {cls} -- {len(rules)} BINDING rule(s). "
          f"Comply before acting. ===")
    for r in rules:
        print("\n" + "-" * 68)
        print(f"{r.rule_id} -- {r.title}")
        if r.trigger:
            print(f"  TRIGGER : {r.trigger}")
        if r.stop:
            print(f"  ACTION  : {r.stop}")
        if r.exception:
            print(f"  EXCEPT  : {r.exception}")
        if r.evidence:
            print(f"  EVIDENCE: {r.evidence}")
        if r.form.value == "IMPERATIVE" and r.body:
            print(f"  {r.body.strip()[:600]}")
    return 0


def cmd_list() -> int:
    res = compile_rules()
    for r in res.valid:
        print(f"{r.rule_id:<32} {r.title[:88]}")
    print(f"\n{len(res.valid)} valid rules "
          f"({len(res.rejected)} rejected -- see --rejects)")
    return 0


def cmd_rejects() -> int:
    res = compile_rules()
    for r in res.rejected:
        print(f"\n{r.rule_id} -- {r.title[:80]}")
        print(f"  source: {r.source}")
        for reason in r.rejections:
            print(f"  ! {reason.value}: {REASON_HELP[reason]}")
    print(f"\n{len(res.rejected)} rejected.")
    return 0


def cmd_binding() -> int:
    """Exit 1 on an UNRECOGNISED level, 0 otherwise.

    Undeclared rules do NOT fail: 149 of 149 declare nothing today, so
    failing on absence would make the command red forever and it would
    stop being read -- the fate of every alarm that is always on. An
    unrecognised level is different: someone tried to declare and got it
    wrong, and that is a repair with a known owner.
    """
    from modules.rule_compiler.schema import BINDING_LADDER, binding_coverage
    res = compile_rules()
    cov = binding_coverage(res.valid)
    print(f"corpus       : {cov['total']} binding rules")
    print(f"  declared   : {len(cov['declared'])}")
    print(f"  undeclared : {len(cov['undeclared'])}")
    print(f"  unrecognised: {len(cov['unrecognized'])}")
    print("\nladder (weakest consequence first): "
          + " < ".join(b.value for b in BINDING_LADDER))
    if cov["by_binding"]:
        print("\ndistribution:")
        for level, n in cov["by_binding"].items():
            print(f"  {level:<28} {n}")
    if cov["unrecognized"]:
        print("\nUNRECOGNISED -- declared a level this compiler does not "
              "know; a typo'd consequence is not a consequence:")
        for rid in cov["unrecognized"]:
            print(f"  {rid}")
    if cov["undeclared"]:
        print(f"\nNOT DECLARED ({len(cov['undeclared'])}) -- treat as "
              "blocking until each declares. An undeclared consequence is "
              "not a mild one:")
        for rid in cov["undeclared"]:
            print(f"  {rid}")
    return 1 if cov["unrecognized"] else 0


def cmd_reconcile(show_singletons: bool = False) -> int:
    """Exit 1 only on a rule that FIRES from a hook and never compiles.

    That set is small, actionable and safety-relevant. Prose divergence is
    reported and does not fail, for the same reason cmd_binding tolerates
    UNDECLARED: an alarm that is always on stops being read.
    """
    from modules.rule_compiler.parser import load_corpus
    from modules.rule_compiler.reconcile import PP_ROOT, reconcile, render

    compiled = {r.rule_id for r in load_corpus()}
    res = reconcile(PP_ROOT, compiled)
    print(render(res, show_singletons=show_singletons))
    return 1 if res["enforced_not_compiled"] else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Compile hard rules into a validated DB + a "
                    "token-bounded trigger digest + a rejection report.")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--compile", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--show", nargs="+", metavar="RULE_ID")
    g.add_argument("--class", dest="klass", metavar="CLASS")
    g.add_argument("--list", action="store_true")
    g.add_argument("--rejects", action="store_true")
    g.add_argument("--binding", action="store_true")
    g.add_argument("--reconcile", action="store_true")
    # A modifier, NOT a member of the mutually-exclusive group: putting it in
    # `g` would make `--reconcile --singletons` an argparse error.
    p.add_argument("--singletons", action="store_true",
                   help="with --reconcile: list one-file ids")
    a = p.parse_args(argv)
    if a.reconcile or a.singletons:
        return cmd_reconcile(show_singletons=a.singletons)
    if a.binding:
        return cmd_binding()
    if a.compile:
        return cmd_compile()
    if a.klass:
        return cmd_class(a.klass)
    if a.show:
        return cmd_show(list(a.show))
    if a.list:
        return cmd_list()
    if a.rejects:
        return cmd_rejects()
    return cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
