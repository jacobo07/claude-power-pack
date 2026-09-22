"""Mutation drill for test_gsd_x_manifest_reachability.py.

Each mutant is one of the defects this capability actually shipped with, or
the next one along the same axis. A mutant is CAUGHT only if the gate exits 1
AND the specific gate named for that defect is among the failures -- a red for
an unrelated reason is not a catch, it is a coincidence.

Mutants are written to a scratch COPY and the gate is pointed at it through
GSDX_REACH_MANIFEST, so the tracked manifest is never edited. The tracked file
is hashed before and after as a guard on that promise.

A green control (the unmutated manifest, through the same override path) runs
first: if the override path itself were broken, every mutant would be "caught"
for a reason that has nothing to do with the mutation.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATE = REPO / "tools" / "test_gsd_x_manifest_reachability.py"
MANIFEST = REPO / "capabilities" / "cpp-gsd-x-mission" / "capability.json"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _run(manifest: dict, workdir: Path, name: str) -> tuple[int, str]:
    target = workdir / f"{name}.json"
    target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    env = {**os.environ, "GSDX_REACH_MANIFEST": str(target), "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, str(GATE)], capture_output=True,
                       text=True, encoding="utf-8", env=env, timeout=120)
    return r.returncode, r.stdout


def _set_gate(m: dict, **kv) -> dict:
    m = copy.deepcopy(m)
    m["gates"][0].update(kv)
    return m


def mutants(base: dict) -> list[tuple[str, dict, str]]:
    """(name, mutated manifest, the gate id that must go red)"""
    out: list[tuple[str, dict, str]] = []

    # 1. The historical point: its only dispatch reads check.query.
    out.append(("point-execute-wave-post",
                _set_gate(base, point="execute:wave:post"),
                "V-GSDXREACH-POINT-DISPATCHES[0]"))

    # 2. The next trap on the same axis: dispatches a predicate, but passes
    #    --phase-number only, so ${PHASE_DIR} arrives empty.
    out.append(("point-execute-post",
                _set_gate(base, point="execute:post"),
                "V-GSDXREACH-POINT-DISPATCHES[0]"))

    # 3. The historical activation key: validator-clean, resolves false forever.
    m = copy.deepcopy(base)
    cfg_val = m["config"].pop("gsd_x_mission.enabled")
    m["config"]["enabled"] = cfg_val
    m["activationKey"] = "enabled"
    m["gates"][0]["when"] = "enabled"
    out.append(("bare-activation-key", m, "V-GSDXREACH-WHEN-DOTTED[0]"))

    # 4. Capability and hook gating on different keys.
    out.append(("when-disagrees-with-activation",
                _set_gate(base, when="other_ns.enabled"),
                "V-GSDXREACH-ACTIVATION-AGREES[0]"))

    # 5. activationKey not declared in config.
    m = copy.deepcopy(base)
    m["config"] = {"something_else.enabled": m["config"]["gsd_x_mission.enabled"]}
    out.append(("activation-not-declared", m, "V-GSDXREACH-ACTIVATION-DECLARED[0]"))

    # 6. On by default: a blocking, fail-closed gate installed globally.
    m = copy.deepcopy(base)
    m["config"]["gsd_x_mission.enabled"]["default"] = True
    out.append(("default-on", m, "V-GSDXREACH-DEFAULT-OFF[0]"))

    # 7. A query in place of the predicate -- unavailable to a third party.
    out.append(("query-not-predicate",
                _set_gate(base, check={"query": "gsd-x.mission"}),
                "V-GSDXREACH-USES-PREDICATE[0]"))
    return out


def main() -> int:
    before = _sha(MANIFEST)
    base = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    caught = 0
    results: list[str] = []

    with tempfile.TemporaryDirectory(prefix="gsdx_reach_mut_") as tmp:
        work = Path(tmp)

        code, out = _run(base, work, "control")
        if code != 0:
            print("HARNESS-FAILED: the unmutated manifest does not pass through the "
                  f"override path (exit {code}); every catch below would be spurious.")
            print(out)
            print("GSDX_REACH_MUTATIONS_CAUGHT=0/0  threshold=HARNESS")
            return 2
        print("  CONTROL unmutated manifest via override: exit 0")

        ms = mutants(base)
        for name, m, must_fail in ms:
            code, out = _run(m, work, name)
            failed_gates = [ln.split()[1].rstrip(":") for ln in out.splitlines()
                            if ln.strip().startswith("FAIL ")]
            hit = code == 1 and must_fail in failed_gates
            caught += hit
            verdict = "CAUGHT" if hit else "SURVIVED"
            results.append(f"  {verdict:8} {name:32} expected {must_fail}  "
                           f"exit={code} failed={failed_gates}")

    for r in results:
        print(r)

    after = _sha(MANIFEST)
    if after != before:
        print(f"HARNESS-FAILED: tracked manifest changed during the drill "
              f"({before[:12]} -> {after[:12]})")
        return 2
    print(f"  tracked manifest untouched: sha256 {after[:16]}")

    print(f"\nGSDX_REACH_MUTATIONS_CAUGHT={caught}/{len(ms)}  threshold={len(ms)}/{len(ms)}")
    return 0 if caught == len(ms) else 1


if __name__ == "__main__":
    sys.exit(main())
