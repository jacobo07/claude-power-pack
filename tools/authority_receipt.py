"""Portable authority receipt (mission-capital W4, spec vault/specs/mission-capital-state.md section "W4").

H3 (measured 2026-11-23, GEX44 m-76e04d86896d): an Owner approval typed in a LAPTOP pane cannot be verified on GEX44,
because verify_owner_turn() opens the transcript through the local lr.find_transcript. The raise 175M -> 215M therefore
went in by hand with owner_turn=null, and the provenance was lost.

A receipt moves the verified Owner turn, not the transcript:
- The ISSUING host verifies the Owner turn locally (gsd_mission.verify_owner_turn, unchanged) and signs one act with
  HMAC-SHA256 under an estate key held only by authorized nodes.
- The CONSUMING host verifies the HMAC, the mission id and the goal fingerprint, and the expiry. It never reads a
  transcript.
- Scope: one mission_id, one goal_sha and one act ("authority" or "close"). A raise is bounded by the receipt's
  figures; the same receipt applied twice is the idempotent replay that set_authority already has (keyed by the turn).

The key is never printed, logged or put in a receipt: a receipt names it only by key_id (a hash of the key).
Kill switch: CPP_AUTHORITY_RECEIPT=off refuses every receipt (issue and consume) and stops flagging receipt-less
raises. The local --owner-turn path is untouched by the switch.

usage:
  authority_receipt.py init-key                      create the estate key (refuses to overwrite)
  authority_receipt.py key-id                        print the key id (never the key)
  authority_receipt.py goal-sha --mission <id>       the goal fingerprint of a LOCAL mission (run where it lives)
  authority_receipt.py issue --mission <id> --goal-sha <sha> --owner-turn <session>:<ts> --act authority
                             [--tokens 255M] [--extend-hours 12] [--ceiling 255M] [--step 40M] [--stage S]
                             [--ttl-hours 72] [--out file]
  authority_receipt.py issue ... --act close --outcome HALTED --reason "..."
  authority_receipt.py verify --mission <id> --receipt <file|token>
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import socket
import sys
import time
from pathlib import Path

PREFIX = "ar1."
VERSION = 1
ACTS = ("authority", "close")
DEFAULT_TTL_H = 72.0      # a receipt is consumed within hours of the Owner's turn; three days covers a weekend
MAX_SKEW_S = 300.0        # clock skew tolerated between issuer and consumer
KEY_BYTES = 32            # HMAC-SHA256 key length
SHA_HEX = 64              # length of a sha256 hex digest
GROUP_OTHER_BITS = 0o077  # POSIX permission bits a private key must not carry


class ReceiptError(Exception):
    """A receipt that cannot be issued or must not be consumed. The message names why, never the key."""


def enabled() -> bool:
    return os.environ.get("CPP_AUTHORITY_RECEIPT", "").strip().lower() not in ("off", "0", "false", "no")


def key_path() -> Path:
    env = os.environ.get("CPP_ESTATE_KEY_FILE")
    return Path(env) if env else Path.home() / ".claude" / "secrets" / "estate-authority.key"


def load_key() -> bytes:
    """The estate key, or ReceiptError naming why there is none. On POSIX a key readable by group/other is refused:
    a receipt signed with a key anyone on the host can read proves nothing about the Owner."""
    p = key_path()
    if not p.is_file():
        raise ReceiptError(f"no estate key at {p} (this node is not authorized to issue or consume receipts)")
    if os.name == "posix" and p.stat().st_mode & GROUP_OTHER_BITS:
        raise ReceiptError(f"estate key {p} is readable by group/other (mode {oct(p.stat().st_mode & 0o777)}); "
                           "chmod 600 it")
    raw = p.read_text(encoding="ascii", errors="strict").strip()
    try:
        key = bytes.fromhex(raw)
    except ValueError:
        raise ReceiptError(f"estate key {p} is not hex") from None
    if len(key) < KEY_BYTES:
        raise ReceiptError(f"estate key {p} is shorter than {KEY_BYTES} bytes")
    return key


def key_id(key: bytes) -> str:
    return hashlib.sha256(b"cpp-estate-key-id|" + key).hexdigest()[:12]


def init_key() -> Path:
    p = key_path()
    if p.exists():
        raise ReceiptError(f"estate key {p} already exists; refusing to overwrite it")
    p.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="ascii") as fh:
        fh.write(secrets.token_hex(KEY_BYTES) + "\n")
    return p


def goal_sha(rec: dict) -> str:
    """The goal fingerprint a receipt is bound to: identity fields that never change over the mission's life (the
    resume command can be rewritten by a pivot, so it is not one of them)."""
    ident = [rec.get("mission_id"), rec.get("created_at"), rec.get("workstream"), list(rec.get("mission_terms") or [])]
    return hashlib.sha256(json.dumps(ident, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _canon(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sign(key: bytes, payload: dict) -> str:
    return hmac.new(key, _canon(payload), hashlib.sha256).hexdigest()


def encode(receipt: dict) -> str:
    return PREFIX + base64.urlsafe_b64encode(_canon(receipt)).decode("ascii").rstrip("=")


def decode(token: str) -> dict:
    """A token (ar1.<base64url>), a path to a file holding one, or a JSON object."""
    s = str(token or "").strip()
    if s and not s.startswith(PREFIX) and not s.startswith("{"):
        p = Path(s)
        if p.is_file():
            s = p.read_text(encoding="utf-8").strip()
    if s.startswith("{"):
        try:
            return json.loads(s)
        except ValueError:
            raise ReceiptError("receipt is not valid JSON") from None
    if not s.startswith(PREFIX):
        raise ReceiptError(f"not a receipt (expected {PREFIX}<base64url>, a file holding one, or JSON)")
    body = s[len(PREFIX):]
    try:
        return json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    except (ValueError, TypeError):
        raise ReceiptError("receipt body does not decode") from None


def _tokens(v):
    if v is None:
        return None
    import mission_topup as mt   # one token parser for the estate ("255M", "1.5G", plain ints)
    return int(mt.parse_tokens(v))


def issue(mission_id: str, goal: str, owner_turn: str, act: str, *, tokens=None, extend_hours=None, ceiling=None,
          step=None, stage=None, outcome=None, reason="", ttl_h: float = DEFAULT_TTL_H, finder=None,
          now: float | None = None) -> dict:
    """Verify the Owner turn HERE, then sign one act for one mission. -> the receipt dict (see encode)."""
    if not enabled():
        raise ReceiptError("CPP_AUTHORITY_RECEIPT=off: receipts are disabled")
    if act not in ACTS:
        raise ReceiptError(f"act must be one of {', '.join(ACTS)}, not {act!r}")
    if not goal or len(str(goal)) != SHA_HEX:
        raise ReceiptError("--goal-sha must be the 64-hex goal fingerprint (authority_receipt.py goal-sha on the "
                           "host that holds the mission)")
    terms = {"tokens": _tokens(tokens), "extend_hours": float(extend_hours) if extend_hours else None,
             "ceiling": _tokens(ceiling), "step": _tokens(step), "stage": stage}
    if act == "authority":
        if terms["tokens"] is None and not terms["extend_hours"]:
            raise ReceiptError("an authority receipt needs --tokens and/or --extend-hours")
        if terms["ceiling"] is not None and terms["tokens"] is not None and terms["ceiling"] < terms["tokens"]:
            raise ReceiptError("--ceiling must be >= --tokens")
        if (terms["step"] is None) != (terms["ceiling"] is None):
            raise ReceiptError("a top-up policy needs both --ceiling and --step (or neither)")
        close = None
    else:
        if not str(reason or "").strip() or not outcome:
            raise ReceiptError("a close receipt needs --outcome and --reason")
        if any(v is not None for v in terms.values()):
            raise ReceiptError("a close receipt carries no authority figures")
        close = {"outcome": outcome, "reason": str(reason).strip()[:1000]}
    import gsd_mission as gm   # the issuing host's own verifier: a laptop turn is checked against a laptop transcript
    try:
        turn = gm.verify_owner_turn(owner_turn, finder)
    except gm.MissionError as exc:
        raise ReceiptError(f"owner turn not verified here: {exc}") from None
    key = load_key()
    now = time.time() if now is None else now
    payload = {"v": VERSION, "kind": "authority_receipt", "act": act, "mission_id": mission_id, "goal_sha": goal,
               "terms": terms, "close": close,
               "source": {"host": socket.gethostname(), "session": turn["session"], "timestamp": turn["timestamp"],
                          "uuid": turn["uuid"], "text_sha256": turn["text_sha256"], "text_head": turn["text_head"]},
               "issued_at": now, "expires_at": now + float(ttl_h) * 3600.0,
               "nonce": secrets.token_hex(8), "key_id": key_id(key)}
    return {**payload, "sig": _sign(key, payload)}


def verify(receipt, rec: dict, act: str, now: float | None = None) -> dict:
    """Consume-side check. -> the signed payload (no sig). ReceiptError names the first check that failed."""
    if not enabled():
        raise ReceiptError("CPP_AUTHORITY_RECEIPT=off: receipts are disabled")
    r = decode(receipt) if isinstance(receipt, str) else dict(receipt or {})
    sig = r.pop("sig", None)
    if r.get("kind") != "authority_receipt" or r.get("v") != VERSION:
        raise ReceiptError(f"not a v{VERSION} authority receipt")
    key = load_key()
    if r.get("key_id") != key_id(key):
        raise ReceiptError(f"receipt was signed with key {r.get('key_id')}, this node holds {key_id(key)}")
    if not isinstance(sig, str) or not hmac.compare_digest(sig, _sign(key, r)):
        raise ReceiptError("signature does not verify (the receipt was altered or forged)")
    if r.get("act") != act:
        raise ReceiptError(f"receipt authorizes act {r.get('act')!r}, not {act!r}")
    if r.get("mission_id") != rec.get("mission_id"):
        raise ReceiptError(f"receipt is for mission {r.get('mission_id')}, not {rec.get('mission_id')}")
    if r.get("goal_sha") != goal_sha(rec):
        raise ReceiptError("receipt goal fingerprint does not match this mission's goal")
    now = time.time() if now is None else now
    if float(r.get("issued_at") or 0) > now + MAX_SKEW_S:
        raise ReceiptError("receipt is issued in the future (clock skew beyond 5 min)")
    if float(r.get("expires_at") or 0) < now:
        raise ReceiptError(f"receipt expired at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(r['expires_at']))}")
    return r


def owner_turn_of(payload: dict) -> dict:
    """The verified-turn shape set_authority / close_mission record, marked portable."""
    s = payload["source"]
    return {"session": s["session"], "timestamp": s["timestamp"], "uuid": s["uuid"], "text_sha256": s["text_sha256"],
            "text_head": s["text_head"], "transcript": None,
            "portable": {"host": s["host"], "key_id": payload["key_id"], "nonce": payload["nonce"],
                         "issued_at": payload["issued_at"]}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-key")
    sub.add_parser("key-id")
    g = sub.add_parser("goal-sha")
    g.add_argument("--mission", required=True)
    i = sub.add_parser("issue")
    i.add_argument("--mission", required=True)
    i.add_argument("--goal-sha", required=True)
    i.add_argument("--owner-turn", required=True)
    i.add_argument("--act", choices=ACTS, required=True)
    for f in ("--tokens", "--ceiling", "--step", "--stage", "--outcome", "--out"):
        i.add_argument(f)
    i.add_argument("--extend-hours", type=float)
    i.add_argument("--reason", default="")
    i.add_argument("--ttl-hours", type=float, default=DEFAULT_TTL_H)
    v = sub.add_parser("verify")
    v.add_argument("--mission", required=True)
    v.add_argument("--receipt", required=True)
    v.add_argument("--act", choices=ACTS, default="authority")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "init-key":
            p = init_key()
            print(f"ESTATE KEY CREATED path={p} key_id={key_id(load_key())}")
        elif a.cmd == "key-id":
            print(f"KEY_ID {key_id(load_key())} path={key_path()}")
        elif a.cmd == "goal-sha":
            import gsd_mission as gm
            rec = gm.load(a.mission)
            if rec is None:
                print(f"GOAL-SHA REFUSED: no mission {a.mission} on this host", file=sys.stderr)
                return 3
            print(f"GOAL_SHA {goal_sha(rec)} mission={a.mission}")
        elif a.cmd == "issue":
            r = issue(a.mission, a.goal_sha, a.owner_turn, a.act, tokens=a.tokens, extend_hours=a.extend_hours,
                      ceiling=a.ceiling, step=a.step, stage=a.stage, outcome=a.outcome, reason=a.reason,
                      ttl_h=a.ttl_hours)
            tok = encode(r)
            if a.out:
                Path(a.out).write_text(tok + "\n", encoding="ascii")
            print(f"RECEIPT ISSUED mission={a.mission} act={a.act} terms={json.dumps(r['terms'])} "
                  f"turn={r['source']['uuid']} key_id={r['key_id']} expires={r['expires_at']:.0f}"
                  + (f" out={a.out}" if a.out else f"\n{tok}"))
        elif a.cmd == "verify":
            import gsd_mission as gm
            rec = gm.load(a.mission)
            if rec is None:
                print(f"VERIFY REFUSED: no mission {a.mission} on this host", file=sys.stderr)
                return 3
            r = verify(a.receipt, rec, a.act)
            print(f"RECEIPT VALID mission={a.mission} act={r['act']} terms={json.dumps(r['terms'])} "
                  f"from={r['source']['host']} turn={r['source']['uuid']}")
    except ReceiptError as exc:
        print(f"RECEIPT REFUSED: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
