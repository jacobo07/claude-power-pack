"""V-MPOL-*: mission policy -- precedence, config-as-control, capability preflight, Owner Escalation Gate,
blocked-state typing, cleanup proof. Every refusal is paired with a control that is admitted.

Run: python tools/test_mission_policy.py   (exit 0 = all pass)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("MPOL_DRILL_DIR"):  # --drills: the mutant copy of mission_policy.py shadows the real one
    sys.path.insert(0, os.environ["MPOL_DRILL_DIR"])
import mission_policy as mp  # noqa: E402

OWNER_FIXTURE = Path(__file__).resolve().parent.parent / "vault" / "evidence" / "phys" / "g2" / \
    "phys-p14-owner-gate-questions-fixture.json"
KILL_SWITCH = "CPP_MISSION_OWNER_GATES"
DONE_CLS = "DONE_GATE_OR_DEVIATION"

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

    # S11 A1: a certification/truth-contract change is the Owner's. Incident 2026-11-02 (Game-A S10, mission
    # m-e6e0340e743d): the sweep answered this exact question RESOLVE_BY_DEFAULT.
    sd8 = ("Decide whether cert-cxx may admit an sd8 variant (fn_00000A01 is the case in question); then a new S10-1 "
           "plan can be written")
    g = mp.gate_question(sd8, pv)
    check("V-MPOL-GATE-TRUTH-SD8", g["result"] == "OWNER_REQUIRED" and g.get("owner_class") == "TRUTH_CONTRACT",
          f"sd8 admission incident -> {g.get('owner_class') or g['result']}")
    tsynth = ["Relax exactness to accept 99.5 % matches for this class?",
              "Should the certification contract admit a -O4,s variant?",
              "Count the corroborating configurations as independent evidence?",
              "Can we change the held-out rules and reuse H as development data?",
              "Accept pct >= 99 as certified for the near misses?",
              "Lower the match threshold of the judge to 99?"]
    tbad = [s for s in tsynth if mp.gate_question(s, pv).get("owner_class") != "TRUTH_CONTRACT"]
    check("V-MPOL-GATE-TRUTH-SYNTH", not tbad, f"{len(tsynth) - len(tbad)}/{len(tsynth)} -> TRUTH_CONTRACT; missed={tbad}")
    tneg = ["Should I certify the dev batch before the census?",
            "Change the batch size of the census from 25 to 50?",
            "Should I run the held-out preflight after B5?",
            "Which certifier controls should run first, positive or negative?",
            "Lower the log verbosity of the judge script?",
            "Should I count exact matches per batch in the report?"]
    tbadn = [s for s in tneg if mp.gate_question(s, pv)["result"] != "RESOLVE_BY_DEFAULT"]
    check("V-MPOL-GATE-TRUTH-NEG", not tbadn, f"{len(tneg) - len(tbadn)}/{len(tneg)} HOW questions stay default; "
                                              f"wrongly escalated={tbadn}")
    # S11 D3: incident 2026-11-02 23:31Z (m-f0b595fd509f epoch 12) -- waiving a held-out release control was answered
    # RESOLVE_BY_DEFAULT. A positive/negative control or a release/kill gate is part of the truth contract.
    waive = "Waive fn_00000A02 for OM-PR1, or authorize a new source-shape approach beyond declaration order"
    g = mp.gate_question(waive, pv)
    wsynth = [waive, "Can we waive the positive control that still fails?", "Drop one negative control from the release set?",
              "Relax the kill gate K5 for this wave?", "Treat OM-PR1 as passed at 2/3?",
              # 2026-11-03 05:33Z, same mission, still RESOLVE_BY_DEFAULT after the D3 fix (no control noun in it):
              "Owner to waive fn_00000A02, or supply a donor with the same two-block lookup"]
    wbad = [s for s in wsynth if mp.gate_question(s, pv).get("owner_class") != "TRUTH_CONTRACT"]
    check("V-MPOL-GATE-TRUTH-CONTROL-WAIVER", not wbad, f"{len(wsynth) - len(wbad)}/{len(wsynth)} control waivers -> "
                                                        f"TRUTH_CONTRACT; missed={wbad}")
    # S11 D2: incident 2026-11-03 (same mission): the checkpoint reason "in-scope routes falsified" read as PRODUCT_SCOPE,
    # which would have parked an engineering pivot for the Owner. A descriptive in-scope adjective is not a scope question;
    # a question ABOUT scope still is.
    reason = ("OM-PR1 2/3: fn_00000A02 98.9 (mwcc reg priority), in-scope routes falsified; "
              "6 dev registry-attributable CXX")
    sneg = [reason, "All in-scope methods exhausted for the residual; next route is the ctor hint generator"]
    sbad = [s for s in sneg if mp.gate_question(s, pv)["result"] != "RESOLVE_BY_DEFAULT"]
    spos = ["Is the ctor hint route in scope?", "Should we expand the scope to the C++ runtime library?",
            "Is that out of scope for S11?"]
    sbadp = [s for s in spos if mp.gate_question(s, pv).get("owner_class") != "PRODUCT_SCOPE"]
    check("V-MPOL-GATE-SCOPE-DESCRIPTIVE", not sbad and not sbadp,
          f"descriptive stays default (wrongly escalated={sbad}); scope questions stay PRODUCT_SCOPE (missed={sbadp})")

    # Spec capsule-seal-on-question-end D2: incident m-81b9650c6ff2 2026-11-03 15:47Z -- a request to switch a guard off
    # was answered RESOLVE_BY_DEFAULT. Switching a guard off is the Owner's call.
    gd_inc = "set CPP_SEM_BREAKER=off (or clear the breaker) so WU-FE2 Phase 1 judging can resume"
    gpos = [gd_inc, "CPP_SEM_BREAKER=off", "Clear the breaker so judging can resume?", "Disable the write-gate hook for this run?",
            "Turn off the popup firewall for one run?", "Should I bypass the console-popup guard?",
            "Set the kill switch off and continue?"]
    gbad = [s for s in gpos if mp.gate_question(s, pv).get("owner_class") != "GUARD_DISABLE"]
    gneg = ["Should I run the gate before the suite?", "The breaker receipt says GOOD_PROGRESS; next phase?",
            "Which gate order, A then B?", "Skip the docs, then run the gate?", "Should I add a hook test for the stop chain?",
            "Clear the scratch dir before the next render?",
            # review F2: status sentences, the adjective and "kick off" are descriptions (checkpoint reasons are gated too)
            "kill gate K5 cleared at 3/3; next route is ctor hints", "The breaker reset overnight; resume?",
            "It's not clear which gate applies, A or B?", "Kick off the gate suite now?", "the gate cleared"]
    gbadn = [s for s in gneg if mp.gate_question(s, pv)["result"] != "RESOLVE_BY_DEFAULT"]
    check("V-MPOL-GATE-GUARD-DISABLE", not gbad and not gbadn,
          f"{len(gpos) - len(gbad)}/{len(gpos)} guard switch-offs -> GUARD_DISABLE (missed={gbad}); "
          f"{len(gneg) - len(gbadn)}/{len(gneg)} ordinary stay default (wrongly escalated={gbadn})")
    gb = mp.classify_blocked({"state": "blocked", "needs": gd_inc}, pv)
    check("V-MPOL-BLOCKED-GUARD-DISABLE-OWNER", gb["class"] == "QUESTION_OWNER", str(gb["class"]))

    # 14-01 W2a: done-gate / overrun / deviation Owner class (addendum section 3), kill switch CPP_MISSION_OWNER_GATES.
    saved_ks = os.environ.pop(KILL_SWITCH, None)
    try:
        fx = json.loads(OWNER_FIXTURE.read_text(encoding="utf-8")) if OWNER_FIXTURE.is_file() else {"questions": []}
        qs = fx.get("questions", [])
        real = [q for q in qs if not q.get("standin")]
        stand = [q for q in qs if q.get("standin")]
        got = [mp.gate_question(q["text"], pv) for q in qs]
        check("V-MPOL-OWNER-FIXTURE-QUESTIONS",
              bool(qs) and (bool(real) or all(q.get("standin") and q.get("standin_quotes") for q in qs))
              and all(g["result"] == "OWNER_REQUIRED" and g.get("owner_class") == DONE_CLS for g in got),
              f"{len(real)} real + {len(stand)} stand-in questions -> {[g.get('owner_class') or g['result'] for g in got]}")
        os.environ[KILL_SWITCH] = "off"
        hist = [(q["recorded_result"], mp.gate_question(q["text"], pv)["result"]) for q in qs]
        check("V-MPOL-OWNER-REPLAY-HISTORICAL", bool(qs) and all(a == b for a, b in hist),
              f"kill switch off: {len(hist)} fixture questions give the recorded result {sorted(set(a for a, _ in hist))}")
        os.environ.pop(KILL_SWITCH, None)
        synth = ["Override the done-gate and mark the phase passed?",
                 "Accept the spend breach and continue?",
                 "Set the VERIFICATION status to passed with the gaps recorded as accepted deviations?",
                 "Record the gap as a deviation and continue?",
                 "Accept the overrun past P95 and keep going?",
                 "Release the envelope STOP for one verifier run?"]
        bad = [s for s in synth if mp.gate_question(s, pv).get("owner_class") != DONE_CLS]
        check("V-MPOL-OWNER-SYNTH", not bad, f"{len(synth) - len(bad)}/{len(synth)} synthetic forms -> {DONE_CLS}; missed={bad}")
        neg = ["Should I write the SERP notes before the intent map?",
               "Should I run the drills before the full suite?",
               "Close the gap between the two grid columns first?",
               "Which deviation metric should the chart use, sigma or MAD?",
               "Is the verification script under tools/ or scripts/?"]
        badn = [s for s in neg if mp.gate_question(s, pv)["result"] != "RESOLVE_BY_DEFAULT"]
        inc_ok = mp.gate_question(INCIDENT_JOB["needs"], pv)["result"] == "RESOLVE_BY_POLICY"
        check("V-MPOL-OWNER-NEG", not badn and inc_ok,
              f"{len(neg) - len(badn)}/{len(neg)} ordinary questions stay RESOLVE_BY_DEFAULT; worktree incident stays "
              f"RESOLVE_BY_POLICY={inc_ok}; wrongly escalated={badn}")
        probe = synth[0]
        states = {}
        for val in (None, "on", "1", "off", "OFF", "On"):
            if val is None:
                os.environ.pop(KILL_SWITCH, None)
            else:
                os.environ[KILL_SWITCH] = val
            states[val] = mp.gate_question(probe, pv)["result"]
        want = {None: "OWNER_REQUIRED", "on": "OWNER_REQUIRED", "1": "OWNER_REQUIRED", "On": "OWNER_REQUIRED",
                "off": "RESOLVE_BY_DEFAULT", "OFF": "RESOLVE_BY_DEFAULT"}
        check("V-MPOL-OWNER-KILL-SWITCH", states == want, f"read at call time in one process: {states}")
    finally:
        os.environ.pop(KILL_SWITCH, None)
        if saved_ks is not None:
            os.environ[KILL_SWITCH] = saved_ks

    # Blocked typing.
    b = mp.classify_blocked(INCIDENT_JOB, pv)
    check("V-MPOL-BLOCKED-INCIDENT", b["class"] == "QUESTION_RESOLVABLE", str(b["class"]))
    # S11H P5 (GEX44 2026-11-03 09:54:41Z): after the supervisor's own stop the job record read `stopped`, which was
    # typed QUESTION_RESOLVABLE with the question "stopped" -- a decision recovery spent on a lifecycle word.
    life = [mp.classify_blocked(j, pv)["class"] for j in ({"state": "blocked", "detail": "stopped"},
                                                         {"state": "stopped", "detail": "stopped"},
                                                         {"state": "blocked", "needs": " Done "})]
    check("V-MPOL-BLOCKED-LIFECYCLE-NOT-QUESTION", all(c == "STOPPED" for c in life), str(life))
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


# --drills: each mutant of mission_policy.py must turn the named gate red (the drill never writes tools/mission_policy.py).
DRILLS = (
    ("M1 class entry removed", '    ("DONE_GATE_OR_DEVIATION", DONE_GATE_RX),\n', "", "V-MPOL-OWNER-FIXTURE-QUESTIONS"),
    ("M2 kill-switch read ignored", '.lower() == "off"', '.lower() == "off-ignored-by-drill"', "V-MPOL-OWNER-KILL-SWITCH"),
    ("M3 class pattern reduced to one literal phrase", '("DONE_GATE_OR_DEVIATION", DONE_GATE_RX)',
     '("DONE_GATE_OR_DEVIATION", re.compile(r"override the done-gate", re.I))', "V-MPOL-OWNER-SYNTH"),
    ("M4 truth-contract class removed", '    ("TRUTH_CONTRACT", TRUTH_CONTRACT_RX),\n', "", "V-MPOL-GATE-TRUTH-SD8"),
    ("M5 control terms dropped from the truth contract", r'|kill[- ]gates?|OM-PR\d+|', "|",
     "V-MPOL-GATE-TRUTH-CONTROL-WAIVER"),
    ("M7 named-function waiver dropped", '    r"\\bwaiv\\w*\\b[^?.]{0,20}\\bfn_[0-9a-f]{6,8}\\b|"\n', "",
     "V-MPOL-GATE-TRUTH-CONTROL-WAIVER"),
    ("M8 lifecycle words read as questions",
     'if str(job.get("state") or "").lower() in LIFECYCLE_WORDS or needs.strip().lower() in LIFECYCLE_WORDS:',
     "if False:", "V-MPOL-BLOCKED-LIFECYCLE-NOT-QUESTION"),
    ("M6 descriptive-scope neutraliser bypassed", "t_scope = _DESCRIPTIVE_SCOPE_RX.sub(\" \", t)", "t_scope = t",
     "V-MPOL-GATE-SCOPE-DESCRIPTIVE"),
    ("M9 guard-disable class removed", '    ("GUARD_DISABLE", GUARD_DISABLE_RX),\n', "", "V-MPOL-GATE-GUARD-DISABLE"),
)


def drills() -> int:
    src = (Path(__file__).resolve().parent / "mission_policy.py").read_text(encoding="utf-8")
    ok = 0
    for name, needle, repl, gate in DRILLS:
        if needle not in src:
            print(f"DRILL-FAIL {name}: needle absent from tools/mission_policy.py")
            continue
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "mission_policy.py").write_text(src.replace(needle, repl, 1), encoding="utf-8")
            env = {**os.environ, "MPOL_DRILL_DIR": td}
            env.pop(KILL_SWITCH, None)
            r = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve())], capture_output=True, text=True,
                               env=env, timeout=300)
        red = f"FAIL {gate}" in r.stdout
        print(f"{'DRILL-PASS' if red else 'DRILL-FAIL'} {name}: expected 'FAIL {gate}' -> {'seen' if red else 'NOT seen'} (exit {r.returncode})")
        ok += int(red)
    print(f"MPOL_DRILLS_PASS={ok}/{len(DRILLS)}")
    return 0 if ok == len(DRILLS) else 1


if __name__ == "__main__":
    sys.exit(drills() if "--drills" in sys.argv[1:] else main())
