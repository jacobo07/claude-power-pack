#!/usr/bin/env python
"""V-W4-* gates: portable authority receipt (mission-capital W4, spec vault/specs/mission-capital-state.md "W4").

Hermetic: state, transcripts and the estate key live in a temp dir. The "issuing host" is the one whose finder sees
the Owner transcript; the "consuming host" is the default finder, which sees none (projects dir empty) -- exactly the
GEX44 shape of H3. Every refusal pole has a control that passes through the same call.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="authority-receipt-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects-consumer")   # the consumer sees no transcript
os.environ["CPP_WORK_CLASS_PROFILE_DIR"] = str(Path(TMP) / "wcp")
os.environ["CPP_ESTATE_KEY_FILE"] = str(Path(TMP) / "keys" / "estate.key")
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
os.environ["CPP_MISSION_ACCOUNT_ADMISSION"] = "off"
os.environ["CPP_MISSION_NOTIFY_TOAST"] = "off"
for _k in ("CPP_MISSION_AUTO_TOPUP", "TELEGRAM_BOT_TOKEN", "CPP_TOPUP_EVENT", "CPP_TOPUP_PREDICTIVE",
           "CPP_CAPITAL_STATE", "CPP_PROGRESS_RECEIPTS", "CPP_AUTHORITY_RECEIPT"):
    os.environ.pop(_k, None)
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import gsd_mission as gm  # noqa: E402
import mission_topup as mt  # noqa: E402
import authority_receipt as ar  # noqa: E402
import account_governor as _ag  # noqa: E402
import mission_spend as _ms  # noqa: E402

_ag.DEFAULT_STATE = os.path.join(TMP, "governor")
_ag.check = lambda state_dir, action: (0, "ALLOW", "test governor", {})
SPEND: dict = {}
_ms.processed_tokens = lambda rec, *a, **k: SPEND.get(rec.get("mission_id"))

passes = fails = 0
ISSUER_PROJECTS = Path(TMP) / "projects-issuer" / "laptop-pane"
ISSUER_PROJECTS.mkdir(parents=True)
SID = "8fd6ace9-0000-4000-8000-00000000w4w4"
TS = "2026-11-24T19:00:00"


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


class env:
    def __init__(self, **kv):
        self.kv, self.old = kv, {}

    def __enter__(self):
        for k, v in self.kv.items():
            self.old[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def __exit__(self, *exc):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def owner_turn(text, ts):
    """One Owner message in the ISSUER's transcript. -> the <session>:<timestamp> ref."""
    p = ISSUER_PROJECTS / f"{SID}.jsonl"
    row = {"type": "user", "timestamp": ts + ".000Z", "uuid": f"u-{ts[-8:].replace(':', '')}",
           "message": {"role": "user", "content": text}}
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    return f"{SID}:{ts}"


def issuer_finder(sid):
    p = ISSUER_PROJECTS / f"{sid}.jsonl"
    return p if p.is_file() else None


def mission(name, spend=50_000_000):
    mid = f"m-{name}"
    SPEND[mid] = 1_000_000
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, mission_terms=[f"goal {name}"])
    with env(CPP_AUTHORITY_RECEIPT="off"):   # the fixture's own arm raise is not under test: not flagged
        gm.set_authority(mid, tokens="100M", reason="w4 test arm")
    SPEND[mid] = spend
    return mid


def rows(mid, event):
    return [e for e in gm.lr.ledger_events(mid) if e.get("event") == event]


def issue(mid, act="authority", ref=None, **kw):
    rec = gm.load(mid)
    return ar.issue(mid, ar.goal_sha(rec), ref or owner_turn("si", TS), act, finder=issuer_finder, **kw)


def refused(fn):
    try:
        fn()
    except (gm.MissionError, ar.ReceiptError) as exc:
        return str(exc)
    return None


def key_gates():
    p = ar.init_key()
    k1 = ar.key_id(ar.load_key())
    again = refused(ar.init_key)
    check("V-W4-KEY-INIT", p.is_file() and len(p.read_text().strip()) == 64 and again and "refusing" in again
          and ar.key_id(ar.load_key()) == k1, f"key_id={k1} second={again!r}")
    if os.name == "posix":
        os.chmod(p, 0o644)
        why = refused(ar.load_key)
        os.chmod(p, 0o600)
        check("V-W4-KEY-PERMS", why and "group/other" in why and ar.load_key(), why)
    else:
        print("SKIP V-W4-KEY-PERMS (POSIX-only check; runs on GEX44)")


def consume_gates():
    mid = mission("consume")
    ref = owner_turn("+90 M y 2 top-ups de 40 M", "2026-11-24T19:01:00")
    # Control: the GEX44 shape before W4. The consumer cannot see the laptop transcript, so the turn is refused.
    why = refused(lambda: gm.set_authority(mid, tokens="190M", owner_turn=ref))
    check("V-W4-CONSUME-CONTROL-NO-TRANSCRIPT", why and "no transcript" in why, why)
    r = ar.issue(mid, ar.goal_sha(gm.load(mid)), ref, "authority", tokens="190M", finder=issuer_finder)
    tok = ar.encode(r)
    rec = gm.set_authority(mid, receipt=tok, reason="portable")
    last = rec["authority_receipts"][-1]
    check("V-W4-CONSUME-AUTHORITY",
          rec["authority_tokens"] == 190_000_000 and last["provenance"] == "portable_receipt"
          and last["owner_turn"]["portable"]["key_id"] == r["key_id"] and last["owner_turn"]["transcript"] is None
          and last["owner_turn"]["uuid"] == r["source"]["uuid"] and not rows(mid, "authority_receipt_missing"),
          f"auth={rec['authority_tokens']} prov={last['provenance']}")
    n = len(gm.load(mid)["authority_receipts"])
    gm.set_authority(mid, receipt=tok)
    check("V-W4-REPLAY-NOOP", len(gm.load(mid)["authority_receipts"]) == n and rows(mid, "authority_replay_noop"),
          f"receipts={n}")
    why = refused(lambda: gm.set_authority(mid, tokens="250M", receipt=tok))
    check("V-W4-BOUNDED-TOKENS", why and "not the signed" in why, why)
    why = refused(lambda: gm.set_authority(mid, extend_hours=12, receipt=tok))
    check("V-W4-BOUNDED-HOURS", why and "not the signed" in why, why)
    why = refused(lambda: gm.set_authority(mid, receipt=tok, owner_turn=ref))
    check("V-W4-ONE-AUTHORITY-SOURCE", why and "not both" in why, why)


def forgery_gates():
    mid = mission("forge")
    r = issue(mid, ref=owner_turn("raise to 150M", "2026-11-24T19:02:00"), tokens="150M")
    bad = dict(r, terms=dict(r["terms"], tokens=900_000_000))
    why = refused(lambda: gm.set_authority(mid, receipt=ar.encode(bad)))
    check("V-W4-TAMPER", why and "signature" in why and gm.load(mid)["authority_tokens"] == 100_000_000, why)
    other = mission("other")
    why = refused(lambda: gm.set_authority(other, receipt=ar.encode(r)))
    check("V-W4-WRONG-MISSION", why and "is for mission" in why, why)
    r2 = ar.issue(mid, "0" * 64, owner_turn("raise to 150M again", "2026-11-24T19:03:00"), "authority",
                  tokens="150M", finder=issuer_finder)
    why = refused(lambda: gm.set_authority(mid, receipt=ar.encode(r2)))
    check("V-W4-GOAL-MISMATCH", why and "goal fingerprint" in why, why)
    why = refused(lambda: gm.set_authority(mid, receipt=ar.encode(r), now=r["expires_at"] + 1))
    check("V-W4-EXPIRED", why and "expired" in why, why)
    keyp = Path(os.environ["CPP_ESTATE_KEY_FILE"])
    with env(CPP_ESTATE_KEY_FILE=str(Path(TMP) / "keys2" / "other.key")):
        ar.init_key()
        why = refused(lambda: gm.set_authority(mid, receipt=ar.encode(r)))
    check("V-W4-WRONG-KEY", why and "signed with key" in why, why)
    with env(CPP_ESTATE_KEY_FILE=str(Path(TMP) / "keys3" / "absent.key")):
        why = refused(lambda: gm.set_authority(mid, receipt=ar.encode(r)))
    check("V-W4-NO-KEY-NODE", why and "not authorized" in why, why)
    rec = gm.set_authority(mid, receipt=ar.encode(r))
    check("V-W4-FORGERY-CONTROL", rec["authority_tokens"] == 150_000_000 and keyp.is_file(),
          f"auth={rec['authority_tokens']}")


def flag_gates():
    mid = mission("flag")
    before = len(rows(mid, "authority_receipt_missing"))
    lin0 = gm.authority_lineage(gm.load(mid))["receipt_less_raises"]   # the fixture's arm raise carries none too
    rec = gm.set_authority(mid, tokens="130M", reason="hand raise, no turn")
    last = rec["authority_receipts"][-1]
    lin = gm.authority_lineage(gm.load(mid))
    check("V-W4-RECEIPTLESS-FLAGGED", last["provenance"] == "none"
          and len(rows(mid, "authority_receipt_missing")) == before + 1 and lin["receipt_less_raises"] == lin0 + 1,
          f"prov={last['provenance']} count {lin0} -> {lin['receipt_less_raises']}")
    # review M1: a hand call claiming the top-up label is downgraded to "none" and flagged with the claim
    gm.set_authority(mid, tokens="135M", reason="hand raise dressed as a top-up", provenance="topup_policy")
    miss = rows(mid, "authority_receipt_missing")
    check("V-W4-FORGED-TOPUP-LABEL", gm.load(mid)["authority_receipts"][-1]["provenance"] == "none"
          and len(miss) == before + 2 and miss[-1].get("claimed_provenance") == "topup_policy",
          f"prov={gm.load(mid)['authority_receipts'][-1]['provenance']} rows={len(miss)}")
    why = refused(lambda: gm.set_authority(mid, tokens="136M", provenance="owner_turn"))
    check("V-W4-PROVENANCE-LABEL-REFUSED", why and "only 'topup_policy'" in why, why)
    # control: the real shape -- inside a top-up pass, the current policy's last grant raising to exactly this figure
    mt.save_policy({"schema": mt.SCHEMA, "mission_id": mid, "policy_epoch": 0, "prior_grants": [],
                    "grants": [{"n": 1, "from": 135_000_000, "to": 140_000_000, "hold_set_at": 1.0}]})
    with mt._Quiet():
        gm.set_authority(mid, tokens="140M", reason="auto top-up 1 under Owner policy", provenance="topup_policy")
    check("V-W4-RECEIPTLESS-CONTROL-TOPUP", len(rows(mid, "authority_receipt_missing")) == before + 2
          and gm.load(mid)["authority_receipts"][-1]["provenance"] == "topup_policy")
    with mt._Quiet():   # inside a pass, but the figure is not the grant's: not proven
        gm.set_authority(mid, tokens="141M", reason="wrong figure", provenance="topup_policy")
    check("V-W4-TOPUP-LABEL-WRONG-FIGURE", gm.load(mid)["authority_receipts"][-1]["provenance"] == "none"
          and len(rows(mid, "authority_receipt_missing")) == before + 3)
    with env(CPP_AUTHORITY_RECEIPT="off"):
        gm.set_authority(mid, tokens="145M", reason="switch off")
        why = refused(lambda: issue(mid, ref=owner_turn("x", "2026-11-24T19:04:00"), tokens="150M"))
    check("V-W4-KILL-SWITCH", why and "disabled" in why and len(rows(mid, "authority_receipt_missing")) == before + 3,
          why)


def budget_gates():
    mid = mission("budget")
    r = issue(mid, ref=owner_turn("90M with top-ups to 255M by 40M", "2026-11-24T19:05:00"),
              tokens="175M", ceiling="255M", step="40M")
    tok = ar.encode(r)
    why = refused(lambda: mt.budget(mid, "200M", None, None, receipt=tok))
    check("V-W4-BUDGET-MISMATCH", why and "not the signed" in why, why)
    pol = mt.budget(mid, None, None, None, receipt=tok)
    rec = gm.load(mid)
    check("V-W4-BUDGET-RECEIPT", pol["ceiling"] == 255_000_000 and pol["step"] == 40_000_000
          and pol["authority"] == 175_000_000 and pol["provenance"] == "portable_receipt"
          and pol["receipts"][-1]["nonce"] == r["nonce"] and rec["authority_tokens"] == 175_000_000
          and rec["authority_receipts"][-1]["provenance"] == "portable_receipt",
          f"ceiling={pol['ceiling']} epoch={pol['policy_epoch']}")
    ep = pol["policy_epoch"]
    pol2 = mt.budget(mid, None, None, None, receipt=tok)
    check("V-W4-BUDGET-REPLAY-NOOP", pol2["policy_epoch"] == ep and rows(mid, "authority_receipt_replay_noop"),
          f"epoch {ep} -> {pol2['policy_epoch']}")
    plain = mission("budget-plain")
    pol3 = mt.budget(plain, "120M", 2, "40M", reason="arm without a turn")
    check("V-W4-BUDGET-RECEIPTLESS-FLAGGED", pol3["provenance"] == "none"
          and rows(plain, "authority_receipt_missing"), f"prov={pol3['provenance']}")
    # review M2: a local Owner-turn budget replayed AFTER a later budget must not open a fresh epoch
    tm = mission("budget-turns")
    a_ref = owner_turn("budget A", "2026-11-24T19:10:00")
    b_ref = owner_turn("budget B", "2026-11-24T19:11:00")
    c_ref = owner_turn("budget C", "2026-11-24T19:12:00")
    d_ref = owner_turn("authority D", "2026-11-24T19:13:00")
    with env(GSD_LONG_RUN_PROJECTS_DIR=str(ISSUER_PROJECTS.parent)):   # the local turns are visible on this host
        mt.budget(tm, "120M", 2, "40M", owner_turn=a_ref)
        e1 = mt.budget(tm, "130M", 2, "40M", owner_turn=b_ref)["policy_epoch"]
        e_replay = mt.budget(tm, "120M", 2, "40M", owner_turn=a_ref)["policy_epoch"]
        check("V-W4-BUDGET-TURN-REPLAY-ACROSS-EPOCHS", e1 == 1 and e_replay == 1, f"epoch {e1} -> replay {e_replay}")
        e_c = mt.budget(tm, "140M", 2, "40M", owner_turn=c_ref)["policy_epoch"]
        check("V-W4-BUDGET-TURN-CONTROL-FRESH", e_c == 2, f"fresh turn epoch {e_c}")
        gm.set_authority(tm, tokens="150M", owner_turn=d_ref)   # the turn already applied as a plain raise
        e_d = mt.budget(tm, "150M", 2, "40M", owner_turn=d_ref)["policy_epoch"]
        check("V-W4-BUDGET-TURN-ALREADY-APPLIED", e_d == 2 and gm.load(tm)["authority_tokens"] == 150_000_000,
              f"epoch {e_c} -> {e_d}")


def close_gates():
    mid = mission("close")
    ref = owner_turn("close the duplicate mission", "2026-11-24T19:06:00")
    auth_r = issue(mid, ref=owner_turn("raise it", "2026-11-24T19:07:00"), tokens="150M")
    why = refused(lambda: gm.close_mission(mid, None, None, receipt=ar.encode(auth_r)))
    check("V-W4-CLOSE-ACT-MISMATCH", why and "act" in why and gm.load(mid)["state"] not in gm.TERMINAL, why)
    why = refused(lambda: gm.close_mission(mid, "dup", ref))
    check("V-W4-CLOSE-CONTROL-NO-TRANSCRIPT", why and "no transcript" in why, why)
    r = ar.issue(mid, ar.goal_sha(gm.load(mid)), ref, "close", outcome="HALTED",
                 reason="duplicate armed in error", finder=issuer_finder)
    why = refused(lambda: gm.close_mission(mid, None, None, outcome="COMPLETED", receipt=ar.encode(r)))
    check("V-W4-CLOSE-OUTCOME-MISMATCH", why and "not the signed" in why and gm.load(mid)["state"] not in gm.TERMINAL,
          why)
    out = gm.close_mission(mid, "caller words", None, receipt=ar.encode(r))
    c = out["record"].get("closed") or {}
    check("V-W4-CLOSE-RECEIPT", out["closed"] and out["record"]["state"] == "HALTED"
          and c.get("reason") == "duplicate armed in error" and c["owner_turn"]["portable"]["nonce"] == r["nonce"],
          f"state={out['record']['state']} reason={c.get('reason')!r}")


def leak_gate():
    key_hex = Path(os.environ["CPP_ESTATE_KEY_FILE"]).read_text().strip()
    hay = []
    for p in Path(TMP).rglob("*"):
        if p.is_file() and "keys" not in p.parts and p.suffix in (".json", ".jsonl", ".txt", ""):
            hay.append(p.read_text(encoding="utf-8", errors="replace"))
    r = issue(mission("leak"), ref=owner_turn("leak check", "2026-11-24T19:08:00"), tokens="120M")
    hay.append(ar.encode(r))
    cli = subprocess.run([sys.executable, str(TOOLS / "authority_receipt.py"), "key-id"], capture_output=True,
                         text=True, env=os.environ.copy())
    hay.append(cli.stdout + cli.stderr)
    check("V-W4-NO-KEY-LEAK", cli.returncode == 0 and "KEY_ID" in cli.stdout and len(hay) > 3
          and not any(key_hex in h for h in hay), f"scanned={len(hay)} cli={cli.stdout.strip()[:40]}")


def cli_gate():
    mid = mission("cli")
    gs = subprocess.run([sys.executable, str(TOOLS / "authority_receipt.py"), "goal-sha", "--mission", mid],
                        capture_output=True, text=True, env=os.environ.copy())
    sha = gs.stdout.split()[1] if gs.returncode == 0 else ""
    ref = owner_turn("cli raise 160M", "2026-11-24T19:09:00")
    out = Path(TMP) / "r.txt"
    issuer_env = dict(os.environ, GSD_LONG_RUN_PROJECTS_DIR=str(ISSUER_PROJECTS.parent))
    iss = subprocess.run([sys.executable, str(TOOLS / "authority_receipt.py"), "issue", "--mission", mid,
                          "--goal-sha", sha, "--owner-turn", ref, "--act", "authority", "--tokens", "160M",
                          "--out", str(out)], capture_output=True, text=True, env=issuer_env)
    con = subprocess.run([sys.executable, str(TOOLS / "gsd_mission.py"), "authority", "--mission", mid,
                          "--receipt", str(out)], capture_output=True, text=True, env=os.environ.copy())
    check("V-W4-CLI-ROUNDTRIP", gs.returncode == 0 and iss.returncode == 0 and con.returncode == 0
          and "AUTHORITY SET" in con.stdout and gm.load(mid)["authority_tokens"] == 160_000_000,
          f"gs={gs.returncode} issue={iss.returncode} consume={con.returncode} {(iss.stderr + con.stderr)[:160]}")


if __name__ == "__main__":
    t0 = time.time()
    for group in (key_gates, consume_gates, forgery_gates, flag_gates, budget_gates, close_gates, leak_gate,
                  cli_gate):
        try:
            group()
        except Exception as exc:  # noqa: BLE001 -- a crashed group is a failed gate, named
            import traceback
            traceback.print_exc()
            check(f"V-W4-GROUP-{group.__name__}", False, f"{type(exc).__name__}: {exc}")
    print(f"W4_PASS={passes}/{passes + fails} secs={time.time() - t0:.1f}")
    sys.exit(0 if fails == 0 else 1)
