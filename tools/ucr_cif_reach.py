"""UCR-CIF W7 -- activation reach calibration CLI.

Read-only over the estate. Changes no routing, no gate, no ledger.

    python tools/ucr_cif_reach.py --ceiling
    python tools/ucr_cif_reach.py --funnel --sessions 400
    python tools/ucr_cif_reach.py --ceiling --funnel --out vault/audits/...

Every printed ratio carries its numerator and denominator. A percentage
whose population is not on the same line is the failure mode this wave is
most exposed to, so the formatter refuses to produce one.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.ucr_cif.prompt_population import (  # noqa: E402
    iter_prompts, iter_sessions)
from modules.repo_identity.identity import is_power_pack  # noqa: E402
from modules.ucr_cif.reach_calibration import measure_ceiling  # noqa: E402
from modules.ucr_cif.reach_funnel import replay  # noqa: E402
from modules.ucr_cif.reach_ground_truth import (  # noqa: E402
    DEFAULT_WINDOW_HOURS, label_case, load_history, parse_ts, paths_touched)


def _ratio(num: int, den: int) -> str:
    if den <= 0:
        return f"{num}/0 (no population -- not 0 %)"
    return f"{num}/{den} = {100.0 * num / den:.1f} %"


def run_ceiling() -> dict:
    t0 = time.perf_counter()
    rep = measure_ceiling()
    rep["elapsed_s"] = round(time.perf_counter() - t0, 2)
    pop = rep["population"]
    print("== REPO-SIDE CEILING ==")
    print(f"  working dirs discovered : {pop['working_dirs_discovered']}")
    print(f"  distinct repositories   : {pop['distinct_repositories']}")
    print(f"  population floor {pop['floor']}     : "
          f"{'MET' if pop['floor_met'] else 'NOT MET -- sweep suspect'}")
    if pop["missing_roots"]:
        print(f"  roots absent            : {pop['missing_roots']}")
    if pop["sweep_errors"]:
        print(f"  sweep errors            : {len(pop['sweep_errors'])}")
    if pop["groups_with_split_verdict"]:
        print("  split-verdict groups    : "
              f"{pop['groups_with_split_verdict']}")
    for label, key in (("by repository       ", "ceiling_by_repository"),
                       ("by working directory", "ceiling_by_working_dir")):
        c = rep[key]
        print(f"  door OPEN {label}: "
              f"{_ratio(c['door_reachable'], c['denominator'])}")
    for window, c in rep["ceiling_by_activity"].items():
        print(f"  door OPEN {window:<20}: "
              f"{_ratio(c['door_reachable'], c['denominator'])}")
    print("  shut by glob            : "
          + ", ".join(f"{g} x{n}" for g, n in rep["shut_by_glob"].items()))
    return rep


def _label_ground_truth(cases_with_ctx: list, window_h: int) -> None:
    """Attach the independent POST-HOC relevance label, in place.

    Runs inside the funnel pass because the oracle needs the real cwd and
    the privacy boundary forbids persisting it: the path is used here and
    dropped, and only the label survives into the artifact.

    History is loaded once per repository and reused, so the oracle costs
    one git subprocess per repo rather than one per prompt.
    """
    hist_cache: dict[str, object] = {}
    domain_cache: dict[str, bool] = {}
    for case, cwd, ts in cases_with_ctx:
        if not cwd:
            case.gt_label = "UNLABELLED_BY_DOMAIN"
            continue
        if cwd not in domain_cache:
            try:
                domain_cache[cwd] = bool(is_power_pack(cwd))
            except Exception:  # noqa: BLE001
                domain_cache[cwd] = False
        if not domain_cache[cwd]:
            case.gt_label = "UNLABELLED_BY_DOMAIN"
            continue
        if cwd not in hist_cache:
            hist_cache[cwd] = load_history(Path(cwd))
        hist = hist_cache[cwd]
        when = parse_ts(ts)
        if hist.error is not None or when is None:
            case.gt_label = "UNLABELLED_NO_HISTORY"
            continue
        touched = paths_touched(hist, when, window_h)
        case.gt_label, case.gt_owner_hits = label_case(
            case.owners_routed, touched, had_history=True, in_domain=True)


def run_funnel(n_sessions: int, window_h: int) -> dict:
    sessions = iter_sessions(limit=n_sessions)
    t0 = time.perf_counter()
    cases = []
    ctx = []
    for text, cwd, sid, ts in iter_prompts(sessions):
        c = replay(text, cwd, sid, ts)
        cases.append(c)
        ctx.append((c, cwd, ts))
    elapsed = time.perf_counter() - t0
    t_gt = time.perf_counter()
    _label_ground_truth(ctx, window_h)
    gt_elapsed = time.perf_counter() - t_gt

    # One prompt repeated across resumes is one observation, not several.
    seen: set[str] = set()
    uniq = []
    for c in cases:
        if c.prompt_sha in seen:
            continue
        seen.add(c.prompt_sha)
        uniq.append(c)

    eng = [c for c in uniq if not c.is_slash_command]
    layers = Counter(c.miss_layer for c in eng)
    t2 = [c for c in eng if c.reached_tier2]
    judged = [c for c in t2 if c.miss_layer != "cwd_unreadable"
              and c.miss_layer != "error"]
    with_owners = [c for c in judged if c.owners_routed]
    rendered = [c for c in judged if c.miss_layer == "none"]
    silent = [c for c in judged if c.miss_layer == "owners_routed_signal_silent"]

    print()
    print("== PROMPT-SIDE FUNNEL (real UserPromptSubmit history) ==")
    print(f"  sessions sampled        : {len(sessions)}")
    print(f"  prompt events read      : {len(cases)}")
    print(f"  unique prompts          : {len(uniq)}")
    print(f"  slash commands excluded : {len(uniq) - len(eng)}")
    print(f"  engineering population  : {len(eng)}")
    print(f"  reached Tier >= 2       : {_ratio(len(t2), len(eng))}")
    print(f"  judgeable at the door   : {_ratio(len(judged), len(t2))}")
    print(f"  owners COMPUTED         : {_ratio(len(with_owners), len(judged))}")
    print(f"  owners RENDERED         : {_ratio(len(rendered), len(judged))}")
    print(f"  owners computed, silent : {_ratio(len(silent), len(judged))}")
    print("  miss layers:")
    for layer, n in layers.most_common():
        print(f"      {layer:<32} {n}")
    print(f"  replay elapsed          : {elapsed:.1f} s "
          f"({1000 * elapsed / max(1, len(cases)):.1f} ms/prompt)")

    # --- activation quality against the INDEPENDENT oracle -------------
    # The population is only those cases the oracle could actually judge.
    # Everything it could not judge is printed beside the metric rather
    # than folded into it: an unlabelled case counted as a negative is how
    # a miss becomes a true negative and recall becomes a fiction.
    gt = Counter(c.gt_label for c in judged)
    labelled = [c for c in judged
                if c.gt_label in ("RELEVANT", "NOT_RELEVANT")]
    tp = [c for c in labelled
          if c.miss_layer == "none" and c.gt_label == "RELEVANT"]
    fp = [c for c in labelled
          if c.miss_layer == "none" and c.gt_label == "NOT_RELEVANT"]
    fn = [c for c in labelled
          if c.miss_layer != "none" and c.gt_label == "RELEVANT"]
    tn = [c for c in labelled
          if c.miss_layer != "none" and c.gt_label == "NOT_RELEVANT"]
    tp_exact = [c for c in tp
                if set(c.owners_routed) & set(c.gt_owner_hits)]

    print()
    print("== ACTIVATION QUALITY vs INDEPENDENT ORACLE (POST-HOC) ==")
    print(f"  oracle window           : {window_h} h")
    for lab, n in gt.most_common():
        print(f"      {lab:<24} {n}")
    print(f"  labelled population     : {_ratio(len(labelled), len(judged))}")
    if labelled:
        print(f"      TP {len(tp):<4} FP {len(fp):<4} "
              f"FN {len(fn):<4} TN {len(tn)}")
        print("      activation precision : "
              + _ratio(len(tp), len(tp) + len(fp)))
        print("      activation recall    : "
              + _ratio(len(tp), len(tp) + len(fn)))
        print("      miss rate            : "
              + _ratio(len(fn), len(tp) + len(fn)))
        print("      false activation rate: "
              + _ratio(len(fp), len(fp) + len(tn)))
        print("      correct-owner TP     : "
              + _ratio(len(tp_exact), max(1, len(tp))))
    else:
        print("      NO LABELLED POPULATION -- precision and recall are "
              "UNMEASURED, not 0. Report the reason, never a number.")

    by_class = Counter(c.semantic_class for c in t2)
    silent_by_class = Counter(c.semantic_class for c in silent)
    print("  Tier>=2 by semantic class (silent-with-owners in brackets):")
    for k, n in by_class.most_common():
        print(f"      {k:<16} {n}  [{silent_by_class.get(k, 0)}]")

    return {
        "sessions_sampled": len(sessions),
        "prompt_events": len(cases),
        "unique_prompts": len(uniq),
        "slash_excluded": len(uniq) - len(eng),
        "engineering_population": len(eng),
        "reached_tier2": len(t2),
        "judgeable": len(judged),
        "owners_computed": len(with_owners),
        "owners_rendered": len(rendered),
        "owners_computed_but_silent": len(silent),
        "miss_layers": dict(layers),
        "tier2_by_class": dict(by_class),
        "silent_by_class": dict(silent_by_class),
        "elapsed_s": round(elapsed, 2),
        "ms_per_prompt": round(1000 * elapsed / max(1, len(cases)), 2),
        "ground_truth": {
            "window_hours": window_h,
            "labels": dict(gt),
            "labelled": len(labelled),
            "tp": len(tp), "fp": len(fp), "fn": len(fn), "tn": len(tn),
            "tp_correct_owner": len(tp_exact),
            "elapsed_s": round(gt_elapsed, 2),
        },
        "cases": [c.__dict__ for c in uniq],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ceiling", action="store_true")
    ap.add_argument("--funnel", action="store_true")
    ap.add_argument("--sessions", type=int, default=300)
    ap.add_argument("--window-hours", type=int,
                    default=DEFAULT_WINDOW_HOURS,
                    help="ground-truth attribution window")
    ap.add_argument("--out", type=str, default="")
    args = ap.parse_args(argv)
    if not (args.ceiling or args.funnel):
        ap.error("choose --ceiling and/or --funnel")

    report: dict = {"measured_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if args.ceiling:
        report["repo_side"] = run_ceiling()
    if args.funnel:
        report["prompt_side"] = run_funnel(args.sessions, args.window_hours)

    if args.out:
        dest = Path(args.out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(report, indent=1, ensure_ascii=False),
                        encoding="utf-8")
        print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
