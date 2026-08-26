#!/usr/bin/env python3
"""V-SREE-* -- a redundant search is SKIPPED, not annotated.

Two facts, both measured before this was written:

  1. `deep_research._dedup_urls_against_history` (deep_research.py:1808) is
     the only overlap detection in the pipeline. It is called at :1847,
     INSIDE write_research_artifacts -- after the entire run has finished,
     every query issued and every page fetched. Its output is used for one
     length comparison that appends a footnote; the Sources list still
     prints every URL. Nothing is skipped and no token is saved.

  2. `research_discovery.discover_for_cwd` computes exactly the thing that
     WOULD prevent the run -- prior research relevant to this directory,
     inside a 24h window, with an age -- and had ZERO callers. It is
     classified ORPHAN in the repo's own 2026-06-01 manual-tools audit.

So the estate could detect redundancy after paying for it, and could have
prevented it but never called the code that would.

The gates assert reuse AND its bound. A cache with no freshness limit does
not eliminate redundant search, it fossilises a stale answer.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))
sys.path.insert(0, str(PP / "modules" / "deep-research"))

HOOK = PP / "hooks" / "research-intent-detector.js"

EXPECTED_GATES = 6
_passes = 0
_fails = 0


def _ok(g: str, e: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {g}: {e}")


def _fail(g: str, d: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {g}: {d}")


def main() -> int:
    print("V-SREE -- prior research is reused instead of re-run")

    import research_discovery as rd  # noqa: PLC0415

    # The orphan must now have a caller, or nothing changed.
    src = HOOK.read_text(encoding="utf-8-sig")
    if "discover_for_cwd" in src and "priorResearch" in src:
        _ok("V-SREE-ORPHAN-HAS-A-CALLER",
            "research-intent-detector consults discover_for_cwd before spawning")
    else:
        _fail("V-SREE-ORPHAN-HAS-A-CALLER",
              "the discovery module is still unreachable from the live surface")

    # The skip must come BEFORE the spawn, or it saves nothing.
    i_prior = src.find("const prior = priorResearch()")
    i_spawn = src.find("spawnDetached(prompt);\n  process.exit(0);")
    if 0 <= i_prior < i_spawn:
        _ok("V-SREE-SKIP-PRECEDES-SPAWN",
            "the reuse check runs before the detached run is started")
    else:
        _fail("V-SREE-SKIP-PRECEDES-SPAWN",
              f"prior@{i_prior} spawn@{i_spawn} -- a check after the spawn "
              "is the same defect as annotating after the run")

    # Freshness bound exists and is finite. This is the anti-fossilisation
    # control: without it, reuse hardens a stale answer into a fact.
    window = getattr(rd, "RECENT_WINDOW_HOURS", None)
    if isinstance(window, (int, float)) and 0 < window <= 24 * 14:
        _ok("V-SREE-REUSE-IS-BOUNDED",
            f"reuse limited to a {window}h window")
    else:
        _fail("V-SREE-REUSE-IS-BOUNDED", f"window is {window!r}")

    # Behaviour against a controlled index: a FRESH row is discoverable.
    tmp = Path(tempfile.mkdtemp(prefix="sree_"))
    saved_index = getattr(rd, "INDEX_PATH", None)
    try:
        idx = tmp / "index.json"
        report = tmp / "report.md"
        report.write_text("# prior\n", encoding="utf-8")

        # Derived from the module's OWN tokenizer, never guessed. A first
        # version hand-built a prompt from `Path.cwd().name` and matched
        # nothing, because "claude" is a stop word -- so the fresh case
        # returned None and the stale bookend passed vacuously against it.
        here = Path.cwd()
        tokens = sorted(rd._cwd_tokens(here))
        if not tokens:
            here = PP
            tokens = sorted(rd._cwd_tokens(here))
        probe_prompt = "deep research about " + " ".join(tokens[:4])

        def _row(age_h, prompt):
            # The index's own format: %Y-%m-%dT%H:%M:%SZ. _parse_iso returns
            # None on anything else, and a None timestamp is silently skipped.
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                               time.gmtime(time.time() - age_h * 3600))
            return json.dumps({
                "ts": ts, "slug": "s", "prompt": prompt,
                "report_path": str(report),
            })

        if saved_index is None:
            _fail("V-SREE-FRESH-IS-FOUND", "research_discovery has no INDEX_PATH")
            _fail("V-SREE-STALE-IS-NOT-REUSED", "cannot exercise without INDEX_PATH")
        else:
            idx.write_text(_row(1, probe_prompt) + "\n", encoding="utf-8")
            rd.INDEX_PATH = idx
            fresh = rd.discover_for_cwd(here)
            if fresh and fresh.get("report_path"):
                _ok("V-SREE-FRESH-IS-FOUND",
                    f"a 1h-old matching run is discoverable "
                    f"({fresh.get('age_hours')}h)")
            else:
                _fail("V-SREE-FRESH-IS-FOUND", f"got {fresh!r}")

            # BOOKEND. An aged-out run must NOT be reused -- it expires into
            # a real search rather than answering from a stale document.
            idx.write_text(_row(24 * 30, probe_prompt) + "\n",
                           encoding="utf-8")
            stale = rd.discover_for_cwd(here)
            if not stale:
                _ok("V-SREE-STALE-IS-NOT-REUSED",
                    "a 30-day-old run is not offered for reuse")
            else:
                _fail("V-SREE-STALE-IS-NOT-REUSED",
                      f"stale run offered: {stale!r}")
    finally:
        if saved_index is not None:
            rd.INDEX_PATH = saved_index
        shutil.rmtree(tmp, ignore_errors=True)

    # The hook must still parse. It is live on the Stop chain.
    node = shutil.which("node")
    if node is None:
        _fail("V-SREE-HOOK-PARSES", "node not on PATH -- cannot verify the hook")
    else:
        chk = subprocess.run([node, "--check", str(HOOK)],
                             capture_output=True, text=True, timeout=30)
        if chk.returncode == 0:
            _ok("V-SREE-HOOK-PARSES", "research-intent-detector.js parses")
        else:
            _fail("V-SREE-HOOK-PARSES", (chk.stderr or "").strip()[:160])

    total = _passes + _fails
    print(f"SEARCH_REUSE_PASS={_passes}/{total}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if total != EXPECTED_GATES:
        print(f"FAIL: {total} gates executed, {EXPECTED_GATES} declared")
        return 1
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
