#!/usr/bin/env python3
"""guarantee_ledger.py -- CO-10: Enforcement Guarantee Ledger (the conscience).

The kernel's honesty layer. Every enforcement mechanism makes a claim ("the
ceiling holds", "the cap is enforced"). CO-10 classifies each claim by the
guarantee it can ACTUALLY provide, names what no PP mechanism can guarantee, and
detects the un-gated paths that escape enforcement -- so the kernel never pretends
a guarantee it does not have. This is the dataset that keeps the family out of
theater.

The five honest levels (CO-10 I.2), by where a mechanism can act:
  1 PROMPT_ONLY  -- advisory text. Guarantees nothing enforceable.
  2 HOOK         -- in-process Claude Code hook. Detect/project/WARN reliably;
                    CANNOT block a running turn (response is advisory, BL-0003).
  3 WRAPPER      -- kclaude pre-launch. The ONLY surface that can truly BLOCK
                    (refuses to START an over-limit op at a boundary it owns).
  4 CURSOR_EXT   -- UI surface / cold-start dedup. No compute veto.
  5 HOST_LIMITED -- Windows/Cursor/Claude-Code internals the PP cannot reach.
                    Named as the residual; covered only by Owner discipline.

Block-power (can it actually stop the op?): only WRAPPER blocks. CO-10's central
prohibition is GUARANTEE INFLATION -- a mechanism claiming a stronger level than it
holds (e.g. an "absolute physical ceiling" for a level-2/3 mechanism). It also owns
the UN-GATED-PATH detector: a session/op with no wrapper pre-launch record escapes
every level-3 guarantee; its burn is counted (never hidden) and surfaced, never
falsely claimed as governed.
"""
from __future__ import annotations

from dataclasses import dataclass

PROMPT_ONLY, HOOK, WRAPPER, CURSOR_EXT, HOST_LIMITED = (
    "PROMPT_ONLY", "HOOK", "WRAPPER", "CURSOR_EXT", "HOST_LIMITED")

# Block-power: can the level actually STOP an operation? Only the wrapper.
_BLOCK_POWER = {PROMPT_ONLY: 0, HOOK: 1, CURSOR_EXT: 1, WRAPPER: 3,
                HOST_LIMITED: 0}


@dataclass
class GuaranteeEntry:
    mechanism: str
    level: str
    guarantees: str
    residual: str


# The living ledger (CO-10 II.1): every kernel enforcement, classified honestly.
LEDGER = {
    "CO-00-ceiling": GuaranteeEntry(
        "CO-00-ceiling", WRAPPER,
        "no op admitted whose projection breaches 60%; running session warned",
        "a running turn growing mid-generation; a manual non-kclaude launch"),
    "CO-02-governor": GuaranteeEntry(
        "CO-02-governor", WRAPPER,
        "over-budget launch refused/downgraded; breach registered",
        "mid-turn spend of a running session; an un-gated session"),
    "CO-03-router": GuaranteeEntry(
        "CO-03-router", HOOK,
        "cheapest-first model selection where it owns the call path",
        "a model call issued outside the cascade"),
    "CO-08-cap": GuaranteeEntry(
        "CO-08-cap", WRAPPER,
        "hard hot-session cap at the kclaude launch boundary",
        "a manually-opened terminal outside kclaude"),
    "CO-09-loop": GuaranteeEntry(
        "CO-09-loop", WRAPPER,
        "no uncapped loop admitted; kill switch at iteration boundaries",
        "one iteration's mid-generation interior"),
    "CO-04-paging": GuaranteeEntry(
        "CO-04-paging", HOOK,
        "proactive HOT minimization + eviction (load less)",
        "context the running turn holds mid-generation"),
    "CO-06-gc": GuaranteeEntry(
        "CO-06-gc", HOOK,
        "proactive eviction + conservative registry prune (never .jsonl)",
        "a running turn's context"),
    "CO-07-hibernation": GuaranteeEntry(
        "CO-07-hibernation", WRAPPER,
        "store-then-destroy; never loses a session",
        "host surfaces the host cannot restore (G4 PARTIAL)"),
    "CO-05-registry": GuaranteeEntry(
        "CO-05-registry", HOOK,
        "zero-cost retrieval when a fresh asset exists",
        "a retrieval miss silently costs a model call"),
    "restore_guard-dedup": GuaranteeEntry(
        "restore_guard-dedup", CURSOR_EXT,
        "reload-duplication prevented",
        "a manual duplicate terminal"),
}


def classify(mechanism: str):
    """The honest guarantee entry for a kernel mechanism, or None if unregistered
    (an enforcement claim with no registration is itself a flag -- III.1)."""
    return LEDGER.get(mechanism)


def block_power(level: str) -> int:
    return _BLOCK_POWER.get(level, 0)


@dataclass
class ClaimAudit:
    inflated: bool
    registered_level: str | None
    claimed_level: str
    note: str


def audit_claim(mechanism: str, claimed_level: str) -> ClaimAudit:
    """Flag GUARANTEE INFLATION: a claim asserting more blocking power than the
    mechanism's registered level holds. The path back to theater (III.4)."""
    entry = classify(mechanism)
    if entry is None:
        return ClaimAudit(True, None, claimed_level,
                          "unregistered mechanism claiming enforcement -- flagged")
    if block_power(claimed_level) > block_power(entry.level):
        return ClaimAudit(
            True, entry.level, claimed_level,
            f"INFLATION: claims {claimed_level} (block-power "
            f"{block_power(claimed_level)}) but registered {entry.level} "
            f"(block-power {block_power(entry.level)})")
    return ClaimAudit(False, entry.level, claimed_level,
                      "claim within registered guarantee level")


@dataclass
class UnGatedReport:
    un_gated: list                     # live sids with no wrapper pre-launch record
    covered: list                      # live sids that were wrapper-launched
    note: str = ""


def un_gated_sessions(live_sids, wrapper_prelaunch_sids) -> UnGatedReport:
    """The External Automation Control Plane (CO-10 II.2): a live session with no
    wrapper pre-launch record is UN-GATED -- it escapes every level-3 guarantee.
    Its burn still counts (CO-02) and it is surfaced; it is NEVER counted as
    governed, and the manual launch it represents is NEVER claimed as prevented."""
    w = set(wrapper_prelaunch_sids or ())
    live = list(live_sids or ())
    un = [s for s in live if s not in w]
    cov = [s for s in live if s in w]
    note = (f"{len(un)} un-gated of {len(live)} live -- counted + surfaced, "
            f"never claimed governed" if un else "all live sessions wrapper-gated")
    return UnGatedReport(un, cov, note)


def main(argv=None) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--mechanism", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.mechanism:
        e = classify(args.mechanism)
        if e and args.json:
            print(json.dumps(e.__dict__))
        elif e:
            print(f"{e.mechanism}: level={e.level} (block-power "
                  f"{block_power(e.level)})\n  guarantees: {e.guarantees}\n"
                  f"  residual: {e.residual}")
        else:
            print(f"# {args.mechanism}: UNREGISTERED (an enforcement claim here "
                  "would be flagged)")
        return 0
    for e in LEDGER.values():
        print(f"{e.level:13} bp={block_power(e.level)}  {e.mechanism}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
