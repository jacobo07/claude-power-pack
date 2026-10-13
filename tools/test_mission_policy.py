"""V-MPOL-*: mission policy -- precedence, config-as-control, capability preflight, Owner Escalation Gate,
blocked-state typing, cleanup proof. Every refusal is paired with a control that is admitted.

Run: python tools/test_mission_policy.py   (exit 0 = all pass)
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mission_policy as mp  # noqa: E402

passes = fails = 0


def check(gate: str, cond: bool, evidence: str) -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {evidence}")
    else:
        fails += 1
        print(f"FAIL {gate}: {evidence}")


# The real host record of the incident (trimmed to the fields the classifier reads), 2026-10-12.
INCIDENT_JOB = {
    "state": "blocked", "tempo": "blocked",
    "detail": "cd` into the worktree and restart the session from there?",
    "needs": "cd` into the worktree and restart the session from there?",
    "sessionId": "1659fc31-aed0-4ccf-9837-727e5cd44b3a",
    "suggestedReply": "Work through the worktree by absolute path",
}


def main() -> int:
    # Arrange: a repo whose policy forbids worktrees, and one that says nothing.
    with tempfile.TemporaryDirectory() as td:
        no_wt = Path(td) / "no_wt"
        (no_wt / ".planning").mkdir(parents=True)
        (no_wt / ".planning" / "config.json").write_text(
            json.dumps({"runtime": "claude", "workflow": {"use_worktrees": False}}), encoding="utf-8")
        silent = Path(td) / "silent"
        silent.mkdir()
        broken = Path(td) / "broken"
        (broken / ".planning").mkdir(parents=True)
        (broken / ".planning" / "config.json").write_text("{not json", encoding="utf-8")

        rp = mp.repo_policy(str(no_wt), root=no_wt)
        check("V-MPOL-CONFIG-READ", rp["values"] == {"use_worktrees": False} and rp["fingerprint"],
              f"values={rp['values']} fp={rp['fingerprint']}")
        check("V-MPOL-CONFIG-ABSENT", mp.repo_policy(str(silent), root=silent)["values"] == {}, "no file -> no values")
        rb = mp.repo_policy(str(broken), root=broken)
        check("V-MPOL-CONFIG-BROKEN", rb["values"] == {} and "error" in rb, f"error={rb.get('error')}")

    # Precedence: Owner beats repo; repo beats runtime default; unknown layer refused.
    r = mp.resolve("use_worktrees", {"owner": {"values": {"use_worktrees": True}, "source": "owner"},
                                     "repo": {"values": {"use_worktrees": False}, "source": "cfg"}})
    check("V-MPOL-PREC-OWNER", r["layer"] == "owner" and r["value"] is True, str(r))
    r = mp.resolve("use_worktrees", {"repo": {"values": {"use_worktrees": False}, "source": "cfg"},
                                     "runtime_default": {"values": {"use_worktrees": True}}})
    check("V-MPOL-PREC-REPO", r["layer"] == "repo" and r["value"] is False, str(r))
    try:
        mp.resolve("x", {"reop": {"values": {"x": 1}}})
        check("V-MPOL-PREC-UNKNOWN-LAYER", False, "typo layer accepted")
    except ValueError as exc:
        check("V-MPOL-PREC-UNKNOWN-LAYER", True, str(exc))

    # Capability preflight: the measured machine (git only at its absolute path).
    absent = lambda _n: None  # noqa: E731
    only_abs = lambda p: p == mp.GIT_CANDIDATES[0]  # noqa: E731
    h = mp.probe_capabilities(["git", "EnterWorktree"], which=absent, exists=only_abs)
    check("V-MPOL-CAP-PATH-MISMATCH", h["git"]["health"] == "PATH_MISMATCH" and h["EnterWorktree"]["health"] == "UNHEALTHY",
          str(h))
    h2 = mp.probe_capabilities(["git", "EnterWorktree"], which=lambda n: "/usr/bin/git", exists=lambda p: False)
    check("V-MPOL-CAP-HEALTHY-CONTROL", h2["EnterWorktree"]["health"] == "HEALTHY", str(h2))
    h3 = mp.probe_capabilities(["git"], which=absent, exists=lambda p: False)
    check("V-MPOL-CAP-NOT-FOUND", h3["git"]["health"] == "EXECUTABLE_NOT_FOUND", str(h3))
    check("V-MPOL-CAP-PROPORTIONAL", set(mp.probe_capabilities([], which=absent)) == set(), "nothing needed -> nothing probed")

    # Environment failure classification (the incident's own error text).
    msg = "`git -C ... worktree list` failed: Command 'git' not found or is in an unsafe location (current directory)"
    check("V-MPOL-ENV-CLASS", mp.classify_env_failure(msg) == "EXECUTABLE_NOT_FOUND", mp.classify_env_failure(msg))
    check("V-MPOL-ENV-UNKNOWN", mp.classify_env_failure("something odd") == "UNKNOWN", "unmatched -> UNKNOWN, never a guess")

    # Topology: policy forbids -> main tree even with a healthy tool; allowed + unhealthy -> fallback; allowed + healthy.
    forb = {"value": False, "layer": "repo", "source": "cfg"}
    t = mp.compile_topology(forb, {"EnterWorktree": {"health": "HEALTHY"}})
    check("V-MPOL-TOPO-POLICY-FORBIDS", t["kind"] == "main_tree" and "EnterWorktree" in t["disallowed_tools"], t["why"])
    t = mp.compile_topology({"value": True, "source": "cfg"}, {"EnterWorktree": {"health": "UNHEALTHY"}})
    check("V-MPOL-TOPO-FALLBACK", t["kind"] == "main_tree" and t.get("fallback"), t["why"])
    t = mp.compile_topology({"value": True, "source": "cfg"}, {"EnterWorktree": {"health": "HEALTHY"}})
    check("V-MPOL-TOPO-ALLOWED-CONTROL", t["worktrees"] and "EnterWorktree" in t["allowed_tools"], t["why"])
    t = mp.compile_topology({"value": None}, {})
    check("V-MPOL-TOPO-DEFAULT", t["worktrees"], "unstated policy keeps today's default")

    # Command admission under the forbidding topology, with a control.
    tf = mp.compile_topology(forb)
    cmd = "& 'C:\\Program Files\\Git\\cmd\\git.exe' worktree add -b gsd/x .claude/worktrees/x HEAD"
    check("V-MPOL-DENY-MANUAL-WORKTREE", bool(mp.denies_command(cmd, tf)), str(mp.denies_command(cmd, tf)))
    check("V-MPOL-DENY-CONTROL-LIST", mp.denies_command("git worktree list", tf) is None, "read-only worktree list admitted")
    check("V-MPOL-DENY-CONTROL-ALLOWED", mp.denies_command(cmd, mp.compile_topology({"value": True}, {})) is None,
          "allowed topology admits worktree add")

    # Owner Escalation Gate.
    pv = {"use_worktrees": False}
    g = mp.gate_question(INCIDENT_JOB["needs"], pv)
    check("V-MPOL-GATE-INCIDENT", g["result"] == "RESOLVE_BY_POLICY" and "main checkout" in g["resolution"], g["result"])
    full = ("Decision for you: should I work through the hand-made worktree by absolute path, or would you rather "
            "type `! cd` into the worktree and restart the session from there?")
    check("V-MPOL-GATE-INCIDENT-FULL", mp.gate_question(full, pv)["result"] == "RESOLVE_BY_POLICY", "full question text")
    check("V-MPOL-GATE-HR04", mp.gate_question("Shall I push to main and deploy?", pv)["result"] == "OWNER_REQUIRED",
          "deploy reaches the Owner")
    check("V-MPOL-GATE-GA4", mp.gate_question("Can you create the GA4 property?", pv)["owner_class"] == "EXTERNAL_PROPERTY",
          "external property reaches the Owner")
    check("V-MPOL-GATE-DEFAULT", mp.gate_question("Should I write the SERP notes before the intent map?", pv)["result"]
          == "RESOLVE_BY_DEFAULT", "ordering question resolved by the recommended option")
    mixed = "I'm on the main checkout -- should I push to main and deploy to production?"
    check("V-MPOL-GATE-OWNER-BEATS-POLICY",
          all(mp.gate_question(mixed, {"use_worktrees": v})["result"] == "OWNER_REQUIRED" for v in (True, False)),
          "worktree/main-checkout question that also asks to deploy reaches the Owner under both policies (review F1)")
    check("V-MPOL-GATE-NO-POLICY", mp.gate_question(INCIDENT_JOB["needs"], {})["result"] == "RESOLVE_BY_DEFAULT",
          "worktree question with no stated policy: not an Owner class either")

    # Blocked typing.
    b = mp.classify_blocked(INCIDENT_JOB, pv)
    check("V-MPOL-BLOCKED-INCIDENT", b["class"] == "QUESTION_RESOLVABLE", str(b["class"]))
    check("V-MPOL-BLOCKED-LOGIN", mp.classify_blocked({"state": "blocked", "needs": "login required"}, pv)["class"]
          == "HOST_GATE", "login gate stays a human wait")
    check("V-MPOL-BLOCKED-PERMISSION", mp.classify_blocked({"waitingFor": "approve Bash"}, pv)["class"]
          == "PERMISSION_PROMPT", "permission prompt stays a human wait")
    check("V-MPOL-BLOCKED-OWNER-Q", mp.classify_blocked({"needs": "OK to deploy to production?"}, pv)["class"]
          == "QUESTION_OWNER", "Owner-class question")
    check("V-MPOL-BLOCKED-UNKNOWN", mp.classify_blocked(None, pv)["class"] == "UNKNOWN", "no job record -> UNKNOWN")
    with tempfile.TemporaryDirectory() as td:
        j = Path(td) / INCIDENT_JOB["sessionId"][:8]
        j.mkdir()
        (j / "state.json").write_text(json.dumps(INCIDENT_JOB), encoding="utf-8")
        check("V-MPOL-JOB-READ", mp.job_state(INCIDENT_JOB["sessionId"], Path(td))["needs"] == INCIDENT_JOB["needs"],
              "host job record read by sid prefix")
        check("V-MPOL-JOB-OTHER-SID", mp.job_state("1659fc31-0000-0000-0000-000000000000", Path(td)) is None,
              "prefix collision with another sid refused")

    # Goal liveness: the incident is an INCIDENT before recovery, valid once recovering.
    inc = mp.goal_liveness("BLOCKED", "WAITING_HUMAN", b, recovering=False, owner_packet=False)
    check("V-MPOL-LIVENESS-INCIDENT", inc == "INCIDENT", inc)
    check("V-MPOL-LIVENESS-RECOVERING", mp.goal_liveness("BLOCKED", "WAITING_HUMAN", b, True, False)
          == "SUCCESSOR_COMPILING", "recovery is a valid state")
    check("V-MPOL-LIVENESS-OWNER", mp.goal_liveness("BLOCKED", "WAITING_HUMAN", {"class": "QUESTION_OWNER"}, False, True)
          == "OWNER_BOUNDARY", "Owner question with a packet is valid")
    check("V-MPOL-LIVENESS-OWNER-NOPACKET", mp.goal_liveness("BLOCKED", "WAITING_HUMAN", {"class": "QUESTION_OWNER"},
                                                             False, False) == "INCIDENT", "uncertified Owner wait")

    # Cleanup proof against real git: empty worktree is safe; dirty / unique-commit worktrees are not.
    exe = mp.git_exe()
    if exe:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "r"
            repo.mkdir()
            run = lambda *a, cwd=repo: subprocess.run([exe, "-C", str(cwd), *a], capture_output=True, text=True)  # noqa: E731
            run("init", "-q", "-b", "main")
            run("config", "user.email", "t@t")
            run("config", "user.name", "t")
            (repo / "a.txt").write_text("a", encoding="utf-8")
            run("add", "a.txt")
            run("commit", "-q", "-m", "a")
            for name in ("empty", "dirty", "ahead"):
                run("worktree", "add", "-q", "-b", f"b/{name}", str(Path(td) / name), "HEAD")
            (Path(td) / "dirty" / "notes.md").write_text("valuable", encoding="utf-8")
            (Path(td) / "ahead" / "c.txt").write_text("c", encoding="utf-8")
            run("add", "c.txt", cwd=Path(td) / "ahead")
            run("commit", "-q", "-m", "c", cwd=Path(td) / "ahead")
            pe = mp.worktree_cleanup_proof(str(repo), str(Path(td) / "empty"), "b/empty")
            pd = mp.worktree_cleanup_proof(str(repo), str(Path(td) / "dirty"), "b/dirty")
            pa = mp.worktree_cleanup_proof(str(repo), str(Path(td) / "ahead"), "b/ahead")
            check("V-MPOL-CLEANUP-EMPTY", pe["safe"], pe["why"])
            check("V-MPOL-CLEANUP-DIRTY", not pd["safe"] and "dirty" in pd["why"], pd["why"])
            check("V-MPOL-CLEANUP-AHEAD", not pa["safe"] and "unique_commits" in pa["why"], pa["why"])
            pn = mp.worktree_cleanup_proof(str(repo), str(Path(td) / "nope"), "b/nope")
            check("V-MPOL-CLEANUP-UNANSWERABLE", not pn["safe"], pn["why"])
    else:
        check("V-MPOL-CLEANUP-EMPTY", False, "git unavailable: cleanup proof untested")

    print(f"MPOL_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
