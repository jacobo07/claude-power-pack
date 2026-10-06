"""GGMC C6 -- `status --surface`: HOT / WARM / COLD / TERMINAL, the Owner-only flag and the estate KPIs.

Spec: vault/specs/goal-governed-mission-control.md (C6, Acceptance 6).

    python tools/test_gsd_mission_surface.py           every gate
    python tools/test_gsd_mission_surface.py --drill   each mutant must turn at least one gate red
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="surface-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_mission as gm  # noqa: E402
import mission_surface as msf  # noqa: E402

NOW = 1_800_000_000.0
RESULTS: list[tuple[str, bool, str]] = []
QUIET = [False]


def check(name, cond, ev=""):
    RESULTS.append((name, bool(cond), str(ev)))
    if not QUIET[0]:
        print(f"{'PASS' if cond else 'FAIL'} {name}: {ev}")


def guarded(name, fn):
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- a crash is a FAIL that names itself
        cond, ev = False, f"{type(exc).__name__}: {exc}"
    check(name, cond, ev)


def rec(state="RUNNING", **extra):
    return {"mission_id": "m-x", "state": state, "epoch": 1, **extra}


def sleep(kind, **wake):
    return {"cause": f"c-{kind}", "wake": {"kind": kind, **wake}, "epoch": 1, "reason": "r", "since": NOW}


def cls(r, action="relay"):
    return msf.classify(r, {"action": action, "reason": "x"}, NOW, gm.TERMINAL)["class"]


def gates():
    def rules():
        got = {
            "terminal": cls(rec(state=gm.COMPLETED), "none"),
            "unreadable": msf.classify(None, None, NOW, gm.TERMINAL)["class"],
            "owner_hold": cls(rec(owner_hold={"reason": "Owner"}), "none"),
            "quarantine": cls(rec(sleep=sleep("owner", action="release"))),
            "surface_blocked": cls(rec(), "surface_blocked"),
            "env_ready": cls(rec(sleep=sleep("env_ready", reasons=["auth_expired"]))),
            "cwd_aligned": cls(rec(sleep=sleep("cwd_aligned", status="diverged"))),
            "gsd_hold": cls(rec(state="BLOCKED", gsd_hold={"outcome": "UNAVAILABLE"}), "none"),
            "await": cls(rec(state="LAUNCHING"), "await"),
            "live_owner": cls(rec(), "none"),
        }
        want = {"terminal": "TERMINAL", "unreadable": "COLD", "owner_hold": "COLD", "quarantine": "COLD",
                "surface_blocked": "COLD", "env_ready": "WARM", "cwd_aligned": "WARM", "gsd_hold": "WARM",
                "await": "WARM", "live_owner": "HOT"}
        bad = {k: (got[k], want[k]) for k in want if got[k] != want[k]}
        return not bad, f"wrong={bad}" if bad else f"{len(want)} rules classed as specified"
    guarded("V-SURF-RULES", rules)

    def sleeping_relay():
        asleep = cls(rec(sleep=sleep("time", at=NOW + 600)), "relay")
        awake = cls(rec(), "relay")
        return asleep == "WARM" and awake == "HOT", f"asleep+relay={asleep} control(no sleep)+relay={awake}"
    guarded("V-SURF-SLEEP-BEFORE-PLAN", sleeping_relay)

    def due_wake():
        due = cls(rec(sleep=sleep("time", at=NOW - 1)), "relay")
        unknown = cls(rec(sleep=sleep("time", at=None)), "relay")
        return due == "HOT" and unknown == "WARM", f"due={due} unknown_time={unknown}"
    guarded("V-SURF-DUE-WAKE-IS-HOT", due_wake)

    def owner_only_flag():
        c = msf.classify(rec(owner_hold={"reason": "o"}), {"action": "none"}, NOW, gm.TERMINAL)
        w = msf.classify(rec(sleep=sleep("env_ready")), {"action": "relay"}, NOW, gm.TERMINAL)
        return c["owner_only"] is True and w["owner_only"] is False, f"cold={c['owner_only']} warm={w['owner_only']}"
    guarded("V-SURF-OWNER-ONLY-FLAG", owner_only_flag)

    def kpis():
        empty = msf.kpis([])
        rows = [{"class": "HOT"}, {"class": "WARM", "sleep_cause": "provider_quota"},
                {"class": "COLD", "owner_only": True, "sleep_cause": "provider_auth"}, {"class": "TERMINAL"}]
        k = msf.kpis(rows)
        ok = (empty["hot_ratio"] is None and empty["non_terminal"] == 0 and k["non_terminal"] == 3
              and k["hot_ratio"] == round(1 / 3, 3) and k["owner_only"] == 1
              and k["holds_by_cause"] == {"provider_auth": 1, "provider_quota": 1})
        return ok, f"empty_hot_ratio={empty['hot_ratio']} kpi={k}"
    guarded("V-SURF-KPI", kpis)

    def cli():
        for p in Path(TMP).glob("gsd-mission-*.json"):
            p.unlink()
        gm.create(TMP, "/gsd-autonomous", mission_id="m-surf-a", now=NOW)
        gm.transition("m-surf-a", expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                      sleep=sleep("env_ready", reasons=["auth_expired"]))
        gm.create(TMP, "/gsd-autonomous", mission_id="m-surf-b", now=NOW)
        env = {**os.environ, "CPP_CLAUDE_EXE": str(Path(TMP) / "no-such-claude.exe"), "PYTHONIOENCODING": "utf-8"}
        run = lambda *a: subprocess.run([sys.executable, str(HERE / "gsd_mission.py"), "status", *a],  # noqa: E731
                                        capture_output=True, text=True, encoding="utf-8", timeout=120, env=env)
        s, plain = run("--surface"), run()
        out = json.loads(s.stdout)
        by = {a["mission_id"]: a["class"] for a in out["attempts"]}
        legacy = json.loads(plain.stdout[plain.stdout.find("["):])
        ok = (s.returncode == 0 and by == {"m-surf-a": "WARM", "m-surf-b": "HOT"}
              and out["kpi"]["hot_ratio"] == 0.5 and out["kpi"]["holds_by_cause"] == {"c-env_ready": 1}
              and isinstance(legacy, list) and all("class" not in r for r in legacy) and len(legacy) == 2)
        return ok, f"rc={s.returncode} classes={by} kpi={out['kpi']} plain_rows={len(legacy)}"
    guarded("V-SURF-CLI-END-TO-END", cli)


def _mutants():
    real_classify, real_kpis = msf.classify, msf.kpis

    def ignore_sleep(r, plan, now, term):
        return real_classify({k: v for k, v in r.items() if k != "sleep"} if r else r, plan, now, term)

    def time_never_due(r, plan, now, term):
        if r and isinstance(r.get("sleep"), dict) and (r["sleep"].get("wake") or {}).get("kind") == "time":
            r = {**r, "sleep": {**r["sleep"], "wake": {"kind": "time", "at": None}}}
        return real_classify(r, plan, now, term)

    def empty_is_zero(rows):
        k = real_kpis(rows)
        return {**k, "hot_ratio": k["hot_ratio"] or 0.0}
    return [("plan-before-sleep", lambda: setattr(msf, "classify", ignore_sleep)),
            ("time-never-due", lambda: setattr(msf, "classify", time_never_due)),
            ("empty-estate-zero", lambda: setattr(msf, "kpis", empty_is_zero))], \
        lambda: (setattr(msf, "classify", real_classify), setattr(msf, "kpis", real_kpis))


def main(argv) -> int:
    if "--drill" in argv:
        mutants, restore = _mutants()
        QUIET[0] = True
        survived = []
        for name, apply in mutants:
            RESULTS.clear()
            apply()
            try:
                gates()
            finally:
                restore()
            red = [n for n, ok, _ in RESULTS if not ok]
            print(f"{'KILLED' if red else 'SURVIVED'} {name}: red={red}")
            if not red:
                survived.append(name)
        print(f"SURF_DRILL killed={len(mutants) - len(survived)}/{len(mutants)}")
        return 1 if survived else 0
    gates()
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"SURF_PASS={passed}/{len(RESULTS)}  threshold={len(RESULTS)}/{len(RESULTS)}")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
