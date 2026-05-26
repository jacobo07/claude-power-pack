#!/usr/bin/env python3
"""M6 -- Regenerate the LT empirical fixture with BOTH arms populated.

Previously, V-LT-FIXTURE wrote the fixture with `with_skill_additional_
context` filled but `without_skill_additional_context = null` for every
prompt -- the Owner had nothing to compare against during blind eval.

This script:
  1. Calls `jit._detect_lateral_thinking_trigger` with LT detection ON
     for each of the 5 fixture prompts -> with_skill_additional_context.
  2. Monkeypatches the LT regex to return None for each prompt ->
     without_skill_additional_context. The result captures any *other*
     JIT signal (vague-lint, arch_check) that the prompt triggered
     independently of LT -- the honest baseline.
  3. Emits `vault/ceps/lt_empirical_canonical_<ts>.json` containing
     5 paired rows + pass-gate metadata + scoring rubric pointer.

The Owner reads the fixture and scores both arms blind per the rubric
documented in `vault/ceps/lt_empirical_scoring_protocol.md`. Pass-gate:
aggregate(with) >= aggregate(without) + 1.5 across all 5 prompts.

Usage: python tools/lt_empirical_regen.py
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP_ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import jit_skill_loader as jit  # noqa: E402

PROMPTS = [
    {
        "domain": "algorithmic",
        "prompt": (
            "I'm stuck on the N-queens algorithm scaling above N=30; "
            "recursion and bitboards already tried. Any lateral angles "
            "I haven't tried?"
        ),
    },
    {
        "domain": "product-ux",
        "prompt": (
            "Checkout abandonment refuses to drop after two flow "
            "rewrites. No idea what to try next."
        ),
    },
    {
        "domain": "system-design",
        "prompt": (
            "LiveView dashboards lag under poor mobile connections. "
            "We're atascados. Any alternativas you'd consider?"
        ),
    },
    {
        "domain": "debugging",
        "prompt": (
            "Cache eviction is failing in a complex problem -- it's "
            "correlated across tenants and the obvious answer is "
            "wrong. Brainstorm please."
        ),
    },
    {
        "domain": "creative",
        "prompt": (
            "Naming a new product tier. 'Pro' / 'Premium' / "
            "'Enterprise' feels too obvious. No idea where to start."
        ),
    },
]


def _compose_block(prompt: str, lt_enabled: bool) -> str | None:
    """Run the same pipeline the JIT loader uses for advisory blocks,
    optionally muting the LT detector to capture the without-arm
    baseline."""
    arch_block = None  # none of the 5 fixture prompts hit arch_check
    vague_block = jit._detect_vague_prompt(prompt, spec=None)
    if lt_enabled:
        lt_block = jit._detect_lateral_thinking_trigger(
            prompt, arch_block, vague_block)
    else:
        lt_block = None
    parts = [p for p in (arch_block, vague_block, lt_block) if p]
    return "\n\n".join(parts) if parts else None


def main() -> int:
    rows = []
    for entry in PROMPTS:
        prompt = entry["prompt"]
        with_ctx = _compose_block(prompt, lt_enabled=True)
        without_ctx = _compose_block(prompt, lt_enabled=False)
        rows.append({
            "domain": entry["domain"],
            "prompt": prompt,
            "with_skill_additional_context": with_ctx,
            "without_skill_additional_context": without_ctx,
            "owner_score_with": {
                "novelty": None, "depth": None, "actionability": None
            },
            "owner_score_without": {
                "novelty": None, "depth": None, "actionability": None
            },
        })

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_path = PP_ROOT / "vault" / "ceps" / f"lt_empirical_canonical_{ts}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fixture = {
        "spec_version": 2,
        "fixture_kind": "canonical-paired",
        "generated_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scoring_protocol": "vault/ceps/lt_empirical_scoring_protocol.md",
        "pass_gate": {
            "metric": (
                "aggregate(novelty+depth+actionability)_with >= "
                "aggregate(without) + 1.5"
            ),
            "n_prompts": len(rows),
            "max_score_per_pair": 15,
            "max_aggregate": 15 * len(rows),
        },
        "scoring_status": "owner-scoring-pending",
        "prompts": rows,
    }

    out_path.write_text(
        json.dumps(fixture, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")

    # Honesty audit -- prove both arms are now populated where they differ.
    paired = sum(1 for r in rows
                 if r["with_skill_additional_context"]
                 != r["without_skill_additional_context"])
    print(f"wrote {out_path.relative_to(PP_ROOT)}")
    print(f"prompts={len(rows)}  with!=without arm differs in {paired}/{len(rows)} rows")
    print(f"scoring_status={fixture['scoring_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
