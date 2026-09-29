"""V-RSC-* gates: a capsule is found by the SESSION's directory, not the shell's.

Measured 2026-09-29, crossing 357823a8 -> a15bd244: the session ran in
`Desktop\\Cursor Projects\\InfinityOps`, but /kclear was executed after a `cd` into
`Apps\\io-chatgpt-plugin`, so the capsule recorded cwd = repo.root = io-chatgpt-plugin.
The successor opened at InfinityOps: the hub found no capsule (no card, no
`/kresume focus on ...`), and the capsule was claimed by hand four minutes later.

cef6d56 fixed the subdirectory shape in rollover.py (cwd OR repo.root) and left the
hub on an exact compare. Neither rule can see a capsule sealed from ANOTHER repo.
The session's own directory lives in ~/.claude/sessions/<pid>.json (the record the
daemon already routes by); the capsule now carries it as `session_cwd`, and both
matchers accept it. `cwd` and `repo` keep describing the work tree, unchanged.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
HUB = Path(os.environ.get("RSC_TEST_HUB") or HERE.parent / "hooks" / "session_start_hub.js")

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


SESSION_DIR = r"C:\p\InfinityOps"
WORK_REPO = r"C:\p\io-chatgpt-plugin"


def rollover_gates():
    reg = Path(tempfile.mkdtemp(prefix="rsc_sessions_"))
    os.environ["CPP_CLAUDE_SESSIONS_DIR"] = str(reg)
    import rollover
    (reg / "26416.json").write_text(json.dumps(
        {"pid": 26416, "sessionId": "pred-aaaa", "cwd": SESSION_DIR}), encoding="utf-8")
    (reg / "999.json").write_text("{not json", encoding="utf-8")

    got = rollover.session_cwd("pred-aaaa")
    check("V-RSC-SESSION-CWD-FROM-REGISTRY", got == SESSION_DIR, f"got={got!r}")
    got = rollover.session_cwd("someone-else")
    check("V-RSC-SESSION-CWD-OTHER-SID-NONE", got is None, f"got={got!r}")
    check("V-RSC-SESSION-CWD-EMPTY-SID-NONE", rollover.session_cwd("") is None, "")

    # The capsule records it, and the work-tree fields are left as they were.
    work = Path(tempfile.mkdtemp(prefix="rsc_work_"))
    cap = rollover.compile_capsule("pred-aaaa", str(work), None, goal=None, next_items=["x"])
    check("V-RSC-CAPSULE-RECORDS-SESSION-CWD",
          cap.get("session_cwd") == SESSION_DIR and cap.get("cwd") == str(work),
          f"session_cwd={cap.get('session_cwd')!r} cwd={cap.get('cwd')!r}")

    # Matching: sealed from another repo, found at the session's directory.
    far = {"cwd": WORK_REPO, "repo": {"root": WORK_REPO}, "session_cwd": SESSION_DIR}
    check("V-RSC-MATCH-BY-SESSION-CWD", rollover.capsule_is_here(far, SESSION_DIR + "\\"), "")
    check("V-RSC-STILL-MATCH-WORK-REPO", rollover.capsule_is_here(far, WORK_REPO), "")
    check("V-RSC-NO-MATCH-ELSEWHERE", not rollover.capsule_is_here(far, r"C:\p\Unrelated"), "")
    # Control: without session_cwd (every capsule sealed before this change) the old rule holds.
    old = {"cwd": WORK_REPO, "repo": {"root": WORK_REPO}}
    check("V-RSC-OLD-CAPSULE-OLD-RULE",
          not rollover.capsule_is_here(old, SESSION_DIR) and rollover.capsule_is_here(old, WORK_REPO), "")


def run_hub(home: Path, cwd: str):
    js = ("const h=require(process.argv[1]);"
          "const line=h.hookRolloverResume(process.argv[2],'clear');"
          "const focus=h.rolloverFocus(process.argv[2],'clear');"
          "process.stdout.write(JSON.stringify({line:!!line,focus:focus}));")
    env = dict(os.environ, USERPROFILE=str(home), HOME=str(home))
    r = subprocess.run(["node", "-e", js, str(HUB), cwd], env=env, capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout or "{}"), r
    except ValueError:
        return {}, r


def seed(home: Path, rec: dict):
    d = home / ".claude" / "state" / "rollover" / "capsules"
    d.mkdir(parents=True, exist_ok=True)
    (d / "pred-aaaa.json").write_text(json.dumps(dict(rec, session_id="pred-aaaa")), encoding="utf-8")


def hub_gates():
    far = {"cwd": WORK_REPO, "repo": {"root": WORK_REPO}, "session_cwd": SESSION_DIR,
           "obligations": ["Ship the plugin manifest"]}

    home = Path(tempfile.mkdtemp(prefix="rsc_hub_"))
    seed(home, far)
    out, r = run_hub(home, SESSION_DIR)
    if not out:
        print(f"HARNESS-FAILED: hub did not answer rc={r.returncode} err={r.stderr[-300:]!r}")
        sys.exit(2)
    check("V-RSC-HUB-FINDS-BY-SESSION-CWD",
          out.get("line") and out.get("focus") == "Ship the plugin manifest", f"out={out}")

    # cef6d56's shape, which the hub never got: sealed from a subdirectory, successor at root.
    home = Path(tempfile.mkdtemp(prefix="rsc_hub_"))
    seed(home, {"cwd": SESSION_DIR + r"\scripts", "repo": {"root": SESSION_DIR}, "obligations": ["y"]})
    out, _ = run_hub(home, SESSION_DIR)
    check("V-RSC-HUB-FINDS-BY-REPO-ROOT", out.get("line") and out.get("focus") == "y", f"out={out}")

    # Case and trailing separator do not hide it (Windows paths).
    home = Path(tempfile.mkdtemp(prefix="rsc_hub_"))
    seed(home, far)
    out, _ = run_hub(home, SESSION_DIR.lower() + "\\")
    check("V-RSC-HUB-PATH-NORMALISED", out.get("line"), f"out={out}")

    # Negative pole: another directory entirely stays invisible.
    home = Path(tempfile.mkdtemp(prefix="rsc_hub_"))
    seed(home, far)
    out, _ = run_hub(home, r"C:\p\Unrelated")
    check("V-RSC-HUB-NOT-ELSEWHERE", not out.get("line") and out.get("focus") == "", f"out={out}")

    # A parent of the session dir is not the session dir (no ancestor matching).
    home = Path(tempfile.mkdtemp(prefix="rsc_hub_"))
    seed(home, far)
    out, _ = run_hub(home, r"C:\p")
    check("V-RSC-HUB-NOT-ANCESTOR", not out.get("line"), f"out={out}")


def main() -> int:
    rollover_gates()
    hub_gates()
    total = passes + fails
    print(f"RSC_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
