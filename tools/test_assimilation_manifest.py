"""V-ASSIM gates: every externally supplied capability has exactly one CPP disposition.

The population is DISCOVERED from the vendored tree (vendor/genesis-suite/modules/*), never
taken from the manifest's own list, so a module the manifest forgot cannot pass as covered.
LIVE entries are executed: a documented capability nobody runs is indistinguishable from a
working one. Synthetic red drills prove each clause can fail.
    python tools/test_assimilation_manifest.py            # full gate incl. LIVE proofs
    python tools/test_assimilation_manifest.py --no-proofs  # structure only
"""
from __future__ import annotations

import copy
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "vault" / "assimilation" / "genesis-2026-09" / "ASSIMILATION_MANIFEST.json"
GENESIS_MODULES = ROOT / "vendor" / "genesis-suite" / "modules"
MODULE_FLOOR = 21
RUNNER_OPS = {"registerPlan", "ready", "taskStatus", "runTask", "checkpoint", "decide", "scan", "researchPass", "snapshot"}
RUNNER_HANDLES = {"ledger", "adaptation", "context", "router", "charters"}
# Capabilities of the unlicensed inputs and Context Budget. They cannot be discovered from bytes we
# chose not to copy, so they are named here; each name maps to a section of the supplied docs.
IDEA_CAPABILITIES = {
    "loop-completion-rearm", "loop-single-flight", "loop-instant-failure-backoff", "loop-failure-quarantine",
    "loop-run-log", "loop-startup-guidance", "wakeup-continuation-order",
    "self-continuation-rubric", "self-continuation-stop-directive", "self-continuation-decision-log",
    "context-budget-meter", "context-budget-token-budget", "fresh-context-tax", "genesis-runner",
}
PYTHON = sys.executable


def discovered() -> set[str]:
    return {p.name for p in GENESIS_MODULES.iterdir() if p.is_dir()} if GENESIS_MODULES.is_dir() else set()


def check(manifest: dict, modules: set[str], run_proofs: bool) -> list[str]:
    errs: list[str] = []
    if len(modules) < MODULE_FLOOR:
        errs.append(f"floor: discovered {len(modules)} genesis modules, expected >= {MODULE_FLOOR}")
    caps = manifest.get("capabilities") or []
    ids = [c.get("id") for c in caps]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        errs.append(f"duplicate entries: {dup}")
    required = modules | IDEA_CAPABILITIES
    missing = sorted(required - set(ids))
    if missing:
        errs.append(f"undisposed capabilities: {missing}")
    allowed_disp = set(manifest.get("dispositions") or [])
    allowed_status = set(manifest.get("statuses") or {})
    for c in caps:
        cid = c.get("id")
        if c.get("disposition") not in allowed_disp:
            errs.append(f"{cid}: disposition {c.get('disposition')!r} not allowed")
        if c.get("status") not in allowed_status:
            errs.append(f"{cid}: status {c.get('status')!r} not allowed")
        if not (c.get("owner") or "").strip():
            errs.append(f"{cid}: no owner")
        src = c.get("source") or ""
        if src.startswith("vendor/") and not (ROOT / src).exists():
            errs.append(f"{cid}: stale entry, source {src} does not exist")
        if cid not in required:
            errs.append(f"{cid}: stale entry, not a supplied capability")
        if c.get("status") == "PLANNED" and not c.get("slice"):
            errs.append(f"{cid}: PLANNED without a slice")
        if c.get("status") == "LIVE":
            # A proof that exits 0 says the code works WHEN INVOKED; LIVE also claims something
            # invokes it. Red team R2 found eight LIVE entries reachable only by a human typing
            # the CLI, so the claim is now a checked edge: a non-test file that names the owner.
            caller = c.get("caller") or {}
            cpath, ref = caller.get("path") or "", caller.get("references") or ""
            if not cpath or not ref:
                errs.append(f"{cid}: LIVE without a production caller")
            elif Path(cpath).name.startswith("test_"):
                errs.append(f"{cid}: LIVE caller {cpath} is a test, not a production caller")
            elif ref not in (c.get("owner") or ""):
                errs.append(f"{cid}: LIVE caller references {ref!r}, which the owner does not name")
            elif not (ROOT / cpath).is_file():
                errs.append(f"{cid}: LIVE caller {cpath} does not exist")
            elif ref not in (ROOT / cpath).read_text(encoding="utf-8", errors="replace"):
                errs.append(f"{cid}: LIVE caller {cpath} never references {ref!r}")
        if c.get("status") in ("LIVE", "IMPLEMENTED"):
            proof = c.get("proof")
            if not proof:
                errs.append(f"{cid}: {c.get('status')} without a proof command")
            elif run_proofs:
                argv = shlex.split(proof)
                if argv[0] == "python":
                    argv[0] = PYTHON
                rc = subprocess.run(argv, cwd=ROOT, capture_output=True).returncode
                if rc != 0:
                    errs.append(f"{cid}: {c.get('status')} proof exited {rc}: {proof}")
    ops = {o.get("op") for o in manifest.get("runner_operations") or []}
    if ops != RUNNER_OPS:
        errs.append(f"runner operations mismatch: missing {sorted(RUNNER_OPS - ops)} extra {sorted(ops - RUNNER_OPS)}")
    for h in manifest.get("runner_handles") or []:
        if h.get("cpp") not in ids:
            errs.append(f"runner handle {h.get('handle')} maps to unknown capability {h.get('cpp')}")
    if {h.get("handle") for h in manifest.get("runner_handles") or []} != RUNNER_HANDLES:
        errs.append("runner handles mismatch")
    return errs


def main() -> int:
    run_proofs = "--no-proofs" not in sys.argv
    passes = fails = 0

    def gate(name, cond, evidence):
        nonlocal passes, fails
        passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
        print(f"{'PASS' if cond else 'FAIL'} {name}: {evidence}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    modules = discovered()
    errs = check(manifest, modules, run_proofs)
    gate("V-ASSIM-MANIFEST", not errs, "clean" if not errs else "; ".join(errs))
    live = [c["id"] for c in manifest["capabilities"] if c["status"] == "LIVE"]
    gate("V-ASSIM-POPULATION", len(modules) >= MODULE_FLOOR,
         f"{len(modules)} modules discovered, {len(manifest['capabilities'])} entries, LIVE={live}")

    # Red drills: each clause must be able to fail on a synthetic subject.
    def drill(name, mutate, needle):
        m = copy.deepcopy(manifest)
        mods = set(modules)
        mutate(m, mods)
        e = check(m, mods, run_proofs=False)
        gate(name, any(needle in x for x in e), f"expected '{needle}' in {e[:2]}")

    drill("V-ASSIM-RED-FORGOTTEN", lambda m, s: m["capabilities"].pop(0), "undisposed")
    drill("V-ASSIM-RED-NEW-MODULE", lambda m, s: s.add("genesis-synthetic-probe"), "undisposed")
    drill("V-ASSIM-RED-IGNORED", lambda m, s: m["capabilities"][1].update(disposition="IGNORED"), "not allowed")
    drill("V-ASSIM-RED-LIVE-NO-PROOF", lambda m, s: m["capabilities"][2].update(status="LIVE", proof=None), "without a proof")
    drill("V-ASSIM-RED-STALE", lambda m, s: m["capabilities"].append(
        {"id": "genesis-gone", "source": "vendor/genesis-suite/modules/genesis-gone", "owner": "x",
         "disposition": "WRAP", "status": "PLANNED", "slice": "T1"}), "stale entry")
    drill("V-ASSIM-RED-FLOOR", lambda m, s: s.clear(), "floor")
    drill("V-ASSIM-RED-DUP", lambda m, s: m["capabilities"].append(dict(m["capabilities"][0])), "duplicate")
    drill("V-ASSIM-RED-IMPLEMENTED-NO-PROOF", lambda m, s: m["capabilities"][2].update(
        status="IMPLEMENTED", proof=None), "without a proof")

    # Caller clauses, on a synthetic entry so the drills survive every real entry being fixed.
    def synthetic(caller):
        return lambda m, s: m["capabilities"].append(
            {"id": "genesis-caller-probe", "source": "brief", "owner": "tools/provider_breaker.py",
             "disposition": "WRAP", "status": "LIVE", "proof": "python -c 0", "caller": caller})

    drill("V-ASSIM-RED-LIVE-NO-CALLER", synthetic(None), "without a production caller")
    drill("V-ASSIM-RED-LIVE-TEST-CALLER", synthetic(
        {"path": "tools/test_provider_breaker.py", "references": "provider_breaker"}), "is a test")
    drill("V-ASSIM-RED-LIVE-CALLER-SILENT", synthetic(
        {"path": "tools/gsd_epoch.py", "references": "provider_breaker"}), "never references")
    drill("V-ASSIM-RED-LIVE-CALLER-OFF-OWNER", synthetic(
        {"path": "tools/gsd_mission.py", "references": "gsd_long_run"}), "owner does not name")
    m = copy.deepcopy(manifest)
    synthetic({"path": "tools/gsd_mission.py", "references": "provider_breaker"})(m, set())
    probe = [x for x in check(m, set(modules), run_proofs=False) if x.startswith("genesis-caller-probe:")]
    gate("V-ASSIM-GREEN-LIVE-CALLER", probe == ["genesis-caller-probe: stale entry, not a supplied capability"],
         f"a real edge raises only the synthetic id's staleness: {probe}")

    print(f"ASSIM_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
