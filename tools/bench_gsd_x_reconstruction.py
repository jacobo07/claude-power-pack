#!/usr/bin/env python3
"""Frozen A/B: does reconstruction_parity add information, and does it cost any?

BASELINE, captured before the contract existed (modules.gsd_x.heartbeat, live
state at 2026-09-20): informative_rate 0.6216 over 111 judgements, by_tier
FORENSIC 51 / LIGHT 41 / DEEP 16 / STANDARD 2 / ABSTAIN 1, by_floor 41.

That number cannot be the A/B subject: it accumulates only as the live hook
fires, so waiting for it would measure elapsed time, not the change. The
subject here is a FROZEN CORPUS run twice -- once with the contract withheld,
once with it present -- with every other input identical. Only the contract
moves, which is what makes the attribution causal.

TWO CLAIMS, AND THE SECOND IS THE ONE THAT CAN FAIL. (1) reconstruction
missions gain posture. (2) ordinary missions do NOT move. A change that raises
posture everywhere has raised the floor, not measured anything, and a benchmark
reporting only claim 1 would call that a success.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.contract import load_contracts  # noqa: E402
from modules.gsd_x import tier  # noqa: E402

CONTRACT_ID = "reconstruction_parity"

# Frozen corpus. RECONSTRUCTION entries name no tool, no lab and no technique --
# that is the point being measured. ORDINARY entries are real estate work.
RECONSTRUCTION = (
    "Port this APK game to Wii faithfully",
    "reimplement the legacy pricing engine with exact parity",
    "we need bit-level fidelity against the reference implementation",
    "port the renderer and keep parity with the original",
)
ORDINARY = (
    "fix the typo in the README heading",
    "que hora es",
    "add a unit test for the date parser",
    "why is the hook dispatcher timing out on the Stop chain",
    "rename the variable in line 40",
    "update the changelog for this release",
    "the build is failing on Windows with a path separator error",
    "summarise what changed in the last three commits",
    "increase the log level to debug in the staging config",
    "remove the unused import from the scorer",
)

RANK = {tier.LIGHT: 0, tier.STANDARD: 1, tier.DEEP: 2, tier.FORENSIC: 3}


def _classify(prompt: str, contracts):
    return tier.classify_prompt(prompt, contracts=contracts, root=_PP_ROOT)


def main() -> int:
    every = load_contracts()
    without = [c for c in every if c.id != CONTRACT_ID]
    if len(without) == len(every):
        print(f"HARNESS-FAILED: {CONTRACT_ID} absent, so A and B are the same run.")
        return 2
    print(f"contracts: {len(without)} without / {len(every)} with\n")

    raised, unchanged_recon = [], []
    for p in RECONSTRUCTION:
        a, b = _classify(p, without), _classify(p, every)
        arrow = f"{a.tier} -> {b.tier}"
        if RANK.get(b.tier, -1) > RANK.get(a.tier, -1):
            raised.append(p)
            print(f"  RAISED    {arrow:22s} {p!r}")
        else:
            unchanged_recon.append(p)
            print(f"  no change {arrow:22s} {p!r}")

    print()
    moved = []
    for p in ORDINARY:
        a, b = _classify(p, without), _classify(p, every)
        if a.tier != b.tier or a.by_floor != b.by_floor:
            moved.append((p, a.tier, b.tier))
            print(f"  MOVED     {a.tier} -> {b.tier:9s} {p!r}")
    if not moved:
        print(f"  ordinary corpus: {len(ORDINARY)}/{len(ORDINARY)} unchanged")

    # Informativeness over the whole frozen corpus.
    corpus = RECONSTRUCTION + ORDINARY
    inf_a = sum(1 for p in corpus if _classify(p, without).informative)
    inf_b = sum(1 for p in corpus if _classify(p, every).informative)
    n = len(corpus)
    print(f"\ninformative: {inf_a}/{n} without -> {inf_b}/{n} with "
          f"({inf_a / n:.3f} -> {inf_b / n:.3f})")

    ok = bool(raised) and not moved
    print(f"\nrecon raised: {len(raised)}/{len(RECONSTRUCTION)}   "
          f"ordinary moved: {len(moved)}/{len(ORDINARY)} (must be 0)")
    if unchanged_recon:
        print("recon NOT raised: " + "; ".join(repr(p) for p in unchanged_recon))
    print(f"RECON_AB={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
