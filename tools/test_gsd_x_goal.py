#!/usr/bin/env python3
"""V-gates for the goal spine: identity, revision, event log, single owner.

Every clause is driven in both directions. A gate that could only ever answer
"ok" carries no information, so each refusal here sits beside the case that
must still succeed.

    python tools/test_gsd_x_goal.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import contract as gc  # noqa: E402
from modules.gsd_x.goal import log as gl       # noqa: E402
from modules.gsd_x.mission import store as st  # noqa: E402

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"   # PATH first: GEX44 (Linux) runs these
REPO = "a" * 40

RACE_SCRIPT = r"""
import sys, time
sys.path.insert(0, sys.argv[1])
from modules.gsd_x.goal import log as gl
lg = gl.GoalLog(sys.argv[2], sys.argv[3], base=__import__('pathlib').Path(sys.argv[4]))
deadline = float(sys.argv[5])
while time.time() < deadline:
    pass
try:
    lg.append(2, "race.probe", {"who": sys.argv[6]}, sys.argv[6])
    print("WON")
except gl.LostRace:
    print("LOST")
except gl.Inconclusive:
    print("INCONCLUSIVE")
"""


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

    base = Path(tempfile.mkdtemp(prefix="gsdx_goal_"))

    # --- identity -------------------------------------------------------------
    lg = gl.GoalLog(REPO, "g-001", base=base)
    s = gc.declare(lg, "Wake the dormant runner.", ["a job runs through the proxy"],
                   [], {"paths": ["tools/smoke-test"]})
    check("V-GOAL-ID-DECLARED", s.last_seq == 1 and s.revision and lg.exists(),
          f"seq=1 revision={s.revision}", f"state={s}")
    try:
        gc.declare(lg, "something else")
        bad("V-GOAL-ID-UNIQUE", "a second declaration of g-001 was accepted")
    except gc.GoalExists:
        ok("V-GOAL-ID-UNIQUE", "re-declaring an existing goal id refused")
    try:
        gl.GoalLog(REPO, "Bad Id!", base=base)
        bad("V-GOAL-ID-SYNTAX", "an id with spaces and punctuation was accepted")
    except gl.GoalLogError:
        ok("V-GOAL-ID-SYNTAX", "malformed goal id refused")
    try:
        gc.declare(gl.GoalLog(REPO, "g-empty", base=base), "   ")
        bad("V-GOAL-INTENT-REQUIRED", "an empty intent was declared")
    except gl.GoalLogError:
        ok("V-GOAL-INTENT-REQUIRED", "a goal without the Founder's words refused")

    # --- revision -------------------------------------------------------------
    a = gc.revision_of(gc.normalise("X", ["b", "a"], [], {"paths": ["q", "p"]}))
    b = gc.revision_of(gc.normalise("X", ["b", "a"], [], {"paths": ["p", "q"]}))
    c = gc.revision_of(gc.normalise("X", ["a", "b"], [], {"paths": ["p", "q"]}))
    check("V-GOAL-REV-STABLE", a == b, "scope path order does not change the revision",
          f"{a} != {b}")
    check("V-GOAL-REV-SENSITIVE", a != c, "acceptance order is content, and moves it",
          "reordered acceptance criteria produced the same revision")
    s2 = gc.set_budget(lg, 2, {"codex_epochs_per_day": 10}, "owner")
    s3 = gc.set_authority(lg, 3, {"ceiling": "local-code"}, "owner")
    check("V-GOAL-REV-BUDGET-NEUTRAL", s2.revision == s.revision == s3.revision,
          "budget and authority events leave the revision untouched",
          f"{s.revision} -> {s2.revision} -> {s3.revision}")
    try:
        gc.revise(lg, 4, s.intent, s.acceptance, s.constraints, s.scope)
        bad("V-GOAL-REV-NOOP-REFUSED", "an identical revision was minted")
    except gl.GoalLogError:
        ok("V-GOAL-REV-NOOP-REFUSED", "a no-op revision is refused")
    s4 = gc.revise(lg, 4, s.intent, s.acceptance + ["hotbar item observed"],
                   s.constraints, s.scope)
    check("V-GOAL-REV-NEW", s4.revision != s.revision and len(s4.revisions) == 2,
          f"criterion change minted {s4.revision}", f"revisions={s4.revisions}")

    # --- event log: CAS, chain, corruption ------------------------------------
    try:
        lg.append(3, "stale.decision", {}, "t")
        bad("V-GOAL-CAS-STALE", "an append computed on stale state was accepted")
    except gl.LostRace:
        ok("V-GOAL-CAS-STALE", "append at an already-published seq refused as LostRace")

    # The DETERMINISTIC half of the CAS claim: two writers that both got past
    # append()'s pre-read hand the same prepared event to publish(). No timing
    # is involved, so this cannot pass by luck the way the process race below
    # can when the two happen to serialise.
    lgp = gl.GoalLog(REPO, "g-publish", base=base)
    gc.declare(lgp, "publish once")
    prepared = {"seq": 2, "type": "race.probe", "ts": "2026-09-22T00:00:00+00:00",
                "actor": "w1", "data": {}, "prev_digest": lgp.read()[-1].digest}
    prepared["digest"] = gl.event_digest(prepared)
    lgp.publish(prepared)
    try:
        lgp.publish(dict(prepared))
        bad("V-GOAL-CAS-PUBLISH-ONCE", "the same sequence number was published twice")
    except gl.LostRace:
        ok("V-GOAL-CAS-PUBLISH-ONCE", "a second publish of one sequence number refused")
    check("V-GOAL-CAS-PUBLISH-ONE-EVENT", len(lgp.read()) == 2,
          "only one event exists at that sequence", f"{len(lgp.read())} events")

    lg2 = gl.GoalLog(REPO, "g-race", base=base)
    gc.declare(lg2, "race")
    import time
    deadline = time.time() + 2.0
    procs = [subprocess.Popen([sys.executable, "-c", RACE_SCRIPT, str(ROOT), REPO, "g-race",
                               str(base), str(deadline), f"w{i}"],
                              stdout=subprocess.PIPE, text=True) for i in range(2)]
    outs = sorted(p.communicate(timeout=60)[0].strip() for p in procs)
    evs = lg2.read()
    check("V-GOAL-CAS-TWO-WRITERS", outs == ["LOST", "WON"] and len(evs) == 2,
          f"two processes raced for seq 2: {outs}, log has {len(evs)} events",
          f"outcomes={outs} events={len(evs)}")

    (lg2.dir / ".tmp-deadbeef").write_bytes(b'{"half":')
    try:
        check("V-GOAL-CAS-TEMP-IGNORED", len(lg2.read()) == 2,
              "a crashed writer's temp file is not an event", "temp file changed the read")
    except gl.GoalLogCorrupt as exc:
        bad("V-GOAL-CAS-TEMP-IGNORED", f"temp file broke the read: {exc}")

    lg3 = gl.GoalLog(REPO, "g-corrupt", base=base)
    gc.declare(lg3, "corrupt me")
    (lg3.dir / "000002.json").write_text('{"seq": 2, "type": "trunc', encoding="utf-8")
    try:
        lg3.read()
        bad("V-GOAL-LOG-TRUNCATED-RAISES", "a truncated event was read without error")
    except gl.GoalLogCorrupt:
        ok("V-GOAL-LOG-TRUNCATED-RAISES", "truncated event raises; never read as fewer events")

    lg4 = gl.GoalLog(REPO, "g-tamper", base=base)
    gc.declare(lg4, "tamper")
    gc.set_budget(lg4, 2, {"x": 1}, "owner")
    p1 = lg4.dir / "000001.json"
    raw = json.loads(p1.read_text(encoding="utf-8"))
    raw["data"]["semantic"]["intent"] = "edited after the fact"
    p1.write_text(json.dumps(raw), encoding="utf-8")
    try:
        lg4.read()
        bad("V-GOAL-LOG-CHAIN", "an edited historical event was accepted")
    except gl.GoalLogCorrupt:
        ok("V-GOAL-LOG-CHAIN", "editing a past event breaks its digest and is detected")

    lg5 = gl.GoalLog(REPO, "g-gap", base=base)
    gc.declare(lg5, "gap")
    gc.set_budget(lg5, 2, {"x": 1}, "owner")
    (lg5.dir / "000002.json").rename(lg5.dir / "000003.json")
    try:
        lg5.read()
        bad("V-GOAL-LOG-GAP", "a sequence gap was accepted")
    except gl.GoalLogCorrupt:
        ok("V-GOAL-LOG-GAP", "a missing sequence number raises")

    lg7 = gl.GoalLog(REPO, "g-malformed", base=base)
    gc.declare(lg7, "malformed")
    lg7.append(2, gc.REVISED, {"revision": "x"}, "t")   # chain-valid, payload wrong
    try:
        gc.project(lg7)
        bad("V-GOAL-MALFORMED-PAYLOAD", "a revision event with no semantic was replayed")
    except gl.GoalLogCorrupt:
        ok("V-GOAL-MALFORMED-PAYLOAD", "a chain-valid but malformed payload raises Corrupt")
    except KeyError:
        bad("V-GOAL-MALFORMED-PAYLOAD", "raised a bare KeyError, not GoalLogCorrupt")

    lg6 = gl.GoalLog(REPO, "g-perm", base=base)
    gc.declare(lg6, "perm")
    with mock.patch.object(gl.os, "link", side_effect=PermissionError("sharing violation")):
        try:
            lg6.append(2, "x", {}, "t")
            bad("V-GOAL-CAS-PERMISSION", "a sharing violation was reported as success")
        except gl.Inconclusive:
            ok("V-GOAL-CAS-PERMISSION", "sharing violation -> Inconclusive, not lost, not won")
        except gl.LostRace:
            bad("V-GOAL-CAS-PERMISSION", "a sharing violation was read as a lost race")
    check("V-GOAL-CAS-PERMISSION-NOTHING-WRITTEN", len(lg6.read()) == 1,
          "the inconclusive write left no event behind", "an event was published anyway")

    # --- repo identity --------------------------------------------------------
    repo_dir = Path(tempfile.mkdtemp(prefix="gsdx_repo_"))
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    subprocess.run([GIT, "init", "-q", str(repo_dir)], check=True, env=env)
    (repo_dir / "f.txt").write_text("x", encoding="utf-8")
    subprocess.run([GIT, "-C", str(repo_dir), "add", "f.txt"], check=True, env=env)
    subprocess.run([GIT, "-C", str(repo_dir), "commit", "-qm", "root"], check=True, env=env)
    rid = gl.repo_id(repo_dir)
    moved = repo_dir.parent / (repo_dir.name + "_moved")
    repo_dir.rename(moved)
    check("V-GOAL-REPOID-SURVIVES-MOVE", gl.repo_id(moved) == rid and len(rid) == 40,
          "the id is the root commit, unchanged by moving the checkout",
          f"{rid} vs {gl.repo_id(moved)}")
    try:
        gl.repo_id(Path(tempfile.mkdtemp(prefix="gsdx_norepo_")))
        bad("V-GOAL-REPOID-REFUSES", "a directory with no repository got an id")
    except gl.RepoIdUnknown:
        ok("V-GOAL-REPOID-REFUSES", "no repository -> RepoIdUnknown, never a made-up id")

    # --- single owner ---------------------------------------------------------
    mroot = Path(tempfile.mkdtemp(prefix="gsdx_mission_"))
    try:
        st.save(mroot, [])
        ok("V-GOAL-SINGLE-OWNER-UNBOUND", "an unbound root still writes its own store")
    except st.GoalBound:
        bad("V-GOAL-SINGLE-OWNER-UNBOUND", "an unbound root was refused")
    st.bind(mroot, REPO, "g-001")
    try:
        st.save(mroot, [])
        bad("V-GOAL-SINGLE-OWNER", "a goal-bound root still accepted per-root obligations")
    except st.GoalBound:
        ok("V-GOAL-SINGLE-OWNER", "a goal-bound root refuses per-root obligation writes")
    cli = subprocess.run([sys.executable, str(ROOT / "tools" / "gsd_x_mission.py"),
                          "closure", str(mroot)], capture_output=True, text=True,
                         env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    check("V-GOAL-SINGLE-OWNER-CLOSURE", cli.returncode == 2 and "REFUSED" in cli.stdout,
          "mission closure on a bound root is refused, exit 2",
          f"rc={cli.returncode} out={cli.stdout[-200:]!r} err={cli.stderr[-200:]!r}")
    st.binding_path(mroot).write_text("{not json", encoding="utf-8")
    try:
        st.save(mroot, [])
        bad("V-GOAL-SINGLE-OWNER-UNREADABLE", "an unreadable binding reopened the store")
    except st.GoalBound:
        ok("V-GOAL-SINGLE-OWNER-UNREADABLE", "an unreadable binding is not 'unbound'")

    total = len(passes) + len(fails)
    print(f"\nGSDX_GOAL_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
