"""Mission Baseline Capsule -- producer and reader. THE OWNER.

THE CONNECTOR. vault/audits/ucr_cif/10_E1_E2_OWNER_DISPOSITION.md measured the
gap: Construction Return WRITES (fd_07_flywheel deposits), Project Birth READS
(gsd_x/tier.py -> applicability), and nothing joins them. This joins them.

G-3 (09_G3_DECISION.md) decided the lane: the producer runs OUT OF BAND of any
latency-deadline chain and PERSISTS; the prompt path only READS. Production
measurement that forced it -- 815 chain abandonments in 8 days, gsd_x_tier named
in at least 215 of 639 on its own chain, and SessionStart abandoning too, so
there is no safe hook lane. A file read adds no spawn.

G-4 bounds what a capsule may touch. applicability.py evaluates six deterministic
gates before any score, and gate 2 is `if ctx.resolved_owners and ...` (:146):
an EMPTY set DISABLES it and a PARTIAL one turns it into a universal veto. So a
capsule contributes to `available_evidence` ONLY -- which can unblock and can
never invert applicability -- and never to held_scopes or resolved_owners.

vMAX-NULL-ERROR: six states, never silence. A capsule that is legitimately empty
and one that was never produced are different facts and say so.

  exit 0  capsule produced (whatever state)
  exit 2  could not resolve repo identity -- nothing written
"""
from __future__ import annotations

import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

# States. Exhaustive on purpose: "no output" is not one of them.
AVAILABLE = "AVAILABLE"                  # a baseline exists and applies here
NOT_APPLICABLE = "NOT_APPLICABLE"        # this repo is not in the family
EMPTY_BY_EVIDENCE = "EMPTY_BY_EVIDENCE"  # in the family, nothing promoted yet
PRODUCER_FAILURE = "PRODUCER_FAILURE"    # the producer ran and broke
STALE = "STALE"                          # produced, but older than the contract
UNKNOWN = "UNKNOWN"                      # never produced; NOT the same as empty

FRESH_SECONDS = 24 * 3600
FAMILY = "PERSISTENT_STATE"


def _state_dir() -> str:
    d = os.path.join(os.path.expanduser("~"), ".claude", "state", "tower")
    os.makedirs(d, exist_ok=True)
    return d


def _repo_key(path: str | None = None) -> str | None:
    """Canonical key. USE the owner, never a local slug -- repo_identity exists
    because slugging the cwd created a second identity with an empty ledger the
    moment anyone cd'd into a subdirectory (G-5)."""
    try:
        from modules.repo_identity.identity import repo_key
        # ABSOLUTE, always. canonical_repo returns a non-absolute argument
        # UNTOUCHED and says so in its own docstring -- deliberately, so a bare
        # label cannot be turned into an invented key. The consequence for a
        # caller is silent: repo_key(".") is "-", which resolves to a capsule
        # that never exists, and the reader then reports UNKNOWN for a repo that
        # has a perfectly good capsule. Measured here with a relative Path on
        # the first probe of the wired prompt path.
        return repo_key(os.path.abspath(path or os.getcwd()))
    except Exception:  # noqa: BLE001
        return None


def capsule_path(path: str | None = None) -> str | None:
    key = _repo_key(path)
    return os.path.join(_state_dir(), "capsule_%s.json" % key) if key else None


def _deposits_dir() -> str:
    return os.path.join(os.path.expanduser("~"), ".claude", "state",
                        "fable_distillation")


def _read_ledger(p: str) -> list:
    out = []
    if not os.path.exists(p):
        return out
    with open(p, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:  # noqa: BLE001
                continue
    return out


def _deposits_for(key: str) -> list:
    """Deposits from THIS repo's own ledger. Survivors only, by design:
    run_flywheel `continue`s on DUP and DISCARD before _writeback, so the ledger
    holds NEW/STRONGER and nothing else (11_O0_PRETREATMENT_BASELINE.md §4)."""
    return _read_ledger(os.path.join(_deposits_dir(), "deposits_%s.jsonl" % key))


def _deposits_institutional(exclude_key: str | None = None) -> tuple[list, int]:
    """EVERY repo's deposits, which is the whole point of a Tower.

    The first version of this module read only the local ledger, so advancing in
    QuickLease raised QuickLease's own capsule and nothing else -- per-project
    maturity wearing an institutional name. The Owner's ask is the opposite:
    "si yo avanzo con QuickLease, la proxima vez que pida algo en InfinityOps".
    The corpus states it as a Baseline Lift global (B 90.556): InfinityOps pays
    once, ORCA X inherits, KobiiCraft inherits.

    So inheritance is read from the WHOLE estate, and APPLICABILITY decides who
    receives it -- which is the spec's own rule, "la herencia viaja por la
    familia, no por el proyecto". A repo outside the family gets NOT_APPLICABLE
    before this function's result is ever used.

    KNOWN LIMITATION, stated rather than hidden: deposits carry no family tag.
    `task_class` was measured and does NOT carry that axis
    (13_FAMILY_SIGNAL_PROBE.md), so this counts institutional volume, not
    family-filtered maturity. Narrowing it needs family-tagged deposits, which
    is the next slice and not this one.
    """
    d = _deposits_dir()
    if not os.path.isdir(d):
        return ([], 0)
    rows: list = []
    ledgers = 0
    for fn in sorted(os.listdir(d)):
        if not (fn.startswith("deposits_") and fn.endswith(".jsonl")):
            continue
        if exclude_key and fn == "deposits_%s.jsonl" % exclude_key:
            continue
        ledgers += 1
        rows.extend(_read_ledger(os.path.join(d, fn)))
    return (rows, ledgers)


def _family_of(path: str) -> tuple[bool, str]:
    """Is this repo in the family? Delegates to the scanner whose two poles and
    population floor were predeclared and mutation-driven (15_P3...md)."""
    try:
        from tools.family_scan import scan_repo, main_repo_of
    except Exception:  # noqa: BLE001
        try:
            sys.path.insert(0, _HERE)
            from family_scan import scan_repo, main_repo_of  # type: ignore
        except Exception:  # noqa: BLE001
            return (False, "family scanner unavailable")
    try:
        main = main_repo_of(path)
        present = scan_repo(main).get("present") or []
        return (bool(present), ", ".join(present) if present else "no markers")
    except Exception as exc:  # noqa: BLE001
        return (False, "scan failed: %s" % type(exc).__name__)


FAMILY_TOKEN = "tower_family_persistent_state"
HARVEST_TOPIC = "landed-commit"   # pm_03_bus.HARVEST_TOPIC; see _lessons_from

# P4 -- the capsule's token ceiling. A lesson list that grows with the estate
# would turn inheritance into a context cost paid on every session, which is
# exactly how an advisory gets switched off.
MAX_LESSONS = 8
MAX_LESSON_CHARS = 220
MAX_LESSONS_CHARS = 1400
_DEST_RANK = {"hard_rule": 0, "benchmark": 1, "asset": 2, "prompt_fragment": 3,
              "dataset_part": 4}


def _lessons_from(own: list, inherited: list) -> list:
    """The deposits worth putting in front of the agent, bounded.

    Excluded on purpose: `landed-commit` deposits. From ANOTHER repo a commit
    subject is product-specific (class A/B in spec §5) -- CavEX's "Pos is eye
    height" means nothing in InfinityOps. From THIS repo it is already in
    `git log`. Both still count as Tower entries; neither is a lesson to inherit.

    Ranked by destination, then confidence, then recency. That is a priority,
    NOT relevance to the current mission: nothing here reads the prompt, and
    saying otherwise would be a claim this module cannot back.
    """
    pool = []
    for origin, rows in (("own", own), ("inherited", inherited)):
        for d in rows:
            if d.get("delta_class") not in ("NEW", "STRONGER"):
                continue
            if (d.get("task_class") or "") == HARVEST_TOPIC:
                continue
            claim = " ".join(str(d.get("claim") or "").split())
            if not claim:
                continue
            pool.append((_DEST_RANK.get(d.get("destination"), 9),
                         -float(d.get("confidence") or 0), str(d.get("ts") or ""),
                         origin, d.get("destination", "?"), claim))
    pool.sort(key=lambda t: t[2], reverse=True)          # newest first ...
    pool.sort(key=lambda t: (t[0], t[1]))                # ... within rank+confidence
    out, used, seen = [], 0, set()
    for _, _, _, origin, dest, claim in pool:
        text = claim if len(claim) <= MAX_LESSON_CHARS else claim[:MAX_LESSON_CHARS - 1] + "…"
        if text in seen:
            continue
        if len(out) >= MAX_LESSONS or used + len(text) > MAX_LESSONS_CHARS:
            break
        seen.add(text)
        used += len(text)
        out.append({"origin": origin, "destination": dest, "claim": text})
    return out


def produce(path: str | None = None) -> dict:
    """Build and persist the capsule. Out of band by construction: nothing calls
    this from a hook chain.

    TWO LAYERS (spec §12.4). The Tower is universal ancestry and sits ABOVE the
    family baselines; it does not replace them. The first version gated the
    whole capsule behind PERSISTENT_STATE, so a repo outside that one family --
    CavEX, whose level.dat writer destroyed three worlds -- inherited nothing at
    all, and the only lever left was widening a family classifier until it
    over-matched (17_P3B_RESULT_STOPPED.md). Now:

      state    the UNIVERSAL layer. Every repo is in it; never NOT_APPLICABLE.
      family   the family layer, on the strict classifier, with its own state.
    """
    root = os.path.abspath(path or os.getcwd())
    key = _repo_key(root)
    if not key:
        return {"state": PRODUCER_FAILURE, "reason": "repo identity unresolved"}

    try:
        own = _deposits_for(key)
        inherited, ledgers = _deposits_institutional(exclude_key=key)
        promoted = [d for d in own + inherited
                    if d.get("delta_class") in ("NEW", "STRONGER")]
        own_promoted = [d for d in own
                        if d.get("delta_class") in ("NEW", "STRONGER")]

        try:
            in_family, why = _family_of(root)
            family = {"name": FAMILY,
                      "state": AVAILABLE if in_family else NOT_APPLICABLE,
                      "reason": ("in %s (%s)" if in_family
                                 else "repo is not in %s (%s)") % (FAMILY, why)}
        except Exception as exc:  # noqa: BLE001
            in_family = False
            family = {"name": FAMILY, "state": PRODUCER_FAILURE,
                      "reason": "family scan failed: %s" % type(exc).__name__}

        if not promoted:
            cap = {"state": EMPTY_BY_EVIDENCE,
                   "reason": "the estate holds no promoted deposit at all yet",
                   "evidence_tokens": [],
                   "lessons": []}
        else:
            dests: dict[str, int] = {}
            for d in promoted:
                k = d.get("destination", "?")
                dests[k] = dests.get(k, 0) + 1
            harvested = sum(1 for d in promoted
                            if (d.get("task_class") or "") == HARVEST_TOPIC)
            cap = {
                "state": AVAILABLE,
                "reason": "%d promoted delta(s) in the estate: %d from this "
                          "repo, %d INHERITED from %d other ledger(s)"
                          % (len(promoted), len(own_promoted),
                             len(promoted) - len(own_promoted), ledgers),
                "entries": len(promoted),
                "own_entries": len(own_promoted),
                "inherited_entries": len(promoted) - len(own_promoted),
                # Captured automatically from landed commits (C1) vs published
                # as a finding. Volume is not lift; this keeps the two apart.
                "harvested_entries": harvested,
                "source_ledgers": ledgers + 1,
                "destinations": dests,
                # Honest: FD-07 writes portability_proven=False by contract,
                # so the `verified` clause of the canonical Tower definition
                # is NOT claimed here.
                "verified_entries": sum(
                    1 for d in promoted if d.get("portability_proven") is True),
                "evidence_tokens": ["tower_baseline"]
                                   + ([FAMILY_TOKEN] if in_family else []),
                "lessons": _lessons_from(own, inherited),
            }
        cap["family_layer"] = family
    except Exception as exc:  # noqa: BLE001
        cap = {"state": PRODUCER_FAILURE,
               "reason": "%s: %s" % (type(exc).__name__, exc)}

    cap.update({"family": FAMILY, "repo_key": key, "repo": root,
                "produced_at": time.time(), "schema": 2})
    out = capsule_path(root)
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cap, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, out)   # atomic: no observable half-written capsule
    return cap


def read(path: str | None = None) -> dict:
    """What the prompt path sees. NEVER silence -- absence is UNKNOWN, said."""
    p = capsule_path(path)
    if not p or not os.path.exists(p):
        return {"state": UNKNOWN,
                "reason": "no capsule produced for this repo",
                "evidence_tokens": []}
    try:
        with open(p, "r", encoding="utf-8") as fh:
            cap = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        return {"state": PRODUCER_FAILURE,
                "reason": "capsule unreadable: %s" % type(exc).__name__,
                "evidence_tokens": []}
    age = time.time() - float(cap.get("produced_at") or 0)
    if age > FRESH_SECONDS:
        cap["state"] = STALE
        cap["reason"] = "produced %.1f h ago, contract is %.0f h" % (
            age / 3600.0, FRESH_SECONDS / 3600.0)
        cap["evidence_tokens"] = []      # stale evidence is not evidence
        cap["lessons"] = []              # ... and a stale lesson is not a lesson
    cap.setdefault("evidence_tokens", [])
    cap.setdefault("lessons", [])
    return cap


def lessons(path: str | None = None) -> list:
    """The bounded lessons a fresh AVAILABLE capsule hands to the prompt path.
    Anything else -- UNKNOWN, STALE, EMPTY, a schema-1 capsule -- hands over none."""
    try:
        cap = read(path)
        return list(cap.get("lessons") or []) if cap.get("state") == AVAILABLE else []
    except Exception:  # noqa: BLE001
        return []


def evidence_tokens(path: str | None = None) -> list:
    """The ONLY thing a capsule contributes to MissionContext. Adding evidence
    can unblock a capability and can never invert applicability; held_scopes and
    resolved_owners could, and are deliberately never touched (G-4)."""
    try:
        cap = read(path)
        return list(cap.get("evidence_tokens") or []) if cap.get("state") == AVAILABLE else []
    except Exception:  # noqa: BLE001
        return []


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    cap = produce(target)
    if cap.get("state") == PRODUCER_FAILURE and "identity" in str(cap.get("reason")):
        print("CAPSULE: %s -- %s" % (cap["state"], cap["reason"]))
        return 2
    print("CAPSULE %s" % cap.get("state"))
    print("  repo        %s" % cap.get("repo"))
    print("  repo_key    %s" % cap.get("repo_key"))
    print("  family      %s" % cap.get("family"))
    print("  reason      %s" % cap.get("reason"))
    if cap.get("state") == AVAILABLE:
        print("  entries     %d  (verified: %d)"
              % (cap.get("entries", 0), cap.get("verified_entries", 0)))
        print("  destinations %s" % cap.get("destinations"))
    print("  written     %s" % capsule_path(target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
