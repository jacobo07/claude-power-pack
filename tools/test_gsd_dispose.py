#!/usr/bin/env python
"""V-DISPOSE-* gates for `gsd_dossier.py dispose` (A-G1 Proof of Non-Work). Hermetic, both poles."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_dossier as gd  # noqa: E402

passes = fails = 0


def gate(name: str, cond: bool, detail: str = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"[PASS] {name} {detail}".rstrip())
    else:
        fails += 1
        print(f"[FAIL] {name} {detail}".rstrip())


def run(rows, tmp: Path, expect=None, check=True):
    obl = tmp / "obl.json"
    obl.write_text(json.dumps({"expect": expect or [], "obligations": rows}), encoding="utf-8")
    cmd = [sys.executable, "-I", str(HERE / "gsd_dossier.py"), "dispose", "--obligations", str(obl),
           "--out", str(tmp / "out"), "--repo", str(tmp)] + (["--check"] if check else [])
    p = subprocess.run(cmd, capture_output=True, text=True)
    res = json.loads((tmp / "out" / "dispositions.json").read_text(encoding="utf-8"))
    return p.returncode, p.stdout, res


def row(i, claimed, evidence=None, **kw):
    return {"id": i, "text": i, "block": "T", "claimed": claimed, "evidence": evidence or [], **kw}


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "present.txt").write_text("alpha MARKER beta\n", encoding="utf-8")
        ok_probe = [{"kind": "file_exists", "path": "present.txt"}]
        bad_probe = [{"kind": "file_exists", "path": "absent.txt"}]

        gate("V-DISPOSE-VOCAB-CLOSED", len(gd.DISPOSITIONS) == 11 and "MAYBE" not in gd.DISPOSITIONS
             and set(gd.NEEDS_PROBE) <= set(gd.DISPOSITIONS))
        rc, _, res = run([row("X1", "MAYBE")], tmp)
        gate("V-DISPOSE-VOCAB-RED", rc == 1 and res["obligations"][0]["disposition"] == "UNKNOWN", f"rc={rc}")

        rc, _, res = run([row("A", "DETERMINISTIC")], tmp, expect=["A", "B"])
        gate("V-DISPOSE-MISSING-RED", rc == 1 and res["undisposed"] == 1, f"rc={rc} undisposed={res['undisposed']}")
        rc, _, res = run([{"id": "", "claimed": "NO_WORK"}], tmp)
        gate("V-DISPOSE-NOID-RED", rc == 1 and res["undisposed"] == 1, f"rc={rc}")

        rc, _, res = run([row("A", "DETERMINISTIC"), row("A", "DETERMINISTIC")], tmp)
        gate("V-DISPOSE-DUPLICATE-RED", rc == 1 and any(e.startswith("DUPLICATE") for e in res["errors"]), f"rc={rc}")

        rc, out, res = run([row("A", "ALREADY_SATISFIED", ok_probe)], tmp)
        gate("V-DISPOSE-PROBE-PASS-KEPT", rc == 0 and res["obligations"][0]["disposition"] == "ALREADY_SATISFIED",
             f"rc={rc}")
        rc, _, res = run([row("A", "ALREADY_SATISFIED", bad_probe)], tmp)
        gate("V-DISPOSE-PROBE-FAIL-UNKNOWN", rc == 1 and res["obligations"][0]["disposition"] == "UNKNOWN"
             and "MISSING" in res["obligations"][0]["reason"], f"rc={rc}")
        rc, _, res = run([row("A", "NO_WORK")], tmp)
        gate("V-DISPOSE-NO-EVIDENCE-UNKNOWN", rc == 1 and res["obligations"][0]["disposition"] == "UNKNOWN")
        rc, _, res = run([row("A", "REUSE_EXISTING", ok_probe + bad_probe)], tmp)
        gate("V-DISPOSE-ALL-PROBES-REQUIRED", rc == 1 and res["obligations"][0]["disposition"] == "UNKNOWN")

        rc, _, res = run([row("A", "MERGE", ok_probe)], tmp)
        gate("V-DISPOSE-MERGE-NO-TARGET-RED", rc == 1 and res["obligations"][0]["disposition"] == "UNKNOWN", f"rc={rc}")
        rc, _, res = run([row("A", "MERGE", ok_probe, merge_into="NOPE")], tmp)
        gate("V-DISPOSE-MERGE-BAD-TARGET-RED", rc == 1)
        rc, _, res = run([row("A", "MERGE", ok_probe, merge_into="B"), row("B", "DETERMINISTIC")], tmp)
        gate("V-DISPOSE-MERGE-TARGET-OK", rc == 0 and res["obligations"][0]["merge_into"] == "B", f"rc={rc}")

        py = sys.executable
        gate("V-DISPOSE-GREP", gd.run_probe({"kind": "grep", "pattern": "alpha MARKER", "path": "present.txt"}, tmp)["ok"]
             and not gd.run_probe({"kind": "grep", "pattern": "zzz-nope", "path": "present.txt"}, tmp)["ok"])
        gate("V-DISPOSE-CMD", gd.run_probe({"kind": "cmd_rc0", "cmd": [py, "-c", "print('READY')"],
                                            "marker": "READY"}, tmp)["ok"]
             and not gd.run_probe({"kind": "cmd_rc0", "cmd": [py, "-c", "print('READY')"], "marker": "OTHER"}, tmp)["ok"]
             and not gd.run_probe({"kind": "cmd_rc0", "cmd": [py, "-c", "raise SystemExit(3)"], "marker": ""}, tmp)["ok"])
        def g(*a):
            return subprocess.run([gd.GIT, "-C", d, "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                  capture_output=True, text=True).stdout.strip()
        g("init", "-q")
        g("add", "present.txt")
        g("commit", "-qm", "c")
        sha = g("rev-parse", "HEAD")
        gate("V-DISPOSE-COMMIT", bool(sha) and gd.run_probe({"kind": "commit", "sha": sha, "ref": "HEAD"}, tmp)["ok"]
             and not gd.run_probe({"kind": "commit", "sha": "0" * 40, "ref": "HEAD"}, tmp)["ok"])
        gate("V-DISPOSE-UNKNOWN-KIND-FAILS", not gd.run_probe({"kind": "vibes"}, tmp)["ok"])

        rows = [row("A", "NO_WORK", ok_probe), row("B", "MERGE", ok_probe, merge_into="A"),
                row("C", "DETERMINISTIC"), row("D", "STRONG_COGNITION"), row("E", "DEFERRED_EXTERNAL"),
                row("F", "UNKNOWN", reason="gex44_probe_pending")]
        rc, out, res = run(rows, tmp, expect=list("ABCDEF"))
        gate("V-DISPOSE-CONTROL-VALID-EXIT0", rc == 0 and res["undisposed"] == 0 and res["unknown"] == 1
             and "DISPOSE counts=" in out, f"rc={rc}")

    print(f"DISPOSE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
