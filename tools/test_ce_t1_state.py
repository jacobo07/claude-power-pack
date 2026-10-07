#!/usr/bin/env python3
"""V-CE-T1-STATE-* gates: obligation C2 (COMPLETION-PLAN Master Done-Gate) -- the continuation
survives the loss of the transcript and of the handoff prose.

Drives the REAL seal / resume_flow / certify_flow / gate against a throwaway git repo and state
dir; the live ~/.claude/state/rollover is fingerprinted before and after and must not move. Model-
free: answers are read from the tree and the capsule, never from a model. Two controls must go red:
a deleted goal file (CE-T1a forget_safe -> exit 9, capsule not retired) and capsule bytes edited
after the seal (gate REFUSED).
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
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


def make_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    (repo / "vault" / "plans").mkdir(parents=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@example.invalid")
    git(repo, "config", "user.name", "t")
    (repo / "a.txt").write_text("one\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


def scenario(tmp: Path, repo: Path, name: str) -> dict:
    """One sealed interactive capsule whose transcript, handoff prose and goal file are real files."""
    sid = f"ce71{abs(hash(name)) % 10**8:08d}-0000-4000-8000-{name[:12].ljust(12, '0')}"
    side = tmp / name
    side.mkdir()
    goal = repo / "vault" / "plans" / f"goal-{name}.md"
    goal.write_text("# Goal\n\n## Next\n1. Wire the state adapter\n", encoding="utf-8")
    transcript = side / f"{sid}.jsonl"
    transcript.write_text(json.dumps({"type": "user", "sessionId": sid}) + "\n", encoding="utf-8")
    handoff = side / f"{sid}.md"
    handoff.write_text(f"# Handoff\n\n**Session ID**: `{sid}`\n\nNext: wire the state adapter.\n", encoding="utf-8")
    cap = {"schema": ro.SCHEMA, "kind": "interactive", "session_id": sid, "cwd": str(repo),
           "created": ro._iso(), "transcript": str(transcript), "repo": ro.repo_facts(str(repo)),
           "goal": {"state": "OK", "path": str(goal), "basis": "explicit"},
           "obligations": ["Wire the state adapter"], "obligations_source": "explicit",
           "handoff": {"state": "OK", "path": str(handoff), "age_s": 0, "session": sid},
           "children": {"verdict": "CLEAR", "pending": [], "unconsumed": []},
           "foreign": {"state": "OK", "repos": [], "unchecked_non_repo": 0}}
    rc = ro.seal(cap, STATE)
    # The receipt row the CLI seal writes (rollover.py `seal` subcommand); gate() reads only it.
    stf = ro.safe_to_forget(rc, ro.completeness(cap))
    ro.ledger("capsule_sealed", STATE, session_id=sid, cwd=str(repo), capsule=rc,
              safe_to_forget=stf["verdict"], refusals=stf["reasons"])
    return {"cap": cap, "sid": sid, "goal": goal, "transcript": transcript, "handoff": handoff, "seal": rc}


def run_resume(sc: dict, repo: Path, claimant: str, delete=()) -> tuple:
    """resume_flow, then delete the named files, then answer from the tree and certify_flow."""
    cap, sid = sc["cap"], sc["sid"]
    rcode, _ = quiet(ro.resume_flow, cap, claimant, str(repo), STATE, obligations=cap["obligations"])
    answers = {i["key"]: i["a"] for i in ro.exam(cap)}
    for k in delete:
        sc[k].unlink()
    (ccode, res), out = quiet(ro.certify_flow, sid, claimant, answers, STATE)
    p = ro.capsule_path(sid, STATE)
    retired = p.with_suffix(".certified").exists() or not p.exists()
    return rcode, ccode, res, out, retired


def main() -> int:
    global STATE
    before = live_fingerprint()
    tmp = Path(tempfile.mkdtemp(prefix="ce_t1_state_"))
    STATE = tmp / "state"
    ro.STATE_DIR = STATE
    try:
        repo = make_repo(tmp)
        if ro.repo_facts(str(repo)).get("state") != "OK":
            print("HARNESS-FAILED: fixture repo unreadable; no gate judged")
            return 2

        print("C2 a-c: transcript / handoff prose / both deleted -> still RESUME_CERTIFIED")
        for gate, name, delete in [("V-CE-T1-STATE-NO-TRANSCRIPT", "transcript", ("transcript",)),
                                   ("V-CE-T1-STATE-NO-HANDOFF", "handoff", ("handoff",)),
                                   ("V-CE-T1-STATE-NO-BOTH", "both", ("transcript", "handoff"))]:
            sc = scenario(tmp, repo, name)
            rcode, ccode, res, out, retired = run_resume(sc, repo, f"succ-{name}", delete)
            gone = all(not sc[k].exists() for k in delete)
            verdict = (res or {}).get("verdict") if isinstance(res, dict) else None
            check(gate, sc["seal"]["sealed"] and gone and rcode == 0 and ccode == 0
                  and verdict == "RESUME_CERTIFIED" and "RESUME_CERTIFIED" in out,
                  f"deleted={list(delete)} resume={rcode} certify={ccode} verdict={verdict}")
            check(gate + "-RETIRED", retired, "a certified capsule is retired (pole for the goal control)")

        print("C2 d (control, must go red): goal file deleted -> certify refuses (exit 9), not retired")
        sc = scenario(tmp, repo, "nogoal")
        rcode, ccode, res, out, retired = run_resume(sc, repo, "succ-nogoal", ("goal",))
        check("V-CE-T1-STATE-RED-NO-GOAL", rcode == 0 and ccode == 9 and "RESUME_CERTIFIED" not in out,
              f"resume={rcode} certify={ccode}")
        check("V-CE-T1-STATE-RED-NO-GOAL-KEPT", not retired and ro.capsule_path(sc["sid"], STATE).exists(),
              "the refused capsule stays sealed and unretired")

        print("C2 e (control, must go red): capsule bytes edited after the seal -> gate REFUSED")
        sc = scenario(tmp, repo, "tamper")
        pre = ro.gate(sc["sid"], STATE)
        p = ro.capsule_path(sc["sid"], STATE)
        data = json.loads(p.read_text(encoding="utf-8"))
        data["obligations"] = ["Do something else entirely"]
        p.write_text(json.dumps(data), encoding="utf-8")
        post = ro.gate(sc["sid"], STATE)
        check("V-CE-T1-STATE-RED-TAMPER", post["verdict"] == "REFUSED"
              and len(post.get("reasons") or []) > len(pre.get("reasons") or []),
              f"pre={pre['verdict']}/{len(pre.get('reasons') or [])} post={post['verdict']} {post.get('reasons')}")
        check("V-CE-T1-STATE-TAMPER-CONTROL", pre["verdict"] == "SAFE_TO_FORGET",
              f"untouched capsule: {pre['verdict']} {pre.get('reasons')}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check("V-CE-T1-STATE-LIVE-UNTOUCHED", live_fingerprint() == before, "live rollover state did not move")
    total = passes + fails
    print(f"CE_T1_STATE_PASS={passes}/{total}")
    return 0 if fails == 0 else 1


STATE: Path = Path()

if __name__ == "__main__":
    sys.exit(main())
