#!/usr/bin/env python3
"""V-CE-T1-LIFE-* gates: obligation C3 part 1 (COMPLETION-PLAN Master Done-Gate) -- the
/kclear -> /clear -> /kresume lifecycle, driven through the REAL gate / resume_flow / certify_flow /
decide against a throwaway git repo and state dir (sandbox + fixtures imported from
test_ce_t1_state). The live ~/.claude/state/rollover is fingerprinted and must not move.

a. SAFE_TO_FORGET pole: a complete sealed capsule.
b. REFUSED poles, each with its own reason: unsealed, bytes changed, aged out, already certified.
c. Canary: seal -> gate -> transcript removed (the clear) -> resume_flow -> certify_flow ->
   RESUME_CERTIFIED + .certified; a second claimant is refused with exit 5.
d. Autocompact demoted: with a FORGET_SAFE capsule decide() picks rollover at the wall, even when
   usage is unreadable; compaction (would_rollover False) stays the fallback only with no capsule.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rollover as ro  # noqa: E402
import test_ce_t1_state as st  # noqa: E402

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def refused_with(g: dict, needle: str) -> bool:
    return g["verdict"] == "REFUSED" and any(needle in r for r in g["reasons"])


def main() -> int:
    before = st.live_fingerprint()
    tmp = Path(tempfile.mkdtemp(prefix="ce_t1_life_"))
    state = tmp / "state"
    st.STATE = state
    ro.STATE_DIR = state
    try:
        repo = st.make_repo(tmp)
        if ro.repo_facts(str(repo)).get("state") != "OK":
            print("HARNESS-FAILED: fixture repo unreadable; no gate judged")
            return 2

        print("C3 a: complete sealed capsule -> gate SAFE_TO_FORGET")
        sc = st.scenario(tmp, repo, "safe")
        g = ro.gate(sc["sid"], state)
        check("V-CE-T1-LIFE-SAFE", g["verdict"] == "SAFE_TO_FORGET" and not g["reasons"],
              f"verdict={g['verdict']} reasons={g['reasons']}")

        print("C3 b: REFUSED poles, each with its reason")
        sc = st.scenario(tmp, repo, "unsealed")
        rc = {"sealed": False, "reason": "seal refused"}
        stf = ro.safe_to_forget(rc, {"missing": []})
        ro.ledger("capsule_sealed", state, session_id=sc["sid"], cwd=str(repo), capsule=rc,
                  safe_to_forget=stf["verdict"], refusals=stf["reasons"])
        g = ro.gate(sc["sid"], state)
        check("V-CE-T1-LIFE-REFUSED-UNSEALED", refused_with(g, "no sealed hash")
              and refused_with(g, "the seal itself refused"), f"reasons={g['reasons']}")

        sc = st.scenario(tmp, repo, "bytes")
        p = ro.capsule_path(sc["sid"], state)
        p.write_bytes(p.read_bytes() + b"\n")
        g = ro.gate(sc["sid"], state)
        check("V-CE-T1-LIFE-REFUSED-BYTES", refused_with(g, "not the bytes that were sealed"),
              f"reasons={g['reasons']}")

        sc = st.scenario(tmp, repo, "aged")
        fresh = ro.gate(sc["sid"], state)
        g = ro.gate(sc["sid"], state, now=ro._now() + ro.RESET_MAX_AGE_S + 60)
        check("V-CE-T1-LIFE-REFUSED-AGED", fresh["verdict"] == "SAFE_TO_FORGET" and refused_with(g, "seal again"),
              f"fresh={fresh['verdict']} aged reasons={g['reasons']}")

        print("C3 c: canary seal -> gate -> clear -> resume_flow -> certify_flow")
        sc = st.scenario(tmp, repo, "canary")
        cap, sid = sc["cap"], sc["sid"]
        g = ro.gate(sid, state)
        sc["transcript"].unlink()                       # the /clear: the transcript is gone
        rcode, _ = st.quiet(ro.resume_flow, cap, "succ-canary", str(repo), state, obligations=cap["obligations"])
        answers = {i["key"]: i["a"] for i in ro.exam(cap)}
        (ccode, res), out = st.quiet(ro.certify_flow, sid, "succ-canary", answers, state)
        certified = ro.capsule_path(sid, state).with_suffix(".certified").exists()
        check("V-CE-T1-LIFE-CANARY", g["verdict"] == "SAFE_TO_FORGET" and not sc["transcript"].exists()
              and rcode == 0 and ccode == 0 and res.get("verdict") == "RESUME_CERTIFIED"
              and "RESUME_CERTIFIED" in out and certified,
              f"gate={g['verdict']} resume={rcode} certify={ccode} verdict={res.get('verdict')} certified={certified}")
        r2, out2 = st.quiet(ro.resume_flow, cap, "succ-second", str(repo), state, obligations=cap["obligations"])
        (c2, res2), _ = st.quiet(ro.certify_flow, sid, "succ-second", answers, state)
        check("V-CE-T1-LIFE-SECOND-CLAIMANT", r2 == 5 and "already claimed" in out2 and c2 == 5
              and res2.get("verdict") == "FENCED", f"resume={r2} certify={c2} verdict={res2.get('verdict')}")
        g = ro.gate(sid, state)
        check("V-CE-T1-LIFE-REFUSED-CERTIFIED", refused_with(g, "already certified"), f"reasons={g['reasons']}")

        print("C3 d: autocompact demoted -- a FORGET_SAFE capsule never falls to compaction at the wall")
        fs = ro.forget_safe(cap)
        cb = len(ro.bootstrap(cap))                     # what observe() passes for a live capsule
        unk = ro._unknown("no usage row")
        ok = {"state": "OK", "resident": 300_000, "floor": 60_000}
        ratio = {"state": "OK", "write": 1.25, "read": 0.1}
        d_unk = ro.decide(unk, cb, False, 75.0, ratio)
        d_ok = ro.decide(ok, cb, False, 75.0, ratio)
        check("V-CE-T1-LIFE-DEMOTE-CERTIFIED", fs["verdict"] == "FORGET_SAFE" and cb > 0
              and d_unk["would_rollover"] and d_ok["would_rollover"],
              f"forget_safe={fs['verdict']} unknown-usage={d_unk['would_rollover']} ok-usage={d_ok['would_rollover']}")
        d_none = ro.decide(unk, 0, False, 75.0, ratio)
        check("V-CE-T1-LIFE-DEMOTE-NO-CAPSULE", not d_none["would_rollover"],
              f"no capsule -> compaction fallback ({d_none['reason']})")
        d_calm = ro.decide(unk, cb, True, 40.0, ratio)
        check("V-CE-T1-LIFE-DEMOTE-NO-PRESSURE", not d_calm["would_rollover"],
              "below the wall an unreadable usage still never rolls (no pressure, no figures)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    after = st.live_fingerprint()
    check("V-CE-T1-LIFE-LIVE-UNTOUCHED", before == after, "live ~/.claude/state/rollover fingerprint unchanged")
    print(f"CE_T1_LIFE_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
