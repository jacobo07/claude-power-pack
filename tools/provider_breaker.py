"""Provider circuit breaker for mission workers: incapacity pauses a mission, it never churns it.

Assimilated from Genesis worker-router (MIT: attempt budgets, cooldowns, structured failure) and
the event-driven loop kit (ideas only: instant-failure backoff, consecutive-failure quarantine).
Extends tools/gsd_mission.py quota_hold, whose contract is kept byte-for-byte for quota refusals.

The breaker is STATELESS, like quota_hold: every supervisor pass re-derives the hold from the
predecessor worker's own transcript, so no mission state transition can undo it (a BLOCKED
mission with a dead owner is replaced on the next pass -- a state cannot carry a quarantine).

A reply counts only if the HOST wrote it (model "<synthetic>"), or if the worker died having
produced no assistant row at all. Classes:
  quota        weekly/session limit     -> hold until the stated reset (gsd_mission.quota_hold)
  auth         login / key / token      -> QUARANTINE until an operator clears it
  transient    overloaded, 5xx, 429,    -> exponential backoff 300 s * 2^(streak-1), cap 1 h
               timeouts, unknown host text
  no_reply     worker produced nothing  -> same backoff as transient
Streak = consecutive most-recent workers of the mission that ended in a breaker class. At
QUARANTINE_AFTER the mission is quarantined whatever the class: four fresh sessions that each
paid the bootstrap and did nothing is not a transient. Regla 12 (Owner 2026-11-20): IDENTICAL_AFTER (2)
consecutive workers ending in the SAME non-transient failure (same class, same host text with ids and
numbers collapsed) quarantine at once; a known transient (KNOWN_TRANSIENT_RE: overload, 5xx, 429,
timeout, network) keeps the backoff and the 4-worker limit. Kill switch CPP_BREAKER_IDENTICAL=off.

Clearing: `python tools/provider_breaker.py clear --mission <id>` writes a `provider_cleared`
ledger row; a quarantine whose evidence is OLDER than the latest clear is not enforced.
An AUTH quarantine is also released by a RE-LOGIN: the credentials file rewritten AFTER the refusal
with an access token that is usable (unexpired, or lapsed but still refreshable) is the qualifying
precondition change; the release is ledgered as `provider_released`. An unchanged, unreadable or
still-expired (expiresAt 0) credentials file keeps the park. Only mtime, expiresAt,
refreshTokenExpiresAt and the presence of a refresh token are ever read -- never a token value.
Kill switches: CPP_PROVIDER_BREAKER=off -> quota_hold only (the pre-breaker behaviour);
CPP_BREAKER_CRED_RELEASE=off -> a re-login no longer releases (only `clear` does).

    python tools/provider_breaker.py status --mission <id>
    python tools/provider_breaker.py clear  --mission <id> [--note "..."]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402

QUOTA, AUTH, TRANSIENT, NO_REPLY = "quota", "auth", "transient", "no_reply"
BACKOFF_BASE_S = 300
BACKOFF_CAP_S = 3600
QUARANTINE_AFTER = 4
STREAK_WINDOW = 8
MAX_LINEAGE_HOPS = 4
AUTH_RE = re.compile(r"invalid api key|please run /login|not logged in|oauth token (?:has )?expired|"
                     r"authentication[_ ](?:error|failed)|\b401\b|unauthori[sz]ed|credit balance is too low", re.I)
# Regla 12 (Owner 2026-11-20): the same failure twice is not a transient -- quarantine at 2, not 4.
# A KNOWN transient (overload, 5xx, 429, timeout, network) keeps the backoff and the 4-worker limit:
# it repeats identically by nature and the provider recovers without a change on our side.
IDENTICAL_AFTER = 2
KNOWN_TRANSIENT_RE = re.compile(r"overloaded|\b(?:5\d\d|429)\b|rate[ _-]?limit|timed? ?out|timeout|econnreset|"
                                r"etimedout|socket hang up|network|temporarily unavailable|service unavailable|"
                                r"bad gateway|connection (?:error|refused|reset)|fetch failed|econnrefused|"
                                r"enotfound|eai_again|unable to connect|internal server error|capacity", re.I)


def _failure_key(o: dict) -> tuple[str, str]:
    """(class, text with ids/numbers collapsed): two workers fail identically when their keys match."""
    text = re.sub(r"[0-9a-f]{8,}|\d+", "#", " ".join((o.get("text") or "").lower().split()))
    return (o.get("class") or "", text)


def identical_run(run: list[dict]) -> int:
    """How many of the newest breaker outcomes (newest first) are the same NON-transient failure.
    0 when switched off (CPP_BREAKER_IDENTICAL=off) or when the newest is a known transient."""
    if os.environ.get("CPP_BREAKER_IDENTICAL", "").lower() == "off" or not run:
        return 0
    head = run[0]
    if head.get("class") not in (TRANSIENT, NO_REPLY, TOOL_FAILURE):
        return 0
    if head.get("class") != TOOL_FAILURE and KNOWN_TRANSIENT_RE.search(head.get("text") or ""):
        return 0  # a provider transient recovers on its own; a tool that fails the same way twice does not
    key = _failure_key(head)
    n = 0
    for o in run:
        if _failure_key(o) != key:
            break
        n += 1
    return n


# P4 tool-failure signal (Owner 2026-11-20). A worker whose model DID answer, but whose newest
# TOOL_FAIL_STREAK tool results were the same tool failing with the same error, ended stuck. One such
# worker holds nothing (the next one may pivot); two in a row with the same failure are Regla 12 across
# workers and quarantine via identical_run. Kill switch CPP_BREAKER_TOOL_FAILURE=off.
TOOL_FAILURE = "tool_failure"
TOOL_FAIL_STREAK = 2
# Matched against the NORMALISED error (lowercase, digits and long hex collapsed to '#').
TRIVIAL_TOOL_ERROR_RE = re.compile(r"^(?:error:? )?exit code #\.?$")
POLICY_REFUSAL_RE = re.compile(r"hook|blocked by|doesn't want to proceed|tool use was rejected|permission to use")
_DIGEST_ALPHABET = str.maketrans("0123456789abcdef", "ghijklmnopqrstuv")  # never collapsed by _failure_key


def _digest(norm: str) -> str:
    import hashlib
    return hashlib.sha256(norm.encode()).hexdigest()[:12].translate(_DIGEST_ALPHABET)


def _block_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def tool_failure(rows: list[dict]) -> dict | None:
    """{"class": TOOL_FAILURE, "text": "<tool>: <error>"} when the newest TOOL_FAIL_STREAK tool results in
    `rows` are errors of one tool with one (normalised) error and no success came after them; else None."""
    if os.environ.get("CPP_BREAKER_TOOL_FAILURE", "").lower() == "off":
        return None
    names: dict[str, str] = {}
    results: list[tuple[str, str, bool]] = []
    for row in rows:
        msg = row.get("message") if isinstance(row.get("message"), dict) else {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use" and b.get("id"):
                names[b["id"]] = str(b.get("name") or "?")
            elif b.get("type") == "tool_result":
                text = " ".join(_block_text(b.get("content")).split())[:300]
                results.append((names.get(b.get("tool_use_id"), "?"), text, b.get("is_error") is True))
    tail = results[-TOOL_FAIL_STREAK:]
    if len(tail) < TOOL_FAIL_STREAK or not all(err for _, _, err in tail):
        return None
    keys = {_failure_key({"class": name, "text": text}) for name, text, _ in tail}
    if len(keys) != 1:
        return None
    norm = next(iter(keys))[1]
    if TRIVIAL_TOOL_ERROR_RE.search(norm) or POLICY_REFUSAL_RE.search(norm):
        return None  # a bare exit code (grep with no match) or a hook/user refusal is not a stuck tool
    name = tail[-1][0]
    # The raw result is untrusted and may echo a header or token: only the tool and a digest of the
    # normalised error leave this function. The digest keeps identical_run's comparison exact.
    return {"class": TOOL_FAILURE, "text": f"{name}: repeated error {_digest(norm)}"}


# P4 external-effect reconciliation (Owner 2026-11-20). The breaker is asked only when a worker's turn is
# over (relay/replace), so a final effect call with NO result, or one the host interrupted, is an effect whose
# outcome nobody knows: a successor would repeat it blind. Quarantine at once; `provider_breaker.py clear`
# (after the operator checks the remote side) is the reconciliation. Never retried here. Only the matched
# verb is reported, never the command (it can carry a credential). Kill switch CPP_BREAKER_EFFECT=off.
EFFECT_UNCONFIRMED = "effect_unconfirmed"
# (fixed label, pattern): the label is what gets reported, so no captured text can leak a header or token.
EFFECTS = [(label, re.compile(p, re.I)) for label, p in (
    ("git push", r"\bgit(?:\.exe)?['\"]?(?:\s+-[Cc]\s+\S+)*\s+push\b"),
    ("gh write", r"\bgh\s+(?:pr|release|issue|repo)\s+(?:create|merge|edit|delete|close)\b|"
                 r"\bgh\s+api\b[^|;]*-X\s*(?:POST|PUT|PATCH|DELETE)\b"),
    ("npm publish", r"\bnpm\s+publish\b"),
    ("deploy", r"\bdeploy\b"),
    ("kubectl write", r"\bkubectl\s+(?:apply|delete)\b"),
    ("helm write", r"\bhelm\s+(?:install|upgrade)\b"),
    ("terraform apply", r"\bterraform\s+apply\b"),
    ("ssh", r"\bssh\s"),
    ("scp", r"\bscp\s"),
    ("http write", r"\bcurl\b[^|;]*-X\s*(?:POST|PUT|PATCH|DELETE)\b|-Method\s+(?:Post|Put|Patch|Delete)\b"),
    ("vercel", r"\bvercel\b"),
)]
EFFECT_MCP_RE = re.compile(r"^mcp__.+__(?:send|create|post|publish|reply|forward|delete|merge|push|update)(?:_|$)",
                           re.I)
# Only the HOST's interrupt marker: the effect may have run. A user rejection ("doesn't want to proceed")
# means it did not run, and a KeyboardInterrupt inside a remote traceback is a returned, known outcome.
INTERRUPTED_RE = re.compile(r"\[request interrupted by user", re.I)


def effect_unconfirmed(rows: list[dict]) -> dict | None:
    """{"class": EFFECT_UNCONFIRMED, "text": "<tool>: <verb>", "at"} when the worker's LAST tool call is an
    external effect with no result, or with a host-interrupted result; else None."""
    if os.environ.get("CPP_BREAKER_EFFECT", "").lower() == "off":
        return None
    last = None
    results: dict[str, tuple[bool, str]] = {}
    for row in rows:
        msg = row.get("message") if isinstance(row.get("message"), dict) else {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use" and b.get("id"):
                last = (b, row)
            elif b.get("type") == "tool_result" and b.get("tool_use_id"):
                results[b["tool_use_id"]] = (b.get("is_error") is True, _block_text(b.get("content")))
    if not last:
        return None
    use, row = last
    res = results.get(use["id"])
    if res is not None and not (res[0] and INTERRUPTED_RE.search(res[1] or "")):
        return None  # the call returned: its outcome is on the record
    name = str(use.get("name") or "?")
    if EFFECT_MCP_RE.search(name):
        verb = name.split("__")[-1]
    else:
        inp = use.get("input") if isinstance(use.get("input"), dict) else {}
        cmd = str(inp.get("command") or "")
        verb = next((label for label, rx in EFFECTS if rx.search(cmd)), None)
        if verb is None:
            return None
    state = "no result" if res is None else "interrupted"
    return {"class": EFFECT_UNCONFIRMED, "text": f"{name}: {verb} ({state})",
            "at": lr._parse_iso(row.get("timestamp"))}


def enabled() -> bool:
    return os.environ.get("CPP_PROVIDER_BREAKER", "").lower() != "off"


def _gm():
    import gsd_mission as gm
    return gm


def classify(text: str | None) -> str:
    """Class of a HOST-written reply (never call on model output)."""
    t = text or ""
    if _gm().QUOTA_RE.search(t):
        return QUOTA
    if AUTH_RE.search(t):
        return AUTH
    return TRANSIENT


def worker_outcome(session_id: str, find=None) -> dict:
    """How did this worker's LAST turn end? {"class": None|quota|auth|transient|no_reply, "text", "at"}.
    None = the model answered (a real turn). Unreadable transcripts are UNKNOWN and never a class."""
    find = find or lr.find_transcript
    try:
        path = find(session_id)
    except Exception:  # noqa: BLE001
        path = None
    if not path:
        return {"class": None, "unknown": "transcript not found"}
    try:
        rows = lr._tail_rows(path)
        at = os.path.getmtime(path)
    except Exception as exc:  # noqa: BLE001
        return {"class": None, "unknown": f"unreadable: {exc.__class__.__name__}"}
    eff = effect_unconfirmed(rows)
    if eff:
        return {**eff, "at": eff.get("at") or at}  # an unknown remote outcome outranks how the turn ended
    for row in reversed(rows):
        if row.get("type") != "assistant":
            continue
        # WHEN the turn ended is the row's own timestamp; the mtime moves on as the host appends
        # cost/prompt rows. quota_hold anchors a time-only reset on this value (gsd_mission
        # 9b4c64d): with the mtime, "resets 4pm" written at 15:51 read as tomorrow's 4pm.
        row_at = lr._parse_iso(row.get("timestamp")) or at
        msg = row.get("message") if isinstance(row.get("message"), dict) else {}
        text = "".join(b.get("text", "") for b in (msg.get("content") or []) if isinstance(b, dict))
        if msg.get("model") == "<synthetic>":
            return {"class": classify(text), "text": " ".join(text.split())[:200], "at": row_at}
        tf = tool_failure(rows)
        return {**tf, "at": row_at} if tf else {"class": None, "at": row_at}
    # No assistant row in the tail. Only call it no_reply if the transcript is small enough that
    # the tail IS the whole file; otherwise the evidence is out of our aperture.
    if path.stat().st_size <= lr.TAIL_BYTES:
        return {"class": NO_REPLY, "text": "worker produced no assistant reply", "at": at}
    return {"class": None, "unknown": "no assistant row within the read window"}


def mission_workers(mission_id: str) -> list[str]:
    seen: list[str] = []
    for e in lr.ledger_events(mission_id):
        if e.get("event") in ("worker_acked", "worker_adopted") and e.get("worker") and e["worker"] not in seen:
            seen.append(e["worker"])
    return seen


def last_clear(mission_id: str) -> float | None:
    ts = [lr._parse_iso(e.get("ts")) for e in lr.ledger_events(mission_id) if e.get("event") == "provider_cleared"]
    ts = [t for t in ts if t]
    return max(ts) if ts else None


def _secs(value) -> float | None:
    """Credentials instants are epoch milliseconds; 0 is kept as 0.0 (the measured mark of an
    invalidated login). Anything that is not a number is unmeasured."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value == 0:
        return 0.0
    return value / 1000.0 if value > 1e11 else float(value)


def credentials_state(home=None) -> dict:
    """Shape of ~/.claude/.credentials.json, never its secrets: the seven keys below and nothing else.
    expires_at / refresh_expires_at are epoch SECONDS (the file stores milliseconds); refresh_token
    is only whether the key is present."""
    path = (Path(home) if home else Path.home()) / ".claude" / ".credentials.json"
    out = {"path": str(path), "readable": False, "mtime": None, "expires_at": None,
           "refresh_token": False, "refresh_expires_at": None, "why": ""}
    try:
        out["mtime"] = path.stat().st_mtime
    except FileNotFoundError:
        out["why"] = "missing"
        return out
    except OSError as exc:
        out["why"] = exc.__class__.__name__
        return out
    try:
        oauth = json.loads(path.read_text(encoding="utf-8"))["claudeAiOauth"]
        if not isinstance(oauth, dict):
            raise TypeError("claudeAiOauth is not an object")
        out["expires_at"] = _secs(oauth.get("expiresAt"))
        out["refresh_expires_at"] = _secs(oauth.get("refreshTokenExpiresAt"))
        out["refresh_token"] = "refreshToken" in oauth
        out["readable"] = True
    except Exception as exc:  # noqa: BLE001 -- the class name only: a message could quote file content
        out["why"] = exc.__class__.__name__
    return out


def credentials_expired(cred: dict, now: float) -> bool | None:
    """True / False when the login can be judged, None when it cannot (unreadable, no expiresAt, or a lapsed
    access token whose refresh token carries no known expiry).
    The access token lapses every few hours and the CLI refreshes it with the refresh token, so a
    past expiresAt alone is NOT expired (a preflight refusing it would deadlock an idle env);
    expiresAt 0 is the measured a7 mark of an invalidated login."""
    if not cred or not cred.get("readable"):
        return None
    exp = cred.get("expires_at")
    if exp is None:
        return None
    if exp <= 0:
        return True
    if exp > now:
        return False
    if not cred.get("refresh_token"):
        return True
    rexp = cred.get("refresh_expires_at")
    if rexp is None:
        return None          # lapsed access token + refresh token of unknown validity: cannot judge, never "usable"
    return rexp <= now


def _iso(ts: float) -> str:
    import datetime as _dt
    return _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).isoformat(timespec="seconds")


def auth_released(evidence_at: float, cred: dict, now: float) -> str | None:
    """A one-line reason when a re-login qualifies as the precondition change for an AUTH quarantine:
    credentials rewritten strictly AFTER the refusal and still usable. Everything else keeps the park
    (unmeasurable included: churn is the harm being prevented, and `clear` remains)."""
    if os.environ.get("CPP_BREAKER_CRED_RELEASE", "").lower() == "off":
        return None
    if not cred or not cred.get("readable"):
        return None
    mtime = cred.get("mtime")
    if mtime is None or not mtime > evidence_at:
        return None
    if credentials_expired(cred, now) is not False:
        return None
    return f"credentials rewritten {_iso(mtime)} after the refusal at {_iso(evidence_at)}; access token usable"


def decide(mission_id: str, owner_sid: str, now: float, *, workers=None, outcome=worker_outcome,
           cleared_at=None, credentials=None, trace=None) -> dict | None:
    """The hold for this mission's next successor, or None. Pure over its injected readers.
    `credentials` is a callable returning a credentials_state() dict; `trace`, when a dict, receives
    {"released": reason} if a re-login released an AUTH quarantine."""
    first = outcome(owner_sid)
    cls = first.get("class")
    if cls is None:
        return None
    if cls == QUOTA:
        h = _gm().quota_hold(first.get("text"), first.get("at"), now)
        return None if h is None else {**h, "class": QUOTA, "streak": 1, "quarantine": False}
    ws = list(workers if workers is not None else mission_workers(mission_id))
    if owner_sid in ws:
        ws = ws[: ws.index(owner_sid) + 1]
    streak = 0
    run: list[dict] = []
    for sid in reversed(ws[-STREAK_WINDOW:]):
        o = first if sid == owner_sid else outcome(sid)
        if o.get("class") in (AUTH, TRANSIENT, NO_REPLY, QUOTA):
            streak += 1
            run.append(o)
        elif o.get("class") == TOOL_FAILURE:
            run.append(o)  # Regla 12 evidence only: a stuck tool is not a provider failure, so no streak
        else:
            break
    streak = max(streak, 1)
    if not run:
        run = [first]
    clear = cleared_at if cleared_at is not None else last_clear(mission_id)
    evidence_at = float(first.get("at") or now)
    if clear and clear >= evidence_at:
        return None  # an operator cleared the breaker after this evidence was written
    if cls == AUTH:
        released = auth_released(evidence_at, (credentials or credentials_state)(), now)
        if released:
            if isinstance(trace, dict):
                trace["released"] = released
            return None  # a re-login after the refusal: the qualifying precondition change
    reason = f"{cls}: {first.get('text', '')}"[:220]
    identical = identical_run(run)
    if cls in (AUTH, EFFECT_UNCONFIRMED) or streak >= QUARANTINE_AFTER or identical >= IDENTICAL_AFTER:
        if cls == AUTH:
            why = "credentials"
        elif cls == EFFECT_UNCONFIRMED:
            why = "an external effect was started and never confirmed; check the remote side, then clear"
        elif streak >= QUARANTINE_AFTER:
            why = f"{streak} consecutive workers ended in provider failure"
        else:
            why = f"{identical} identical non-transient failures in a row (Regla 12)"
        return {"until": None, "reason": f"QUARANTINE ({why}) -- {reason}", "class": cls, "streak": streak,
                "quarantine": True}
    if cls == TOOL_FAILURE:
        return None  # the provider is fine: one stuck worker earns no backoff; the next may pivot
    wait = min(BACKOFF_CAP_S, BACKOFF_BASE_S * 2 ** (streak - 1))
    until = evidence_at + wait
    if now >= until:
        return None
    return {"until": until, "reason": reason, "class": cls, "streak": streak, "quarantine": False}


def hold_for(rec: dict, now: float, cleared_at=None) -> dict | None:
    """Entry point for gsd_mission's supervisor. Falls back to quota_hold when disabled. `cleared_at` overrides
    the instant of the last operator clear (lineage_hold passes the later of the successor's and the
    predecessor's)."""
    gm = _gm()
    sid = (rec.get("owner") or {}).get("session_id")
    if not sid:
        return None
    # Quota detection stays with its owner (gsd_mission.quota_hold_from_transcript): one detector,
    # asked first. The breaker only ADDS the classes that owner never covered.
    h = gm.quota_hold_from_transcript(sid, now)
    if h is not None:
        return {**h, "class": QUOTA, "streak": 1, "quarantine": False}
    if not enabled():
        return None
    trace: dict = {}
    hold = decide(rec.get("mission_id"), sid, now, cleared_at=cleared_at, trace=trace)
    if trace.get("released"):
        lr.ledger_append(rec.get("mission_id"), "provider_released", mission_id=rec.get("mission_id"),
                         reason=trace["released"])
    return hold


def lineage_hold(rec: dict, now: float, load=None) -> dict | None:
    """The hold a RENEWED successor inherits from the lineage it continues, or None.

    hold_for needs an owner, and a PREPARED successor has none: its `launch` action never reaches
    the relay-only provider hold. Measured on the a7 install: the lineage was renewed after its dead
    iterations -- plan_next halts a mission at its hours budget before any provider hold is read,
    GSD answers OK, the renewal is permitted, and each fresh successor launched one worker into the
    same `Login expired` refusal. A budget renewal must not launder a quarantine.

    The NEAREST predecessor (walking `renewed_from`) that has an owner decides, through hold_for, so a
    healthy nearest predecessor means nothing to inherit and a re-login after the refusal still
    releases. The walk is bounded: a seen-set and at most MAX_LINEAGE_HOPS records, so records that
    point at each other, or a missing or unreadable one, end it with None (an unmeasured lineage is
    not a quarantine; the relay path stays the backstop). A record that has an owner is the relay
    path's case, and a disabled breaker inherits nothing."""
    if not enabled() or rec.get("owner"):
        return None
    load = load or _gm().load
    seen = {rec.get("mission_id")}
    cur = rec
    for _ in range(MAX_LINEAGE_HOPS):
        pid = cur.get("renewed_from")
        if not pid or pid in seen:
            return None
        seen.add(pid)
        try:
            pred = load(pid)
        except Exception:  # noqa: BLE001 -- an unreadable record is unmeasured, not a hold
            return None
        if not isinstance(pred, dict):
            return None
        if pred.get("owner"):
            # An operator clears the id the supervisor row and the logs show, which is the SUCCESSOR's; the hold
            # itself is keyed by the predecessor's. A clear on either releases it.
            clears = [t for t in (last_clear(rec.get("mission_id")), last_clear(pred.get("mission_id") or pid)) if t]
            h = hold_for(pred, now, cleared_at=max(clears) if clears else None)
            return None if h is None else {**h, "inherited_from": pred.get("mission_id") or pid}
        cur = pred
    return None


def _cli(argv=None) -> int:
    ap = argparse.ArgumentParser(description="provider circuit breaker")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status")
    s.add_argument("--mission", required=True)
    c = sub.add_parser("clear")
    c.add_argument("--mission", required=True)
    c.add_argument("--note", default="")
    a = ap.parse_args(argv)
    if a.cmd == "clear":
        ok = lr.ledger_append(a.mission, "provider_cleared", mission_id=a.mission, note=a.note[:200])
        print(json.dumps({"cleared": bool(ok), "mission": a.mission}))
        return 0 if ok else 2
    gm = _gm()
    rec = gm.load(a.mission) if hasattr(gm, "load") else None
    if not rec:
        print(json.dumps({"mission": a.mission, "error": "mission record not found"}))
        return 3
    now = time.time()
    # a PREPARED renewal successor has no owner, so hold_for is None for it while the gate refuses its launch
    print(json.dumps({"mission": a.mission, "hold": hold_for(rec, now) or lineage_hold(rec, now)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
