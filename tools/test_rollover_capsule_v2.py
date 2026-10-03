#!/usr/bin/env python3
"""V-CAP2-* gates: capsule-v2 identity, leased claims, reality-bound certify, precert markers.

Spec vault/specs/mission-capsule-rollover.md (T1-T3, audit G14-G18, G24-G25). Hermetic: a throwaway
git repo and state dir; the live ~/.claude/state/rollover is fingerprinted before and after and
must not move (G24). Every refusal is paired with a control in which the fact exists and the
verdict is the permissive one, so a gate that refuses everything cannot pass.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rollover as ro  # noqa: E402

passes = fails = 0
LIVE = Path.home() / ".claude" / "state" / "rollover"


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def git(root, *args):
    subprocess.run([ro._git_exe(), "-C", str(root), *args], check=True, capture_output=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def live_fingerprint() -> dict:
    out = {}
    for sub in ("capsules", "mission-capsules", "precert"):
        d = LIVE / sub
        out[sub] = sorted((p.name, p.stat().st_mtime_ns) for p in d.iterdir()) if d.is_dir() else None
    p = LIVE / "rollover-ledger.jsonl"
    out["ledger"] = p.stat().st_size if p.is_file() else None
    return out


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a, **k)
    return rc, buf.getvalue()


def cf(key, claimant, answers, state):
    """certify_flow with its stdout captured: (exit, result, printed text)."""
    (rc, res), out = quiet(ro.certify_flow, key, claimant, answers, state)
    return rc, res, out


def make_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    (repo / "vault" / "plans").mkdir(parents=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@example.invalid")
    git(repo, "config", "user.name", "t")
    (repo / "a.txt").write_text("one\n", encoding="utf-8")
    (repo / "vault" / "plans" / "goal.md").write_text(
        "# Goal\n\n## Next\n1. Wire the `mission` adapter into supervise\n2. Write the vault entry\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


def mission_capsule(repo: Path, mid="m-test00000001", epoch=3, **kw) -> dict:
    facts = ro.repo_facts(str(repo))
    cap = {"schema": ro.SCHEMA_V2, "kind": "mission", "capsule_key": ro.mission_key(mid, epoch),
           "session_id": ro.mission_key(mid, epoch), "cwd": str(repo), "created": ro._iso(),
           "run": {"mission_id": mid, "epoch": epoch, "successor_epoch": epoch + 1, "lineage_id": mid},
           "seal_origin": "worker_handoff", "degraded": False, "note": "next: wire the adapter",
           "repo": facts, "goal": {"state": "OK", "path": str(repo / "vault" / "plans" / "goal.md")},
           "obligations": ["execute phase 2: Wire the adapter"], "obligations_source": "gsd",
           "children": {"verdict": "CLEAR", "pending": [], "unconsumed": []},
           "foreign": {"state": "OK", "repos": [], "unchecked_non_repo": 0}}
    cap.update(kw)
    return cap


def claim_in_subprocess(state: Path, key: str, claimant: str, out: Path) -> subprocess.Popen:
    code = ("import sys,json; sys.path.insert(0, r'%s'); import rollover as ro;"
            "from pathlib import Path; r = ro.claim(%r, %r, Path(r'%s'));"
            "Path(r'%s').write_text(json.dumps(r))") % (HERE, key, claimant, state, out)
    return subprocess.Popen([sys.executable, "-c", code], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def main() -> int:
    before = live_fingerprint()
    tmp = Path(tempfile.mkdtemp(prefix="cap2_t_"))
    state = tmp / "state"
    ro.STATE_DIR = state
    try:
        repo = make_repo(tmp)
        if ro.repo_facts(str(repo)).get("state") != "OK":
            print("HARNESS-FAILED: fixture repo unreadable; no gate judged")
            return 2

        print("T1 identity: mission capsules live apart from interactive discovery (G14)")
        mc = mission_capsule(repo)
        key = mc["capsule_key"]
        rc = ro.seal(mc, state)
        check("V-CAP2-OWN-DIR", rc["sealed"] and Path(rc["path"]).parent.name == "mission-capsules", rc.get("path"))
        check("V-CAP2-INTERACTIVE-BLIND", ro.newest_capsule(str(repo), state, exclude="x") is None,
              "an ordinary pane in the mission's repo is never offered the worker's capsule")
        icap = dict(mc, schema=ro.SCHEMA, kind="interactive", session_id="iiiiiiii-0001")
        icap.pop("capsule_key")
        ro.seal(icap, state)
        hit = ro.newest_capsule(str(repo), state, exclude="x")
        check("V-CAP2-INTERACTIVE-CONTROL", hit is not None and hit["session_id"] == "iiiiiiii-0001",
              "positive control: an interactive capsule here IS found")
        check("V-CAP2-KEYSPACE", ro.mission_key("m-1", 2) == "mission-m-1-e2"
              and ro.capsule_path("aaaaaaaa-1", state).parent.name == "capsules", "uuids never collide")

        print("T1 completeness: mission categories, one refusal each + control")
        check("V-CAP2-COMPLETE-CONTROL", ro.completeness(mc)["complete"], ro.completeness(mc)["missing"])
        for gate, mut, needle in [
            ("V-CAP2-RED-RUN", lambda c: c["run"].pop("mission_id"), "run.mission_id"),
            ("V-CAP2-RED-ORIGIN", lambda c: c.update(seal_origin="guess"), "seal_origin"),
            ("V-CAP2-RED-HANDOFF-NO-NOTE", lambda c: c.update(note=""), "note"),
            ("V-CAP2-RED-FALLBACK-NOT-DEGRADED", lambda c: c.update(seal_origin="supervisor_fallback"), "degraded"),
            ("V-CAP2-RED-NO-OBLIGATION", lambda c: c.update(obligations=[]), "obligations"),
            ("V-CAP2-RED-CHILD-HOLD", lambda c: c.update(children={"verdict": "HOLD", "pending": [1]}), "children"),
        ]:
            c = json.loads(json.dumps(mc))
            mut(c)
            miss = ro.completeness(c)["missing"]
            check(gate, any(needle in m for m in miss), miss)
        fb = mission_capsule(repo, seal_origin="supervisor_fallback", degraded=True, note="")
        check("V-CAP2-FALLBACK-DEGRADED-OK", ro.completeness(fb)["complete"], ro.completeness(fb)["missing"])

        print("T2 claim: one holder, lease, takeover, fencing (D5/G18)")
        c1 = ro.claim(key, "succ-A", state)
        c2 = ro.claim(key, "succ-B", state)
        check("V-CAP2-ONE-CLAIM", c1["claimed"] and c1["generation"] == 1 and not c2["claimed"]
              and c2["holder"] == "succ-A", (c1, c2))
        renew = ro.claim(key, "succ-A", state)
        check("V-CAP2-HOLDER-RENEWS", renew["claimed"] and renew["generation"] == 1, renew)
        live_host = {"pid": 4242, "proc_start": "x"}
        k2 = ro.mission_key("m-test00000002", 1)
        ro.claim(k2, "succ-A", state, host=live_host)
        alive = ro.claim(k2, "succ-B", state, alive=lambda pid: None)
        check("V-CAP2-UNKNOWN-LIVENESS-KEEPS", not alive["claimed"], "an unanswered liveness question is not death")
        dead = ro.claim(k2, "succ-B", state, alive=lambda pid: False)
        check("V-CAP2-DEAD-HOLDER-TAKEN-OVER", dead["claimed"] and dead["generation"] == 2
              and dead["took_over_from"] == "succ-A", dead)
        k3 = ro.mission_key("m-test00000003", 1)
        ro.claim(k3, "succ-A", state, now=time.time() - ro.CLAIM_LEASE_S - 5)
        exp = ro.claim(k3, "succ-B", state)
        check("V-CAP2-LEASE-EXPIRY-TAKEN-OVER", exp["claimed"] and "lease expired" in exp.get("takeover_reason", ""), exp)
        k4 = ro.mission_key("m-test00000004", 1)
        torn = ro.capsule_path(k4, state).with_suffix(".claim")
        torn.parent.mkdir(parents=True, exist_ok=True)
        torn.write_text("", encoding="utf-8")
        fresh_torn = ro.claim(k4, "succ-B", state)
        os.utime(torn, (time.time() - ro.CLAIM_TORN_S - 5,) * 2)
        old_torn = ro.claim(k4, "succ-B", state)
        check("V-CAP2-TORN-CLAIM", not fresh_torn["claimed"] and old_torn["claimed"],
              "a torn create is recoverable only after it cannot be a writer mid-flight")

        print("T2 race: 6 processes claim one capsule at once -> exactly one holder")
        k5 = ro.mission_key("m-race", 1)
        outs = [tmp / f"race{i}.json" for i in range(6)]
        procs = [claim_in_subprocess(state, k5, f"racer-{i}", o) for i, o in enumerate(outs)]
        for p in procs:
            p.wait(timeout=60)
        res = [json.loads(o.read_text()) for o in outs if o.is_file()]
        winners = [r for r in res if r.get("claimed")]
        check("V-CAP2-RACE-ONE-WINNER", len(res) == 6 and len(winners) == 1
              and all(r["holder"] == winners[0]["holder"] for r in res), [r.get("holder") for r in res])

        print("T3 certify: snapshot, stale refresh, no answer leak, strict next (D2-D4, G15-G17)")
        k = key
        ro.claim(k, "succ-A", state)
        code, out = quiet(ro.resume_flow, mc, "succ-A", str(repo), state, obligations=mc["obligations"])
        facts = ro.repo_facts(str(repo))
        check("V-CAP2-BOOTSTRAP-NO-HEAD", code == 0 and facts["head"][:7] not in out
              and mc["repo"]["head"][:7] not in out and facts["branch"] not in out,
              "neither the bootstrap nor the refresh lines print the answers the exam asks for")
        good = {"goal": "goal.md", "branch": facts["branch"], "head": facts["head"][:7],
                "next": "execute phase 2: Wire the adapter"}
        code_w, _res_w, out_w = cf(k, "succ-A", {**good, "head": "1111111"}, state)
        check("V-CAP2-FAILED-NAMES-KEYS-ONLY", code_w == 6 and facts["head"][:7] not in out_w and "head" in out_w,
              out_w.strip().splitlines()[-1] if out_w.strip() else out_w)
        check("V-CAP2-NEXT-NOT-A-LETTER", not ro._matches("next", ro._norm("execute phase 2: wire the adapter"), "a"), "D4")
        check("V-CAP2-NEXT-BACKTICKS", ro._matches("next", ro._norm("Wire the `mission` adapter into supervise"),
                                                  ro._norm("Wire the mission adapter into supervise")), "G16")
        check("V-CAP2-NEXT-REAL-FRAGMENT", ro._matches("next", ro._norm("execute phase 2: Wire the adapter"),
                                                       ro._norm("execute phase 2")), "a real fragment passes")
        # Tree moves AFTER the refresh: right answers for the snapshot must not certify (exit 8).
        (repo / "a.txt").write_text("two\n", encoding="utf-8")
        git(repo, "commit", "-q", "-am", "sibling commit")
        led = state / "rollover-ledger.jsonl"
        certified_rows = lambda: led.read_text(encoding="utf-8").count('"resume_certified"') if led.is_file() else 0
        n_cert = certified_rows()
        c8, r8, _o8 = cf(k, "succ-A", good, state)
        check("V-CAP2-STALE-REFRESH-EXIT-8", c8 == 8 and not ro.capsule_path(k, state).with_suffix(".certified").exists(), r8)
        # Review MEDIUM (scenario A): the successor read the NEW head, as kresume.md tells it to.
        new_head = ro.repo_facts(str(repo))["head"][:7]
        c8b, r8b, _o = cf(k, "succ-A", {**good, "head": new_head}, state)
        check("V-CAP2-NEW-HEAD-GETS-8-NOT-6", c8b == 8, f"exit {c8b}: refresh again, never 're-read and retry' for ever")
        check("V-CAP2-NO-CERTIFIED-ROW-WHEN-STALE", certified_rows() == n_cert, "scenario B: no resume_certified row")
        quiet(ro.resume_flow, mc, "succ-A", str(repo), state, obligations=mc["obligations"])
        facts = ro.repo_facts(str(repo))
        good = {**good, "head": facts["head"][:7]}

        print("T3 precert marker: one authority flips it (G25)")
        mid = mc["run"]["mission_id"]
        ro.precert_write(mid, {"worker": f"{mid}-e4", "capsule_key": "mission-other-e9"}, state)
        c_mk, r_mk, _o = cf(k, "succ-A", good, state)
        check("V-CAP2-MARKER-WRONG-CAPSULE-NOT-LIFTED", c_mk == 5 and not (ro.precert_read(mid, state) or {}).get("certified_at"),
              r_mk.get("marker"))
        ro.precert_write(mid, {"capsule_key": k}, state)
        c_heal, _r, _o = cf(k, "succ-A", good, state)
        check("V-CAP2-CRASH-AFTER-RETIRE-HEALED", c_heal == 0 and (ro.precert_read(mid, state) or {}).get("certified_by") == "succ-A",
              "certify again lifts the marker the crash left down")
        fenced = ro.claim(k, "succ-Z", state, alive=lambda pid: False)
        check("V-CAP2-CERTIFIED-NOT-TAKEN-OVER", not fenced["claimed"] and fenced.get("why") == "already certified", fenced)

        print("T3 degraded capsule: RECOVERY adds the dirty question")
        kd = ro.mission_key("m-degraded", 2)
        dc = mission_capsule(repo, mid="m-degraded", epoch=2, seal_origin="supervisor_fallback", degraded=True, note="",
                             capsule_key=kd, session_id=kd)
        ro.seal(dc, state)
        (repo / "a.txt").write_text("three\n", encoding="utf-8")       # one uncommitted tracked path
        quiet(ro.resume_flow, dc, "succ-D", str(repo), state, obligations=dc["obligations"])
        f2 = ro.repo_facts(str(repo))
        base = {"goal": "goal.md", "branch": f2["branch"], "head": f2["head"][:7], "next": "execute phase 2: Wire the adapter"}
        cd0, rd0, _o = cf(kd, "succ-D", base, state)
        check("V-CAP2-DEGRADED-NEEDS-DIRTY", cd0 == 6 and [w["key"] for w in rd0["wrong"]] == ["dirty"], rd0.get("wrong"))
        cd1, rd1, _o = cf(kd, "succ-D", {**base, "dirty": "1"}, state)
        check("V-CAP2-DEGRADED-CONTROL", cd1 == 0, rd1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check("V-CAP2-LIVE-STATE-UNTOUCHED", live_fingerprint() == before, "G24 sentinel over capsules/, mission-capsules/, precert/, ledger")
    print(f"CAP2_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
