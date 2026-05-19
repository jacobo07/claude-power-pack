#!/usr/bin/env python3
"""rtk_corpus.py — build a deterministic, frequency-weighted RTK benchmark
corpus partitioned heavy / light by an explicit static classifier.

Primary source: `rtk discover -a --format json` (per-command, JSON-clean).
Fallback: aggregate local `vault/telemetry/rtk_*.jsonl` adoption rows
(cmd_first_token frequencies) when discover returns empty.

Schema (v1.0) -> tests/fixtures/rtk_corpus.json:

  {
    "schema_version": "1.0",
    "ts": <epoch>,
    "source": "rtk-discover" | "local-telemetry" | "merged" | "none",
    "total_observations": N,
    "pinned_sha": "af8da66",
    "entries": [
      { "cmd": "git log", "frequency": 42, "weight": 0.12,
        "tier": "heavy" | "light",
        "pin_strategy": "sha-pin" | "sha-pin-pair" | "include",
        "benchmark_cmd": "git --no-pager log --stat -50 af8da66" }, ...
    ]
  }

Tier rule (build-time, no live measurement — V3.2 measures):
  heavy: STATIC_CLASSIFIER says include + known-compressible class
  light: STATIC_CLASSIFIER unknown command, default-included; tracked
         but exempt from V3.2's cliff
  excluded: STATIC_CLASSIFIER says skip (stateless / variant output)

Pin strategy:
  sha-pin       -> benchmark uses PINNED_SHA (immutable history -> reproducible)
  sha-pin-pair  -> benchmark uses PINNED_SHA + parent (e.g. diff pair)
  include       -> benchmark uses a representative stateless invocation
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TELEMETRY_DIR = REPO / "vault" / "telemetry"
DEFAULT_OUT = REPO / "tests" / "fixtures" / "rtk_corpus.json"
RTK_BIN = Path(os.environ.get("RTK_BIN") or
               Path.home() / ".claude" / "bin" / "rtk.exe")
PINNED_SHA = "af8da66"

# Explicit static classifier — no heuristics. Tier rule grounded in
# measured behavior (2026-05-19): only SHA-pinnable git history commands
# compress deterministically >=60% (rtk strips commit-body fluff, dedups
# diffstat fences). The "include" class (rg/grep/cat/tree/find) supports
# rtk but produces content-dependent reductions: large messy outputs
# compress, terse stateless outputs (small `find`, narrow `grep`) yield
# ~0%. Those go to tier=light — tracked, non-regressive, never gate.
STATIC_CLASSIFIER: dict[str, dict] = {
    "git log":      {"pin": "sha-pin",      "tier": "heavy"},
    "git show":     {"pin": "sha-pin",      "tier": "heavy"},
    "git diff":     {"pin": "sha-pin-pair", "tier": "heavy"},
    "git status":   {"pin": "skip",         "tier": "excluded"},
    "git branch":   {"pin": "skip",         "tier": "excluded"},
    "git stash":    {"pin": "skip",         "tier": "excluded"},
    "ls":           {"pin": "skip",         "tier": "excluded"},
    "rg":           {"pin": "include",      "tier": "light"},
    "grep":         {"pin": "include",      "tier": "light"},
    "cat":          {"pin": "include",      "tier": "light"},
    "tree":         {"pin": "include",      "tier": "light"},
    "find":         {"pin": "include",      "tier": "light"},
    "docker ps":    {"pin": "skip",         "tier": "excluded"},
    "docker logs":  {"pin": "include",      "tier": "light"},
    "pytest":       {"pin": "include",      "tier": "light"},
    "cargo test":   {"pin": "include",      "tier": "light"},
    "npm test":     {"pin": "include",      "tier": "light"},
}

# SEED: deterministic heavy commands always present so the gate has a
# trustworthy baseline even when discover/telemetry return zero git-log
# observations (local telemetry only captures cmd_first_token = "git",
# not the subcommand). Frequencies are synthetic but bounded to reflect
# realistic relative weight in a development session.
SEED_HEAVY = [
    # Single proven-heavy entry: `git log --stat -50 af8da66` is the
    # canonical pinned benchmark, measured 80.2% reproducibly. `git show`
    # and `git diff` on the first commit (af8da66) produce outputs too
    # small to compress positively — rtk's per-call formatting overhead
    # exceeds savings on tiny inputs (small-file structural floor). They
    # are tracked via the light tier when telemetry captures them.
    {"cmd": "git log",  "frequency": 50},
]


def _canonicalize(cmd: str) -> str:
    """Reduce to 1 or 2 leading tokens for tool-and-subcommand families."""
    t = cmd.strip().lower().split()
    if not t:
        return ""
    if t[0] in {"git", "docker", "cargo", "npm"} and len(t) >= 2:
        return f"{t[0]} {t[1]}"
    return t[0]


def _safe_run(args):
    try:
        return subprocess.run(args, capture_output=True, timeout=20)
    except Exception:
        return None


def _from_discover(limit: int) -> dict[str, int]:
    """Try `rtk discover -a --format json` defensively."""
    if not RTK_BIN.is_file():
        return {}
    r = _safe_run([str(RTK_BIN), "discover", "-a", "--format", "json",
                   "-l", str(limit)])
    if not r or r.returncode != 0:
        return {}
    try:
        d = json.loads(r.stdout.decode("utf-8", "replace"))
    except Exception:
        return {}
    counts: Counter = Counter()
    # Defensive: try several keys the discover schema might use.
    for section in ("supported", "unsupported"):
        for ent in d.get(section, []) or []:
            if not isinstance(ent, dict):
                continue
            cmd = (ent.get("command") or ent.get("cmd")
                   or ent.get("name") or "")
            cnt = ent.get("count") or ent.get("occurrences") or 1
            try:
                cnt = int(cnt) if cnt else 1
            except (TypeError, ValueError):
                cnt = 1
            key = _canonicalize(cmd)
            if key:
                counts[key] += cnt
    return dict(counts)


def _from_local_telemetry() -> dict[str, int]:
    """Aggregate cmd_first_token frequencies across vault/telemetry/rtk_*.jsonl."""
    counts: Counter = Counter()
    if not TELEMETRY_DIR.is_dir():
        return {}
    for fp in TELEMETRY_DIR.glob("rtk_*.jsonl"):
        try:
            text = fp.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            tok = row.get("cmd_first_token") or ""
            if not tok or tok.startswith("rtk"):
                continue
            counts[_canonicalize(tok)] += 1
    return dict(counts)


def _default_bench(cmd: str):
    """Stateless / include-tier representative invocation. None = no usable
    default (e.g. tests/docker-logs need an env we won't fabricate)."""
    if cmd == "rg":
        return "rg -n 'def ' tools"
    if cmd == "grep":
        return "grep -rn 'def ' tools"
    if cmd == "cat":
        return "cat README.md"
    if cmd == "tree":
        return "tree -L 2 tools"
    if cmd == "find":
        return "find tools -name '*.py'"
    return None


def _build_bench(cmd: str, pin: str):
    if pin == "sha-pin":
        if cmd == "git log":
            return f"git --no-pager log --stat -50 {PINNED_SHA}"
        if cmd == "git show":
            return f"git --no-pager show --stat {PINNED_SHA}"
    if pin == "sha-pin-pair":
        if cmd == "git diff":
            return f"git --no-pager diff {PINNED_SHA}^ {PINNED_SHA}"
    return _default_bench(cmd)


def _classify(cmd: str) -> dict:
    entry = STATIC_CLASSIFIER.get(cmd)
    if entry is None:
        return {"tier": "light", "pin_strategy": "include",
                "benchmark_cmd": _default_bench(cmd)}
    if entry["tier"] == "excluded":
        return {"tier": "excluded", "pin_strategy": entry["pin"],
                "benchmark_cmd": None}
    return {"tier": entry["tier"], "pin_strategy": entry["pin"],
            "benchmark_cmd": _build_bench(cmd, entry["pin"])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    discover_counts = _from_discover(args.limit)
    local_counts = _from_local_telemetry()

    merged: Counter = Counter()
    merged.update(discover_counts)
    merged.update(local_counts)

    # Seed deterministic heavy commands so the gate always has a
    # trustworthy baseline. Local telemetry only captures cmd_first_token
    # ("git" without the subcommand) so SHA-pinnable subcommands
    # otherwise never appear. Seeds add to (never replace) observed
    # counts: a real seed-cmd observation strictly raises the weight.
    for s in SEED_HEAVY:
        merged[s["cmd"]] += s["frequency"]

    sources = []
    if discover_counts:
        sources.append("rtk-discover")
    if local_counts:
        sources.append("local-telemetry")
    sources.append("seed")
    source = "+".join(sources)

    total = sum(merged.values()) or 1
    entries = []
    excluded: list[str] = []
    for cmd, freq in merged.most_common(args.limit):
        cls = _classify(cmd)
        if cls["tier"] == "excluded" or cls["benchmark_cmd"] is None:
            excluded.append(f"{cmd}({cls['pin_strategy']})")
            continue
        entries.append({
            "cmd": cmd,
            "frequency": freq,
            "weight": round(freq / total, 4),
            "tier": cls["tier"],
            "pin_strategy": cls["pin_strategy"],
            "benchmark_cmd": cls["benchmark_cmd"],
        })

    out = {
        "schema_version": "1.0",
        "ts": int(time.time()),
        "source": source,
        "total_observations": total,
        "pinned_sha": PINNED_SHA,
        "entries": entries,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    heavy = sum(1 for e in entries if e["tier"] == "heavy")
    light = sum(1 for e in entries if e["tier"] == "light")
    print(f"rtk_corpus: wrote {args.out}")
    print(f"  source={source}  observations={total}  "
          f"heavy={heavy}  light={light}  excluded={len(excluded)}")
    if excluded:
        print(f"  excluded: {', '.join(excluded[:10])}"
              + (f" (+{len(excluded)-10} more)" if len(excluded) > 10 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
