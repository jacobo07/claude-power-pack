"""V-CCRGEN-* gates for tools/ccr_generation_census.py and the impact_class in ACTIVE.json. Temporary roots only."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_generation_census as gc  # noqa: E402
import ccr_release as cr  # noqa: E402

passes = fails = 0


def check(gate: str, cond: bool, ev: str) -> None:
    global passes, fails
    passes += cond
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate}: {ev}")


def session(listing: Path, rdir: Path, pid: int, release_id: str | None, ts: int) -> None:
    (listing / f"{pid}.json").write_text(json.dumps({"pid": pid, "sessionId": f"s{pid}", "cwd": "/tmp", "procStart": "1"}), encoding="utf-8")
    f = rdir / "k" / f"s{pid}.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"ts": ts, "ev": "start", "releaseId": release_id}) + "\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        root = base / "ccr"
        mod = base / "mod"
        (mod / ".claude-plugin").mkdir(parents=True)
        (mod / ".claude-plugin" / "plugin.json").write_text('{"name":"cpp-cognitive-runtime","version":"0.1.0"}', encoding="utf-8")
        digest = base / "digest.md"
        digest.write_text("d", encoding="utf-8")
        r1 = cr.build(root, mod, digest)
        (mod / "x.txt").write_text("v2", encoding="utf-8")
        r2 = cr.build(root, mod, digest)

        rec = cr.activate(root, r1)
        check("V-CCRGEN-IMPACT-DEFAULT", rec["impact_class"] == "policy", f"default impact {rec['impact_class']}")
        rec = cr.activate(root, r2, "breaking")
        on_disk = (root / "ACTIVE.json").read_text(encoding="utf-8")
        check("V-CCRGEN-IMPACT-RECORDED", json.loads(on_disk)["impact_class"] == "breaking", "ACTIVE.json carries impact_class")
        check("V-CCRGEN-ACTIVE-UNDER-200B", len(on_disk.encode()) <= 200, f"{len(on_disk.encode())} bytes (the mod refuses a larger file)")
        try:
            cr.activate(root, r2, "catastrophic")
            check("V-CCRGEN-IMPACT-REFUSED", False, "unknown class accepted")
        except SystemExit:
            check("V-CCRGEN-IMPACT-REFUSED", True, "unknown impact class refused")

        listing, rdir = base / "sessions", root / "state" / "receipts"
        listing.mkdir()
        session(listing, rdir, 21, r2.name, 5)    # current
        session(listing, rdir, 22, r1.name, 4)    # stale
        session(listing, rdir, 23, r1.name, 3)    # stale
        session(listing, rdir, 24, None, 2)       # dev load: nothing to compare
        up = dict(alive=lambda p: True, proc_start=lambda p: "1")
        c = gc.census(root, listing, [], **up)
        check("V-CCRGEN-COUNTS", c["counts"] == {"CURRENT": 1, "STALE": 2, "DEV": 1, "UNKNOWN": 0}, f"{c['counts']}")
        check("V-CCRGEN-RATIO", c["stale_ratio"] == 0.667, f"stale ratio {c['stale_ratio']} = 2/(2+1); DEV is outside the denominator")
        check("V-CCRGEN-ROW", {r["pid"]: (r["loaded"], r["current"], r["stale"], r["startTs"]) for r in c["processes"]}[22] == (r1.name, r2.name, True, 4),
              "per-process loaded/current/stale/start time")
        check("V-CCRGEN-IMPACT-SURFACED", c["impact_class"] == "breaking" and "/clear never migrates" in c["migration"], "impact class and migration policy in the output")
        for p in (21, 22, 23):
            (listing / f"{p}.json").unlink()
        c2 = gc.census(root, listing, [], **up)
        check("V-CCRGEN-RATIO-NULL", c2["stale_ratio"] is None, "no comparable process: ratio is null, not 0")
    print(f"CCRGEN_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
