#!/usr/bin/env python3
"""V-gates for the founder-decision relay (spec: vault/specs/gdd-founder-authority.md §10).

Two hosts are simulated in one process by switching the environment: the
WORKSTATION holds the founder signing key and a copy of the public anchor and no
witness; the STORE HOST (GEX44, as factory-judge) holds the anchor and the
witness and NO signing key. Every refusal is paired with a control in which the
same path, given an honest envelope, is admitted -- a relay that refused
everything would otherwise pass every refusal here.

Cross-user behaviour (resident `factory` and relay `factory-judge` appending to
one store) needs two real POSIX users: it prints UNJUDGED here, never PASS, and
is judged on GEX44.

    python tools/test_gsd_x_goal_relay.py
"""
from __future__ import annotations

import base64
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryptography.hazmat.primitives import serialization          # noqa: E402

from modules.gsd_x.goal import authority as au      # noqa: E402
from modules.gsd_x.goal import contract as gc       # noqa: E402
from modules.gsd_x.goal import log as gl            # noqa: E402
from modules.gsd_x.goal import relay as rl          # noqa: E402

REPO_ID = "b8" * 20
AUTH_ENV = (au.ENV_ANCHOR, au.ENV_FOUNDER_KEY, au.ENV_JUDGE_KEY, au.ENV_WITNESS)


def set_env(anchor=None, founder=None, judge=None, witness=None) -> None:
    for name, value in zip(AUTH_ENV, (anchor, founder, judge, witness)):
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = str(value)


def load_priv(path: Path):
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def count(lg: gl.GoalLog) -> int:
    return len([p for p in lg.dir.iterdir() if gl.EVENT_RE.match(p.name)]) if lg.dir.is_dir() else 0


def mark(wit: Path, lg: gl.GoalLog):
    p = wit / lg.repo / f"{lg.goal_id}.json"
    return json.loads(p.read_text(encoding="utf-8")).get("seq") if p.is_file() else None


def bare(d: dict) -> dict:
    """A projected budget/authority without its signature block (projection keeps
    the whole event data, `_founder` included -- a slice-1 behaviour, not ours)."""
    return {k: v for k, v in (d or {}).items() if k != au.SIG_FIELD}


def declared_data(intent: str) -> dict:
    sem = gc.normalise(intent, ["it works"], [], {"paths": ["."]})
    return {"semantic": sem, "revision": gc.revision_of(sem)}


def forge(env: dict, key, kid: str, **changes) -> dict:
    """An envelope for ``env``'s fields (with ``changes``) signed by ``key``."""
    e = {**env, **changes}
    msg = au.event_message(e["repo"], e["goal"], e["seq"], e["type"], e["data"],
                           e["prev_digest"], e["ts"], e["actor"])
    return {**e, "key_id": kid, "sig": base64.b64encode(key.sign(msg)).decode("ascii")}


def refusal(fn, *args, **kw) -> tuple[str, str]:
    """(reason, message) of a refusal, ('', '') when it did not refuse.

    An EnvelopeRefused answers its named reason; any other goal-log refusal
    answers its class name, so a check that moved to another layer shows up as
    a different reason instead of crashing the suite."""
    try:
        fn(*args, **kw)
    except rl.EnvelopeRefused as exc:
        return exc.reason, str(exc)
    except gl.GoalLogError as exc:
        return exc.__class__.__name__, str(exc)
    return "", ""


def load_cli():
    spec = importlib.util.spec_from_file_location("gsd_x_goal_cli", ROOT / "tools" / "gsd_x_goal.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []
    unjudged: list[str] = []

    def check(g, cond, ev, why):
        (passes if cond else fails).append(g)
        print(f"  {'PASS' if cond else 'FAIL'} {g}: {ev if cond else why}")

    def unjudge(g, why):
        unjudged.append(g)
        print(f"  UNJUDGED {g}: {why}")

    set_env()
    tmp = Path(tempfile.mkdtemp(prefix="gsdx_relay_"))
    base = tmp / "goals"
    base.mkdir()
    os.environ["GSDX_GOALS_ROOT"] = str(base)
    wit = tmp / "witness"
    wit.mkdir()
    keys = tmp / "keys"
    fk, jk, xk = keys / "founder.pem", keys / "judge.pem", keys / "stranger.pem"
    f_id, f_entry = au.generate_keypair(fk, au.FOUNDER)
    j_id, j_entry = au.generate_keypair(jk, au.JUDGE)
    x_id, _ = au.generate_keypair(xk, au.FOUNDER)            # never in the anchor
    anchor = tmp / "anchor.json"
    anchor.write_text(json.dumps({**f_entry, **j_entry}), encoding="utf-8")
    jpriv, xpriv = load_priv(jk), load_priv(xk)

    def workstation():
        set_env(anchor, founder=fk)

    def store_host():
        set_env(anchor, witness=wit)

    def sign(lg, type_, data, actor="owner"):
        store_host()
        h = rl.head(lg)
        workstation()
        env = rl.make_envelope(h["repo"], h["goal"], h["seq"], h["digest"], type_, data, actor)
        store_host()
        return env

    # --- head: read-only ----------------------------------------------------------
    lg = gl.GoalLog(REPO_ID, "g-relay")
    store_host()
    h0 = rl.head(lg)
    check("V-RELAY-HEAD-EMPTY", h0["seq"] == 0 and h0["digest"] == gl.GENESIS and not lg.dir.exists(),
          "an empty goal's head is seq 0 / GENESIS and reading it created nothing",
          f"{h0} dir_exists={lg.dir.exists()}")

    # --- a declaration relayed onto an empty goal -----------------------------------
    env1 = sign(lg, gc.DECLARED, declared_data("relay goal"))
    ev1 = rl.apply_envelope(env1)
    st = gc.project(lg)
    check("V-RELAY-DECLARE-ROUNDTRIP",
          ev1.seq == 1 and st.intent == "relay goal" and au.is_governed(st)
          and mark(wit, lg) == 1,
          "head -> sign -> apply declared the goal: governed, witnessed at seq 1",
          f"seq={ev1.seq} intent={st.intent!r} governed={au.is_governed(st)} mark={mark(wit, lg)}")

    snapshot = sorted((p.name, p.stat().st_mtime_ns) for p in lg.dir.iterdir())
    h1 = rl.head(lg)
    check("V-RELAY-HEAD-READONLY",
          h1["seq"] == 1 and h1["digest"] == lg.read()[-1].digest
          and sorted((p.name, p.stat().st_mtime_ns) for p in lg.dir.iterdir()) == snapshot,
          f"head reports seq 1 / {h1['digest'][:12]} and the store is byte-for-byte untouched",
          f"{h1}")

    # --- budget: round trip, byte-identical signature, witness rises ----------------
    env2 = sign(lg, gc.BUDGET_SET, {"max_hours": 4, "note": "relayed"})
    before_mark = mark(wit, lg)
    ev2 = rl.apply_envelope(env2)
    st = gc.project(lg)
    check("V-RELAY-BUDGET-ROUNDTRIP",
          st.budget.get("max_hours") == 4 and st.last_seq == 2,
          "the relayed budget projects under the anchor", f"budget={st.budget}")
    check("V-RELAY-WITNESS-RISES", before_mark == 1 and mark(wit, lg) == 2,
          "the witness mark rose 1 -> 2 on apply", f"{before_mark} -> {mark(wit, lg)}")
    workstation()
    local = au.sign_event_data(au.load_anchor(), lg.repo, lg.goal_id, 2, gc.BUDGET_SET,
                               {"max_hours": 4, "note": "relayed"}, ev1.digest, env2["ts"], "owner")
    store_host()
    check("V-RELAY-SIG-BYTE-IDENTICAL", ev2.data == local,
          "the stored data (signature included) equals what GoalLog.append's signer makes "
          "for the same fields", f"{ev2.data} != {local}")
    check("V-RELAY-APPLY-NEEDS-NO-KEY", au.ENV_FOUNDER_KEY not in os.environ,
          "apply ran with no founder signing key in its environment",
          "the store host had a signing key")

    # --- indistinguishable from a local append --------------------------------------
    lgb = gl.GoalLog(REPO_ID, "g-local")
    workstation()
    set_env(anchor, founder=fk, witness=wit)          # one host holding everything
    gc.declare(lgb, "relay goal", ["it works"], [], {"paths": ["."]})
    gc.set_budget(lgb, 2, {"max_hours": 4, "note": "relayed"}, "owner")
    store_host()
    ra, la = lg.read()[1], lgb.read()[1]
    sa, sb = gc.project(lg), gc.project(lgb)
    same_shape = (set(ra.to_dict()) == set(la.to_dict())
                  and set(ra.data) == set(la.data)
                  and set(ra.data[au.SIG_FIELD]) == set(la.data[au.SIG_FIELD])
                  and ra.data[au.SIG_FIELD]["key_id"] == la.data[au.SIG_FIELD]["key_id"])
    check("V-RELAY-INDISTINGUISHABLE",
          same_shape and au.verify_event(au.load_anchor(), lg.repo, lg.goal_id, ra)[0]
          and au.verify_event(au.load_anchor(), lgb.repo, lgb.goal_id, la)[0]
          and bare(sa.budget) == bare(sb.budget) and sa.revision == sb.revision
          and au.check_founder_chain(au.load_anchor(), lg.repo, lg.goal_id, sa.events)
          == au.check_founder_chain(au.load_anchor(), lgb.repo, lgb.goal_id, sb.events) == 1
          and mark(wit, lgb) == 2,
          "a relayed event and a locally appended one have the same shape, verify, project "
          "and witness identically", f"shape={same_shape} {sa.budget} vs {sb.budget}")

    # --- tampering: each refused, nothing written; control applies ------------------
    env3 = sign(lg, gc.AUTHORITY_SET, {"may": ["gate"]})
    n = count(lg)
    # Gate names are literal: the mutation drill finds a gate's suite by its name.
    tampered = (
        ("V-RELAY-TAMPER-DATA", "DATA", {**env3, "data": {"may": ["gate", "deploy"]}}),
        ("V-RELAY-TAMPER-TS", "TS", {**env3, "ts": "2030-01-01T00:00:00+00:00"}),
        ("V-RELAY-TAMPER-ACTOR", "ACTOR", {**env3, "actor": "resident"}),
        ("V-RELAY-TAMPER-SEQ", "SEQ", {**env3, "seq": env3["seq"] + 1}),
        ("V-RELAY-TAMPER-PREV", "PREV", {**env3, "prev_digest": "f" * 64}),
    )
    for gate, label, bad in tampered:
        reason, msg = refusal(rl.apply_envelope, bad)
        check(gate,
              reason == au.FOUNDER_SIGNATURE_INVALID and au.BAD_SIGNATURE in msg and count(lg) == n,
              f"tampered {label.lower()} -> {reason} ({au.BAD_SIGNATURE}), {n} events unchanged",
              f"reason={reason!r} msg={msg[:90]!r} count={count(lg)}")

    # --- wrong key ---------------------------------------------------------------------
    judge_env = forge(env3, jpriv, j_id)
    stranger_env = forge(env3, xpriv, x_id)
    rj, mj = refusal(rl.apply_envelope, judge_env)
    rx, mx = refusal(rl.apply_envelope, stranger_env)
    set_env(anchor, founder=jk)
    try:
        rl.make_envelope(lg.repo, lg.goal_id, n, lg.read()[-1].digest, gc.BUDGET_SET, {}, "o")
        judge_signs = "signed"
    except au.SigningKeyUnavailable as exc:
        judge_signs = str(exc)
    store_host()
    check("V-RELAY-WRONG-KEY",
          rj == au.FOUNDER_SIGNATURE_INVALID and au.WRONG_ROLE in mj
          and rx == au.FOUNDER_SIGNATURE_INVALID and au.UNKNOWN_KEY in mx
          and "not founder" in judge_signs and count(lg) == n,
          "a judge-key envelope -> WRONG_ROLE, a key outside the anchor -> UNKNOWN_KEY, and "
          "founder-sign refuses a judge key outright; nothing written",
          f"judge={rj}/{mj[:60]} stranger={rx}/{mx[:60]} sign={judge_signs[:60]}")

    ev3 = rl.apply_envelope(env3)
    check("V-RELAY-TAMPER-CONTROL", ev3.seq == n + 1 and bare(gc.project(lg).authority) == {"may": ["gate"]},
          "the untampered envelope, founder-signed, applies after every forgery was refused",
          f"seq={ev3.seq}")

    # --- replay -------------------------------------------------------------------------
    n, m = count(lg), mark(wit, lg)
    reason, _ = refusal(rl.apply_envelope, env3)
    check("V-RELAY-REPLAY-REFUSED", reason == rl.STALE_ENVELOPE and count(lg) == n and mark(wit, lg) == m,
          f"the same envelope a second time -> {reason}, events and mark unchanged",
          f"reason={reason!r} count={count(lg)} mark={mark(wit, lg)}")

    # --- stale: the log advanced after head --------------------------------------------
    env_stale = sign(lg, gc.PAUSED, {"reason": "hold"})
    lg.append(count(lg) + 1, "test.resident_note", {"note": "resident wrote meanwhile"}, "resident")
    n = count(lg)
    reason, _ = refusal(rl.apply_envelope, env_stale)
    env_fresh = sign(lg, gc.PAUSED, {"reason": "hold"})
    ev_fresh = rl.apply_envelope(env_fresh)
    check("V-RELAY-STALE-REFUSED",
          reason == rl.STALE_ENVELOPE and ev_fresh.seq == n + 1,
          f"an envelope signed before the resident's event -> {reason}, nothing written; "
          "control: re-head + re-sign applies",
          f"reason={reason!r} fresh_seq={ev_fresh.seq} n={n}")

    # --- concurrency: the resident wins the sequence number mid-apply ------------------
    env_race = sign(lg, gc.RESUMED, {"reason": "go"})
    n, m = count(lg), mark(wit, lg)
    original_publish = gl.GoalLog.publish
    state = {"armed": True}

    def racing_publish(self, body):
        if state["armed"]:
            state["armed"] = False
            # the resident publishes this very seq first, through the same CAS
            rb = {"seq": body["seq"], "type": "test.resident_note", "ts": body["ts"],
                  "actor": "resident", "data": {}, "prev_digest": self.read()[-1].digest}
            rb["digest"] = gl.event_digest(rb)
            original_publish(self, rb)
        return original_publish(self, body)

    gl.GoalLog.publish = racing_publish
    try:
        reason, _ = refusal(rl.apply_envelope, env_race)
    finally:
        gl.GoalLog.publish = original_publish
    held = lg.read()
    check("V-RELAY-CAS-LOSES-CLEANLY",
          reason == rl.STALE_ENVELOPE and len(held) == n + 1 and held[-1].actor == "resident"
          and mark(wit, lg) == m and not state["armed"],
          "the resident published the same seq between apply's read and its link: the relay "
          "lost the os.link compare-and-swap, reported STALE, and neither its event nor a "
          "witness mark landed", f"reason={reason!r} held={len(held)} mark={mark(wit, lg)}")

    # --- non-founder types, and payload rules, refused at sign time ---------------------
    workstation()
    h = {"repo": lg.repo, "goal": lg.goal_id, "seq": count(lg), "digest": lg.read()[-1].digest}
    rn, _ = refusal(rl.make_envelope, h["repo"], h["goal"], h["seq"], h["digest"],
                    "goal.obligation_accepted", {"id": "ob-1"}, "owner")
    rd, _ = refusal(rl.make_envelope, h["repo"], h["goal"], h["seq"], h["digest"],
                    gc.DECLARED, declared_data("again"), "owner")
    r1, _ = refusal(rl.make_envelope, h["repo"], "g-empty", 0, gl.GENESIS,
                    gc.BUDGET_SET, {"max_hours": 1}, "owner")
    bad_rev = {**declared_data("x"), "revision": "0" * 16}
    rv, _ = refusal(rl.make_envelope, h["repo"], "g-empty", 0, gl.GENESIS, gc.DECLARED, bad_rev, "owner")
    rs, _ = refusal(rl.make_envelope, h["repo"], h["goal"], h["seq"], h["digest"],
                    gc.BUDGET_SET, {au.SIG_FIELD: {"key_id": "x", "sig": "y"}}, "owner")
    ok_env = rl.make_envelope(h["repo"], h["goal"], h["seq"], h["digest"], gc.TIER_SET,
                              {"tier": 2}, "owner")
    store_host()
    check("V-RELAY-NON-FOUNDER-REFUSED-AT-SIGN",
          rn == rl.ENVELOPE_TYPE_NOT_FOUNDER and ok_env["type"] == gc.TIER_SET,
          f"a non-founder type -> {rn}; control: a founder type signs",
          f"non-founder={rn!r}")
    check("V-RELAY-PAYLOAD-RULES",
          rd == r1 == rv == rs == rl.ENVELOPE_MALFORMED,
          "declared past seq 1, a non-declaration at seq 1, a wrong revision and a smuggled "
          "_founder block are all refused before signing", f"{rd} {r1} {rv} {rs}")
    na = count(lg)
    rt, _ = refusal(rl.apply_envelope, forge({**ok_env, "type": "test.resident_note"},
                                             load_priv(fk), f_id))
    check("V-RELAY-NON-FOUNDER-REFUSED-AT-APPLY", rt == rl.ENVELOPE_TYPE_NOT_FOUNDER and count(lg) == na,
          f"a founder-signed envelope of a non-founder type -> {rt}, nothing written", f"{rt!r}")

    # --- apply without a usable anchor ---------------------------------------------------
    set_env(None, witness=wit)
    ra_, _ = refusal(rl.apply_envelope, ok_env)
    set_env(tmp / "no_such_anchor.json", witness=wit)
    ru, _ = refusal(rl.apply_envelope, ok_env)
    after_refusals = count(lg)
    store_host()
    ev_ok = rl.apply_envelope(ok_env)
    check("V-RELAY-ABSENT-REFUSED",
          ra_ == ru == rl.AUTHORITY_REQUIRED and after_refusals == na and ev_ok.seq == na + 1,
          "apply under ABSENT and under UNVERIFIABLE -> AUTHORITY_REQUIRED, nothing written; "
          "control: the same envelope applies once the anchor is back",
          f"absent={ra_!r} unverifiable={ru!r} count={after_refusals}/{na}")

    # --- rollback: the relay cannot ratify a truncation ----------------------------------
    last = sorted(p for p in lg.dir.iterdir() if gl.EVENT_RE.match(p.name))[-1]
    kept = last.read_bytes()
    last.unlink()
    env_rb = sign(lg, gc.BUDGET_SET, {"max_hours": 9})
    n = count(lg)
    reason, rolled = refusal(rl.apply_envelope, env_rb)
    written = count(lg)
    if written == n:
        last.write_bytes(kept)
    check("V-RELAY-ROLLBACK-REFUSED",
          au.FOUNDER_ROLLBACK in rolled and written == n and gc.project(lg).last_seq == n + 1,
          "an envelope signed on a log truncated below its witness mark -> FOUNDER_ROLLBACK, "
          "nothing written; control: the restored log projects", f"{reason} {rolled[:100]!r}")

    # --- append_presigned is a check of its own, not a pipe ---------------------------
    envp = sign(lg, gc.BUDGET_SET, {"max_hours": 5})
    n = count(lg)
    mark_file = wit / lg.repo / f"{lg.goal_id}.json"
    mark_kept = mark_file.read_bytes()
    good = {**envp["data"], au.SIG_FIELD: {"key_id": envp["key_id"], "sig": envp["sig"]}}
    forged = {**good, "max_hours": 50}
    try:
        lg.append_presigned(envp["seq"], envp["type"], forged, envp["actor"], envp["ts"],
                            envp["prev_digest"])
        bad_sig = "published"
    except gl.GoalLogError as exc:
        bad_sig = str(exc)
    after_bad = count(lg)
    # A signature that is VALID but over a prev_digest the log does not hold.
    other_prev = "e" * 64
    wrong_prev_env = forge({**envp, "prev_digest": other_prev}, load_priv(fk), f_id)
    wp_data = {**wrong_prev_env["data"],
               au.SIG_FIELD: {"key_id": f_id, "sig": wrong_prev_env["sig"]}}
    try:
        lg.append_presigned(envp["seq"], envp["type"], wp_data, envp["actor"], envp["ts"], other_prev)
        wrong_prev = "published"
    except gl.GoalLogError as exc:
        wrong_prev = str(exc)
    after_prev = count(lg)
    # restore the store if a mutant let either through, so later gates stay meaningful
    for p in sorted(x for x in lg.dir.iterdir() if gl.EVENT_RE.match(x.name))[n:]:
        p.unlink()
    mark_file.write_bytes(mark_kept)
    evp = lg.append_presigned(envp["seq"], envp["type"], good, envp["actor"], envp["ts"],
                              envp["prev_digest"])
    check("V-RELAY-PRESIGNED-SIG-VERIFIED",
          au.FOUNDER_SIGNATURE_INVALID in bad_sig and after_bad == n and evp.seq == n + 1,
          "append_presigned itself refuses a pre-signed event whose signature does not verify; "
          "control: the genuine one publishes", f"{bad_sig[:90]!r} count={after_bad}/{n}")
    check("V-RELAY-PRESIGNED-PREV-CHECKED",
          wrong_prev != "published" and after_prev == n,
          "append_presigned refuses a validly signed event whose prev_digest is not the log's "
          "head, and writes nothing", f"{wrong_prev[:90]!r} count={after_prev}/{n}")

    # --- the CLI, end to end -----------------------------------------------------------
    cli = load_cli()
    head_file, env_file = tmp / "head.json", tmp / "env.json"
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc_head = cli.main(["head", "--goal", lg.goal_id, "--repo", lg.repo])
    head_file.write_text(out.getvalue(), encoding="utf-8")
    workstation()
    sout = io.StringIO()
    with contextlib.redirect_stdout(sout):
        rc_sign = cli.main(["founder-sign", "--head", str(head_file), "--type", gc.BUDGET_SET,
                            "--data", json.dumps({"max_hours": 7}), "--out", str(env_file)])
        rc_sign2 = cli.main(["founder-sign", "--head", str(head_file), "--type", gc.BUDGET_SET,
                             "--data", json.dumps({"max_hours": 8}), "--out", str(env_file)])
    store_host()
    n = count(lg)
    with contextlib.redirect_stdout(io.StringIO()):
        rc_apply = cli.main(["founder-apply", "--envelope", str(env_file)])
    aout = io.StringIO()
    with contextlib.redirect_stdout(aout):
        rc_replay = cli.main(["founder-apply", "--envelope", str(env_file)])
    pem = fk.read_text(encoding="utf-8")
    pem_body = "".join(pem.strip().splitlines()[1:-1])
    check("V-RELAY-CLI-ROUNDTRIP",
          (rc_head, rc_sign, rc_sign2, rc_apply, rc_replay) == (0, 0, 2, 0, 2)
          and bare(gc.project(lg).budget) == {"max_hours": 7} and count(lg) == n + 1
          and rl.STALE_ENVELOPE in aout.getvalue(),
          "head -> founder-sign -> founder-apply through the CLI; a second sign onto the same "
          "file is refused (exclusive), a second apply is STALE (exit 2)",
          f"rcs={(rc_head, rc_sign, rc_sign2, rc_apply, rc_replay)} budget={gc.project(lg).budget}")
    check("V-RELAY-KEY-NOT-PRINTED",
          pem_body and pem_body not in sout.getvalue() and "PRIVATE KEY" not in sout.getvalue()
          and pem_body not in env_file.read_text(encoding="utf-8"),
          "neither founder-sign's output nor the envelope contains the private key",
          "the private key leaked")

    # --- cross-user: needs two POSIX users --------------------------------------------
    unjudge("V-RELAY-CROSS-USER-APPEND",
            "needs `factory` and `factory-judge` on GEX44 with the store at 2770 + umask 0007 "
            "(spec §10); a single-user run cannot show another user can append")

    set_env()
    total = len(passes) + len(fails)
    print(f"\nGSDX_GOAL_RELAY_PASS={len(passes)}/{total}  threshold={total}/{total}"
          f"  unjudged={len(unjudged)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
