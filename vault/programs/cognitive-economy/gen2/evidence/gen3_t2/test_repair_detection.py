"""Regression: repair detection reads commit subjects from git per commit hash, so `git commit -F file` commits count.
usage: python test_repair_detection.py   -> REPAIR_DETECT_TEST=PASS|FAIL"""
import datetime as dt, json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_extract as X
REPAIR_SUBJ = re.compile(r"\b(fix|fixes|fixed|revert|hotfix|repair|amend|correct)\b", re.I)   # same regex as t2_instruments.py
fails = []
def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond: fails.append(name)
def git(repo, *a): return subprocess.run([X.GIT, "-C", repo, *a], capture_output=True, text=True, encoding="utf-8", check=True).stdout
with tempfile.TemporaryDirectory() as tmp:
    git(tmp, "init", "-q"); git(tmp, "config", "user.email", "t@t"); git(tmp, "config", "user.name", "t")
    open(os.path.join(tmp, "a.txt"), "w").write("1"); git(tmp, "add", "a.txt")
    msg = os.path.join(tmp, "msg.txt"); open(msg, "w").write("fix: planted -F commit\n\nbody\n")
    out = git(tmp, "commit", "-F", msg)
    h, ps = X.parse_commit_output(out)
    check("commit output parsed to hash", bool(h))
    ts = "2026-10-05T10:00:00Z"
    lines = [{"type": "assistant", "timestamp": ts, "requestId": "r1", "message": {"id": "m1", "usage": {"input_tokens": 1, "output_tokens": 1},
              "content": [{"type": "tool_use", "id": "t1", "name": "PowerShell", "input": {"command": "git commit -F msg.txt"}}]}},
             {"type": "user", "timestamp": ts, "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": out}]}}]
    p = os.path.join(tmp, "s.jsonl"); open(p, "w", encoding="utf-8").write("\n".join(json.dumps(l) for l in lines) + "\n")
    TT, _ = X.load([p], dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc), set())
    rec = TT[0]["calls"][0]["tools"][0]
    check("before resolve: -F commit carries only the command-text stub, not a repair subject", (rec["subj"] or "").startswith("F:") and not REPAIR_SUBJ.search(rec["subj"]))
    check("hash captured from result", rec.get("hash") == h)
    cnt = X.resolve_commit_subjects(TT, repos=[tmp])
    check("after resolve: subject read from git log", rec["subj"] == "fix: planted -F commit" and cnt["git_log"] == 1)
    check("planted -F commit now matches REPAIR_SUBJ", bool(REPAIR_SUBJ.search(rec["subj"])))
    open(msg, "w").write("feat: add b\n"); open(os.path.join(tmp, "b.txt"), "w").write("2"); git(tmp, "add", "b.txt"); out2 = git(tmp, "commit", "-F", msg)
    h2, _ = X.parse_commit_output(out2)
    check("negative control: feat subject is not a repair", not REPAIR_SUBJ.search(X.git_subject(h2, [tmp])))
    check("unknown hash resolves to None (caller falls back to printed subject)", X.git_subject("deadbeef", [tmp]) is None)
print(f"REPAIR_DETECT_TEST={'PASS' if not fails else 'FAIL'}")
sys.exit(1 if fails else 0)
