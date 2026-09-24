#!/usr/bin/env python3
"""V-gates for the brief compiler and the two Claude providers (C9).

The headless provider is driven with a stand-in binary: this suite must not
start real Claude sessions. The real one is exercised by a goal epoch.

    python tools/test_gsd_x_goal_claude_providers.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import brief as br                  # noqa: E402
from modules.gsd_x.goal import contract as gc               # noqa: E402
from modules.gsd_x.goal import convergence as cv            # noqa: E402
from modules.gsd_x.goal import epoch as ep                  # noqa: E402
from modules.gsd_x.goal import log as gl                    # noqa: E402
from modules.gsd_x.goal.providers import claude as cl       # noqa: E402

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"   # PATH first: GEX44 (Linux) runs these
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
REPO_ID = "d" * 40

FAKE = """
import sys, pathlib, subprocess
import shutil
GIT = shutil.which("git") or r"C:\\Program Files\\Git\\cmd\\git.exe"
brief = sys.argv[-1]
root = pathlib.Path.cwd()
(root / "claude_did_this.txt").write_text(brief[:80], encoding="utf-8")
subprocess.run([GIT, "add", "."], cwd=root)
subprocess.run([GIT, "commit", "-qm", "headless work"], cwd=root)
print("claude: done")
"""


def make_repo(name="gsdx_cl_repo_") -> Path:
    d = Path(tempfile.mkdtemp(prefix=name))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run([GIT, "-C", str(d), "add", "."], check=True, env=ENV)
    subprocess.run([GIT, "-C", str(d), "commit", "-qm", "seed"], check=True, env=ENV)
    return d


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    def check(g, cond, ev, why):
        (ok if cond else bad)(g, ev if cond else why)

    base = Path(tempfile.mkdtemp(prefix="gsdx_cl_goals_"))
    sandbox = Path(tempfile.mkdtemp(prefix="gsdx_cl_sandbox_"))
    os.environ[cl.LEDGER_ENV] = str(sandbox / "claude_epochs.jsonl")
    os.environ[cl.DISABLE_FLAG_ENV] = str(sandbox / "claude.disabled")

    # --- a goal with real state to compile a brief from -------------------------
    lg = gl.GoalLog(REPO_ID, "g-brief", base=base)
    s = gc.declare(lg, "Wake the dormant runner and prove a bot reaches the lobby.",
                   ["a job runs through the proxy"], ["read-only: no production writes"],
                   {"paths": ["tools/smoke-test"]})
    for plane in cv.PLANES:
        s = gc.project(lg)
        cv.set_plane(lg, s, plane, plane in cv.ALWAYS, "" if plane in cv.ALWAYS
                     else "no runtime claim yet", "t")
    cv.accept_obligation(lg, gc.project(lg), "ob-outcome", cv.OUTCOME,
                         "a registered job exists", "python scripts/verify_change.py",
                         (("scripts/verify_change.py", "0" * 64),), "t")
    cv.record_failure(lg, gc.project(lg), "f-1", "the previous codex epoch was lost", "t")
    st = gc.project(lg)
    closure = cv.goal_closure(st, "git:abc")
    text = br.compile_brief(st, closure.blocking, "C:/work/wt", "Register the job.")

    check("V-BRIEF-VERBATIM-INTENT", "Wake the dormant runner" in text,
          "the brief carries the Founder's own words", "the intent is missing")
    check("V-BRIEF-OPEN-GAPS", "ob-outcome" in text and "verify_change.py" in text,
          "it names the open obligation and what would prove it", "the open gap is missing")
    check("V-BRIEF-FAILURES", "previous codex epoch was lost" in text,
          "it carries undispositioned failures", "failures are missing")
    check("V-BRIEF-BOUNDARIES",
          "may NOT write to any production system" in text
          and "may NOT mark anything converged" in text,
          "it states the boundaries an executor may not cross", "boundaries missing")
    check("V-BRIEF-DETERMINISTIC",
          br.compile_brief(st, closure.blocking, "C:/work/wt", "Register the job.") == text,
          "the same state compiles the same brief", "the brief is not deterministic")
    check("V-BRIEF-NO-TRANSCRIPT",
          "conversation" not in text.lower() and "transcript" not in text.lower(),
          "nothing in the brief comes from a chat transcript", "the brief mentions a transcript")

    # --- headless ------------------------------------------------------------------
    fake = sandbox / "fake_claude.py"
    fake.write_text(FAKE, encoding="utf-8")
    runs = Path(tempfile.mkdtemp(prefix="gsdx_cl_runs_"))
    hp = cl.HeadlessClaudeProvider(runs, wall_bound_s=60, max_per_day=2,
                                   argv_prefix=[sys.executable, str(fake)])
    ep.check_provider(hp)
    ok("V-CLH-PROVIDER-CONTRACT", "the headless provider satisfies the contract")

    repo = make_repo()

    def spec(token, eid, root=None, brief_text="do the thing"):
        return {"epoch_id": eid, "revision": "rev1", "root": str(root or repo),
                "brief": brief_text, "scope_paths": ["."],
                "identity": {"run_token": token, "epoch_id": eid}}

    plain = Path(tempfile.mkdtemp(prefix="gsdx_cl_plain_"))     # not a git worktree
    try:
        hp.dispatch(spec("t-plain", "ep-plain", root=plain))
        bad("V-CLH-WORKTREE-ONLY", "a headless epoch ran outside an isolated worktree")
    except ep.EpochError as exc:
        check("V-CLH-WORKTREE-ONLY", "isolated worktree" in str(exc),
              "a headless epoch refuses to run outside a worktree the goal owns", str(exc))

    h = hp.dispatch(spec("t-ok", "ep-ok", brief_text="write the file"))
    deadline = time.time() + 60
    while time.time() < deadline and hp.observe(h).state != ep.OBS_ENDED:
        time.sleep(0.05)
    obs = hp.observe(h)
    r = hp.harvest(h, spec("t-ok", "ep-ok"))
    check("V-CLH-RUNS", obs.outcome == ep.COMPLETED and r.commits
          and (repo / "claude_did_this.txt").is_file(),
          f"a headless session runs in its worktree and its commit is in the receipt",
          f"obs={obs} commits={r.commits}")
    check("V-CLH-NO-VERDICT", r.verdicts == [],
          "a headless session yields NO verdict: a gate judges the work", f"{r.verdicts}")

    hp.dispatch(spec("t-2", "ep-2"))
    try:
        hp.dispatch(spec("t-3", "ep-3"))
        bad("V-CLH-CAP", "dispatched past the Owner's 4/day-class cap")
    except ep.EpochError as exc:
        check("V-CLH-CAP", "budget is spent" in str(exc),
              "the Owner's daily cap stops a headless dispatch", str(exc))
    Path(os.environ[cl.DISABLE_FLAG_ENV]).write_text("off", encoding="utf-8")
    hp2 = cl.HeadlessClaudeProvider(runs, max_per_day=99,
                                    argv_prefix=[sys.executable, str(fake)])
    try:
        hp2.dispatch(spec("t-4", "ep-4"))
        bad("V-CLH-KILL-FLAG", "dispatched while headless epochs were disabled")
    except ep.EpochError as exc:
        check("V-CLH-KILL-FLAG", "disabled" in str(exc),
              "the kill-switch file stops a headless dispatch", str(exc))
    Path(os.environ[cl.DISABLE_FLAG_ENV]).unlink()

    # --- interactive -------------------------------------------------------------------
    # 5 s, not 1 s: between dispatch and the first observe this test writes and re-reads
    # the brief, and on a loaded host that took longer than 1 s -- the epoch had
    # legitimately expired and V-CLI-WAITS failed 1 run in 3 (measured 2026-09-23).
    ip = cl.InteractiveClaudeProvider(runs, wall_bound_s=5.0)
    ep.check_provider(ip)
    repo2 = make_repo("gsdx_cl_repo2_")
    s_i = {**spec("t-int", "ep-int", root=repo2, brief_text="an operator does this")}
    hi = ip.dispatch(s_i)
    check("V-CLI-BRIEF-WRITTEN", Path(hi["brief"]).is_file()
          and "an operator does this" in Path(hi["brief"]).read_text(encoding="utf-8"),
          "the brief is written where the operator will find it", "no brief on disk")
    check("V-CLI-WAITS", ip.observe(hi).state == ep.OBS_RUNNING,
          "with no receipt yet, the epoch is running", "it did not wait")
    time.sleep(5.3)
    obs_i = ip.observe(hi)
    check("V-CLI-EXPIRES", obs_i.state == ep.OBS_ENDED and obs_i.outcome == ep.EXPIRED,
          "past its TTL the epoch ends EXPIRED, not LOST -- nobody died, the window closed",
          f"{obs_i}")
    r_i = ip.harvest(hi, s_i)
    check("V-CLI-EXPIRED-FAILURE",
          any(f["signature"] == "interactive-expired" for f in r_i.failures),
          "an expired interactive epoch harvests a named failure", f"{r_i.failures}")

    hi2 = ip.dispatch({**s_i, "identity": {"run_token": "t-int2", "epoch_id": "ep-int2"}})
    Path(hi2["receipt"]).write_text(json.dumps({"narrative": "I registered the job"}),
                                    encoding="utf-8")
    check("V-CLI-RECEIPT-ENDS", ip.observe(hi2).outcome == ep.COMPLETED,
          "a receipt file ends the epoch", f"{ip.observe(hi2)}")
    r_i2 = ip.harvest(hi2, {**s_i, "epoch_id": "ep-int2"})
    check("V-CLI-NARRATIVE-NOT-PROOF", r_i2.verdicts == [] and "registered" in r_i2.narrative,
          "the operator's account is stored as narrative and proves nothing",
          f"verdicts={r_i2.verdicts}")
    found = ip.probe({"run_token": "t-int2"})
    check("V-CLI-PROBE-KEEPS-ROOT", found is not None and found["root"] == str(repo2),
          "a recovered interactive handle knows its real worktree", f"probe={found}")
    check("V-CLI-PROBE-NONE", ip.probe({"run_token": "never"}) is None,
          "a token never handed over probes to None", "probe invented an epoch")

    total = len(passes) + len(fails)
    print(f"\nGSDX_CLAUDE_PROVIDERS_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
