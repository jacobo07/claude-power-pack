#!/usr/bin/env python3
"""UWCP S0-2: characterization of TODAY's behaviour that UWCP must change.

Every V-UWCP-CHAR-* case asserts the CURRENT (defective) behaviour and is green
on the commit that introduces this file. Each names the slice commit that will
invert it; that commit flips the assertion in place, so the diff between the two
versions of the same test is the evidence (vault/specs/uwcp.md §17-18, S0).

Each defect case sits beside a positive control proving the mechanism it pins
can observe anything at all -- a characterization that passes because the
instrument is blind would invert into a vacuous green later.

    python tools/test_uwcp_characterization.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import brief as gb        # noqa: E402
from modules.gsd_x.goal import contract as gc     # noqa: E402
from modules.gsd_x.goal import epoch as ep        # noqa: E402
from modules.gsd_x.goal import git_state as gs    # noqa: E402
from modules.gsd_x.goal import log as gl          # noqa: E402

REPO = "d" * 40
GIT = next((g for g in gs.GIT_CANDIDATES if shutil.which(g) or Path(g).is_file()), None)


def _git(cwd: Path, *args: str) -> str:
    p = subprocess.run([GIT, "-C", str(cwd), *args], capture_output=True, text=True,
                       timeout=60, stdin=subprocess.DEVNULL)
    if p.returncode != 0:
        raise RuntimeError(f"git {args}: {p.stderr.strip()}")
    return p.stdout.strip()


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def check(g, cond, ev, why):
        (passes if cond else fails).append(g)
        print(f"  {'PASS' if cond else 'FAIL'} {g}: {ev if cond else why}")

    base = Path(tempfile.mkdtemp(prefix="uwcp_char_"))

    # --- C1 late receipt after the epoch ended (inverted by S1-8, fence) -------
    lg = gl.GoalLog(REPO, "g-char", base=base / "goals")
    s = gc.declare(lg, "characterize", ["it runs"], [], {"paths": ["src"]})
    key = ep.info_key(s.revision, [], "fake", "initial", "scope0")
    def rcpt(e, rev, **kw):
        """A receipt that echoes its epoch's identity, as every provider now does (A1)."""
        return ep.Receipt(e.epoch_id, "fake", rev, **{**ep.echo({"identity": e.identity}), **kw})

    e1 = ep.begin(lg, gc.project(lg), "fake", {}, key, "initial", "t")
    ep.mark_running(lg, gc.project(lg), e1.epoch_id, {"h": 1}, "t")
    rid_ok = ep.ingest_receipt(lg, gc.project(lg), rcpt(e1, s.revision, narrative="a"), "t")
    check("V-UWCP-CHAR-RECEIPT-CONTROL", bool(rid_ok),
          "control: a receipt for a running epoch is ingested", "control receipt refused")
    ep.end(lg, gc.project(lg), e1.epoch_id, ep.LOST, "stall abort", "t")
    try:
        ep.ingest_receipt(lg, gc.project(lg), rcpt(e1, s.revision, narrative="late"), "t")
        late_ingested = True
    except ep.EpochError:
        late_ingested = False
    # INVERTED by S1-8: was V-UWCP-CHAR-LATE-RECEIPT-INGESTED.
    check("V-UWCP-FENCE-LATE-RECEIPT-REFUSED", not late_ingested,
          "a receipt arriving after its epoch ended LOST is refused (stale fence)",
          "a late receipt was banked into a closed epoch")

    # Fences are minted strictly increasing and a mismatched fence is refused.
    # (One epoch at a time since S1-8b: e2 ends before e3 begins.)
    e2 = ep.begin(lg, gc.project(lg), "fake", {}, "k2", "initial", "t")
    ep.mark_running(lg, gc.project(lg), e2.epoch_id, {"h": 2}, "t")
    try:
        ep.ingest_receipt(lg, gc.project(lg), rcpt(e2, s.revision, fence=e2.fence + 1), "t")
        wrong_fence = False
    except ep.EpochError:
        wrong_fence = True
    right = ep.ingest_receipt(lg, gc.project(lg), rcpt(e2, s.revision), "t")
    check("V-UWCP-FENCE-MISMATCH-REFUSED", wrong_fence and bool(right),
          "a receipt carrying another epoch's fence is refused; its own fence is accepted",
          f"wrong_fence_refused={wrong_fence}")
    ep.end(lg, gc.project(lg), e2.epoch_id, ep.COMPLETED, "done", "t")
    e3 = ep.begin(lg, gc.project(lg), "fake", {}, "k3", "initial", "t")
    check("V-UWCP-FENCE-MONOTONIC",
          e1.fence >= 1 and e2.fence == e1.fence + 1 and e3.fence == e2.fence + 1
          and e3.identity.get("fence") == e3.fence,
          f"fences {e1.fence}<{e2.fence}<{e3.fence}, carried in the pre-minted identity",
          f"fences {e1.fence},{e2.fence},{e3.fence}")
    import hashlib as _h                                                   # noqa: PLC0415
    import json as _j                                                      # noqa: PLC0415
    from dataclasses import asdict as _asdict                              # noqa: PLC0415
    legacy = ep.Receipt("ep-x", "gate", "r1", commits=["abc"])
    # The pre-S1-8 schema had none of the echo fields (fence; goal_id and run_token
    # since S1-8b), so the old id is the hash of the body without all three.
    old_body = {k: v for k, v in _asdict(legacy).items()
                if k not in ("fence", "goal_id", "run_token")}
    old_id = _h.sha256(_j.dumps(old_body, sort_keys=True, ensure_ascii=False,
                                separators=(",", ":")).encode("utf-8")).hexdigest()[:24]
    check("V-UWCP-FENCE-LEGACY-ID-STABLE", legacy.receipt_id() == old_id,
          "an unfenced receipt hashes to the id it had before fencing existed, so a "
          "replay of an old receipt is still caught as a duplicate",
          "legacy receipt ids moved")

    # --- C2 pins hash working-tree bytes: CRLF vs LF disagree (S1-9) ----------
    lf = base / "lf"
    crlf = base / "crlf"
    for d, nl in ((lf, b"\n"), (crlf, b"\r\n")):
        (d / "gate").mkdir(parents=True)
        (d / "gate" / "t.py").write_bytes(b"print(1)" + nl + b"print(2)" + nl)
    pin_lf = gs.file_pin(lf, ["gate/t.py"])
    pin_crlf = gs.file_pin(crlf, ["gate/t.py"])
    check("V-UWCP-CHAR-PIN-CONTROL", gs.file_pin(lf, ["gate/t.py"]) == pin_lf,
          "control: identical bytes pin identically", "pin not deterministic")
    # The legacy sha256 scheme still splits BY DESIGN (stored pins keep verifying
    # byte-exactly); it stays pinned here as the control for the inversion below.
    check("V-UWCP-PIN-LEGACY-STILL-RAW", pin_lf != pin_crlf,
          "control: legacy sha256 pins remain raw-byte (existing goals unaffected)",
          "legacy scheme changed meaning under stored pins")
    # INVERTED by S1-9: was V-UWCP-CHAR-PIN-EOL-SPLIT.
    b_lf = gs.file_pin(lf, ["gate/t.py"], gs.BLOB)
    b_crlf = gs.file_pin(crlf, ["gate/t.py"], gs.BLOB)
    check("V-UWCP-PIN-BLOB-EOL-INVARIANT", b_lf == b_crlf and b_lf[0][1].startswith("blob:"),
          "blob pins of one file agree on a CRLF and an LF checkout", f"{b_lf} != {b_crlf}")
    # INVERTED by S1-9: was V-UWCP-CHAR-SCOPE-EOL-SPLIT.
    check("V-UWCP-SCOPE-EOL-INVARIANT",
          ep.scope_hash(lf, ["gate"]) == ep.scope_hash(crlf, ["gate"]),
          "the retry key is the same on both hosts' checkouts", "scope hash splits on eol")
    (lf / "gate" / "t.py").write_bytes(b"print(9)\n")
    check("V-UWCP-SCOPE-SEES-CONTENT",
          ep.scope_hash(lf, ["gate"]) != ep.scope_hash(crlf, ["gate"]),
          "control: a real content change still moves the key", "scope hash went blind")
    (lf / "gate" / "t.py").write_bytes(b"print(1)\nprint(2)\n")
    if GIT:
        p = subprocess.run([GIT, "hash-object", str(lf / "gate" / "t.py")],
                           capture_output=True, text=True, timeout=30)
        check("V-UWCP-BLOB-MATCHES-GIT",
              b_lf[0][1] == "blob:" + p.stdout.strip(),
              "blob_oid equals `git hash-object` for the LF file (independent instrument)",
              f"{b_lf[0][1]} vs git {p.stdout.strip()}")
    try:
        gs.pin_scheme((("a", "blob:1"), ("b", "ff")))
        mixed_refused = False
    except ValueError:
        mixed_refused = True
    check("V-UWCP-PIN-MIXED-REFUSED", mixed_refused and gs.pin_scheme(pin_lf) == gs.SHA256
          and gs.pin_scheme(b_lf) == gs.BLOB,
          "a pin mixing schemes is refused; each pure pin reports its scheme",
          "mixed pin accepted or scheme misread")
    check("V-UWCP-DIGEST-MATCHES-BOTH",
          gs.digest_matches(lf / "gate" / "t.py", pin_lf[0][1])
          and gs.digest_matches(crlf / "gate" / "t.py", b_lf[0][1])
          and not gs.digest_matches(crlf / "gate" / "t.py", pin_lf[0][1]),
          "the judge's check honours each scheme: legacy exact, blob eol-invariant",
          "digest_matches misjudged a scheme")

    # --- C3 scope_hash ignores build debris (INVERTED by S1-9) ----------------
    before = ep.scope_hash(lf, ["gate"])
    (lf / "gate" / "__pycache__").mkdir()
    (lf / "gate" / "__pycache__" / "t.cpython-312.pyc").write_bytes(b"\x00junk")
    check("V-UWCP-SCOPE-IGNORES-DEBRIS", ep.scope_hash(lf, ["gate"]) == before,
          "running a gate (which writes __pycache__) no longer moves the retry key",
          "debris moved the key")

    # --- C4 brief has no total bound (S1-6) -----------------------------------
    big = "x" * 200_000
    lg2 = gl.GoalLog(REPO, "g-brief", base=base / "goals")
    s2 = gc.declare(lg2, big, ["ok"], [], {"paths": ["src"]})
    try:
        text = gb.compile_brief(s2, [], "/w", "task")
    except gb.BriefTooLarge as exc:
        text = ""
        big_refused = str(exc)
    else:
        big_refused = ""
    small = gb.compile_brief(gc.declare(gl.GoalLog(REPO, "g-small", base=base / "goals"),
                                        "small", ["ok"], [], {"paths": ["src"]}), [], "/w", "t")
    check("V-UWCP-CHAR-BRIEF-CONTROL", 0 < len(small) < 4000,
          f"control: an ordinary brief compiles ({len(small)} chars)", "ordinary brief broke")
    # INVERTED by S1-6: was V-UWCP-CHAR-BRIEF-UNBOUNDED (a 200 KB brief compiled).
    check("V-UWCP-BRIEF-BOUNDED", bool(big_refused) and not text,
          f"a 200 KB intent is refused, not cut to fit ({big_refused[:70]}...)",
          f"compiled a {len(text)}-char brief")
    try:
        gb.compile_brief(gc.project(gl.GoalLog(REPO, "g-small", base=base / "goals")),
                         [], "/w", "t", max_tokens=50)
        tok_refused = False
    except gb.BriefTooLarge:
        tok_refused = True
    check("V-UWCP-BRIEF-TOKEN-BOUND", tok_refused,
          "an executor whose window cannot hold the brief is refused before dispatch",
          "a brief over the executor's token bound compiled")

    # --- C5 autonomy passes off-git (UNKNOWN head -> PASS) (S1-10) ------------
    from modules.gsd_x.goal import sweep as sw  # noqa: PLC0415
    old = os.environ.get("GSDX_GOALS_ROOT")
    os.environ["GSDX_GOALS_ROOT"] = str(base / "auto" / "goals")
    try:
        rec = sw.record_path()
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text(json.dumps({"head": "a" * 40, "green": True, "suites": {}}),
                       encoding="utf-8")
        nongit = base / "nongit_runtime"
        nongit.mkdir()
        allowed, why = sw.autonomy_verdict(nongit)
        # INVERTED by S1-10: was V-UWCP-CHAR-AUTONOMY-NONGIT-PASSES.
        check("V-UWCP-AUTONOMY-NONGIT-REFUSED", not allowed and "no identity" in why,
              "a non-git runtime with no RUNTIME_ID cannot use a green record from other code",
              f"allowed: {why}")
        (nongit / "RUNTIME_ID").write_text("uwcp-runtime:" + "b" * 64, encoding="utf-8")
        allowed_m, why_m = sw.autonomy_verdict(nongit)
        rec.write_text(json.dumps({"head": "uwcp-runtime:" + "b" * 64, "green": True,
                                   "suites": {}}), encoding="utf-8")
        allowed_ok, why_ok = sw.autonomy_verdict(nongit)
        check("V-UWCP-AUTONOMY-RUNTIME-ID",
              not allowed_m and allowed_ok,
              "an installed runtime is identified by its RUNTIME_ID: a record for other code "
              "is refused, a record for this runtime is honoured",
              f"mismatch allowed={allowed_m} ({why_m}); match allowed={allowed_ok} ({why_ok})")
        (nongit / "RUNTIME_ID").write_text("whatever", encoding="utf-8")
        allowed_bad, _ = sw.autonomy_verdict(nongit)
        check("V-UWCP-AUTONOMY-RUNTIME-ID-MALFORMED", not allowed_bad,
              "a RUNTIME_ID without the installer's prefix is not an identity",
              "a malformed RUNTIME_ID licensed autonomy")
        if GIT:
            gitrt = base / "gitrt"
            gitrt.mkdir()
            _git(gitrt, "init", "-q")
            _git(gitrt, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
                 "--allow-empty", "-m", "r")
            allowed2, why2 = sw.autonomy_verdict(gitrt)
            check("V-UWCP-CHAR-AUTONOMY-CONTROL", not allowed2,
                  "control: on a git runtime a record for another head is refused",
                  f"control failed: {why2}")
    finally:
        if old is None:
            os.environ.pop("GSDX_GOALS_ROOT", None)
        else:
            os.environ["GSDX_GOALS_ROOT"] = old

    # --- C6 the long-run provider cannot start a run (S1-11) ------------------
    from modules.gsd_x.goal.providers.long_run import LongRunProvider  # noqa: PLC0415
    try:
        LongRunProvider(base / "lr").dispatch({"identity": {"run_token": "t"}})
        cannot = False
        why6 = "dispatch returned"
    except ep.EpochError as exc:
        cannot = "cannot start" in str(exc)
        why6 = str(exc)[:90]
    check("V-UWCP-LONGRUN-NEEDS-SPEC", cannot and "mission spec" in why6,
          "with neither a mission spec nor a bound session, nothing is started -- and the "
          "refusal names both ways in", f"behaviour changed: {why6}")

    # INVERTED by S1-11: was V-UWCP-CHAR-LONGRUN-CANNOT-START. The goal spine arms a
    # v3 mission itself; launch=False so no worker is spawned in a test.
    old_sd = os.environ.get("GSD_LONG_RUN_STATE_DIR")
    os.environ["GSD_LONG_RUN_STATE_DIR"] = str(base / "mstate")
    (base / "mstate").mkdir()
    try:
        from modules.gsd_x.goal.providers import long_run as lrp  # noqa: PLC0415
        prov = lrp.LongRunProvider(base / "lr3")
        tok = "abcdef0123456789" * 2
        spec3 = {"epoch_id": "ep-m", "revision": "r1", "identity": {"run_token": tok},
                 "mission": {"cwd": str(base), "command": "/gsd-autonomous", "launch": False,
                             "max_cycles": 2, "max_hours": 1}}
        h = prov.dispatch(spec3)
        o = prov.observe(h)
        check("V-UWCP-LONGRUN-ARMS-V3",
              h.get("mission_id") == lrp.mission_id_for(tok)
              and o.state == ep.OBS_RUNNING and "not started" in o.detail,
              f"the spine arms a v3 mission ({h.get('mission_id')}) and reports it ARMED, not "
              f"running: {o.detail}", f"handle={h} obs={o}")
        try:
            prov.dispatch(spec3)
            dup = False
        except ep.EpochError:
            dup = True
        check("V-UWCP-LONGRUN-NO-DOUBLE-ARM", dup,
              "a second dispatch of the same epoch identity is refused (one mission per epoch)",
              "the same epoch armed two missions")
        (base / "lr3" / f"longrun-{tok}.json").unlink()
        check("V-UWCP-LONGRUN-PROBE-ADOPTS",
              (prov.probe({"run_token": tok}) or {}).get("mission_id") == h["mission_id"],
              "a crash that lost the marker still finds the armed mission by its derived id",
              "probe could not adopt the armed mission")
        prov.cancel(h)
        o2 = prov.observe(h)
        r = prov.harvest(h, spec3)
        check("V-UWCP-LONGRUN-CANCEL",
              o2.state == ep.OBS_ENDED and o2.outcome == ep.CANCELLED and r.verdicts == []
              and any("halted" in f["signature"] for f in r.failures),
              "cancel halts the mission through its CAS; the epoch ends CANCELLED and the "
              "receipt carries the halt, no verdict", f"obs={o2} receipt failures={r.failures}")
    finally:
        if old_sd is None:
            os.environ.pop("GSD_LONG_RUN_STATE_DIR", None)
        else:
            os.environ["GSD_LONG_RUN_STATE_DIR"] = old_sd

    # --- C7 repo identity: path key is host-local, no portable id (S1-3) ------
    from modules.repo_identity import identity as ri  # noqa: PLC0415
    if GIT:
        a = base / "clone_a"
        a.mkdir()
        _git(a, "init", "-q")
        (a / "f.txt").write_text("x\n", encoding="utf-8")
        _git(a, "add", "f.txt")
        _git(a, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "root")
        b = base / "elsewhere" / "clone_b"
        b.parent.mkdir()
        subprocess.run([GIT, "clone", "-q", str(a), str(b)], capture_output=True, timeout=60)
        check("V-UWCP-CHAR-REPOID-ROOT-CONTROL", gl.repo_id(a) == gl.repo_id(b),
              "control: the goal log's root-commit id is equal across two clones",
              "root-commit ids differ")
        # INVERTED by S1-3: was V-UWCP-CHAR-REPOKEY-HOSTLOCAL ("no portable id").
        check("V-UWCP-REPOID-PORTABLE",
              ri.repo_key(str(a)) != ri.repo_key(str(b))
              and ri.portable_repo_id(a) == ri.portable_repo_id(b) == gl.repo_id(a),
              "the path key stays host-local by design, and portable_repo_id gives both "
              "clones one id, the same one the goal log uses",
              "portable id missing or disagrees with the goal log")
        sh = base / "shallow"
        (a / "g.txt").write_text("y\n", encoding="utf-8")
        _git(a, "add", "g.txt")
        _git(a, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "two")
        subprocess.run([GIT, "clone", "-q", "--depth", "1", "file://" + a.as_posix(), str(sh)],
                       capture_output=True, timeout=60)
        try:
            ri.portable_repo_id(sh)
            shallow_refused = False
        except ri.PortableIdUnknown:
            shallow_refused = True
        check("V-UWCP-REPOID-SHALLOW-REFUSED", shallow_refused and (sh / ".git").exists(),
              "a shallow clone is refused: its boundary commit is not the root",
              "shallow clone accepted, or the fixture clone did not happen")
        try:
            gl.repo_id(sh)
            wrapper_refuses = False
        except gl.RepoIdUnknown:
            wrapper_refuses = True
        check("V-UWCP-REPOID-WRAPPER-CONTRACT", wrapper_refuses,
              "the goal log keeps raising its own RepoIdUnknown", "wrapper contract changed")
    else:
        fails.append("V-UWCP-CHAR-GIT")
        print("  FAIL V-UWCP-CHAR-GIT: git not found; C5 control and C7 could not run "
              "(HARNESS, not a finding)")

    # --- C8 receipts echo their whole identity; one epoch at a time (A1/S1-8b) --
    # INVERTED in place by S1-8b: the three CHAR gates of 28d1224 are the A1 gates below.
    lg8 = gl.GoalLog(REPO, "g-char-a1", base=base / "goals")
    s8 = gc.declare(lg8, "characterize A1", ["it runs"], [], {"paths": ["src"]})
    e8 = ep.begin(lg8, gc.project(lg8), "fake", {}, "k8", "initial", "t")
    ep.mark_running(lg8, gc.project(lg8), e8.epoch_id, {"h": 8}, "t")

    def refusal(r, state=None):
        try:
            ep.ingest_receipt(lg8, state or gc.project(lg8), r, "t")
            return "<ingested>"
        except ep.EpochError as exc:
            return getattr(exc, "code", "<uncoded>")

    # was V-UWCP-CHAR-UNECHOED-RECEIPT-INGESTED
    unechoed = refusal(ep.Receipt(e8.epoch_id, "fake", s8.revision, narrative="no echo"))
    check("V-UWCP-A1-UNECHOED-REFUSED", unechoed == ep.STALE_FENCE,
          "a fenced epoch refuses a receipt that echoes no fence", f"got {unechoed}")
    foreign = refusal(rcpt(e8, s8.revision, run_token="f" * 32, narrative="other run"))
    check("V-UWCP-A1-FOREIGN-RUN-TOKEN-REFUSED", foreign == ep.EPOCH_MISMATCH,
          "a receipt from another run of the same epoch is refused", f"got {foreign}")
    other_goal = refusal(rcpt(e8, s8.revision, goal_id="g-someone-else", narrative="x"))
    check("V-UWCP-A1-OTHER-GOAL-REFUSED", other_goal == ep.EPOCH_MISMATCH,
          "a receipt naming another goal is refused", f"got {other_goal}")
    # was V-UWCP-CHAR-REFUSAL-UNCODED
    code = refusal(rcpt(e8, "not-the-revision"))
    check("V-UWCP-A1-REFUSAL-CODED", code == ep.REVISION_MISMATCH,
          "a refusal carries a machine-readable code", f"code={code!r}")
    # was V-UWCP-CHAR-BEGIN-WHILE-OPEN
    try:
        ep.begin(lg8, gc.project(lg8), "fake", {}, "k9", "initial", "t")
        stacked = True
    except ep.EpochError:
        stacked = False
    check("V-UWCP-A1-BEGIN-WHILE-OPEN-REFUSED", not stacked,
          "begin() refuses a second epoch while one is open", "a second epoch was opened")
    ok8 = refusal(rcpt(e8, s8.revision, narrative="echoed"))
    check("V-UWCP-A1-ECHOED-CONTROL", ok8 == "<ingested>",
          "control: a receipt echoing its identity is ingested", f"refused: {ok8}")
    dup = refusal(rcpt(e8, s8.revision, narrative="echoed"))
    check("V-UWCP-A1-DUPLICATE-CODED", dup == ep.DUPLICATE, "a replay is refused as duplicate",
          f"got {dup}")
    ep.end(lg8, gc.project(lg8), e8.epoch_id, ep.COMPLETED, "done", "t")
    stale_view = gc.project(lg8)                      # taken before e10 exists
    e10 = ep.begin(lg8, gc.project(lg8), "fake", {}, "k10", "initial", "t")
    ep.mark_running(lg8, gc.project(lg8), e10.epoch_id, {"h": 10}, "t")
    reload_ok = refusal(rcpt(e10, s8.revision, narrative="newer than the view"), stale_view)
    check("V-UWCP-A1-RELOAD-ONCE", reload_ok == "<ingested>",
          "a fence newer than the caller's projection reloads once and is judged on the log",
          f"got {reload_ok}")
    ended = refusal(rcpt(e8, s8.revision, narrative="late"))
    check("V-UWCP-A1-ENDED-CODED", ended == ep.EPOCH_ENDED,
          "a receipt for an ended epoch is refused as epoch_ended", f"got {ended}")

    total = len(passes) + len(fails)
    print(f"UWCP_CHAR_PASS={len(passes)}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
