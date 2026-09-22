"""UCR-CIF W10 -- the paired owner-ranking evaluator W9's headline never had.

W9 reported "of 30 labelled cases with the true owner routed, rank improved
in 6 and worsened in 12, p = 0.238". A repo-wide sweep at W10 open found
that number in exactly two places: prose in `07_W9_STRUCTURAL.md` and a
docstring in `disposition_consumer`. NO COMMITTED CODE COMPUTES IT. The
headline of the previous wave could not be re-derived, which makes the
"re-run both arms fresh" contract unsatisfiable -- there was nothing to run.

This module is that instrument. It also fixes two defects the missing
instrument concealed.

1. THE TRUTH SET WAS A FUNCTION OF THE ARM. See `owner_truth`: crediting an
   owner only when it was routed means dropping a true owner REMOVES the
   case rather than scoring it as a loss. Truth here comes from the 40-owner
   authoritative universe and never from a routed list.

2. RANK AND CAP ARRIVED AS ONE NUMBER. W9 could not apportion its -6, and
   said so. The pre-cap order was computed and discarded one line later, so
   the decomposition was not merely unmeasured, it was unmeasurable. Both
   orders are now carried, and the two effects are reported separately:

       PRE-CAP   what the ranking decided          -- ranking quality
       POST-CAP  what the agent actually saw       -- the product surface
       EVICTION  present pre-cap, absent post-cap  -- the difference

BOTH ARMS RUN IN ONE PROCESS, interleaved per prompt. `_structural_ranking`
reads its env var on every call precisely so a harness can do this, and it
is strictly better than W9's two passes five minutes apart: the corpus, the
ledger, the projection, the working tree and the clock are identical by
construction rather than by hope, so `population drift` is not a caveat this
instrument has to carry.

EXECUTION PROOF. An evaluator that silently failed to enable the treatment
would report two identical arms -- and two identical arms are also what a
genuinely inert mechanism produces. Those must never be the same observable,
so the run FAILS LOUDLY when the arms do not differ: W9 measured reordering
on 78.5 % of routed selections, so identical arms mean the harness did not
drive the treatment, not that the treatment does nothing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter
from math import comb
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.repo_identity.identity import is_power_pack  # noqa: E402
from modules.ucr_cif.disposition_consumer import (  # noqa: E402
    MAX_OWNERS, load_ledger)
from modules.ucr_cif import structural_projection as _sp  # noqa: E402
from modules.ucr_cif.owner_truth import (  # noqa: E402
    modality, owner_units, owner_universe, rank_of, structural_share,
    truth_owners)
from modules.ucr_cif.prompt_population import (  # noqa: E402
    iter_prompts, iter_sessions)
from modules.ucr_cif.reach_funnel import replay  # noqa: E402
from modules.ucr_cif.reach_ground_truth import (  # noqa: E402
    DEFAULT_WINDOW_HOURS, load_history, parse_ts, paths_touched)

#: The env var `disposition_consumer` reads per call to enable M2 ranking.
RANK_ENV = "UCR_CIF_STRUCTURAL_RANK"

#: Schema of the case-level label store. Bumped whenever a field's MEANING
#: changes, because a consumer that silently reads an old meaning out of a
#: new file is how an oracle drifts from the thing it claims to measure.
ORACLE_SCHEMA = "ucr-cif-oracle/1"

#: Reordering floor for the execution proof. W9 measured 78.5 % of routed
#: selections reordered; anything near zero means the treatment arm did not
#: run. Deliberately far below the measurement so an honest change in the
#: mechanism does not trip it, and far above zero so a dead arm always does.
MIN_ARM_DIVERGENCE = 0.05

#: Movement classes. Kept separate on purpose -- collapsing ABSENT_BOTH into
#: "unchanged" would count a true owner neither arm found as agreement.
MOVES = ("improved", "worsened", "unchanged",
         "evicted", "admitted", "absent_both")


def divergence_ok(reordered: int, routed: int) -> bool:
    """Did the treatment arm actually run?

    A separate function so a gate can drive both poles. Inlining this in
    `build` would leave the execution proof itself unfalsifiable, which is
    exactly the shape of defect this suite exists to catch.
    """
    if routed <= 0:
        return False
    return (reordered / routed) >= MIN_ARM_DIVERGENCE


def _arm(text: str, cwd: str, sid: str, ts: str, treatment: bool):
    """One replay of the REAL production chain under one arm."""
    prior = os.environ.get(RANK_ENV)
    if treatment:
        os.environ[RANK_ENV] = "1"
    else:
        os.environ.pop(RANK_ENV, None)
    try:
        return replay(text, cwd, sid, ts)
    finally:
        if prior is None:
            os.environ.pop(RANK_ENV, None)
        else:
            os.environ[RANK_ENV] = prior


def classify(ctrl_rank, treat_rank) -> str:
    """How one true owner moved between the arms."""
    if ctrl_rank is None and treat_rank is None:
        return "absent_both"
    if ctrl_rank is None:
        return "admitted"
    if treat_rank is None:
        return "evicted"
    if treat_rank < ctrl_rank:
        return "improved"
    if treat_rank > ctrl_rank:
        return "worsened"
    return "unchanged"


def sign_test(improved: int, worsened: int) -> float | None:
    """Exact two-sided binomial p over DISCORDANT pairs only.

    Ties carry no directional information and are excluded -- including
    them would bias every result toward the null in proportion to how
    often the mechanism does nothing.
    """
    n = improved + worsened
    if n == 0:
        return None
    k = min(improved, worsened)
    tail = sum(comb(n, i) for i in range(0, k + 1)) / (2.0 ** n)
    return min(1.0, 2.0 * tail)


#: Conventional two-sided alpha and the power this estate sizes against.
#: Stated as constants so the numbers below are arguable rather than buried
#: inside a formula.
ALPHA_Z = 1.96          # two-sided 0.05
POWER_Z = 0.84          # 80 %


def detectable_pi(n_discordant: int) -> float | None:
    """Smallest improvement rate among discordant pairs this n can resolve.

    Solved by iteration rather than with a closed form, because the term
    under the root depends on the answer. Returns None below a handful of
    pairs, where the normal approximation is not honest and a number would
    be false precision.
    """
    if n_discordant < 8:
        return None
    pi = 0.75
    for _ in range(200):
        need = (ALPHA_Z * 0.5 + POWER_Z * (pi * (1 - pi)) ** 0.5)
        nxt = 0.5 + need / (n_discordant ** 0.5)
        if abs(nxt - pi) < 1e-9:
            break
        pi = min(0.999, nxt)
    return pi


def required_discordant(pi: float) -> int | None:
    """Discordant pairs needed to resolve a true rate `pi`."""
    if pi is None or abs(pi - 0.5) < 1e-6:
        return None
    num = ALPHA_Z * 0.5 + POWER_Z * (pi * (1 - pi)) ** 0.5
    return int((num / abs(pi - 0.5)) ** 2 + 0.9999)


def resolution_points(n_discordant: int, n_observed: int) -> float | None:
    """Detectable effect expressed in POINTS of the observed population.

    A sign test speaks about discordant pairs; the decision is about how
    much of the whole routed population moves. The bridge is the discordant
    RATE: resolving a shift to `pi` means resolving a net movement of
    `n_discordant * (2*pi - 1)` pairs, which is that fraction of the
    observed pairs. Reported so "3-point resolution" is a measured claim
    about this population rather than a slogan.
    """
    pi = detectable_pi(n_discordant)
    if pi is None or not n_observed:
        return None
    return 100.0 * (n_discordant / n_observed) * (2 * pi - 1)


def power_block(observed: int, discordant: int, improved: int,
                worsened: int) -> dict:
    """What this population can and cannot resolve, before any verdict."""
    pi = detectable_pi(discordant)
    obs_pi = (improved / discordant) if discordant else None
    return {
        "observed_pairs": observed,
        "discordant": discordant,
        "discordant_rate": round(discordant / observed, 4) if observed else None,
        "detectable_pi": round(pi, 4) if pi else None,
        "resolution_points": (
            round(resolution_points(discordant, observed), 2)
            if resolution_points(discordant, observed) else None),
        "observed_pi": round(obs_pi, 4) if obs_pi is not None else None,
        # How many discordant pairs it would take to resolve the effect
        # actually observed -- the honest answer to "how much more?"
        "required_for_observed_effect": required_discordant(obs_pi),
    }


def _fingerprint(meta, rows, universe, sessions, window_h, cases) -> dict:
    """Enough state to detect that two runs are not comparable.

    A timestamp is not a fingerprint: two runs a minute apart over a
    changed ledger share a minute and measure different worlds.
    """
    uni = hashlib.sha256("\n".join(universe).encode()).hexdigest()[:16]
    ids = hashlib.sha256(
        "\n".join(sorted(c["prompt_sha"] for c in cases)).encode()
    ).hexdigest()[:16]
    return {
        "oracle_schema": ORACLE_SCHEMA,
        "corpus_id": (meta or {}).get("compiled_corpus_id"),
        "ledger_rows": len(rows),
        "owner_universe_n": len(universe),
        "owner_universe_sha": uni,
        "case_set_sha": ids,
        "cases": len(cases),
        "sessions_swept": sessions,
        "window_hours": window_h,
        "max_owners": MAX_OWNERS,
    }


def build(n_sessions: int, window_h: int) -> dict:
    meta, rows = load_ledger()
    if not rows:
        raise RuntimeError("ledger unreadable -- refusing to report numbers")
    universe = owner_universe(rows)
    units = owner_units(rows)

    sessions = iter_sessions(limit=n_sessions)
    t0 = time.perf_counter()

    seen: set[str] = set()
    raw = []
    for text, cwd, sid, ts in iter_prompts(sessions):
        sha = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]
        if sha in seen:
            continue                      # one prompt is one observation
        seen.add(sha)
        raw.append((text, cwd, sid, ts))

    hist_cache: dict = {}
    domain_cache: dict = {}
    cases = []
    reordered = routed_any = 0

    for text, cwd, sid, ts in raw:
        c = _arm(text, cwd, sid, ts, treatment=False)
        t = _arm(text, cwd, sid, ts, treatment=True)
        if c.is_slash_command or not c.reached_tier2:
            continue
        if c.miss_layer in ("cwd_unreadable", "error"):
            continue

        if c.precap_owners:
            routed_any += 1
            if list(c.precap_owners) != list(t.precap_owners):
                reordered += 1

        # --- arm-independent truth ------------------------------------
        if not cwd:
            domain = False
        else:
            if cwd not in domain_cache:
                try:
                    domain_cache[cwd] = bool(is_power_pack(cwd))
                except Exception:                       # noqa: BLE001
                    domain_cache[cwd] = False
            domain = domain_cache[cwd]

        truth: tuple[str, ...] = ()
        status = "UNLABELLED_BY_DOMAIN"
        if domain:
            if cwd not in hist_cache:
                hist_cache[cwd] = load_history(Path(cwd))
            hist = hist_cache[cwd]
            when = parse_ts(ts)
            if hist.error is not None or when is None:
                status = "UNLABELLED_NO_HISTORY"
            else:
                touched = paths_touched(hist, when, window_h)
                if not touched:
                    status = "UNLABELLED_NO_COMMITS"
                else:
                    truth = truth_owners(touched, universe)
                    status = "LABELLED" if truth else "NO_OWNER_TOUCHED"

        cases.append({
            "prompt_sha": c.prompt_sha,
            "session_sha": c.session_sha,
            "date": c.date,
            "cwd_group_id": c.cwd_group_id,
            "semantic_class": c.semantic_class,
            "tier": c.tier,
            "length_bucket": c.length_bucket,
            "status": status,
            "truth_owners": list(truth),
            "control_precap": list(c.precap_owners),
            "control_routed": list(c.owners_routed),
            "treatment_precap": list(t.precap_owners),
            "treatment_routed": list(t.owners_routed),
            "gt_label_w7": c.gt_label,
        })

    elapsed = time.perf_counter() - t0
    fp = _fingerprint(meta, rows, universe, len(sessions), window_h, cases)
    div = (reordered / routed_any) if routed_any else 0.0
    # Modality is a property of the OWNER and of the evidence family, not of
    # any arm, so it is computed once here and frozen into the store with
    # the cases it describes.
    proj = _sp.load(corpus_id=(meta or {}).get("compiled_corpus_id"))
    return {
        "fingerprint": fp,
        "structural_share": structural_share(rows, proj),
        "projection_status": proj.status,
        "arm_divergence": {
            "routed_cases": routed_any,
            "reordered": reordered,
            "rate": round(div, 4),
            "floor": MIN_ARM_DIVERGENCE,
            "ok": div >= MIN_ARM_DIVERGENCE,
        },
        "owner_units": dict(units),
        "elapsed_s": round(elapsed, 1),
        "cases": cases,
    }


def _pairs(cases, precap: bool):
    """(case, owner, control_rank, treatment_rank) for every true owner."""
    ck = "control_precap" if precap else "control_routed"
    tk = "treatment_precap" if precap else "treatment_routed"
    for c in cases:
        if c["status"] != "LABELLED":
            continue
        for owner in c["truth_owners"]:
            yield c, owner, rank_of(owner, c[ck]), rank_of(owner, c[tk])


def _case_verdict(moves: list[str]) -> str:
    """Collapse one case's owner movements into ONE observation.

    Owner pairs drawn from a single prompt are not independent: they share
    a repository, a moment and an intent, so counting five of them as five
    observations manufactures power that is not there. A case is improved
    only when it improved and did not worsen, and a case that did both is
    `mixed` rather than silently resolved toward either pole.
    """
    d = [m for m in moves if m != "absent_both"]
    if not d:
        return "absent_both"
    up = any(m in ("improved", "admitted") for m in d)
    down = any(m in ("worsened", "evicted") for m in d)
    if up and down:
        return "mixed"
    if up:
        return "improved"
    if down:
        return "worsened"
    return "unchanged"


def slot_precision(cases) -> dict:
    """True vs false OWNER SLOTS on the surface the agent actually reads.

    PR-W10-20: a precision improvement must correspond to a real reduction
    in false owners. The rank metrics above cannot answer that -- they
    follow the true owner and say nothing about what fills the other
    slots, so a treatment could look neutral on rank while quietly
    swapping correct owners for incorrect ones.

    Slot counts are near-constant by construction, because the cap fills
    the same number of slots in both arms. That is what makes this a clean
    SUBSTITUTION measurement: any true-owner loss is a false-owner gain.
    """
    out = {"labelled_cases": 0,
           "control": {"slots": 0, "true": 0},
           "treatment": {"slots": 0, "true": 0}}
    for c in cases:
        if c["status"] != "LABELLED":
            continue
        out["labelled_cases"] += 1
        truth = set(c["truth_owners"])
        for arm, key in (("control", "control_routed"),
                         ("treatment", "treatment_routed")):
            out[arm]["slots"] += len(c[key])
            out[arm]["true"] += sum(1 for o in c[key] if o in truth)
    for arm in ("control", "treatment"):
        a = out[arm]
        a["false"] = a["slots"] - a["true"]
        a["precision"] = (a["true"] / a["slots"]) if a["slots"] else None
    c_, t_ = out["control"], out["treatment"]
    out["delta_true"] = t_["true"] - c_["true"]
    out["delta_false"] = t_["false"] - c_["false"]
    out["delta_precision_points"] = (
        round(100.0 * (t_["precision"] - c_["precision"]), 4)
        if c_["precision"] is not None and t_["precision"] is not None
        else None)
    return out


def analyse(store: dict) -> dict:
    cases = store["cases"]
    shares = store.get("structural_share") or {}
    out: dict = {"fingerprint": store["fingerprint"],
                 "arm_divergence": store["arm_divergence"],
                 "structural_share": shares}

    status = Counter(c["status"] for c in cases)
    out["status"] = dict(status)
    out["slot_precision"] = slot_precision(cases)

    for name, precap in (("pre_cap", True), ("post_cap", False)):
        moves = Counter()
        observed = 0          # owner present in at least one arm
        by_owner: dict = {}
        by_modality: dict = {}
        per_case: dict = {}
        for c, owner, cr, tr in _pairs(cases, precap):
            m = classify(cr, tr)
            moves[m] += 1
            if m != "absent_both":
                observed += 1
            by_owner.setdefault(owner, Counter())[m] += 1
            by_modality.setdefault(modality(owner, shares), Counter())[m] += 1
            per_case.setdefault(c["prompt_sha"], []).append(m)

        imp = moves["improved"] + moves["admitted"]
        wor = moves["worsened"] + moves["evicted"]

        # Cluster-respecting: one prompt contributes one observation.
        cv = Counter(_case_verdict(v) for v in per_case.values())
        c_imp, c_wor = cv["improved"], cv["worsened"]

        mod_stats = {}
        for mod, cnt in by_modality.items():
            i = cnt["improved"] + cnt["admitted"]
            w = cnt["worsened"] + cnt["evicted"]
            mod_stats[mod] = {
                "moves": {k: cnt[k] for k in MOVES},
                "improved": i, "worsened": w,
                "p_two_sided": sign_test(i, w),
            }

        out[name] = {
            "moves": {k: moves[k] for k in MOVES},
            "observed_pairs": observed,
            "discordant": imp + wor,
            "improved_incl_admitted": imp,
            "worsened_incl_evicted": wor,
            "p_two_sided": sign_test(imp, wor),
            "power": power_block(observed, imp + wor, imp, wor),
            # Nominal n is the pair count; EFFECTIVE n is the case count.
            # Both are reported because their gap IS the clustering, and a
            # single number would hide whichever direction flatters us.
            "effective": {
                "cases_contributing": sum(
                    1 for v in per_case.values()
                    if any(m != "absent_both" for m in v)),
                "verdicts": dict(cv),
                "discordant": c_imp + c_wor,
                "improved": c_imp, "worsened": c_wor,
                "p_two_sided": sign_test(c_imp, c_wor),
            },
            "by_modality": mod_stats,
            "by_owner": {o: dict(v) for o, v in sorted(by_owner.items())},
        }
    return out


def _print(rep: dict) -> None:
    fp = rep["fingerprint"]
    ad = rep["arm_divergence"]
    print("== POPULATION FINGERPRINT ==")
    for k in ("oracle_schema", "corpus_id", "ledger_rows", "owner_universe_n",
              "owner_universe_sha", "case_set_sha", "cases", "sessions_swept",
              "window_hours", "max_owners"):
        print(f"  {k:<20} {fp[k]}")
    print()
    print("== TREATMENT EXECUTION PROOF ==")
    print(f"  routed cases            {ad['routed_cases']}")
    print(f"  pre-cap order changed   {ad['reordered']} "
          f"= {100 * ad['rate']:.1f} %  (floor {100 * ad['floor']:.0f} %)")
    print(f"  verdict                 "
          f"{'ARMS DIVERGE -- treatment ran' if ad['ok'] else 'IDENTICAL ARMS -- HARNESS FAILURE'}")
    print()
    print("== ORACLE POPULATION ==")
    for k, n in sorted(rep["status"].items(), key=lambda x: -x[1]):
        print(f"  {k:<24} {n}")
    sp = rep["slot_precision"]
    print()
    print("== OWNER SLOTS ON THE RENDERED SURFACE (PR-W10-20) ==")
    for arm in ("control", "treatment"):
        a = sp[arm]
        pr = "n/a" if a["precision"] is None else f"{100 * a['precision']:.2f} %"
        print(f"  {arm:<10} slots {a['slots']:<5} true {a['true']:<4} "
              f"false {a['false']:<5} precision {pr}")
    print(f"  delta      true {sp['delta_true']:+d}  "
          f"false {sp['delta_false']:+d}  "
          f"precision {sp['delta_precision_points']:+.4f} points")
    for name in ("pre_cap", "post_cap"):
        s = rep[name]
        m = s["moves"]
        print()
        print(f"== {name.upper().replace('_', '-')} RANK MOVEMENT ==")
        print(f"  observed (owner, case) pairs : {s['observed_pairs']}")
        for k in MOVES:
            print(f"      {k:<14} {m[k]}")
        p = s["p_two_sided"]
        print(f"  discordant                   : {s['discordant']}")
        print(f"  improved / worsened          : "
              f"{s['improved_incl_admitted']} / {s['worsened_incl_evicted']}")
        print(f"  two-sided sign test p        : "
              f"{'n/a (no discordant pairs)' if p is None else f'{p:.4f}'}")
        pw = s["power"]
        print(f"  -- RESOLUTION (derived, not asserted) --")
        print(f"      discordant rate          : {pw['discordant_rate']}")
        print(f"      detectable pi @80%/.05   : {pw['detectable_pi']}")
        print(f"      RESOLUTION               : "
              f"{pw['resolution_points']} points of the observed population")
        print(f"      observed pi              : {pw['observed_pi']}")
        print(f"      discordant needed for it : "
              f"{pw['required_for_observed_effect']}")
        e = s["effective"]
        ep = e["p_two_sided"]
        print(f"  -- EFFECTIVE n (one prompt = one observation) --")
        print(f"      cases contributing       : {e['cases_contributing']}")
        print(f"      improved / worsened      : "
              f"{e['improved']} / {e['worsened']}  "
              f"(mixed {e['verdicts'].get('mixed', 0)}, "
              f"unchanged {e['verdicts'].get('unchanged', 0)})")
        print(f"      discordant               : {e['discordant']}")
        print(f"      p                        : "
              f"{'n/a' if ep is None else f'{ep:.4f}'}")
        print(f"  -- BY REPRESENTATION MODALITY --")
        for mod in ("prose", "code", "unknown"):
            st = s["by_modality"].get(mod)
            if not st:
                continue
            mp = st["p_two_sided"]
            print(f"      {mod:<8} improved {st['improved']:<3} "
                  f"worsened {st['worsened']:<3} "
                  f"p {'n/a' if mp is None else f'{mp:.4f}'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sessions", type=int, default=573)
    ap.add_argument("--window-hours", type=int, default=DEFAULT_WINDOW_HOURS)
    ap.add_argument("--store", default="vault/ucr_cif/oracle_cases.json")
    ap.add_argument("--out", default="")
    ap.add_argument("--from-store", action="store_true",
                    help="recompute the report from the canonical store "
                         "instead of re-running the arms")
    args = ap.parse_args(argv)

    store_path = Path(args.store)
    if args.from_store:
        store = json.loads(store_path.read_text(encoding="utf-8"))
    else:
        store = build(args.sessions, args.window_hours)
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store_path.write_text(
            json.dumps(store, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"wrote canonical store {store_path} "
              f"({len(store['cases'])} cases, {store['elapsed_s']} s)\n")

    rep = analyse(store)
    _print(rep)

    if args.out:
        dest = Path(args.out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(rep, indent=1, ensure_ascii=False),
                        encoding="utf-8")
        print(f"\nwrote derived report {dest}")

    if not store["arm_divergence"]["ok"]:
        print("\nHARNESS FAILURE: the arms are identical. The treatment path "
              "did not run, and no verdict about the mechanism follows.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
