"""What the paired oracle run actually costs, so admission is a measurement.

W11's paired `w11-prose` run was killed by the harness for host memory pressure
during its build phase, and the wave recorded the treatment as UNMEASURED. The
honest reading of that is not "the host was busy" -- it is that nobody knew what
the run needed, so nobody could say whether the host was ever going to carry it.
`modules/sqi/environment_qualifier.Workload` is explicit that the requirement is
DECLARED and never inferred, and a declaration pulled out of the air is the guess
that module refuses to make on the caller's behalf. This tool measures it.

Three properties it is built around:

* **Peak working set is measured in a CHILD, one child per sweep point.** Peak RSS
  is monotonic inside a process, so sweeping in-process would report the largest
  point for every point after it. A fresh child per point is the only reading that
  is attributable.
* **The subject's own peak is not confounded by host drift.** Free host memory on
  this estate moved 2245 -> 1055 -> 3795 MB inside one wave, so any figure derived
  from it needs a both-directions sweep before it means anything. The peak working
  set of my own child process is a direct property of the workload and is immune to
  what the rest of the machine is doing, which is precisely why the measurement is
  taken there rather than from the host gauge.
* **It writes nothing.** `build()` returns the store; `ucr_cif_oracle.main` is what
  persists it, and its `--store` DEFAULTS to the canonical
  `vault/ucr_cif/oracle_cases.json`. This tool never calls main and never writes a
  store, so a footprint sweep cannot damage the population a paired verdict is
  about.

The sweep is linear in sessions and the extrapolation is reported with the residual
that justifies it. An extrapolation is evidence about a shape, not a promise about a
number, so the admission record carries both.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def peak_working_set_mb() -> int | None:
    """Peak physical memory this process has ever held, in MB.

    None means "could not look", never zero. Windows first because that is this
    estate; `resource` covers posix so the tool is not silently single-platform.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class _Counters(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            c = _Counters()
            c.cb = ctypes.sizeof(_Counters)

            # HANDLE is pointer-width. Left at the ctypes default the pseudo-handle
            # -1 returned by GetCurrentProcess is marshalled as a 32-bit int, the
            # call fails, and this function returns None -- which reads exactly like
            # "this platform cannot be measured". Caught by the smoke test only
            # because the fail path refuses to invent a number.
            kernel32 = ctypes.windll.kernel32
            kernel32.GetCurrentProcess.restype = ctypes.c_void_p
            kernel32.GetCurrentProcess.argtypes = []
            handle = kernel32.GetCurrentProcess()

            # GetProcessMemoryInfo lives in psapi.dll and is ALSO exported from
            # kernel32 as K32GetProcessMemoryInfo. Try both: one missing export
            # must not be reported as an unmeasurable host.
            for dll, name in ((ctypes.windll.psapi, "GetProcessMemoryInfo"),
                              (kernel32, "K32GetProcessMemoryInfo")):
                try:
                    fn = getattr(dll, name)
                except AttributeError:
                    continue
                fn.restype = wintypes.BOOL
                fn.argtypes = [ctypes.c_void_p, ctypes.POINTER(_Counters),
                               wintypes.DWORD]
                if fn(handle, ctypes.byref(c), c.cb):
                    return int(c.PeakWorkingSetSize // (1024 * 1024))
            return None
        except Exception:
            return None
    try:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Linux reports KB, macOS reports bytes.
        return int(peak // 1024) if sys.platform.startswith("linux") else int(peak // (1024 * 1024))
    except Exception:
        return None


def run_child(n_sessions: int, arm: str) -> dict:
    """One sweep point, in this process. Only ever called via --child."""
    import ucr_cif_oracle as O  # noqa: PLC0415 -- deliberate: after sys.path

    t0 = time.time()
    store = O.build(n_sessions, O.DEFAULT_WINDOW_HOURS, arm=arm)
    elapsed = round(time.time() - t0, 2)
    return {
        "sessions": n_sessions,
        "arm": arm,
        "cases": len(store["cases"]),
        "routed": store["arm_divergence"].get("routed_cases"),
        "peak_mb": peak_working_set_mb(),
        "elapsed_s": elapsed,
    }


def _fit(points: list[dict]) -> dict:
    """Least-squares peak_mb = intercept + slope * sessions.

    Reported with the residual, because a two-point 'fit' through noise and a real
    linear cost look identical once you print only the prediction.
    """
    usable = [p for p in points if p.get("peak_mb") is not None]
    if len(usable) < 2:
        return {"ok": False,
                "reason": f"{len(usable)} usable point(s); a fit needs at least 2"}
    xs = [float(p["sessions"]) for p in usable]
    ys = [float(p["peak_mb"]) for p in usable]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return {"ok": False, "reason": "every sweep point used the same session count"}
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom
    intercept = my - slope * mx
    resid = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    return {
        "ok": True,
        "intercept_mb": round(intercept, 1),
        "slope_mb_per_session": round(slope, 4),
        "max_abs_residual_mb": round(max(abs(r) for r in resid), 1),
        "points": n,
    }


def predict(fit: dict, target: int) -> int | None:
    if not fit.get("ok"):
        return None
    return max(1, int(round(fit["intercept_mb"] + fit["slope_mb_per_session"] * target)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--child", type=int, default=0,
                    help="internal: run ONE sweep point in this process and "
                         "print its JSON. One child per point, because peak RSS "
                         "is monotonic within a process.")
    ap.add_argument("--arm", default="w11-prose")
    ap.add_argument("--sweep", default="30,60,120",
                    help="session counts to measure")
    ap.add_argument("--target", type=int, default=573,
                    help="the session count the real run will use")
    ap.add_argument("--reserve-mb", type=int, default=1024,
                    help="what the rest of the machine still needs to live on")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)

    if args.child:
        print(json.dumps(run_child(args.child, args.arm)))
        return 0

    from modules.sqi.environment_qualifier import Workload, capacity_probe, available_mb

    points: list[dict] = []
    for n in [int(x) for x in args.sweep.split(",") if x.strip()]:
        before = available_mb()
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()),
             "--child", str(n), "--arm", args.arm],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        after = available_mb()
        if proc.returncode != 0 or not proc.stdout.strip():
            points.append({"sessions": n, "peak_mb": None, "cases": None,
                           "child_exit": proc.returncode,
                           "child_stderr": (proc.stderr or "").strip()[-400:],
                           "host_avail_before_mb": before,
                           "host_avail_after_mb": after})
            print(f"  n={n:<5} CHILD FAILED exit={proc.returncode} "
                  f"-- this is a measurement failure, not a footprint")
            continue
        rec = json.loads(proc.stdout.strip().splitlines()[-1])
        rec["host_avail_before_mb"] = before
        rec["host_avail_after_mb"] = after
        points.append(rec)
        print(f"  n={rec['sessions']:<5} cases={rec['cases']:<6} "
              f"peak={rec['peak_mb']} MB  {rec['elapsed_s']} s "
              f"(host avail {before} -> {after} MB)")

    fit = _fit(points)
    peak = predict(fit, args.target)

    print("\n== FOOTPRINT ==")
    if not fit.get("ok"):
        print(f"  UNMEASURED: {fit['reason']}")
    else:
        print(f"  peak_mb = {fit['intercept_mb']} + "
              f"{fit['slope_mb_per_session']} x sessions   "
              f"(max |residual| {fit['max_abs_residual_mb']} MB over "
              f"{fit['points']} points)")
        print(f"  predicted peak at {args.target} sessions: {peak} MB")

    print("\n== ADMISSION ==")
    record: dict = {"arm": args.arm, "target_sessions": args.target,
                    "points": points, "fit": fit, "predicted_peak_mb": peak}
    if peak is None:
        print("  BLOCKED-UNMEASURABLE: no footprint, so no workload can be "
              "declared, and an undeclared workload is exactly what was never "
              "known when the W11 run was killed.")
        record["admission"] = {"passed": False,
                               "blocker": "footprint unmeasurable"}
    else:
        wl = Workload(name=f"ucr_cif_oracle paired build ({args.target} sessions, "
                           f"control vs {args.arm})",
                      peak_mb_per_unit=peak, units_in_flight=1,
                      reserve_mb=args.reserve_mb)
        res = capacity_probe(wl)
        verdict = {True: "ADMITTED", None: "MARGINAL", False: "REFUSED"}[res.passed]
        print(f"  {verdict}")
        print(f"  {res.observed}")
        if getattr(res, "blocker", None):
            print(f"  blocker: {res.blocker}")
        record["admission"] = {
            "passed": res.passed, "verdict": verdict,
            "observed": res.observed, "blocker": getattr(res, "blocker", None),
            "required_mb": wl.required_mb, "reserve_mb": wl.reserve_mb,
        }

    if args.out:
        dest = Path(args.out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(record, indent=1), encoding="utf-8")
        print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
