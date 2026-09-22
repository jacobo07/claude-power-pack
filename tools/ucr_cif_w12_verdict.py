"""The W12 verdict: run validity first, and movement only if validity passes.

Written and committed BEFORE either arm produced a number, for the same reason
`w12_preregistration.md` was: a comparator authored after the data exists can be
shaped by the data without anybody intending it, and nothing downstream would show
the difference.

The ordering is the whole instrument. W10 measured that every set-level effect in
this system belongs to the cap rather than to the ranking, so a treatment can look
repaired pre-cap and still arrive at the agent worse; and a paired verdict across two
populations that were never the same is not a weak result but a meaningless one. So
this tool refuses in three places before it will compute a single movement:

1. **comparability** -- `compare_fingerprints` must return COMPARABLE and
   `paired_verdict_allowed` must license it. UNREADABLE is neither DRIFTED nor
   COMPARABLE and is its own refusal, because a fingerprint that could not be read
   says nothing about drift.
2. **execution** -- both arms must show divergence from their own control. Identical
   arms are a HARNESS FAILURE, never a finding that the treatment does nothing; that
   is exactly the defect W8 found in `ucr_cif_shadow.py`.
3. **baseline identity** -- the freshly derived W9 arm must reproduce the
   pre-registered stratum. If it does not, the reference the comparison rests on has
   moved and the headline waits.

Only past all three does `--movement` print. Refusal exits non-zero and prints no
rank movement at all, so a reader cannot learn the answer and then decide whether the
run counted.

The recovery rule is `w12_preregistration.md` §4, transcribed rather than reinvented,
including the clause that makes an eviction disqualifying: an apparent gain bought by
removing the owner from the agent's view is the substitution W10 already measured, not
a repair.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ucr_cif_oracle as O  # noqa: E402

OWNER = "modules/governance-overlay"

#: The pre-registered W9-arm value for the harmed stratum, from the committed store
#: via `w12_precheck_from_store.json`. Named here so a drifted baseline is a refusal
#: rather than a silently different comparison.
PREREG_WORSENED = 8
PREREG_EVICTED = 0


def _load(path: str) -> dict | None:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _stratum(rep: dict, half: str, owner: str = OWNER) -> dict:
    """The owner's movement block, with every class present as an integer.

    `analyse` stores only non-zero classes, so a caller reading `.get("evicted")`
    gets None for "this owner was never evicted" and for "this half is missing"
    alike. Normalising here keeps that distinction in ONE place.
    """
    blk = ((rep.get(half) or {}).get("by_owner") or {}).get(owner) or {}
    return {m: int(blk.get(m, 0)) for m in O.MOVES}


def recovery(base: dict, treat: dict) -> tuple[str, str]:
    """w12_preregistration.md §4, applied to one half."""
    b_w, t_w = base["worsened"], treat["worsened"]
    b_e, t_e = base["evicted"], treat["evicted"]

    if t_e > b_e:
        return ("NOT_RECOVERED",
                f"worsened {b_w} -> {t_w}, but evicted {b_e} -> {t_e}: the owner "
                f"left the agent's view. A gain bought by eviction is the "
                f"substitution W10 measured, not a repair.")
    if t_w >= b_w:
        return ("NOT_RECOVERED",
                f"worsened {b_w} -> {t_w}: the movements did not move.")
    if t_w == 0:
        return ("FULLY_RECOVERED",
                f"worsened {b_w} -> 0, evicted {b_e} -> {t_e}.")
    return ("RECOVERED",
            f"worsened {b_w} -> {t_w}, evicted {b_e} -> {t_e}.")


def _fmt(d: dict) -> str:
    live = {k: v for k, v in d.items() if v}
    return ", ".join(f"{k} {v}" for k, v in live.items()) or "no movement"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--w9", required=True, help="derived report, control vs w9-structural")
    ap.add_argument("--w11", required=True, help="derived report, control vs w11-prose")
    ap.add_argument("--movement", action="store_true",
                    help="print rank movement -- only honoured once validity passes")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)

    a, b = _load(args.w9), _load(args.w11)
    record: dict = {"validity": {}, "movement": None}

    print("== RUN VALIDITY (decided before any outcome is visible) ==")

    # ---- 1. comparability -------------------------------------------------
    cmp = O.compare_fingerprints(a.get("fingerprint") if a else None,
                                 b.get("fingerprint") if b else None)
    licensed = O.paired_verdict_allowed(cmp)
    print(f"  comparability   {cmp['status']}  -- {cmp['reason']}")
    for k in cmp["moved"]:
        print(f"    moved         {k}: {cmp['detail'][k][0]} -> {cmp['detail'][k][1]}")
    record["validity"]["comparability"] = cmp
    record["validity"]["licensed"] = licensed

    # ---- 2. execution proof ----------------------------------------------
    divs = {}
    for name, rep in (("w9-structural", a), ("w11-prose", b)):
        ad = (rep or {}).get("arm_divergence") or {}
        divs[name] = ad
        ok = bool(ad.get("ok"))
        print(f"  arms diverge    {name:<14} {'YES' if ok else 'NO'}  "
              f"({ad.get('reordered')}/{ad.get('routed_cases')} reordered, "
              f"floor {ad.get('floor')})")
    record["validity"]["divergence"] = divs
    executed = all(bool(d.get("ok")) for d in divs.values())

    # ---- 3. baseline identity --------------------------------------------
    base_pre = _stratum(a, "pre_cap") if a else {m: 0 for m in O.MOVES}
    base_post = _stratum(a, "post_cap") if a else {m: 0 for m in O.MOVES}
    baseline_ok = (base_post["worsened"] == PREREG_WORSENED
                   and base_post["evicted"] == PREREG_EVICTED)
    print(f"  baseline        {OWNER} post-cap: {_fmt(base_post)} "
          f"(pre-registered: worsened {PREREG_WORSENED}, evicted {PREREG_EVICTED}) "
          f"-> {'REPRODUCED' if baseline_ok else 'MOVED'}")
    record["validity"]["baseline"] = {"pre_cap": base_pre, "post_cap": base_post,
                                      "reproduced": baseline_ok}

    valid = licensed and executed and baseline_ok
    print(f"\n  RUN {'VALID' if valid else 'INVALID'}")

    if not valid:
        print("\nREFUSED: no movement is reported from this pair. "
              "A verdict withheld for an invalid run is not a negative result; "
              "it is the absence of one.")
        if args.out:
            Path(args.out).write_text(json.dumps(record, indent=1), encoding="utf-8")
        return 1

    if not args.movement:
        print("\nValidity passes. Re-run with --movement to expose the outcome.")
        if args.out:
            Path(args.out).write_text(json.dumps(record, indent=1), encoding="utf-8")
        return 0

    # ---- movement, and not one line before here --------------------------
    treat_pre = _stratum(b, "pre_cap")
    treat_post = _stratum(b, "post_cap")
    mv: dict = {}

    print(f"\n== PRE-REGISTERED CAUSAL TEST -- {OWNER} ==")
    for half, base, treat in (("pre-cap", base_pre, treat_pre),
                              ("post-cap", base_post, treat_post)):
        verdict, why = recovery(base, treat)
        p_b = O.sign_test(base["improved"] + base["admitted"],
                          base["worsened"] + base["evicted"])
        p_t = O.sign_test(treat["improved"] + treat["admitted"],
                          treat["worsened"] + treat["evicted"])
        print(f"  {half:<9} w9  : {_fmt(base)}   p {p_b}")
        print(f"  {half:<9} w11 : {_fmt(treat)}   p {p_t}")
        print(f"  {half:<9} -> {verdict}  -- {why}")
        mv[half] = {"w9": base, "w11": treat, "verdict": verdict, "why": why,
                    "p_w9": p_b, "p_w11": p_t}

    headline = mv["post-cap"]["verdict"]
    print(f"\n  HEADLINE (post-cap, the half that reaches the agent): {headline}")

    print("\n== SAFETY STRATA ==")
    for half in ("pre_cap", "post_cap"):
        for mod in ("prose", "code", "mixed", "unknown"):
            ba = (((a.get(half) or {}).get("by_modality") or {}).get(mod) or {}).get("moves")
            tb = (((b.get(half) or {}).get("by_modality") or {}).get(mod) or {}).get("moves")
            if not ba and not tb:
                continue
            print(f"  {half:<9} {mod:<8} w9 {_fmt(ba or {})}  |  w11 {_fmt(tb or {})}")
            mv.setdefault("modality", {}).setdefault(half, {})[mod] = {
                "w9": ba, "w11": tb}

    print("\n== OWNER SLOTS ON THE RENDERED SURFACE ==")
    for name, rep in (("w9-structural", a), ("w11-prose", b)):
        sp = rep.get("slot_precision") or {}
        c, t = sp.get("control") or {}, sp.get("treatment") or {}
        print(f"  {name:<14} control true {c.get('true')} false {c.get('false')} | "
              f"treatment true {t.get('true')} false {t.get('false')} | "
              f"delta {sp.get('precision_delta_points')} points")
        mv.setdefault("slots", {})[name] = sp

    print("\n== TRUE-OWNER EVICTION, ALL OWNERS ==")
    for name, rep in (("w9-structural", a), ("w11-prose", b)):
        ev = {o: blk["evicted"]
              for o, blk in ((o, {m: int(v.get(m, 0)) for m in O.MOVES})
                             for o, v in ((rep.get("post_cap") or {})
                                          .get("by_owner") or {}).items())
              if blk["evicted"]}
        print(f"  {name:<14} {ev or 'none'}")
        mv.setdefault("evictions", {})[name] = ev

    record["movement"] = mv
    if args.out:
        Path(args.out).write_text(json.dumps(record, indent=1), encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
