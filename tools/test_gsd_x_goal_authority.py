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
AUTH_ENV = (au.ENV_ANCHOR, au.ENV_FOUNDER_KEY, au.ENV_JUDGE_KEY)


def set_env(anchor=None, founder=None, judge=None) -> None:
    for name, value in zip(AUTH_ENV, (anchor, founder, judge)):
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = str(value)


def load_priv(path: Path):
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def raw_append(lg: gl.GoalLog, type_: str, data: dict) -> None:
    """Write an event WITHOUT the API -- what a principal with store access can do."""
    events = lg.read()
    body = {"seq": len(events) + 1, "type": type_,
            "ts": datetime.now(timezone.utc).isoformat(), "actor": "founder",
            "data": data, "prev_digest": events[-1].digest if events else gl.GENESIS}
    body["digest"] = gl.event_digest(body)
    lg.publish(body)


def forged_data(lg: gl.GoalLog, type_: str, data: dict, key, kid: str) -> dict:
    events = lg.read()
    seq, prev = len(events) + 1, events[-1].digest
    sig = key.sign(au.event_message(lg.repo, lg.goal_id, seq, type_, data, prev))
    return {**data, au.SIG_FIELD: {"key_id": kid, "sig": base64.b64encode(sig).decode()}}


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
    if os.name == "nt":
        unjudge("V-AUTH-MODE-ENFORCED", "Windows host: os.access is not an ACL boundary; "
                "judged on GEX44")
    elif hasattr(os, "geteuid") and os.geteuid() == 0:
        unjudge("V-AUTH-MODE-ENFORCED", "running as root: every file is writable, the "
                "permission drill cannot fail; judged as a non-root user")
    else:
        rodir = tmp / "anchor_dir"
        rodir.mkdir()
        ro = rodir / "ro_anchor.json"
        ro.write_text(anchor.read_text(encoding="utf-8"), encoding="utf-8")
        r_only = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
        os.chmod(ro, r_only)
        os.chmod(rodir, r_only | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        set_env(ro)
        writable_ro = os.access(ro, os.W_OK) or os.access(rodir, os.W_OK)
        m_ro = au.load_anchor().mode
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
    gc.adopt(lg_adopt, "owner")
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
        gc.adopt(lg, "owner")
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
    gc.adopt(lg_sw, "owner")
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
    with contextlib.redirect_stdout(buf):
        rc_ad = cli.main(["adopt", "--goal", "g-cli", "--root", str(cli_repo)])
        rc_twice = cli.main(["adopt", "--goal", "g-cli", "--root", str(cli_repo)])
    st_cli = gc.project(gl.GoalLog(gl.repo_id(cli_repo), "g-cli"))
    check("V-AUTH-CLI-ADOPT",
          rc_abs == 2 and rc_ad == 0 and rc_twice == 2 and au.is_governed(st_cli)
          and st_cli.events[-1].type == gc.ADOPTED,
          "`adopt` governs a legacy goal (exit 0); refused without an anchor and when already "
          "governed (exit 2)", f"absent={rc_abs} adopt={rc_ad} twice={rc_twice} "
          f"out={buf.getvalue()[-300:]!r}")

    set_env()
    total = len(passes) + len(fails)
    print(f"\nGSDX_GOAL_AUTHORITY_PASS={len(passes)}/{total}  threshold={total}/{total}"
          f"  unjudged={len(unjudged)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
