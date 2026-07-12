#!/usr/bin/env python3
"""Rule Compiler CLI (P1) -- replaces the seal path of bug_to_hardrule.py.

  --compile   validate the corpus, write the 3 artifacts (db, digest,
              rejection report)
  --check     validate and report WITHOUT writing (CI / pre-commit)
  --show ID*  print the full body of one or more rules (the drill-down
              the digest points at)
  --list      list every valid rule id + title
  --rejects   print the rejection report to stdout

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
    from modules.rule_compiler.digest import TRIGGER_CLASSES, UNCLASSIFIED
    known = [c[0] for c in TRIGGER_CLASSES] + [UNCLASSIFIED]
    if name.upper() not in known:
        print(f"[FAIL] unknown class '{name}'. Known: "
              f"{', '.join(known)}", file=sys.stderr)
        return 2
    rules = rules_in_class(name)
    print(f"=== {name.upper()} -- {len(rules)} BINDING rule(s). "
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
    a = p.parse_args(argv)
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
