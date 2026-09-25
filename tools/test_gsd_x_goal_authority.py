#!/usr/bin/env python3
"""V-gates for founder authority (spec: vault/specs/gdd-founder-authority.md).

Every refusal is paired with a control in which the same path, given the real
key, is admitted -- a gate that refuses everything would otherwise pass every
refusal assertion here.

The ENFORCED mode needs a real POSIX permission drill. On Windows (and as root,
where os.access is not a boundary) that case prints UNJUDGED: it is neither
counted as a pass nor as a fail, and the GEX44 run is the one that judges it.

    python tools/test_gsd_x_goal_authority.py
"""
from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryptography.hazmat.primitives import serialization          # noqa: E402

from modules.gsd_x.goal import authority as au      # noqa: E402
from modules.gsd_x.goal import contract as gc       # noqa: E402
from modules.gsd_x.goal import convergence as cv    # noqa: E402
from modules.gsd_x.goal import git_state as gs      # noqa: E402
from modules.gsd_x.goal import log as gl            # noqa: E402
from modules.gsd_x.goal import sweep as sw          # noqa: E402

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "PYTHONIOENCODING": "utf-8"}
REPO_ID = "a7" * 20
AUTH_ENV = (au.ENV_ANCHOR, au.ENV_FOUNDER_KEY, au.ENV_JUDGE_KEY, au.ENV_WITNESS)
# Events written past the API carry this ts, so a signature made for them
# (which covers ts and actor) matches what is stored.
RAW_TS = datetime(2026, 9, 24, tzinfo=timezone.utc).isoformat()


def set_env(anchor=None, founder=None, judge=None, witness=None) -> None:
    for name, value in zip(AUTH_ENV, (anchor, founder, judge, witness)):
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = str(value)


def load_priv(path: Path):
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def raw_append(lg: gl.GoalLog, type_: str, data: dict) -> None:
    """Write an event WITHOUT the API -- what a principal with store access can do."""
    events = lg.read()
    body = {"seq": len(events) + 1, "type": type_, "ts": RAW_TS, "actor": "founder",
            "data": data, "prev_digest": events[-1].digest if events else gl.GENESIS}
    body["digest"] = gl.event_digest(body)
    lg.publish(body)


def forged_data(lg: gl.GoalLog, type_: str, data: dict, key, kid: str) -> dict:
    events = lg.read()
    seq, prev = len(events) + 1, events[-1].digest
    sig = key.sign(au.event_message(lg.repo, lg.goal_id, seq, type_, data, prev,
                                    RAW_TS, "founder"))
    return {**data, au.SIG_FIELD: {"key_id": kid, "sig": base64.b64encode(sig).decode()}}


def adopt_reviewed(lg: gl.GoalLog, actor: str = "owner") -> gc.GoalState:
    """Adopt attesting the digest a reviewer would have seen just now."""
    return gc.adopt(lg, actor, gc.project(lg).events[-1].digest)


def rewrite(lg: gl.GoalLog, mutate, rechain: bool) -> None:
    files = sorted(p for p in lg.dir.iterdir() if gl.EVENT_RE.match(p.name))
    raws = [json.loads(p.read_text(encoding="utf-8")) for p in files]
    mutate(raws)
    prev = gl.GENESIS
    for p, raw in zip(files, raws):
        if rechain:
            raw["prev_digest"] = prev
            raw["digest"] = gl.event_digest(raw)
            prev = raw["digest"]
        p.write_text(json.dumps(raw, indent=2), encoding="utf-8")


def corrupt_reason(lg: gl.GoalLog) -> str:
    try:
        gc.project(lg)
    except gl.GoalLogCorrupt as exc:
        return str(exc)
    return ""


def event_count(lg: gl.GoalLog) -> int:
    return len([p for p in lg.dir.iterdir() if gl.EVENT_RE.match(p.name)]) if lg.dir.is_dir() else 0


def make_repo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="gsdx_auth_repo_"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "gate.py").write_text("import sys\nprint('1 passed')\nsys.exit(0)\n", encoding="utf-8")
    subprocess.run([GIT, "-C", str(d), "add", "."], check=True, env=ENV)
    subprocess.run([GIT, "-C", str(d), "commit", "-qm", "seed"], check=True, env=ENV)
    return d


def sweepable_goal(base: Path, gid: str, repo: Path) -> gl.GoalLog:
    """A legacy (ABSENT-mode) goal the sweep would plan work for."""
    lg = gl.GoalLog(REPO_ID, gid, base=base)
    gc.declare(lg, f"auth {gid}", ["the gate passes"], [], {"paths": ["."]})
    for plane in cv.PLANES:
        cv.set_plane(lg, gc.project(lg), plane, plane in cv.ALWAYS,
                     "" if plane in cv.ALWAYS else "not claimed", "t")
    cv.accept_obligation(lg, gc.project(lg), "ob-outcome", cv.OUTCOME, "prove it",
                         f'"{sys.executable}" gate.py', gs.file_pin(repo, ["gate.py"]), "t")
    sw.set_autonomous(lg, gc.project(lg), True, "test", "owner")
    return lg


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []
    unjudged: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    def check(g, cond, ev, why):
        (ok if cond else bad)(g, ev if cond else why)

    def unjudge(g, why):
        unjudged.append(g)
        print(f"  UNJUDGED {g}: {why}")

    set_env()
    tmp = Path(tempfile.mkdtemp(prefix="gsdx_auth_"))
    base = tmp / "goals"
    base.mkdir()
    os.environ["GSDX_GOALS_ROOT"] = str(base)
    keys = tmp / "keys"
    fk, jk, xk = keys / "founder.pem", keys / "judge.pem", keys / "stranger.pem"
    f_id, f_entry = au.generate_keypair(fk, au.FOUNDER)
    j_id, j_entry = au.generate_keypair(jk, au.JUDGE)
    x_id, _x_entry = au.generate_keypair(xk, au.FOUNDER)       # never put in the anchor
    anchor = tmp / "anchor.json"
    anchor.write_text(json.dumps({**f_entry, **j_entry}), encoding="utf-8")
    fpriv, jpriv, xpriv = load_priv(fk), load_priv(jk), load_priv(xk)

    # --- the set of founder-class events is the one the modules declare -----------
    declared = {gc.DECLARED, gc.REVISED, gc.BUDGET_SET, gc.AUTHORITY_SET, sw.AUTONOMOUS_EVENT,
                gc.PAUSED, gc.RESUMED, gc.TIER_SET, gc.DECISION_ANSWERED, gc.ADOPTED}
    check("V-AUTH-FOUNDER-CLASS-MATCHES", declared == set(au.FOUNDER_CLASS),
          f"{len(declared)} founder-class types, identical in authority and contract/sweep",
          f"drift: {declared ^ set(au.FOUNDER_CLASS)}")

    # --- modes ---------------------------------------------------------------------
    a = au.load_anchor()
    check("V-AUTH-MODE-ABSENT", a.mode == au.ABSENT and "unverified" in au.describe(a),
          f"no anchor -> {a.mode}: {au.describe(a)}", f"{a.mode}: {au.describe(a)}")
    lg_abs = gl.GoalLog(REPO_ID, "g-absent", base=base)
    gc.declare(lg_abs, "legacy goal", ["x"], [], {"paths": ["."]})
    raw1 = (lg_abs.dir / "000001.json").read_text(encoding="utf-8")
    check("V-AUTH-ABSENT-UNCHANGED", au.SIG_FIELD not in raw1 and gc.project(lg_abs).last_seq == 1,
          "in ABSENT a founder event is written exactly as before: no signature field",
          "ABSENT mode altered the stored event")

    set_env(anchor)
    a = au.load_anchor()
    expect_unprot = os.name == "nt" or os.access(anchor, os.W_OK)
    check("V-AUTH-MODE-UNPROTECTED", a.mode == au.UNPROTECTED and expect_unprot
          and "not a boundary" in au.describe(a),
          f"a writable anchor -> {a.mode}: {au.describe(a)[:90]}", f"{a.mode}")

    bad_anchor = tmp / "bad_anchor.json"
    bad_anchor.write_text("{not json", encoding="utf-8")
    mismatched = tmp / "mismatch_anchor.json"
    mismatched.write_text(json.dumps({"0" * 16: f_entry[f_id]}), encoding="utf-8")
    modes = {}
    for label, path in (("malformed", bad_anchor), ("missing", tmp / "nope.json"),
                        ("key-id-mismatch", mismatched)):
        set_env(path)
        modes[label] = au.load_anchor().mode
    set_env(anchor)
    check("V-AUTH-MODE-UNVERIFIABLE",
          all(m == au.UNVERIFIABLE for m in modes.values()) and au.load_anchor().mode != au.UNVERIFIABLE,
          f"malformed / missing / id-mismatched anchors are UNVERIFIABLE ({modes}); "
          "control: the valid anchor is not", f"{modes}")

    # --- ENFORCED needs a real POSIX permission drill ----------------------------------
    posix_gates = ("V-AUTH-MODE-ENFORCED", "V-AUTH-MODE-WITNESS-REQUIRED",
                   "V-AUTH-SYMLINK-ANCHOR-NOT-ENFORCED")
    if os.name == "nt":
        for g in posix_gates:
            unjudge(g, "Windows host: os.access is not an ACL boundary; judged on GEX44")
    elif hasattr(os, "geteuid") and os.geteuid() == 0:
        for g in posix_gates:
            unjudge(g, "running as root: every file is writable, the permission drill "
                    "cannot fail; judged as a non-root user")
    else:
        rodir = tmp / "anchor_dir"
        rodir.mkdir()
        ro = rodir / "ro_anchor.json"
        ro.write_text(anchor.read_text(encoding="utf-8"), encoding="utf-8")
        r_only = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
        rx_only = r_only | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        # The witness must be out of reach too, INCLUDING its named parent.
        wit_outer = tmp / "wit_outer"
        ro_wit = wit_outer / "witness"
        ro_wit.mkdir(parents=True)
        os.chmod(ro_wit, rx_only)
        os.chmod(wit_outer, rx_only)
        # A symlink to the read-only anchor, itself inside a read-only directory:
        # resolving it would read ENFORCED; the link is still not a boundary.
        linkdir = tmp / "link_dir"
        linkdir.mkdir()
        link = linkdir / "anchor_link.json"
        try:
            os.symlink(ro, link)
            linked = True
        except OSError:
            linked = False
        os.chmod(linkdir, rx_only)
        os.chmod(ro, r_only)
        os.chmod(rodir, rx_only)
        set_env(ro)
        m_nowit = au.load_anchor()
        set_env(ro, witness=tmp)
        m_rwwit = au.load_anchor()
        if linked:
            set_env(link, witness=ro_wit)
            m_link = au.load_anchor()
            check("V-AUTH-SYMLINK-ANCHOR-NOT-ENFORCED",
                  m_link.mode == au.UNPROTECTED and "symlink" in m_link.detail,
                  f"a symlinked anchor in a read-only dir -> {m_link.mode} ({m_link.detail}); "
                  "control: the same file named directly is judged below",
                  f"{m_link.mode}: {m_link.detail}")
        else:
            unjudge("V-AUTH-SYMLINK-ANCHOR-NOT-ENFORCED", "this host refused os.symlink")
        set_env(ro, witness=ro_wit)
        writable_ro = os.access(ro, os.W_OK) or os.access(rodir, os.W_OK)
        m_ro = au.load_anchor().mode
        check("V-AUTH-MODE-WITNESS-REQUIRED",
              m_nowit.mode == au.UNPROTECTED and "WITNESS_UNSET" in m_nowit.detail
              and m_rwwit.mode == au.UNPROTECTED and "WITNESS_WRITABLE" in m_rwwit.detail
              and m_ro == au.ENFORCED,
              "a protected anchor with no witness, or a writable one, is UNPROTECTED and says "
              f"so; control: a protected witness -> {m_ro}",
              f"nowit={m_nowit.mode}/{m_nowit.detail} rwwit={m_rwwit.mode}/{m_rwwit.detail} "
              f"ro={m_ro}")
        lg_enf = gl.GoalLog(REPO_ID, "g-enforced", base=base)
        refused = False
        try:
            gc.declare(lg_enf, "enforced without key", ["x"], [], {})
        except au.SigningKeyUnavailable:
            refused = True
        # The gap this closes: a read-only FILE in a writable DIRECTORY is replaceable.
        os.chmod(rodir, stat.S_IRWXU)
        m_dir = au.load_anchor().mode
        os.chmod(ro, stat.S_IRUSR | stat.S_IWUSR)
        m_rw = au.load_anchor().mode
        check("V-AUTH-MODE-ENFORCED",
              not writable_ro and m_ro == au.ENFORCED and refused and event_count(lg_enf) == 0,
              f"read-only anchor in a read-only dir -> {m_ro}, founder write without key "
              "refused and nothing written",
              f"ro={m_ro} refused={refused} written={event_count(lg_enf)} writable={writable_ro}")
        check("V-AUTH-MODE-WRITABLE-DIR-IS-UNPROTECTED",
              m_dir == au.UNPROTECTED and m_rw == au.UNPROTECTED,
              f"read-only file in a writable dir -> {m_dir}; writable file -> {m_rw}",
              f"dir={m_dir} file={m_rw}")
        set_env(anchor)

    # --- append: no key, wrong key, judge key -> raises, writes nothing ------------------
    lg_nokey = gl.GoalLog(REPO_ID, "g-nokey", base=base)
    outcomes = {}
    for label, key in (("no-key", None), ("stranger", xk), ("judge", jk)):
        set_env(anchor, founder=key)
        try:
            gc.declare(lg_nokey, "no key", ["x"], [], {})
            outcomes[label] = "WRITTEN"
        except au.SigningKeyUnavailable:
            outcomes[label] = "raised"
    check("V-AUTH-APPEND-WITHOUT-KEY-RAISES",
          set(outcomes.values()) == {"raised"} and event_count(lg_nokey) == 0,
          f"founder write under {au.load_anchor().mode} without a usable founder key raises "
          f"SigningKeyUnavailable and writes nothing ({outcomes})",
          f"{outcomes}, events on disk={event_count(lg_nokey)}")

    set_env(anchor, founder=fk)
    lg_signed = gl.GoalLog(REPO_ID, "g-signed", base=base)
    gc.declare(lg_signed, "signed goal", ["x"], [], {"paths": ["."]})
    st_signed = gc.project(lg_signed)
    blk = st_signed.events[0].data.get(au.SIG_FIELD) or {}
    check("V-AUTH-SIGNED-FOUNDER-ACCEPTED",
          blk.get("key_id") == f_id and au.is_governed(st_signed),
          f"control: with the founder key the declaration is signed by {f_id} and projects "
          "as governed", f"block={blk} governed={au.is_governed(st_signed)}")

    set_env(anchor)                                   # the founder key is gone
    cv.set_plane(lg_signed, gc.project(lg_signed), cv.PLANES[0], True, "", "resident")
    ev2 = gc.project(lg_signed).events[-1]
    check("V-AUTH-NON-FOUNDER-NEEDS-NO-SIGNATURE",
          ev2.type not in au.FOUNDER_CLASS and au.SIG_FIELD not in ev2.data,
          f"a {ev2.type} event is written and projects without any signing key",
          f"{ev2.type} {ev2.data}")

    set_env(anchor, founder=fk)
    check("V-AUTH-KEY-ID-IS-PUBLIC-HASH",
          f_id == au.key_id_of(fpriv.public_key().public_bytes(
              serialization.Encoding.Raw, serialization.PublicFormat.Raw))
          and x_id != f_id and x_id == au.key_id_of(xpriv.public_key().public_bytes(
              serialization.Encoding.Raw, serialization.PublicFormat.Raw)),
          "the key_id is sha256 of the PUBLIC key bytes; control: a different key has a "
          "different id", "key_id is not the public hash")

    # --- unsigned founder event after adoption -----------------------------------------
    set_env()
    lg_adopt = gl.GoalLog(REPO_ID, "g-adopt", base=base)
    gc.declare(lg_adopt, "legacy then adopted", ["x"], [], {"paths": ["."]})
    gc.set_budget(lg_adopt, 2, {"epochs": 3}, "owner")
    set_env(anchor, founder=fk)
    legacy_ok = corrupt_reason(lg_adopt) == "" and not au.is_governed(gc.project(lg_adopt))
    adopt_reviewed(lg_adopt)
    governed = au.is_governed(gc.project(lg_adopt))
    raw_append(lg_adopt, gc.BUDGET_SET, {"epochs": 999})
    why = corrupt_reason(lg_adopt)
    check("V-AUTH-UNSIGNED-AFTER-ADOPTION-REFUSED",
          legacy_ok and governed and au.FOUNDER_SIGNATURE_INVALID in why and "seq 4" in why,
          f"legacy unsigned events project (control), adoption governs, and an unsigned "
          f"founder event written past the API is refused: {why[:90]}",
          f"legacy_ok={legacy_ok} governed={governed} why={why!r}")

    # --- forged / wrong key / judge key, each paired with a real-key control -----------
    def governed_goal(gid: str) -> gl.GoalLog:
        set_env(anchor, founder=fk)
        lg = gl.GoalLog(REPO_ID, gid, base=base)
        gc.declare(lg, gid, ["x"], [], {"paths": ["."]})
        return lg

    lg_ctl = governed_goal("g-manual-control")
    raw_append(lg_ctl, gc.BUDGET_SET, forged_data(lg_ctl, gc.BUDGET_SET, {"epochs": 1}, fpriv, f_id))
    check("V-AUTH-MANUAL-SIGN-CONTROL", corrupt_reason(lg_ctl) == "",
          "control: an event signed past the API with the REAL founder key is accepted, so "
          "the refusals below are about the key, not the helper", corrupt_reason(lg_ctl))

    lg_forge = governed_goal("g-forged")
    d = forged_data(lg_forge, gc.BUDGET_SET, {"epochs": 1}, fpriv, f_id)
    d[au.SIG_FIELD]["sig"] = base64.b64encode(b"\x01" * 64).decode()
    raw_append(lg_forge, gc.BUDGET_SET, d)
    why = corrupt_reason(lg_forge)
    check("V-AUTH-FORGED-SIGNATURE-REFUSED",
          au.FOUNDER_SIGNATURE_INVALID in why and au.BAD_SIGNATURE in why,
          f"a forged signature under the founder's key_id is refused: {why[:80]}", repr(why))

    lg_wrong = governed_goal("g-wrong-key")
    raw_append(lg_wrong, gc.BUDGET_SET,
               forged_data(lg_wrong, gc.BUDGET_SET, {"epochs": 1}, xpriv, x_id))
    why = corrupt_reason(lg_wrong)
    check("V-AUTH-WRONG-KEY-REFUSED", au.FOUNDER_SIGNATURE_INVALID in why and au.UNKNOWN_KEY in why,
          f"a valid signature by a key the anchor does not hold is refused: {why[:80]}", repr(why))

    lg_judge = governed_goal("g-judge-key")
    raw_append(lg_judge, gc.BUDGET_SET,
               forged_data(lg_judge, gc.BUDGET_SET, {"epochs": 1}, jpriv, j_id))
    why = corrupt_reason(lg_judge)
    check("V-AUTH-JUDGE-KEY-ON-FOUNDER-REFUSED",
          au.FOUNDER_SIGNATURE_INVALID in why and au.WRONG_ROLE in why,
          f"a judge-role signature on a founder event is refused: {why[:80]}", repr(why))

    # --- history rewrite before the signed event -----------------------------------------
    def adopted_legacy(gid: str) -> gl.GoalLog:
        set_env()
        lg = gl.GoalLog(REPO_ID, gid, base=base)
        gc.declare(lg, "the original intent", ["x"], [], {"paths": ["."]})
        gc.set_budget(lg, 2, {"epochs": 3}, "owner")
        set_env(anchor, founder=fk)
        adopt_reviewed(lg)
        return lg

    def edit_intent(raws):
        raws[0]["data"]["semantic"]["intent"] = "a rewritten intent"

    lg_rw_ctl = adopted_legacy("g-rewrite-control")
    lg_rechain = adopted_legacy("g-rewrite-rechained")
    rewrite(lg_rechain, edit_intent, rechain=True)
    lg_nochain = adopted_legacy("g-rewrite-unchained")
    rewrite(lg_nochain, edit_intent, rechain=False)
    why_re, why_no = corrupt_reason(lg_rechain), corrupt_reason(lg_nochain)
    check("V-AUTH-HISTORY-REWRITE-DETECTED",
          corrupt_reason(lg_rw_ctl) == "" and au.FOUNDER_SIGNATURE_INVALID in why_re
          and "seq 3" in why_re and "digest" in why_no,
          "rewriting history before the adoption is caught: re-chained -> the adoption's "
          f"signature fails ({why_re[:60]}); not re-chained -> the chain fails; control: the "
          "untouched copy projects", f"control={corrupt_reason(lg_rw_ctl)!r} re={why_re!r} "
          f"no={why_no!r}")

    lg_strip = adopted_legacy("g-rewrite-stripped")

    def edit_and_strip(raws):
        edit_intent(raws)
        raws[2]["data"].pop(au.SIG_FIELD, None)
    rewrite(lg_strip, edit_and_strip, rechain=True)
    st_strip = gc.project(lg_strip)
    check("V-AUTH-STRIPPED-REWRITE-IS-UNGOVERNED",
          not au.is_governed(st_strip) and "adopt" in sw.governance_refusal(st_strip),
          "a rewrite that also strips the signature projects, but only as an UNGOVERNED goal "
          "the resident refuses -- a downgrade, never a silent pass",
          f"governed={au.is_governed(st_strip)} refusal={sw.governance_refusal(st_strip)!r}")

    # --- the licence ------------------------------------------------------------------
    rec = sw.record_path()
    rec.parent.mkdir(parents=True, exist_ok=True)
    green = {"head": gs.head(ROOT), "ts": "t", "green": True,
             "suites": {s: {"ok": True, "detail": "x"} for s in sw.REQUIRED_SUITES}}

    set_env()
    rec.write_text(json.dumps(green), encoding="utf-8")
    allowed, why_abs = sw.autonomy_verdict(ROOT)
    check("V-AUTH-LICENCE-ABSENT-UNCHANGED", allowed,
          "in ABSENT an unsigned green record is still a licence (today's behaviour)", why_abs)

    set_env(anchor)
    allowed, why = sw.autonomy_verdict(ROOT)
    check("V-AUTH-LICENCE-UNSIGNED-REFUSED",
          not allowed and "not signed by the judge" in why,
          f"under {au.load_anchor().mode} an unsigned record is refused: {why}", why)

    set_env(anchor, judge=jk)
    signed = au.sign_licence(green, au.load_anchor())
    set_env(anchor)
    rec.write_text(json.dumps(signed), encoding="utf-8")
    allowed, why = sw.autonomy_verdict(ROOT)
    check("V-AUTH-LICENCE-JUDGE-SIGNED-ACCEPTED", allowed,
          f"control: a judge-signed record is a licence ({why})", why)

    tampered = dict(signed, head="0" * 40)
    rec.write_text(json.dumps(tampered), encoding="utf-8")
    allowed_t, why_t = sw.autonomy_verdict(ROOT)
    body = {k: v for k, v in green.items()}
    fsig = fpriv.sign(gl._canonical(body))
    rec.write_text(json.dumps({**body, au.LICENCE_SIG_FIELD: {
        "key_id": f_id, "sig": base64.b64encode(fsig).decode()}}), encoding="utf-8")
    allowed_f, why_f = sw.autonomy_verdict(ROOT)
    check("V-AUTH-LICENCE-FOUNDER-SIGNED-REFUSED",
          not allowed_f and au.WRONG_ROLE in why_f and not allowed_t and au.BAD_SIGNATURE in why_t,
          f"a founder-signed record is refused ({why_f}); an edited judge-signed one too "
          f"({why_t})", f"founder={why_f!r} tampered={why_t!r}")

    rec.unlink()
    set_env(anchor)                                     # no judge key
    raised = False
    try:
        sw.record_gates(ROOT)
    except au.SigningKeyUnavailable:
        raised = True
    check("V-AUTH-RECORD-GATES-NEEDS-JUDGE-KEY", raised and not rec.exists(),
          "record-gates under an anchor without the judge key refuses BEFORE running the "
          "suites and writes no record", f"raised={raised} written={rec.exists()}")

    set_env(bad_anchor, founder=fk)
    rec.write_text(json.dumps(signed), encoding="utf-8")
    allowed_u, why_u = sw.autonomy_verdict(ROOT)
    lg_unv = gl.GoalLog(REPO_ID, "g-unverifiable", base=base)
    unv_raised = False
    try:
        gc.declare(lg_unv, "unverifiable", ["x"], [], {})
    except au.AuthorityUnverifiable:
        unv_raised = True
    check("V-AUTH-UNVERIFIABLE-REFUSES",
          not allowed_u and "UNVERIFIABLE" in why_u and unv_raised and event_count(lg_unv) == 0,
          "an unusable anchor refuses the licence and every founder write -- never a pass",
          f"licence={why_u!r} write_raised={unv_raised}")

    # --- the sweep refuses ungoverned goals, and admits them after adopt ------------------
    repo = make_repo()
    set_env()
    lg_sw = sweepable_goal(base, "g-sweep", repo)
    rec.write_text(json.dumps(green), encoding="utf-8")
    rep_abs = sw.sweep(ROOT, [(lg_sw, repo)], dry_run=True)
    set_env(anchor)
    rec.write_text(json.dumps(signed), encoding="utf-8")
    rep = sw.sweep(ROOT, [(lg_sw, repo)], dry_run=True)
    direct = sw.sweep_goal(lg_sw, repo, dry_run=True)
    check("V-AUTH-SWEEP-REFUSES-UNGOVERNED",
          not rep.refused and any("g-sweep" in s and "adopt" in s for s in rep.skipped)
          and not rep.acted and direct and "REFUSED" in direct[0] and "adopt" in direct[0]
          and any("would run" in x for x in rep_abs.acted),
          f"an ungoverned goal is refused by the sweep and by the direct driver, naming "
          f"`adopt` ({rep.skipped[0][:80] if rep.skipped else ''}); control: ABSENT plans work",
          f"acted={rep.acted} skipped={rep.skipped} direct={direct} absent={rep_abs.acted}")

    set_env(anchor, founder=fk)
    adopt_reviewed(lg_sw)
    set_env(anchor)
    rep = sw.sweep(ROOT, [(lg_sw, repo)], dry_run=True)
    check("V-AUTH-SWEEP-ADMITS-AFTER-ADOPT",
          not rep.skipped and any("would run" in x for x in rep.acted),
          f"after a signed adoption the same goal is admitted ({rep.acted})",
          f"acted={rep.acted} skipped={rep.skipped}")

    # --- CLI: keygen prints no secret; adopt refuses without an anchor --------------------
    import importlib.util
    spec = importlib.util.spec_from_file_location("gsd_x_goal_cli", ROOT / "tools" / "gsd_x_goal.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    out_key = tmp / "cli_keys" / "judge2.pem"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_kg = cli.main(["founder-keygen", "--out", str(out_key), "--role", "judge"])
    printed = buf.getvalue()
    secret_lines = [ln for ln in out_key.read_text(encoding="utf-8").splitlines()
                    if ln and not ln.startswith("-----")]
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        rc_again = cli.main(["founder-keygen", "--out", str(out_key), "--role", "judge"])
    perm_ok = True if os.name == "nt" else (os.stat(out_key).st_mode & 0o777) == 0o600
    entry = json.loads(printed.strip().splitlines()[-1]) if rc_kg == 0 else {}
    check("V-AUTH-KEYGEN-NO-SECRET-PRINTED",
          rc_kg == 0 and "PRIVATE" not in printed and not any(s in printed for s in secret_lines)
          and list(entry.values())[0]["role"] == "judge" and rc_again == 2 and perm_ok,
          f"keygen prints only the public entry; the PEM is written {'0600' if os.name != 'nt' else '(ACL not judged on Windows)'} "
          "and an existing key is never overwritten (exit 2)",
          f"rc={rc_kg} again={rc_again} perm_ok={perm_ok} printed={printed!r}")

    cli_repo = make_repo()
    set_env()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli.main(["declare", "--goal", "g-cli", "--root", str(cli_repo), "--intent", "cli goal"])
        rc_abs = cli.main(["adopt", "--goal", "g-cli", "--root", str(cli_repo)])
    set_env(anchor, founder=fk)
    lg_cli = gl.GoalLog(gl.repo_id(cli_repo), "g-cli")
    d0, n0 = gc.project(lg_cli).events[-1].digest, event_count(lg_cli)
    review = io.StringIO()
    with contextlib.redirect_stdout(review):
        rc_rev = cli.main(["adopt", "--goal", "g-cli", "--root", str(cli_repo)])
    n_after_review = event_count(lg_cli)
    # History planted AFTER the review: the reviewed digest must no longer sign.
    raw_append(lg_cli, gc.BUDGET_SET, {"epochs": 999})
    with contextlib.redirect_stdout(buf):
        rc_stale = cli.main(["adopt", "--goal", "g-cli", "--root", str(cli_repo),
                             "--attest-digest", d0])
    n_after_stale = event_count(lg_cli)
    review2 = io.StringIO()
    with contextlib.redirect_stdout(review2):
        cli.main(["adopt", "--goal", "g-cli", "--root", str(cli_repo)])
    d1 = gc.project(lg_cli).events[-1].digest
    with contextlib.redirect_stdout(buf):
        rc_ad = cli.main(["adopt", "--goal", "g-cli", "--root", str(cli_repo),
                          "--attest-digest", d1])
        rc_twice = cli.main(["adopt", "--goal", "g-cli", "--root", str(cli_repo),
                             "--attest-digest", gc.project(lg_cli).events[-1].digest])
    st_cli = gc.project(lg_cli)
    rv = review.getvalue()
    check("V-AUTH-CLI-ADOPT",
          rc_abs == 2 and rc_ad == 0 and rc_twice == 2 and au.is_governed(st_cli)
          and st_cli.events[-1].type == gc.ADOPTED
          and st_cli.events[-1].data.get("attests_digest") == d1,
          "`adopt --attest-digest <reviewed digest>` governs a legacy goal (exit 0); refused "
          "without an anchor and when already governed (exit 2)",
          f"absent={rc_abs} adopt={rc_ad} twice={rc_twice} out={buf.getvalue()[-300:]!r}")
    check("V-AUTH-ADOPT-REVIEW-BEFORE-SIGN",
          rc_rev == 2 and n_after_review == n0 and gc.DECLARED in rv and d0 in rv
          and "--attest-digest" in rv and "autonomous=" in rv and "budget=" in rv
          and rc_stale == 2 and n_after_stale == n0 + 1 and '"epochs":999' in review2.getvalue(),
          "without --attest-digest adopt lists the founder-class events and resulting state, "
          "prints the digest and signs nothing (exit 2); a digest reviewed before history was "
          "planted is refused and signs nothing; control: the current digest adopts",
          f"rev={rc_rev} written_on_review={n_after_review - n0} stale={rc_stale} "
          f"written_on_stale={n_after_stale - n0 - 1} review={rv[-400:]!r}")

    lg_lib = gl.GoalLog(REPO_ID, "g-adopt-lib", base=base)
    set_env()
    gc.declare(lg_lib, "library adopt", ["x"], [], {"paths": ["."]})
    set_env(anchor, founder=fk)
    lib_refused = False
    try:
        gc.adopt(lg_lib, "owner", "")
    except gl.GoalLogError as exc:
        lib_refused = "history changed since review" in str(exc)
    lib_n = event_count(lg_lib)
    adopt_reviewed(lg_lib)
    check("V-AUTH-ADOPT-LIBRARY-NEEDS-ATTEST",
          lib_refused and lib_n == 1 and au.is_governed(gc.project(lg_lib)),
          "the library adopt refuses an empty attestation and writes nothing; control: the "
          "reviewed digest adopts", f"refused={lib_refused} n={lib_n}")

    # --- the witness: a truncated log is a rolled-back founder ---------------------------
    wit = tmp / "witness"

    def autonomy_goal(gid: str) -> gl.GoalLog:
        set_env(anchor, founder=fk, witness=wit)
        lg = gl.GoalLog(REPO_ID, gid, base=base)
        gc.declare(lg, gid, ["x"], [], {"paths": ["."]})
        sw.set_autonomous(lg, gc.project(lg), True, "go", "owner")
        sw.set_autonomous(lg, gc.project(lg), False, "the founder stops it", "owner")
        return lg

    lg_rb_ctl = autonomy_goal("g-rollback-control")
    lg_rb = autonomy_goal("g-rollback")
    (lg_rb.dir / "000003.json").unlink()                # delete the founder's disable
    set_env(anchor, witness=wit)
    why_rb = corrupt_reason(lg_rb)
    ctl_ok = corrupt_reason(lg_rb_ctl) == "" and not sw.is_autonomous(gc.project(lg_rb_ctl))
    set_env(anchor)                                     # the same attack, no witness
    blind = corrupt_reason(lg_rb) == "" and sw.is_autonomous(gc.project(lg_rb))
    set_env(anchor, founder=fk, witness=wit)
    sign_refused = False
    try:
        gc.set_budget(lg_rb, 3, {"epochs": 1}, "owner")
    except gl.GoalLogCorrupt as exc:
        sign_refused = au.FOUNDER_ROLLBACK in str(exc)
    check("V-AUTH-FOUNDER-ROLLBACK-REFUSED",
          au.FOUNDER_ROLLBACK in why_rb and ctl_ok and blind and sign_refused
          and event_count(lg_rb) == 2,
          f"deleting a later signed disable is refused ({why_rb[:80]}); the founder cannot sign "
          "atop the truncated log either; control: the untouched copy projects, disabled; "
          "without a witness the same truncation re-enables autonomy silently",
          f"why={why_rb!r} control={ctl_ok} blind={blind} sign_refused={sign_refused} "
          f"n={event_count(lg_rb)}")

    set_env(anchor, founder=fk)                         # signed, never witnessed
    lg_unw = gl.GoalLog(REPO_ID, "g-unwitnessed", base=base)
    gc.declare(lg_unw, "never witnessed", ["x"], [], {"paths": ["."]})
    set_env()
    lg_leg = gl.GoalLog(REPO_ID, "g-legacy-witness", base=base)
    gc.declare(lg_leg, "legacy, ungoverned", ["x"], [], {"paths": ["."]})
    set_env(anchor, witness=wit)
    why_unw = corrupt_reason(lg_unw)
    check("V-AUTH-FOUNDER-WITNESS-MISSING",
          au.FOUNDER_WITNESS_MISSING in why_unw and corrupt_reason(lg_rb_ctl) == ""
          and corrupt_reason(lg_leg) == "",
          f"a governed goal with no witness file is refused ({why_unw[:70]}); control: a "
          "witnessed goal projects, and an ungoverned legacy goal needs no witness",
          f"why={why_unw!r} ctl={corrupt_reason(lg_rb_ctl)!r} leg={corrupt_reason(lg_leg)!r}")

    # --- witness modes: the writer's umask must not decide who can write the mark ------
    # GEX44 2026-09-25: the relay runs under umask 0007; the judge's mark was
    # unreadable to the resident, and inheriting 0007 would make it group-writable.
    if os.name == "nt":
        unjudge("V-AUTH-WITNESS-MODES", "POSIX modes are not judged on Windows")
        unjudge("V-AUTH-WITNESS-UNREADABLE-NAMED", "POSIX modes are not judged on Windows")
    else:
        wit_m = tmp / "witness-modes"
        old_mask = os.umask(0o007)
        try:
            set_env(anchor, founder=fk, witness=wit_m)
            lg_m = gl.GoalLog(REPO_ID, "g-witness-modes", base=base)
            gc.declare(lg_m, "witness modes", ["x"], [], {"paths": ["."]})
        finally:
            os.umask(old_mask)
        mark_file = wit_m / REPO_ID / "g-witness-modes.json"
        f_mode = os.stat(mark_file).st_mode & 0o7777
        d_mode = os.stat(mark_file.parent).st_mode & 0o7777
        check("V-AUTH-WITNESS-MODES",
              f_mode == au.WITNESS_FILE_MODE and d_mode == au.WITNESS_DIR_MODE,
              f"under umask 0007 the mark is {oct(f_mode)} in a {oct(d_mode)} dir: readers in the "
              "group read it, only the writer writes it",
              f"file={oct(f_mode)} dir={oct(d_mode)}")
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            unjudge("V-AUTH-WITNESS-UNREADABLE-NAMED", "root reads through mode 000")
        else:
            set_env(anchor, witness=wit_m)
            ctl_named = corrupt_reason(lg_m)
            os.chmod(mark_file, 0)
            try:
                try:
                    gc.project(lg_m)
                    why_ur = ""
                except Exception as exc:                # the class is the point of the gate
                    why_ur = f"{exc.__class__.__name__}: {exc}"
            finally:
                os.chmod(mark_file, au.WITNESS_FILE_MODE)
            check("V-AUTH-WITNESS-UNREADABLE-NAMED",
                  why_ur.startswith("GoalLogCorrupt") and au.FOUNDER_WITNESS_UNREADABLE in why_ur
                  and ctl_named == "",
                  f"an unreadable mark is a named refusal ({why_ur[:70]}), never a crash; "
                  "control: the readable mark projects", f"why={why_ur!r} control={ctl_named!r}")

    # --- ts and actor are signed ------------------------------------------------------
    lg_ts_ctl = governed_goal("g-ts-control")
    lg_ts = governed_goal("g-ts-tamper")
    lg_ac = governed_goal("g-actor-tamper")
    rewrite(lg_ts, lambda raws: raws[0].__setitem__("ts", "2020-01-01T00:00:00+00:00"),
            rechain=True)
    rewrite(lg_ac, lambda raws: raws[0].__setitem__("actor", "resident"), rechain=True)
    why_ts, why_ac = corrupt_reason(lg_ts), corrupt_reason(lg_ac)
    check("V-AUTH-SIGNED-TS-ACTOR",
          au.BAD_SIGNATURE in why_ts and au.BAD_SIGNATURE in why_ac
          and corrupt_reason(lg_ts_ctl) == "",
          "editing a signed event's ts or actor (re-chained) breaks its signature; control: "
          "the untouched copy projects", f"ts={why_ts!r} actor={why_ac!r} "
          f"ctl={corrupt_reason(lg_ts_ctl)!r}")

    # --- the licence: empty head, replay --------------------------------------------------
    set_env(anchor, judge=jk)
    blank = au.sign_licence(dict(green, head=""), au.load_anchor())
    set_env(anchor)
    rec.write_text(json.dumps(blank), encoding="utf-8")
    ok_blank, why_blank = sw.autonomy_verdict(ROOT)
    rec.write_text(json.dumps(signed), encoding="utf-8")
    ok_notree, why_notree = sw.autonomy_verdict(tmp)            # not a repository: no head
    ok_real, why_real = sw.autonomy_verdict(ROOT)
    check("V-AUTH-LICENCE-EMPTY-HEAD-REFUSED",
          not ok_blank and "unknown head" in why_blank and not ok_notree
          and "unknown head" in why_notree and ok_real,
          "a licence with no head, or a tree with none, is refused; control: the real head "
          f"on both sides is a licence ({why_real})",
          f"blank={why_blank!r} notree={why_notree!r} real={why_real!r}")

    lic_repo = make_repo()
    wit_l = tmp / "witness_licence"
    set_env(anchor, judge=jk, witness=wit_l)
    r1 = sw.record_gates(lic_repo)            # no suites there: fast, and not green
    r2 = sw.record_gates(lic_repo)
    head_l = gs.head(lic_repo)
    w_now = au.read_licence_witness(au.load_anchor())
    set_env(anchor, witness=wit_l)
    _ok_cur, why_cur = sw.autonomy_verdict(lic_repo)
    rec.write_text(json.dumps(r1), encoding="utf-8")            # replay the older licence
    ok_old, why_old = sw.autonomy_verdict(lic_repo)
    set_env(anchor, judge=jk, witness=wit_l)
    lic3 = au.sign_licence({"head": head_l, "ts": "t", "green": True, "licence_seq": 3,
                            "suites": {s: {"ok": True, "detail": "x"} for s in sw.REQUIRED_SUITES}},
                           au.load_anchor())
    au.witness_licence(au.load_anchor(), 3, head_l)
    set_env(anchor, witness=wit_l)
    rec.write_text(json.dumps(lic3), encoding="utf-8")
    ok_cur3, why_cur3 = sw.autonomy_verdict(lic_repo)
    set_env(anchor, witness=tmp / "witness_empty")
    ok_unw, why_unw_l = sw.autonomy_verdict(lic_repo)
    check("V-AUTH-LICENCE-REPLAY-REFUSED",
          r2.get("licence_seq") == r1.get("licence_seq", -9) + 1
          and w_now == {"licence_seq": r2.get("licence_seq"), "head": head_l}
          and "not green" in why_cur and not ok_old and au.LICENCE_STALE in why_old
          and ok_cur3 and not ok_unw and au.LICENCE_UNWITNESSED in why_unw_l,
          "record-gates advances a witnessed licence_seq; an older signed licence restored over "
          f"it is refused ({why_old[:60]}); an unwitnessed one too; control: the witnessed "
          f"licence is accepted ({why_cur3})",
          f"r1={r1.get('licence_seq')} r2={r2.get('licence_seq')} w={w_now} cur={why_cur!r} "
          f"old={why_old!r} cur3={why_cur3!r} unw={why_unw_l!r}")

    set_env()
    total = len(passes) + len(fails)
    print(f"\nGSDX_GOAL_AUTHORITY_PASS={len(passes)}/{total}  threshold={total}/{total}"
          f"  unjudged={len(unjudged)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
