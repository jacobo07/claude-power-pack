"""V-LIVE gates for tools/session_liveness.py (P5 shadow classifier). Each rule is driven from both poles; the mutation
drill flips IDLE to be reachable on a single signal and a gate must go red."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import session_liveness as sl  # noqa: E402

BASE = dict(cpu_delta_s=0.0, busy_children=0, job_state=None, transcript_age_s=5000.0, protected=False)
FAILS = []


def gate(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" -- " + detail) if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def st(**kw):
    return sl.classify({**BASE, **kw})[0]


def run_all():
    gate("V-LIVE-01 all signals say quiet => IDLE", st() == sl.IDLE)
    gate("V-LIVE-02 cpu delta alone => ACTIVE", st(cpu_delta_s=2.0) == sl.ACTIVE)
    gate("V-LIVE-03 busy non-MCP child alone => ACTIVE", st(busy_children=1) == sl.ACTIVE)
    gate("V-LIVE-04 working bg job alone => ACTIVE", st(job_state="working") == sl.ACTIVE)
    gate("V-LIVE-05 fresh transcript alone => ACTIVE", st(transcript_age_s=10.0) == sl.ACTIVE)
    gate("V-LIVE-06 stale transcript alone never makes IDLE (cpu unknown => UNKNOWN)", st(cpu_delta_s=None) == sl.UNKNOWN)
    gate("V-LIVE-07 children unknown => UNKNOWN", st(busy_children=None) == sl.UNKNOWN)
    gate("V-LIVE-08 transcript unknown => UNKNOWN", st(transcript_age_s=None) == sl.UNKNOWN)
    gate("V-LIVE-09 transcript between fresh and stale => UNKNOWN", st(transcript_age_s=400.0) == sl.UNKNOWN)
    gate("V-LIVE-10 mission/job lease protects even a quiet session", st(protected=True) == sl.UNKNOWN)
    gate("V-LIVE-11 unrecognised job state is not IDLE", st(job_state="weird") == sl.UNKNOWN)
    gate("V-LIVE-12 a single CPU sample cannot prove idle (None)", sl.classify({**BASE, "cpu_delta_s": None})[0] != sl.IDLE)
    rep = sl.report([{"state": sl.IDLE, "private_mb": 100.0}, {"state": sl.UNKNOWN, "private_mb": 900.0}])
    gate("V-LIVE-13 report counts only IDLE memory as reclaimable and says nothing is stopped",
         rep["idle_private_mb"] == 100.0 and rep["mode"] == "shadow" and "nothing is stopped" in rep["note"])
    src = open(sl.__file__, encoding="utf-8").read()
    gate("V-LIVE-14 module can stop nothing (no kill/terminate/suspend/taskkill call)",
         not any(w in src for w in (".kill(", ".terminate(", ".suspend(", "taskkill", "os.kill")))


def main():
    run_all()
    base_fails = list(FAILS)
    FAILS.clear()
    orig = sl.classify
    def mutant(s):  # IDLE on transcript age alone
        return (sl.IDLE, "mutant") if (s.get("transcript_age_s") or 0) >= sl.TRANSCRIPT_STALE_S else orig(s)
    sl.classify = mutant
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        run_all()
    sl.classify = orig
    caught = bool(FAILS)
    FAILS.clear()
    print(("PASS " if caught else "FAIL ") + "V-LIVE-MUT mutant (idle on transcript age alone) is caught")
    total_fail = len(base_fails) + (0 if caught else 1)
    print(f"{'ALL' if not total_fail else total_fail} gates {'PASS' if not total_fail else 'FAIL'}")
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
