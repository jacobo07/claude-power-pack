#!/usr/bin/env python3
"""agent_discovery_curve -- measure the parent's context cost of N resident agents.

Spec: vault/specs/agent-capability-virtualization.md (S0 flat curve, S2 carrier curve).

For each N it builds a throwaway project whose .claude/agents holds N SYNTHETIC
agents (named `synthetic-agent-NNNN`, never installed anywhere), runs ONE real
`claude -p` turn in it, and reads the parent's own usage accounting
(input + cache-creation + cache-read tokens). The global estate and hooks are a
constant offset shared by every N, so the slope between points is the per-agent
listing cost the runtime actually charges -- not a model of it.

  python tools/agent_discovery_curve.py --ns 0 100 400            flat estate
  python tools/agent_discovery_curve.py --ns 0 100 --desc-bytes 300
  python tools/agent_discovery_curve.py --ns 0 1000 --catalog-only
        (--catalog-only puts the N agents in a NON-listed folder: the virtual-spec
         case, which must cost ~nothing -- S2 claim check)

A run whose usage cannot be read is recorded as status=UNMEASURED with the
reason; it is never recorded as zero.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "vault" / "audits" / "agent_estate" / "discovery_curve.json"
WORDS = ("verify inspect runtime schema migration frontend render latency process queue "
         "contract boundary evidence audit security review parser cache index ledger").split()


def synth_desc(i: int, target: int) -> str:
    base = f"Synthetic load-test agent {i}. Specialist for "
    out, k = base, i
    while len(out.encode()) < target:
        out += WORDS[k % len(WORDS)] + " "
        k = k * 7 + 3
    return out.strip()


def build(project: Path, n: int, desc_bytes: int, catalog_only: bool):
    where = project / ("agent-catalog" if catalog_only else ".claude/agents")
    where.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        name = f"synthetic-agent-{i:04d}"
        (where / f"{name}.md").write_text(
            f"---\nname: {name}\ndescription: {synth_desc(i, desc_bytes)}\ntools: Read, Grep\n---\n"
            f"SYNTHETIC load-test body for {name}. Never dispatched.\n", encoding="utf-8")


def measure(project: Path, model: str, timeout: int) -> dict:
    exe = shutil.which("claude")
    if not exe:
        return {"status": "UNMEASURED", "reason": "claude CLI not on PATH"}
    t0 = time.time()
    try:
        p = subprocess.run([exe, "-p", "Reply with the single word ok.", "--model", model,
                            "--output-format", "json"], cwd=project, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"status": "UNMEASURED", "reason": f"timeout {timeout}s"}
    line = next((l for l in reversed(p.stdout.splitlines()) if l.strip().startswith("{")), None)
    if not line:
        return {"status": "UNMEASURED", "reason": f"no json (exit {p.returncode})", "stderr": p.stderr[-300:]}
    try:
        u = json.loads(line).get("usage") or {}
    except json.JSONDecodeError as e:
        return {"status": "UNMEASURED", "reason": f"bad json: {e}"}
    keys = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
    if not all(isinstance(u.get(k), int) for k in keys):
        return {"status": "UNMEASURED", "reason": f"usage fields missing: {sorted(u)}"}
    return {"status": "MEASURED", "context_tokens": sum(u[k] for k in keys),
            **{k: u[k] for k in keys}, "seconds": round(time.time() - t0, 1)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ns", type=int, nargs="+", required=True)
    ap.add_argument("--desc-bytes", type=int, default=310, help="measured estate mean was ~310 B")
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--catalog-only", action="store_true")
    ap.add_argument("--label", default="flat")
    args = ap.parse_args(argv)
    rows = []
    for n in args.ns:
        with tempfile.TemporaryDirectory(prefix="adc-") as t:
            build(Path(t), n, args.desc_bytes, args.catalog_only)
            r = {"n": n, **measure(Path(t), args.model, args.timeout)}
        rows.append(r)
        print(json.dumps(r))
    measured = [r for r in rows if r["status"] == "MEASURED"]
    slope = None
    if len(measured) >= 2:
        a, b = min(measured, key=lambda r: r["n"]), max(measured, key=lambda r: r["n"])
        if b["n"] > a["n"]:
            slope = round((b["context_tokens"] - a["context_tokens"]) / (b["n"] - a["n"]), 2)
    run = {"label": args.label, "catalog_only": args.catalog_only, "desc_bytes": args.desc_bytes,
           "model": args.model, "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "rows": rows, "tokens_per_agent": slope,
           "note": "offset = global estate + hooks, shared by every N; slope is the per-agent cost"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    hist = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    hist.append(run)
    OUT.write_text(json.dumps(hist, indent=1), encoding="utf-8")
    print(f"DISCOVERY_CURVE label={args.label} tokens_per_agent={slope} measured={len(measured)}/{len(rows)}")
    return 0 if len(measured) == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
