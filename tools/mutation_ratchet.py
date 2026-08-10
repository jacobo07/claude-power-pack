"""Mutation ratchet -- a suite's demonstrated kill count may not fall.

G1/G2/G3 ratchet on NAMES of offending suites. That catches a suite that stops
looking rigorous. It cannot catch a suite that stops BEING rigorous, because the
G1 burndown established that its criterion tracks spelling rather than coverage.

This ratchets on what `tools/mutation_probe.py` measures: how many injected
defects the suite actually catches. Weakening a suite lowers that number, and no
rewording raises it back.

    python tools/mutation_ratchet.py --tier push
    python tools/mutation_ratchet.py --tier all --baseline

TIERS, assigned by measurement rather than preference. A probe costs one suite
run per mutant plus one clean run, so the suite's own runtime sets the price:

    test_capability_runtime.py    0.4s   ->  ~3s for a 6-mutant sweep
    test_egcc_residue.py          3.2s   -> ~22s
    test_duplicate_to_advantage.py 35.2s -> ~4min

The first two run on every push. d2a is on the weekly tier for that measured
reason alone -- moving it back is a one-word edit in the config, and the cost is
stated here so the choice is informed rather than inherited.

WHY A DROP IS NOT ALWAYS A FAILURE. The probe samples evenly across a module's
mutable constructs, so editing the module changes the candidate count and shifts
which constructs are sampled. A kill count can then fall with no test regression
at all. Pinning a number that moves for someone else's correct commit is how a
gate earns its uninstall by the third false alarm, so the module's hash is
recorded with the count: a drop against an UNCHANGED module is a FAIL, a drop
against a CHANGED one is a WARN naming the re-baseline. The limit is that a test
weakened in the same commit that edits its module lands as a WARN.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.mutation_probe import probe  # noqa: E402

CONFIG = REPO_ROOT / "vault" / "governance" / "mutation_ratchet.json"

# Sampled per pair. Higher is stronger and linearly slower; 6 keeps the push tier
# inside half a minute on the measured suites above.
DEFAULT_MAX = 6

PASS, FAIL, WARN, UNMEASURABLE = "PASS", "FAIL", "WARN", "UNMEASURABLE"


def module_hash(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except OSError:
        return ""


def load_config() -> dict:
    if not CONFIG.exists():
        return {"pairs": {}}
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"pairs": {}}


def pairs_for(cfg: dict, tier: str) -> list[tuple[str, dict]]:
    return sorted((k, v) for k, v in cfg.get("pairs", {}).items()
                  if tier == "all" or v.get("tier") == tier)


def measure(key: str, spec: dict) -> dict:
    """Run the probe for one pair and judge it against the recorded floor."""
    suite_rel, module_rel = key.split("::")
    suite, module = REPO_ROOT / suite_rel, REPO_ROOT / module_rel
    row = {"pair": key, "min_kill": spec.get("min_kill"), "killed": None}

    if not suite.is_file() or not module.is_file():
        return {**row, "verdict": UNMEASURABLE,
                "reason": "suite or module is absent from this checkout"}

    res = probe(suite, module, spec.get("max", DEFAULT_MAX))
    row["killed"] = len(res["killed"])
    row["sampled"] = res.get("sampled", 0)
    row["restored_intact"] = res.get("restored_intact", True)
    if res["verdict"] == UNMEASURABLE:
        return {**row, "verdict": UNMEASURABLE, "reason": res.get("reason", "")}

    floor = spec.get("min_kill")
    if floor is None:
        return {**row, "verdict": UNMEASURABLE, "reason": "no floor recorded yet"}

    if row["killed"] >= floor:
        return {**row, "verdict": PASS,
                "reason": f"{row['killed']} caught, floor {floor}"}

    changed = module_hash(module) != spec.get("module_hash", "")
    if changed:
        return {**row, "verdict": WARN,
                "reason": (f"{row['killed']} caught, floor {floor}, but the module "
                           "changed since the floor was set, so the sample shifted. "
                           "Re-baseline this pair after reviewing it.")}
    return {**row, "verdict": FAIL,
            "reason": (f"{row['killed']} caught, floor {floor}, module UNCHANGED. "
                       "The suite catches fewer injected defects than it did.")}


def write_baseline(tier: str) -> int:
    cfg = load_config()
    selected = pairs_for(cfg, tier)
    if not selected:
        print(f"no pairs configured for tier {tier!r}; nothing measured")
        return 1
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for key, spec in selected:
        suite_rel, module_rel = key.split("::")
        suite, module = REPO_ROOT / suite_rel, REPO_ROOT / module_rel
        if not suite.is_file() or not module.is_file():
            print(f"  SKIP  {key} -- absent")
            continue
        res = probe(suite, module, spec.get("max", DEFAULT_MAX))
        if res["verdict"] == UNMEASURABLE:
            print(f"  SKIP  {key} -- {res.get('reason', '')}")
            continue
        spec.update({"min_kill": len(res["killed"]),
                     "sampled": res.get("sampled", 0),
                     "module_hash": module_hash(module),
                     "measured_at": stamp})
        print(f"  SET   {key}  min_kill={spec['min_kill']}/{spec['sampled']}")
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, indent=1) + "\n", encoding="utf-8")
    print(f"baseline written: {CONFIG}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mutation kill-count ratchet")
    ap.add_argument("--tier", default="push", choices=("push", "weekly", "all"))
    ap.add_argument("--baseline", action="store_true",
                    help="record the current kill counts as the floor")
    args = ap.parse_args(argv)

    if args.baseline:
        return write_baseline(args.tier)

    cfg = load_config()
    selected = pairs_for(cfg, args.tier)
    if not selected:
        # Silence would read as health. An empty tier is reported, never passed.
        print(f"MUTATION_RATCHET=UNMEASURABLE  no pairs configured for tier "
              f"{args.tier!r}; nothing was checked")
        return 1

    rows = [measure(k, s) for k, s in selected]
    for r in rows:
        print(f"  {r['verdict']:13s} {r['pair']}")
        print(f"                {r.get('reason', '')}")
        if not r.get("restored_intact", True):
            print("                the module was NOT restored; git checkout it")

    failed = [r for r in rows if r["verdict"] == FAIL]
    warned = [r for r in rows if r["verdict"] == WARN]
    unmeasured = [r for r in rows if r["verdict"] == UNMEASURABLE]
    print(f"MUTATION_RATCHET={'FAIL' if failed else 'PASS'}  "
          f"tier={args.tier} pairs={len(rows)} fail={len(failed)} "
          f"warn={len(warned)} unmeasurable={len(unmeasured)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
