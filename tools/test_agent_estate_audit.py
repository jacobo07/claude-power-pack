#!/usr/bin/env python3
"""V-AGE-* gates for tools/agent_estate_audit.py (spec agent-capability-virtualization, S0).

Every detector is driven from both poles on synthetic fixtures: a planted defect
must be found (positive control) and a clean fixture must read zero. A detector
that only ever reported zero would pass the clean half and fail here.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import agent_estate_audit as aea  # noqa: E402

passes = fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"  FAIL {gate}: {ev}")


def check(gate, cond, ev):
    (_ok if cond else _fail)(gate, ev)


SHARED = ("Always verify the repository state before you trust a handoff claim, and report "
          "every unknown as unknown rather than as absent or as zero in the final output. ")


def agent(d: Path, file: str, name: str, body: str, tools="Read, Grep"):
    (d / file).write_text(f"---\nname: {name}\ndescription: fixture {name}\ntools: {tools}\n---\n{body}\n",
                          encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        dirty, clean = Path(t, "dirty"), Path(t, "clean")
        dirty.mkdir(); clean.mkdir()
        agent(dirty, "alpha.md", "alpha", SHARED + "alpha specific words about databases only here")
        agent(dirty, "alpha.compact.md", "alpha", SHARED + "compact twin")
        agent(dirty, "beta.md", "beta", "beta intro. " + SHARED + "beta specific words about frontends")
        agent(dirty, "gamma.md", "gamma", "gamma has entirely unique content with no overlap at all anywhere")
        (dirty / "README.md").write_text("# not an agent\n", encoding="utf-8")
        agent(clean, "one.md", "one", "first agent speaks of kernels and schedulers and interrupts today")
        agent(clean, "two.md", "two", "second agent discusses gardens rivers mountains and quiet evenings")

        rd = aea.audit({"dirty": dirty})
        s = rd["surfaces"]["dirty"]
        check("V-AGE-COLLISION-FOUND", s["collisions"] == {"alpha": ["alpha.compact.md", "alpha.md"]}, s["collisions"])
        check("V-AGE-NON-AGENT-SKIPPED", s["files"] == 4, f"files={s['files']}")
        check("V-AGE-RESIDENT-PER-UNIQUE-NAME", s["unique_names"] == 3, f"unique={s['unique_names']}")
        d = rd["duplication"]
        pair_names = {(p["a"], p["b"]) for p in d["top_pairs"]}
        check("V-AGE-DUP-FOUND", d["shared_shingles"] > 0 and ("alpha", "beta") in pair_names, d["top_pairs"])
        check("V-AGE-DUP-UNIQUE-AGENT-ZERO", d["per_agent_shared_share"].get("gamma") == 0.0,
              d["per_agent_shared_share"])
        check("V-AGE-TWINS-NOT-DUP", not any("alpha" == p["a"] == p["b"] for p in d["top_pairs"]), "twins excluded")

        rc = aea.audit({"clean": clean})
        sc = rc["surfaces"]["clean"]
        check("V-AGE-CLEAN-ZERO", sc["collisions"] == {} and rc["duplication"]["shared_shingles"] == 0,
              f"collisions={sc['collisions']} shared={rc['duplication']['shared_shingles']}")

        rr = aea.audit({"repo": dirty, "global": clean})
        check("V-AGE-DORMANT", rr["dormant_repo_agents"] == ["alpha", "beta", "gamma"], rr["dormant_repo_agents"])

        rc2 = aea.main(["--roots", str(Path(t, "does-not-exist"))])
        check("V-AGE-UNREADABLE-IS-FAILURE", rc2 == 2, f"exit={rc2}")

    # live estate: the real surfaces must be readable and non-empty (population floor)
    live = aea.audit(aea.surfaces())
    g = live["surfaces"].get("global", {})
    check("V-AGE-LIVE-FLOOR", g.get("unique_names", 0) >= 10 and "repo" in live["surfaces"],
          f"global unique={g.get('unique_names')} unreadable={live['unreadable']}")

    print(f"AGENT_ESTATE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
