#!/usr/bin/env python3
"""Where would shadow-deferred work have gone? (plan s14 S3)

A deferred spawn is not a saving. The work may have been available already, been
running already, run later anyway, or simply not been placeable by history. This
module classifies each spawn a replay did not ALLOW, from the usage index only,
and keeps the cost of each class apart so nobody can sum it into "savings".

RETROSPECTIVE ONLY. It reads what happened after each judged spawn, so its output
must never feed a pre-spawn decision, a receipt or a recommendation (audit G7).
Read-only SQL; no model call. Audit: vault/audits/ccp-s14-s3-audit.md.

Classes, first match wins, all among spawns with the same input_hash AND the same
root prompt (audit G2):
  REUSABLE_RESULT_EXISTED  an equivalent finished before t: its child transcript's
                           last call is at or before t and its launch was not refused.
  EQUIVALENT_ACTIVE        an equivalent started before t and its child was still
                           calling after t.
  RAN_LATER_EQUIVALENT     an equivalent started in (t, t + LATER_HORIZON_S].
  UNMEASURED_NO_HASH       the spawn itself has no input_hash.
  UNKNOWN                  none of the above: history cannot place the work.

"Finished" is the child's last call, never spawns.result_ts: 1,184 of 1,452
recorded results on 2026-10-03 were "Async agent launched successfully.", the
launch acknowledgement, so result_ts dates a launch, not a return.
Never asserted, for lack of any historical evidence: ELIMINATED, CONSUMED."""
from __future__ import annotations

from collections import Counter, defaultdict

REUSABLE = "REUSABLE_RESULT_EXISTED"
ACTIVE = "EQUIVALENT_ACTIVE"
RAN_LATER = "RAN_LATER_EQUIVALENT"
NO_HASH = "UNMEASURED_NO_HASH"
UNKNOWN = "UNKNOWN"
CLASSES = (REUSABLE, ACTIVE, RAN_LATER, NO_HASH, UNKNOWN)
# A saving is at most possible where the work had a result to reuse, was already
# being done, or cannot be placed. Work that ran later anyway was moved, not saved.
POSSIBLE_SAVING = (REUSABLE, ACTIVE, NO_HASH, UNKNOWN)
LATER_HORIZON_S = 6 * 3600     # unvalidated bound, reported with every result
NEVER_ASSERTED = ("ELIMINATED", "CONSUMED")


def refused_launches(con) -> set:
    """tool_use_ids whose launch returned an error: their child calls are not a result."""
    return {t for (t,) in con.execute("SELECT tool_use_id FROM spawns WHERE is_error = 1")}


def classify(spawn: dict, peers: list[dict], last_call: dict, refused: set) -> str:
    """One judged spawn against the other spawns of its (input_hash, root).
    last_call: fanout_ledger.child_last_call, the one definition of "finished"."""
    if not spawn.get("input_hash"):
        return NO_HASH
    t, me = spawn["ts"], spawn["tool_use_id"]
    others = [p for p in peers if p["tool_use_id"] != me]
    ran = [(p["ts"], last_call.get(p["tool_use_id"])) for p in others
           if p["tool_use_id"] not in refused]
    if any(ts < t and last is not None and last <= t for ts, last in ran):
        return REUSABLE                                # an equivalent had finished
    if any(ts < t and last is not None and last > t for ts, last in ran):
        return ACTIVE                                  # an equivalent was still running
    if any(t < p["ts"] <= t + LATER_HORIZON_S for p in others):
        return RAN_LATER
    return UNKNOWN


def displacement(con, judged: list[dict], verdict_of: dict, universe: list[dict]) -> dict:
    """judged: spawns_in rows of the judged window. verdict_of: tool_use_id -> v2
    verdict. universe: spawns_in rows of a window wide enough to hold every
    equivalent (before the judged window and LATER_HORIZON_S after it)."""
    groups = defaultdict(list)
    for p in universe:                 # an unresolved root matches nothing, not other unknowns
        if p.get("input_hash") and p.get("prompt"):
            groups[(p["input_hash"], p["prompt"])].append(p)
    import fanout_ledger as fl         # tools/ sibling, already on sys.path for every caller
    last_call, refused = fl.child_last_call(con), refused_launches(con)
    count, calls, cache_read = Counter(), Counter(), Counter()
    no_transcript, rows = 0, []
    for s in judged:
        verdict = verdict_of.get(s["tool_use_id"])
        if verdict is None or verdict == "ALLOW":
            continue
        cls = classify(s, groups.get((s.get("input_hash"), s["prompt"]), []),
                       last_call, refused)
        count[cls] += 1
        no_transcript += s["subtree_calls"] is None
        calls[cls] += s["subtree_calls"] or 0
        cache_read[cls] += s["subtree_cache_read"] or 0
        rows.append({"tool_use_id": s["tool_use_id"], "verdict": verdict, "class": cls})
    return {
        "evidence": "REPLAY + HINDSIGHT: retrospective, never a pre-spawn feature",
        "judged_not_allowed": sum(count.values()),
        "classes": {c: {"spawns": count[c],
                        "observed_child_file_cost": {"calls": calls[c],
                                                     "cache_read": cache_read[c]}}
                    for c in CLASSES},
        "possible_saving_cache_read": {"lower": 0,
                                       "upper": sum(cache_read[c] for c in POSSIBLE_SAVING)},
        "moved_not_saved_cache_read": cache_read[RAN_LATER],
        "cost_scope": "the child's own transcript only: grandchildren excluded; "
                      "a spawn without a child transcript counts 0",
        "no_transcript": no_transcript,
        "later_horizon_s": LATER_HORIZON_S,
        "never_asserted": list(NEVER_ASSERTED),
        "spawns": rows,
    }
