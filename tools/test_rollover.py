#!/usr/bin/env python3
"""V-ROLLOVER-* gates for tools/rollover.py (spec vault/specs/interactive-context-rollover.md).

Hermetic: a throwaway git repo and a throwaway state dir per run; the real
~/.claude/state is never written. Every refusal is paired with a control in
which the fact exists and the verdict is SAFE_TO_FORGET, so a gate that refuses
everything cannot pass.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rollover as ro  # noqa: E402

passes = fails = 0
SID = "aaaaaaaa-0001"          # hex-shaped, like a real session id
OTHER = "bbbbbbbb-0002"        # a sibling pane in the same repo


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"  FAIL {gate}: {ev}")


def check(gate, cond, ev):
    (_ok if cond else _fail)(gate, ev)


def git(root, *args):
    subprocess.run([ro._git_exe(), "-C", str(root), *args], check=True, capture_output=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def make_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    (repo / "vault" / "plans").mkdir(parents=True)
    (repo / "memory").mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@example.invalid")
    git(repo, "config", "user.name", "t")
    (repo / "a.txt").write_text("one\n", encoding="utf-8")
    (repo / "vault" / "plans" / "goal.md").write_text(
        "# Goal\n\n## Done\n- old thing\n\n## Next 3 actions\n1. Wire the shadow observer\n2. Write the vault entry\n",
        encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    write_handoff(repo, SID)
    return repo


def write_handoff(repo: Path, sid: str) -> None:
    (repo / "memory" / "project_session_handoff.md").write_text(
        f"# Session Handoff\n\n**Session ID**: `{sid}`\n\n## Pending\n1. from handoff of {sid}\n", encoding="utf-8")


def make_transcript(tmp: Path, goal: Path, resident: list[int]) -> Path:
    tp = tmp / "sess.jsonl"
    rows = [{"entrypoint": "cli", "type": "assistant", "requestId": f"r{i}", "timestamp": "2026-09-28T10:00:00Z",
             "message": {"id": f"m{i}", "model": "claude-opus-5-5",
                         "usage": {"input_tokens": 10, "cache_creation_input_tokens": 0,
                                   "cache_read_input_tokens": r - 10, "output_tokens": 5},
                         "content": ([{"type": "tool_use", "name": "Write", "input": {"file_path": str(goal)}}]
                                     if i == 1 else [{"type": "text", "text": "x"}])}}
            for i, r in enumerate(resident)]
    rows.append(dict(rows[-1]))  # the same call on a second content line: counted once
    tp.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return tp


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="rollover_t_"))
    state = tmp / "state"
    real_child = ro.child_state
    ro.child_state = lambda sid: {"verdict": "CLEAR", "pending": [], "unconsumed": []}
    try:
        repo = make_repo(tmp)
        goal = repo / "vault" / "plans" / "goal.md"
        tp = make_transcript(tmp, goal, [190_000, 250_000, 520_000])

        pre = ro.repo_facts(str(repo))
        if pre.get("state") != "OK" or isinstance(pre.get("head"), dict):
            # The fixture repo could not be read (measured: git timeouts at 473 MB free). That is
            # the harness failing to establish its precondition, not a verdict on rollover.py.
            print(f"HARNESS-FAILED: fixture repo unreadable ({pre}); no gate judged")
            return 2
        print("capsule")
        cap = ro.compile_capsule(SID, str(repo), str(tp))
        check("V-ROLLOVER-GOAL-FROM-WRITES", cap["goal"].get("path") == str(goal), cap["goal"])
        check("V-ROLLOVER-OBLIGATIONS", cap["obligations"][:1] == ["Wire the shadow observer"], cap["obligations"])
        check("V-ROLLOVER-USAGE-DEDUP", cap["usage"].get("calls") == 3 and cap["usage"].get("floor") == 190_000
              and cap["usage"].get("resident") == 520_000, cap["usage"])
        check("V-ROLLOVER-REPO", cap["repo"].get("branch") and len(str(cap["repo"].get("head"))) == 40
              and cap["repo"].get("dirty") == [], cap["repo"])

        print("safe-to-forget: control, then one refusal per missing category")
        rc = ro.seal(cap, state)
        stf = ro.safe_to_forget(rc, ro.completeness(cap))
        check("V-ROLLOVER-GREEN-CONTROL", rc["sealed"] and stf["verdict"] == "SAFE_TO_FORGET", stf)

        def refused(mutate, needle):
            c = json.loads(json.dumps(cap))
            c["session_id"] = c["handoff"]["session"] = "cccccccc-0003"  # own handoff: one reason only
            mutate(c)
            v = ro.safe_to_forget(ro.seal(c, state), ro.completeness(c))
            return v["verdict"] == "REFUSED" and any(needle in r for r in v["reasons"]), v["reasons"]

        for gate, mut, needle in [
            ("V-ROLLOVER-RED-GOAL", lambda c: c.update(goal=ro._unknown("x")), "goal"),
            ("V-ROLLOVER-RED-OBLIGATIONS", lambda c: c.update(obligations=[]), "obligations"),
            ("V-ROLLOVER-RED-HEAD-UNKNOWN", lambda c: c["repo"].update(head=ro._unknown("t")), "repo.head"),
            ("V-ROLLOVER-RED-HANDOFF-STALE", lambda c: c["handoff"].update(age_s=ro.HANDOFF_MAX_AGE_S + 1), "handoff"),
            ("V-ROLLOVER-RED-CHILD-HOLD", lambda c: c.update(children={"verdict": "HOLD", "pending": [1]}), "children"),
            ("V-ROLLOVER-RED-CHILD-UNKNOWN", lambda c: c.update(children={"verdict": "UNKNOWN", "reason": "no transcript"}), "children"),
        ]:
            ok, ev = refused(mut, needle)
            check(gate, ok, ev)

        ok, ev = refused(lambda c: c["handoff"].update(session=OTHER), "not this one")
        check("V-ROLLOVER-RED-FOREIGN-HANDOFF", ok, ev)

        print("obligations never adopted from a sibling's handoff")
        bare = repo / "vault" / "plans" / "bare.md"
        bare.write_text("# Bare goal\n\nNo next section.\n", encoding="utf-8")
        write_handoff(repo, OTHER)
        foreign = ro.compile_capsule(SID, str(repo), str(tp), goal=str(bare))
        check("V-ROLLOVER-FOREIGN-OBLIGATIONS-NOT-ADOPTED", foreign["obligations"] == []
              and not ro.completeness(foreign)["complete"], foreign["obligations"])
        write_handoff(repo, SID)
        own = ro.compile_capsule(SID, str(repo), str(tp), goal=str(bare))
        check("V-ROLLOVER-OWN-HANDOFF-ADOPTED", own["obligations"] == [f"from handoff of {SID}"]
              and own["obligations_source"] == "own handoff", own["obligations"])
        bare.unlink()

        print("a sibling's /kclear overwrites the shared file; the per-session copy survives")
        write_handoff(repo, OTHER)
        per = repo / "memory" / "handoffs" / f"{SID}.md"
        per.parent.mkdir(exist_ok=True)
        per.write_text(f"# Session Handoff\n\n**Session ID**: `{SID}`\n", encoding="utf-8")
        surv = ro.compile_capsule(SID, str(repo), str(tp))
        check("V-ROLLOVER-PER-SESSION-HANDOFF", surv["handoff"].get("session") == SID
              and surv["handoff"].get("path") == str(per) and ro.completeness(surv)["complete"],
              surv["handoff"].get("path"))
        per.unlink()
        write_handoff(repo, SID)

        rc2 = ro.seal(dict(cap, session_id="s-tamper"), state)
        Path(rc2["path"]).write_text(Path(rc2["path"]).read_text(encoding="utf-8").replace("Wire", "Wyre"), encoding="utf-8")
        v = ro.safe_to_forget(rc2, ro.completeness(cap))
        check("V-ROLLOVER-RED-TAMPER", v["verdict"] == "REFUSED" and "changed since" in " ".join(v["reasons"]), v["reasons"])

        print("policy")
        ratio = {"state": "OK", "write": 8.0, "read": 0.2}
        u = {"state": "OK", "floor": 190_000, "resident": 600_000}
        d = ro.decide(u, 4000, True, 40.0, ratio)
        want = round((190_000 + 1000) * 7.8 / ((600_000 - 191_000) * 0.2), 1)
        check("V-ROLLOVER-BREAKEVEN", d["breakeven_calls"] == want and d["would_rollover"], (d["breakeven_calls"], want, d["reason"]))
        check("V-ROLLOVER-NOT-AT-BOUNDARY", not ro.decide(u, 4000, False, 40.0, ratio)["would_rollover"], "boundary=False")
        check("V-ROLLOVER-SMALL-GROWTH", not ro.decide({**u, "resident": 300_000}, 4000, True, 40.0, ratio)["would_rollover"], "growth<150k")
        check("V-ROLLOVER-PRESSURE", ro.decide({**u, "resident": 300_000}, 4000, False, 75.0, ratio)["would_rollover"], "75%>=70%")
        du = ro.decide(u, 4000, True, 40.0, ro._unknown("no row"))
        check("V-ROLLOVER-UNPRICED-UNKNOWN", du["breakeven_calls"] is None and not du["would_rollover"], du["reason"])

        print("successor")
        c1 = ro.claim(SID, "succ-A", state)
        c2 = ro.claim(SID, "succ-B", state)
        c3 = ro.claim(SID, "succ-A", state)
        check("V-ROLLOVER-ONE-CLAIM", c1["claimed"] and not c2["claimed"] and c2["holder"] == "succ-A" and c3["claimed"], (c1, c2, c3))
        check("V-ROLLOVER-REFRESH-CONTINUE", ro.refresh(cap, str(repo))["verdict"] == "CONTINUE", "unchanged tree")
        (repo / "a.txt").write_text("two\n", encoding="utf-8")
        git(repo, "commit", "-q", "-am", "moved")
        rf = ro.refresh(cap, str(repo))
        check("V-ROLLOVER-REFRESH-HEAD-MOVED", rf["verdict"] == "RECOMPILE" and any(x.startswith("head") for x in rf["divergences"]), rf["divergences"])
        good = {"goal": "goal.md", "branch": cap["repo"]["branch"], "head": cap["repo"]["head"][:7],
                "next": "wire the shadow observer"}
        check("V-ROLLOVER-EXAM-PASS", ro.certify(cap, good)["verdict"] == "RESUME_CERTIFIED", good)
        bad = ro.certify(cap, {**good, "head": "0000000"})
        check("V-ROLLOVER-EXAM-FAIL", bad["verdict"] == "RESUME_FAILED" and bad["wrong"][0]["key"] == "head", bad["wrong"])
        check("V-ROLLOVER-EXAM-EMPTY-FAILS", ro.certify(cap, {})["verdict"] == "RESUME_FAILED", "no answers")
        found = ro.newest_capsule(str(repo), state, exclude="nobody")
        check("V-ROLLOVER-NEWEST-BY-CWD", found is not None and found["cwd"] == str(repo), found and found["session_id"])
        check("V-ROLLOVER-OTHER-CWD-IGNORED", ro.newest_capsule(str(tmp), state) is None, "different cwd")

        # 2026-09-29 (ea5c9025): sealed from a subdirectory after a `cd`, resumed from the repo
        # root. Own state dir so the ordering checks below are untouched.
        sub_state = tmp / "state_subdir"
        drifted = json.loads(json.dumps(cap))
        drifted.update(session_id="subdir-0001", cwd=str(repo / "scripts"))
        ro.seal(drifted, sub_state)
        hit = ro.newest_capsule(str(repo), sub_state, exclude="nobody")
        check("V-ROLLOVER-SUBDIR-SEAL-FOUND-AT-ROOT", hit is not None and hit["session_id"] == "subdir-0001",
              hit and hit["session_id"])
        check("V-ROLLOVER-SUBDIR-SEAL-OTHER-DIR-IGNORED", ro.newest_capsule(str(tmp), sub_state) is None,
              "a directory that is neither the sealed cwd nor the repo root")

        # An uncertifiable capsule (no goal, no obligation -- what the shadow seals for a session
        # that wrote no plan) sealed NEWER than a good one. It must be skipped, never claimed.
        NR = "nnnnnnnn-0009"
        nr = json.loads(json.dumps(cap))
        nr.update(session_id=NR, goal=ro._unknown("wrote no plan"), obligations=[])
        ro.seal(nr, state)
        check("V-ROLLOVER-UNRESUMABLE-NAMED", len(ro.resumable(nr)) == 2 and not ro.resumable(cap), ro.resumable(nr))
        sk: list = []
        pick = ro.newest_capsule(str(repo), state, exclude="nobody", skipped=sk)
        check("V-ROLLOVER-UNRESUMABLE-SKIPPED", pick is not None and pick["session_id"] != NR and NR in sk,
              (pick and pick["session_id"], sk))
        ro.STATE_DIR = state
        rc_nr = ro.main(["resume", "--cwd", str(repo), "--claimant", "succ-Z", "--from", NR])
        check("V-ROLLOVER-UNRESUMABLE-NOT-CLAIMED", rc_nr == 4 and not (state / "capsules" / f"{NR}.claim").exists(),
              f"rc={rc_nr}")

        boot = ro.bootstrap(cap)
        check("V-ROLLOVER-BOOTSTRAP-SMALL", len(boot) <= ro.BOOTSTRAP_MAX_CHARS and "goal.md" in boot
              and "Wire the shadow observer" in boot, f"{len(boot)} chars")

        print("shadow observe")
        ro.child_state = real_child  # the real reader: this synthetic session has no transcript it can find
        row = ro.observe("s-shadow", str(repo), str(tp), 40.0, "t1", state_dir=state)
        led = (state / "rollover-ledger.jsonl").read_text(encoding="utf-8")
        check("V-ROLLOVER-SHADOW-LEDGERED", '"shadow_candidate"' in led and row["mode"] == "shadow", row["safe_to_forget"])
        check("V-ROLLOVER-SHADOW-UNKNOWN-CHILD-REFUSES", row["safe_to_forget"] == "REFUSED"
              and any("children" in r for r in row["refusals"]), row["refusals"])
        os.environ["CPP_ROLLOVER_SHADOW"] = "off"
        n_before = led.count("\n")
        ro.STATE_DIR = state  # a broken switch would write HERE, where the gate reads
        ro.main(["shadow", "--session", "s-off", "--cwd", str(repo)])
        n_after = (state / "rollover-ledger.jsonl").read_text(encoding="utf-8").count("\n")
        os.environ.pop("CPP_ROLLOVER_SHADOW", None)
        check("V-ROLLOVER-KILL-SWITCH", n_after == n_before, f"{n_before}->{n_after}")

        print("certify through the CLI: fencing and shell-safe answers")
        ro.STATE_DIR = state                      # succ-A holds the claim on SID (above)
        flags = ["--goal", "goal.md", "--branch", cap["repo"]["branch"], "--head", cap["repo"]["head"][:7],
                 "--next", "Wire the shadow observer"]
        rc_b = ro.main(["certify", "--from", SID, "--claimant", "succ-B", *flags])
        check("V-ROLLOVER-CERTIFY-FENCED", rc_b == 5 and not (state / "capsules" / f"{SID}.certified").exists(), f"rc={rc_b}")
        rc_bad = ro.main(["certify", "--from", SID, "--claimant", "succ-A", "--answers", "{goal:goal.md}"])
        check("V-ROLLOVER-ANSWERS-UNREADABLE", rc_bad == 7, f"rc={rc_bad} (PowerShell-stripped JSON)")
        rc_ok = ro.main(["certify", "--from", SID, "--claimant", "succ-A", *flags])
        check("V-ROLLOVER-CERTIFY-FLAGS", rc_ok == 0 and (state / "capsules" / f"{SID}.certified").exists(), f"rc={rc_ok}")
        check("V-ROLLOVER-CERTIFIED-RETIRED", ro.newest_capsule(str(repo), state, exclude="x") is None
              or ro.newest_capsule(str(repo), state, exclude="x")["session_id"] != SID, "certified capsule not offered again")

        print("reset gate: may /clear be typed for this session RIGHT NOW?")
        ro.STATE_DIR = state
        gsid = "gggggggg-0007"
        gcap = json.loads(json.dumps(cap))
        gcap["session_id"] = gcap["handoff"]["session"] = gsid
        grc = ro.seal(gcap, state)
        gstf = ro.safe_to_forget(grc, ro.completeness(gcap))
        ro.ledger("capsule_sealed", state, session_id=gsid, cwd=str(repo), capsule=grc,
                  safe_to_forget=gstf["verdict"], refusals=gstf["reasons"])
        # POSITIVE CONTROL. Without it a gate that refused everything would satisfy every
        # assertion below and read exactly like a working one.
        g = ro.gate(gsid, state)
        check("V-ROLLOVER-GATE-GREEN", g["verdict"] == "SAFE_TO_FORGET" and not g["reasons"], g["reasons"])
        check("V-ROLLOVER-GATE-EXIT-0", ro.main(["gate", "--session", gsid]) == 0, "a good capsule may reset")

        # "nothing was ever sealed" is NOT "your capsule went bad": different code, different fix.
        check("V-ROLLOVER-GATE-NO-CAPSULE", ro.gate("zzzzzzzz-9999", state)["verdict"] == "NO_CAPSULE"
              and ro.main(["gate", "--session", "zzzzzzzz-9999"]) == 4, "absent != refused, 4 != 3")

        # The branch a self-comparing hash can never reach: the bytes on disk are no longer
        # the bytes the receipt was taken over. This is the whole reason the hash is read
        # from the ledger rather than recomputed from the file and compared to itself.
        ro.capsule_path(gsid, state).write_text('{"schema":"tampered"}', encoding="utf-8")
        gt = ro.gate(gsid, state)
        check("V-ROLLOVER-GATE-TAMPER", gt["verdict"] == "REFUSED"
              and any("not the bytes that were sealed" in r for r in gt["reasons"]), gt["reasons"])

        ro.seal(gcap, state)                       # restore the sealed bytes
        gs = ro.gate(gsid, state, now=ro._now() + ro.RESET_MAX_AGE_S + 60)
        check("V-ROLLOVER-GATE-STALE", gs["verdict"] == "REFUSED"
              and any("seal again" in r for r in gs["reasons"]), gs["reasons"])

        ro.capsule_path(gsid, state).with_suffix(".certified").write_text("x", encoding="utf-8")
        gc = ro.gate(gsid, state)
        check("V-ROLLOVER-GATE-CERTIFIED", gc["verdict"] == "REFUSED"
              and any("certified" in r for r in gc["reasons"]), gc["reasons"])

        bsid = "hhhhhhhh-0008"                      # the seal itself refused; the gate must say so
        bcap = json.loads(json.dumps(gcap))
        bcap["session_id"] = bcap["handoff"]["session"] = bsid
        bcap["obligations"] = []
        brc = ro.seal(bcap, state)
        bstf = ro.safe_to_forget(brc, ro.completeness(bcap))
        ro.ledger("capsule_sealed", state, session_id=bsid, cwd=str(repo), capsule=brc,
                  safe_to_forget=bstf["verdict"], refusals=bstf["reasons"])
        gb = ro.gate(bsid, state)
        check("V-ROLLOVER-GATE-CARRIES-SEAL-REFUSAL", gb["verdict"] == "REFUSED"
              and any("obligations" in r for r in gb["reasons"])
              and ro.main(["gate", "--session", bsid]) == 3, gb["reasons"])

        os.environ.pop("CPP_ROLLOVER_ACTIVE", None)
        unset = ro.active_enabled()
        os.environ["CPP_ROLLOVER_ACTIVE"] = "0"
        off = ro.active_enabled()
        os.environ["CPP_ROLLOVER_ACTIVE"] = "1"
        on = ro.active_enabled()
        os.environ.pop("CPP_ROLLOVER_ACTIVE", None)
        check("V-ROLLOVER-ACTIVE-DEFAULT-ON", unset and on and not off,
              f"unset={unset} '1'={on} '0'={off} (the switch only ever disables)")
    finally:
        ro.child_state = real_child
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"ROLLOVER_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    ro.STATE_DIR = Path(tempfile.gettempdir()) / "rollover_t_never_used"
    sys.exit(main())
