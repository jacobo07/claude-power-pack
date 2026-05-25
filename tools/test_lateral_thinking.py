#!/usr/bin/env python3
"""M4 (empirical fixture + objective gates) + M5 (no-collision)
for the lateral-thinking skill JIT trigger family #10.

Run: `python tools/test_lateral_thinking.py` from the PP root.
Exit 0 = all objective gates pass. Empirical Owner-eval fixture is
written to `vault/ceps/lt_empirical_<ts>.json` for asynchronous
scoring (no LLM-in-the-loop here per Reality Contract).
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jit_skill_loader import run, LATERAL_CARD, VAGUE_LINT_MESSAGE  # noqa: E402

LT_PREFIX = "[lateral-thinking-skill]"
VAGUE_PREFIX = "[vague-prompt-lint]"


def _clean_cwd() -> str:
    return tempfile.mkdtemp(prefix="lt-test-")


def _ctx(r: dict) -> str:
    return r.get("additionalContext") or ""


# ---------------------------------------------------------------------------
# M4 — objective gates (LT trigger fires on stuck/design-pivot prompts)
# ---------------------------------------------------------------------------

OBJECTIVE_PROMPTS_FIRE = [
    # 5 mixed-domain prompts the trigger SHOULD fire on. Each one carries
    # >= 1 _LATERAL_RX keyword and at most 1 _ARCH_DESIGN_VERB substring
    # (so arch_check does NOT mutex them out).
    ("algorithmic",
     "I'm stuck on the N-queens algorithm scaling above N=30; recursion "
     "and bitboards already tried. Any lateral angles I haven't tried?"),
    ("product-ux",
     "Checkout abandonment refuses to drop after two flow rewrites. "
     "No idea what to try next."),
    ("system-design",
     "LiveView dashboards lag under poor mobile connections. We're "
     "atascados. Any alternativas you'd consider?"),
    ("debugging",
     "Cache eviction is failing in a complex problem -- it's correlated "
     "across tenants and the obvious answer is wrong. Brainstorm please."),
    ("creative",
     "Naming a new product tier. 'Pro' / 'Premium' / 'Enterprise' feels "
     "too obvious. No idea where to start."),
]


def gate_v_lt_fire() -> list[tuple[bool, str]]:
    """Each of the 5 prompts must trigger the LT card."""
    results = []
    for domain, prompt in OBJECTIVE_PROMPTS_FIRE:
        cwd = _clean_cwd()
        r = run({"prompt": prompt, "cwd": cwd})
        ctx = _ctx(r)
        ok = LT_PREFIX in ctx
        results.append((
            ok,
            f"V-LT-FIRE-{domain:14s} ctx_len={len(ctx):4d} "
            f"lt={'yes' if ok else 'NO '}",
        ))
    return results


# ---------------------------------------------------------------------------
# M5 — no-collision (LT defers to arch_check and vague-lint)
# ---------------------------------------------------------------------------

COLLISION_PROMPTS = [
    # 1) Triggers arch_check (>=2 design verbs) AND has LT keywords ->
    #    LT must defer (arch_check covers it)
    ("arch+lt",
     "Should I design the architecture between a microservice and a "
     "monolith? I'm stuck on which approach to propose to the team.",
     "arch_defers_lt"),
    # 2) Triggers vague-lint AND has LT keywords -> BOTH fire (mutex
    #    with vague-lint was dropped 2026-05-25 after empirical run --
    #    vague-lint's pronoun matchers over-fire on conversational use;
    #    the two advisories coexist and the agent decides which to act
    #    on. Updated expectation: both signals visible in extras.
    ("vague+lt",
     "I'm stuck on the bug",
     "both_fire"),
    # 3) Triggers ONLY vague-lint, no LT keywords -> only vague fires
    ("only-vague",
     "fix the auth bug",
     "vague_alone"),
    # 4) Triggers NEITHER -> nothing fires. Must avoid `this/that/it`
    #    (vague-lint would fire) and >= 30 tokens isn't necessary because
    #    we can also avoid the vague-referent regex entirely.
    ("neither",
     "list the most recent commit hashes available locally for review",
     "neither"),
]


def gate_v_lt_collision() -> list[tuple[bool, str]]:
    results = []
    for name, prompt, expectation in COLLISION_PROMPTS:
        cwd = _clean_cwd()
        r = run({"prompt": prompt, "cwd": cwd})
        ctx = _ctx(r)
        has_lt = LT_PREFIX in ctx
        has_vague = VAGUE_PREFIX in ctx

        if expectation == "arch_defers_lt":
            # We accept either arch fires OR neither -- the strict check
            # is that LT does NOT fire on its own when arch verbs >= 2.
            ok = not has_lt
            label = f"V-LT-COLL-{name:12s} lt_absent={'yes' if ok else 'NO'}"
        elif expectation == "both_fire":
            ok = has_lt and has_vague
            label = (f"V-LT-COLL-{name:12s} vague={has_vague} lt={has_lt} "
                     f"both={'yes' if ok else 'NO'}")
        elif expectation == "vague_alone":
            ok = has_vague and (not has_lt)
            label = (f"V-LT-COLL-{name:12s} vague={has_vague} lt={has_lt} "
                     f"isolated={'yes' if ok else 'NO'}")
        elif expectation == "neither":
            ok = (not has_lt) and (not has_vague)
            label = (f"V-LT-COLL-{name:12s} lt={has_lt} vague={has_vague} "
                     f"none={'yes' if ok else 'NO'}")
        else:
            ok = False
            label = f"V-LT-COLL-{name:12s} unknown-expectation"
        results.append((ok, label))
    return results


# ---------------------------------------------------------------------------
# Owner-eval fixture (M4 empirical pass-gate seed; no LLM in the loop)
# ---------------------------------------------------------------------------

def write_empirical_fixture() -> Path:
    """Save the 5 prompts + their LT-injected context to vault/ceps/.

    Owner can then run two parallel sessions per prompt (with the
    additionalContext payload pasted vs blank) and score the pair on
    novelty/depth/actionability (1-5 each, max 75 pts aggregate).
    Pass-gate (per plan P7): aggregate-with >= aggregate-without + 1.5.
    """
    ceps_dir = Path("vault/ceps")
    ceps_dir.mkdir(parents=True, exist_ok=True)
    fixture = {
        "spec_version": 1,
        "generated_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pass_gate": {
            "metric": "aggregate(novelty+depth+actionability)_with >= "
                      "aggregate_without + 1.5",
            "n_prompts": len(OBJECTIVE_PROMPTS_FIRE),
            "max_score_per_pair": 15,
        },
        "prompts": [],
    }
    for domain, prompt in OBJECTIVE_PROMPTS_FIRE:
        r = run({"prompt": prompt, "cwd": _clean_cwd()})
        fixture["prompts"].append({
            "domain": domain,
            "prompt": prompt,
            "with_skill_additional_context": _ctx(r) or None,
            "without_skill_additional_context": None,
            "owner_score_with": {"novelty": None, "depth": None,
                                 "actionability": None},
            "owner_score_without": {"novelty": None, "depth": None,
                                    "actionability": None},
        })
    out = ceps_dir / f"lt_empirical_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    out.write_text(json.dumps(fixture, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    failed: list[str] = []

    # M4 objective gates
    for ok, msg in gate_v_lt_fire():
        print(f"{'PASS' if ok else 'FAIL'}  {msg}")
        if not ok:
            failed.append(msg.split()[0])

    # M5 collision gates
    for ok, msg in gate_v_lt_collision():
        print(f"{'PASS' if ok else 'FAIL'}  {msg}")
        if not ok:
            failed.append(msg.split()[0])

    # Owner-eval fixture
    try:
        fix = write_empirical_fixture()
        print(f"PASS  V-LT-FIXTURE wrote {fix} ({fix.stat().st_size} B)")
    except Exception as exc:
        print(f"FAIL  V-LT-FIXTURE {type(exc).__name__}: {exc}")
        failed.append("V-LT-FIXTURE")

    # Card content sanity
    card_ok = (
        "lateral-thinking" in LATERAL_CARD
        and "5-frame" in LATERAL_CARD
        and "audit-trail" in LATERAL_CARD
    )
    print(f"{'PASS' if card_ok else 'FAIL'}  "
          f"V-LT-CARD-CONTENT len={len(LATERAL_CARD)} "
          f"contains_keys={'yes' if card_ok else 'NO'}")
    if not card_ok:
        failed.append("V-LT-CARD-CONTENT")

    if failed:
        print(f"\nFAILED: {', '.join(failed)}")
        return 1
    print("\nAll gates PASS. Empirical fixture awaiting Owner scoring.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
