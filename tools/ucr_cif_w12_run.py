"""One command for the W12 paired run: preflight, both arms, then the verdict.

W12 ended `BLOCKED — RESOURCE / EXTERNAL`. The run itself is cheap (155 MB peak,
measured) and the thing that kills it is the harness's background-shell pressure
reaper, which reads host memory while the session is idle and therefore cannot be
reached by making the job smaller. The only lever is an environment variable set when
Claude Code STARTS — a shell-set value has no effect — so the unblocking action belongs
to the Owner, and everything after it should be one auditable command rather than a
six-step protocol a fresh session reconstructs from a handoff.

**The preflight is the point.** Each arm takes about half an hour. A run that is going
to be reaped should fail in two seconds with the reason, not in thirty minutes with a
killed shell and nothing written — that is precisely how W11 and W12 each lost an
afternoon. So every precondition is checked before a single session is swept, each
refusal is its own class with its own message, and the reasons are disjoint because they
send you to different places.

It also guards the destructive default that this wave found and deliberately did not
repair: `ucr_cif_oracle.main`'s `--store` points at the canonical case store, so a
treatment run with default flags overwrites the control record the comparison is against.
This runner refuses to write there at all.

Nothing here touches the frozen subject. It orchestrates existing tools and adds no
semantics: the arms are `ucr_cif_oracle`, the verdict is `ucr_cif_w12_verdict`, and the
recovery rule lives in `w12_preregistration.md`.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

REAPER_ENV = "CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP"

#: Measured by tools/ucr_cif_footprint.py: peak_mb = 36.5 + 0.2071 x sessions,
#: max |residual| 1.9 MB over three points, 155 MB at 573 sessions. Declared rather
#: than inferred, because Workload refuses to guess on a caller's behalf.
PEAK_MB_PER_ARM = 155

CANONICAL_STORE = "vault/ucr_cif/oracle_cases.json"

DEFAULT_W9_STORE = "vault/ucr_cif/w12_arm_w9.json"
DEFAULT_W11_STORE = "vault/ucr_cif/w12_arm_w11.json"
DEFAULT_W9_REPORT = "vault/audits/ucr_cif/w12_report_w9.json"
DEFAULT_W11_REPORT = "vault/audits/ucr_cif/w12_report_w11.json"

#: The frozen constants. A run that starts with any of these moved is not measuring
#: the treatment this wave pre-registered, and the movement would be attributed to
#: the wrong cause.
FROZEN = {
    "STRUCTURAL_RANKING_ENABLED": False,
    "REQUIRE_STRUCTURAL_ATTRIBUTION": False,
    "MAX_OWNERS": 5,
    "MAX_DISTINCTIVE_REQUIRED": 3,
}


class Refusal(Exception):
    """A named precondition failure. Each carries its own remedy."""


def _check_reaper(allow: bool) -> str:
    live = os.environ.get(REAPER_ENV, "") != "1"
    if not live:
        return f"{REAPER_ENV}=1 — background shells will not be reaped"
    if allow:
        return (f"{REAPER_ENV} is NOT set and --allow-reaper was passed; proceeding "
                f"on the caller's assurance that the reaper is off")
    raise Refusal(
        f"{REAPER_ENV} is not set in this process, so the harness may reap this run "
        f"while the session is idle — which is what killed W11's and W12's arms, at "
        f"12.8 % and 12.3 % host free respectively, with a 155 MB job.\n"
        f"    This variable only takes effect when Claude Code STARTS; setting it from "
        f"a shell has no effect.\n"
        f"    Remedy: relaunch Claude Code with {REAPER_ENV}=1 in its environment, then "
        f"run this again.\n"
        f"    If you have confirmed by other means that the reaper is off, pass "
        f"--allow-reaper.")


def _check_capacity(arms: int) -> str:
    from modules.sqi.environment_qualifier import Workload, capacity_probe

    wl = Workload(name=f"ucr_cif W12 paired run ({arms} arms concurrent)",
                  peak_mb_per_unit=PEAK_MB_PER_ARM, units_in_flight=arms)
    res = capacity_probe(wl)
    if res.passed is True:
        return res.observed
    if res.passed is None:
        raise Refusal(
            f"host capacity is MARGINAL, which is neither a pass nor a failure and is "
            f"the state a thirty-minute run must not start in: {res.observed}\n"
            f"    blocker: {getattr(res, 'blocker', None)}")
    raise Refusal(f"host capacity REFUSED: {getattr(res, 'blocker', res.observed)}")


def _check_projection() -> str:
    from modules.ucr_cif import structural_projection as sp

    proj = sp.load()
    if not proj.usable:
        raise Refusal(
            f"the structural projection is {proj.status}, so the treatment arm would "
            f"contribute no structural evidence and the run would measure nothing. "
            f"Rebuild: python -m modules.ucr_cif.structural_projection --build")

    # Freshness is NOT a field on Projection -- `load()` records the fingerprint the
    # projection was built with and never compares it. `--verify` does the comparison
    # itself. The first version of this check read `getattr(proj, "source_fresh")`,
    # which is therefore ALWAYS None, so the stale branch below could never fire: a
    # vacuous guard in front of the one precondition that silently voids the treatment,
    # because a stale projection still loads, still reports LOADED, and still answers.
    built = proj.repo_fingerprint
    if not built:
        raise Refusal(
            "the projection carries no repo_fingerprint, so its freshness cannot be "
            "judged. 'Could not look' is not 'fresh'.")
    fresh = (built == sp.repo_fingerprint(ROOT))
    if fresh is False:
        raise Refusal(
            "the structural projection is LOADED but STALE against current sources. "
            "Staleness is safe while ranking is off; these arms switch ranking ON, so "
            "it is load-bearing here. Rebuild both arms against ONE generation: "
            "python -m modules.ucr_cif.structural_projection --build")
    return f"projection {proj.status}, source_fresh {fresh}"


def _check_frozen() -> str:
    from modules.ucr_cif import disposition_consumer as dc
    from modules.ucr_cif import ownership_evidence as oe

    seen = {k: getattr(dc, k, None) for k in FROZEN}
    seen["DISTINCTIVE_MAX_HOLDERS"] = getattr(oe, "DISTINCTIVE_MAX_HOLDERS", None)
    want = dict(FROZEN)
    want["DISTINCTIVE_MAX_HOLDERS"] = 3
    moved = {k: (want[k], seen[k]) for k in want if seen[k] != want[k]}
    if moved:
        raise Refusal(
            f"frozen constants have moved: {moved}. A paired verdict taken now would "
            f"attribute their effect to the treatment. Restore them, or open a new "
            f"treatment identity for the changed subject.")
    return "frozen constants unchanged: " + ", ".join(f"{k}={v}" for k, v in want.items())


def _check_stores(paths: list[str], force: bool) -> str:
    canon = (ROOT / CANONICAL_STORE).resolve()
    for p in paths:
        rp = (ROOT / p).resolve()
        if rp == canon:
            raise Refusal(
                f"refusing to write an arm to the CANONICAL case store ({p}). "
                f"ucr_cif_oracle's --store defaults there, so a run with default flags "
                f"overwrites the control record the comparison is against.")
        if rp.exists() and not force:
            raise Refusal(
                f"{p} already exists. Two arms must come from ONE session over ONE "
                f"population; reusing a store from an earlier run is the stored-report "
                f"defect W8 measured. Pass --force to overwrite.")
    return f"{len(paths)} store path(s) clear of the canonical store"


def preflight(arms: int, allow_reaper: bool, stores: list[str], force: bool) -> bool:
    checks = (
        ("reaper", lambda: _check_reaper(allow_reaper)),
        ("capacity", lambda: _check_capacity(arms)),
        ("projection", _check_projection),
        ("frozen", _check_frozen),
        ("stores", lambda: _check_stores(stores, force)),
    )
    ok = True
    print("== PREFLIGHT ==")
    for name, fn in checks:
        try:
            print(f"  PASS  {name:<12} {fn()}")
        except Refusal as exc:
            print(f"  REFUSE {name:<12} {exc}")
            ok = False
        except Exception as exc:                      # noqa: BLE001
            # A check that could not run is not a check that passed.
            print(f"  ERROR {name:<12} the check itself failed: {exc!r}")
            ok = False
    return ok


def _arm_cmd(arm: str, store: str, report: str, sessions: int) -> list[str]:
    return [sys.executable, "-u", str(ROOT / "tools" / "ucr_cif_oracle.py"),
            "--sessions", str(sessions), "--arm", arm,
            "--store", store, "--out", report]


def run_arms(sessions: int, w9_store: str, w9_report: str,
             w11_store: str, w11_report: str, logdir: Path) -> dict:
    """Both arms CONCURRENTLY, because the session store is live.

    Two arms half an hour apart re-create the population drift W7/W8 measured
    (23.5 %/2,350 re-derived as 20.0 %/2,306 with nothing changed). Ranking is
    deterministic, so contention changes wall time and cannot change a verdict.
    """
    logdir.mkdir(parents=True, exist_ok=True)
    jobs = {}
    for name, cmd in (("w9-structural", _arm_cmd("w9-structural", w9_store, w9_report, sessions)),
                      ("w11-prose", _arm_cmd("w11-prose", w11_store, w11_report, sessions))):
        log = logdir / f"w12_run_{name}.log"
        fh = log.open("w", encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        jobs[name] = {
            "proc": subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT,
                                     cwd=str(ROOT), env=env),
            "fh": fh, "log": log,
        }
        print(f"  started {name:<14} -> {log}")

    t0 = time.time()
    out = {}
    for name, j in jobs.items():
        rc = j["proc"].wait()
        j["fh"].close()
        out[name] = rc
        print(f"  {name:<14} exit={rc}  ({round(time.time() - t0)} s elapsed)")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--sessions", type=int, default=573)
    ap.add_argument("--w9-store", default=DEFAULT_W9_STORE)
    ap.add_argument("--w11-store", default=DEFAULT_W11_STORE)
    ap.add_argument("--w9-report", default=DEFAULT_W9_REPORT)
    ap.add_argument("--w11-report", default=DEFAULT_W11_REPORT)
    ap.add_argument("--logdir", default="_logs")
    ap.add_argument("--allow-reaper", action="store_true",
                    help="proceed although the reaper appears live; only if you have "
                         "confirmed by other means that it is off")
    ap.add_argument("--force", action="store_true",
                    help="overwrite existing arm stores")
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--rebuild-projection", action="store_true",
                    help="recompile the structural projection before preflight. "
                         "Opt-in, never automatic: it regenerates the evidence both "
                         "arms read, and that must be a visible decision rather than "
                         "something a runner did on the way past.")
    args = ap.parse_args(argv)

    if args.rebuild_projection:
        print("== REBUILDING PROJECTION (both arms will share this generation) ==")
        rc = subprocess.run(
            [sys.executable, "-u", "-m", "modules.ucr_cif.structural_projection",
             "--build"], cwd=str(ROOT)).returncode
        if rc != 0:
            print("projection rebuild FAILED; refusing to run arms against an unknown "
                  "evidence generation.")
            return 1
        print()

    stores = [args.w9_store, args.w11_store]
    if not preflight(len(stores), args.allow_reaper, stores, args.force):
        print("\nREFUSED before sweeping a single session. Nothing was written, and no "
              "hour was spent finding out.")
        return 1
    if args.preflight_only:
        print("\nPreflight passes. Re-run without --preflight-only to derive the arms.")
        return 0

    print("\n== ARMS (concurrent, one population) ==")
    rcs = run_arms(args.sessions, args.w9_store, args.w9_report,
                   args.w11_store, args.w11_report, ROOT / args.logdir)
    if any(rc != 0 for rc in rcs.values()):
        print("\nAn arm did not exit 0. A non-zero exit here is usually exit 2 from the "
              "oracle's own IDENTICAL ARMS harness check, which is never a finding that "
              "the treatment does nothing. Read the arm logs before re-running.")
        return 2

    print("\n== POPULATION COMPARABILITY ==")
    cmp_rc = subprocess.run(
        [sys.executable, "-u", str(ROOT / "tools" / "ucr_cif_oracle.py"),
         "--compare", args.w9_report, args.w11_report],
        cwd=str(ROOT)).returncode
    if cmp_rc != 0:
        print("\nThe two arms are not about the same population, so no paired verdict "
              "follows. Re-derive both in one session.")
        return 3

    verdict = [sys.executable, "-u", str(ROOT / "tools" / "ucr_cif_w12_verdict.py"),
               "--w9", args.w9_report, "--w11", args.w11_report]
    print("\n== STAGE 1: VALIDITY (no movement is computed here) ==")
    if subprocess.run(verdict, cwd=str(ROOT)).returncode != 0:
        print("\nValidity refused. No movement is reported, deliberately: a reader who "
              "has seen the outcome can no longer judge the run independently of it.")
        return 4

    print("\n== STAGE 2: MOVEMENT ==")
    return subprocess.run(
        verdict + ["--movement", "--out", "vault/audits/ucr_cif/w12_verdict.json"],
        cwd=str(ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
