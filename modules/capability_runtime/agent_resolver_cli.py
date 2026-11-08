#!/usr/bin/env python3
"""agent_resolver_cli.py -- the command line of agent_resolver (ACV C5 R2).

Moved out of agent_resolver.py so that presentation is not part of the policy id: policy_hash
covers every answer-producing module of this package, and this file only parses arguments and
prints a result (it is in agent_resolver.NOT_POLICY). `python -m
modules.capability_runtime.agent_resolver resolve ...` still works through a delegating stub.

  python -m modules.capability_runtime.agent_resolver_cli resolve "<task>" [--max-class verifier] [--k 3] [--json] [--no-cache]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime import agent_spec as A  # noqa: E402
from modules.capability_runtime import agent_telemetry as T  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="agent_resolver")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve"); r.add_argument("task")
    r.add_argument("--max-class", default="verifier", choices=A.CLASS_ORDER)
    r.add_argument("--k", type=int, default=3); r.add_argument("--json", action="store_true")
    r.add_argument("--no-cache", action="store_true")
    a = ap.parse_args(argv)
    try:
        # The instrumented path (ACV C5): one resolve(), one CO-12 agent_resolution signal. The
        # result is printed exactly as resolve() returned it; telemetry state is shown beside it.
        rec = T.resolve_and_record(a.task, a.max_class, a.k, use_cache=not a.no_cache)
    except A.AgentSpecError as e:
        print(f"AGENTSPEC_ERROR {e.code} {e}", file=sys.stderr)
        return 2
    res = rec.result
    if not rec.recorded:
        print(f"TELEMETRY_NOT_RECORDED resolution_id={rec.resolution_id} "
              "(CO-12 write failed or timed out; the result below is unaffected)", file=sys.stderr)
    if a.json:
        print(json.dumps({**res, "resolution_id": rec.resolution_id, "recorded": rec.recorded}, indent=1))
    else:
        miss = f" miss={res['miss']} {res['miss_ids'] or ''}".rstrip() if res["miss"] else ""
        print(f"{res['status']}{miss} catalog={res['catalog_size']} cache={res['cache']} {res['ms']}ms "
              f"resolution_id={rec.resolution_id}")
        for c in res["candidates"]:
            print(f"  {c['id']}  class={c['class']} verdict={c['verdict']} gate={c['gate_score']} bm25={c['bm25']}")
            print(f"    compile: python -m modules.capability_runtime.agent_spec compile {c['id']} "
                  f"--mission-file <file> --json   (dispatch to {c['carrier']})")
        for n in res["near_misses"]:
            print(f"  near-miss {n['id']}: {n['reason']}")
        for e in res["excluded"]:
            print(f"  excluded {e['id']}: {e['code']} {e['detail']}")
        for b in res["broken"]:
            print(f"  broken {b['spec']}: {b['code']}")
    return 0 if res["status"] == "RESOLVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
