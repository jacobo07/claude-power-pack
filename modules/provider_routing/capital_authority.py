"""Owner Capital Authority (OCA): a capital packet is applied only on evidence that the OWNER typed the approval.

The only authority is a transcript entry carrying the harness fields the model cannot author for itself:
type=user, origin.kind=human, promptSource=typed|queued, string content. An assistant line, a tool_result or a hook
injection never counts. Apply is bound to the packet's sha256, idempotent per (sha, goal), revalidated against the
ledger at apply time, and written append-only to a capsule store.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import time
from pathlib import Path

STATES = ("BOUND", "OWNER_APPROVED", "REVALIDATING", "APPLIED", "RECEIPTED", "RELEASED", "INVALIDATED",
          "REJECTED", "FAILED_SAFE", "REVOKED")
DRIFT_ALLOWANCE = 500_000
# "queued" = typed by the Owner while Stop hooks were still running (same as tools/fanout_ledger.py HUMAN).
OWNER_PROMPT_SOURCES = ("typed", "queued")
_NEG = re.compile(r"(?:\b(?:don't|dont|do not|not|never|can't|cannot|no)\b|n't\b)")
_GOAL = r"[a-z0-9][a-z0-9._-]*"
_TIER = r"p(?:50|80|95)"


def capital_root(root=None) -> Path:
    return Path(root or os.environ.get("CPP_CAPITAL_ROOT") or Path.home() / ".claude" / "state" / "capital-authority")


def packet_sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _amount(s: str) -> int | None:
    s = s.replace(",", "").replace("_", "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(m|k)?", s)
    if not m:
        return None
    return int(round(float(m.group(1)) * {"m": 1_000_000, "k": 1_000, None: 1}[m.group(2)]))


def parse_approval(text) -> dict | None:
    """Whole-message intent only. Returns {action, tier?, goal?, value?} or None. Any negation is None."""
    if not isinstance(text, str):
        return None
    t = re.sub(r"\s+", " ", text.strip().lower()).rstrip(".!")
    if not t or _NEG.search(t):
        return None
    if re.fullmatch(r"(?:yes[, ]+)?approve(?:d)?(?: everything| all)?", t):
        return {"action": "approve", "tier": None, "goal": None}
    m = re.fullmatch(rf"approve (?:all )?({_TIER})", t)
    if m:
        return {"action": "approve", "tier": m.group(1).upper(), "goal": None}
    m = re.fullmatch(rf"approve ({_GOAL}) only", t)
    if m:
        return {"action": "approve", "tier": None, "goal": m.group(1)}
    m = re.fullmatch(rf"modify ({_GOAL}) to ([0-9][0-9,_.]*[mk]?)", t)
    if m:
        v = _amount(m.group(2))
        return {"action": "modify", "goal": m.group(1), "value": v} if v else None
    m = re.fullmatch(rf"revoke ({_GOAL})", t)
    if m:
        return {"action": "revoke", "goal": m.group(1)}
    return None


def _text_of(entry: dict) -> str:
    c = (entry.get("message") or {}).get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return ""


def _is_owner_typed(e: dict) -> bool:
    c = (e.get("message") or {}).get("content")
    # sessionKind / entrypoint: a --bg worker's launch prompt is stamped origin=human, promptSource=typed
    # (measured 2026-10-11, plan econ-succession 5.1), so a worker or -p/sdk entry is never the Owner.
    return (e.get("type") == "user" and (e.get("origin") or {}).get("kind") == "human"
            and e.get("promptSource") in OWNER_PROMPT_SOURCES and isinstance(c, str) and not e.get("isMeta")
            and not e.get("sessionKind") and e.get("entrypoint") in (None, "cli"))


def session_provenance(transcript_path) -> str:
    """Class of the session that wrote `transcript_path`, from the harness stamps on its user entries:
    BG (any sessionKind), SDK (entrypoint sdk-cli), INTERACTIVE (entrypoint cli, no sessionKind), else UNKNOWN.
    Unknown is never interactive."""
    seen_cli = seen_sdk = seen_kind = False
    try:
        lines = Path(transcript_path).read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return "UNKNOWN"
    for ln in lines:
        if '"entrypoint"' not in ln and '"sessionKind"' not in ln:
            continue
        try:
            e = json.loads(ln)
        except ValueError:
            continue
        if not isinstance(e, dict) or e.get("type") != "user":
            continue
        seen_kind = seen_kind or bool(e.get("sessionKind"))
        seen_sdk = seen_sdk or e.get("entrypoint") == "sdk-cli"
        seen_cli = seen_cli or e.get("entrypoint") == "cli"
    return "BG" if seen_kind else "SDK" if seen_sdk else "INTERACTIVE" if seen_cli else "UNKNOWN"


def find_owner_decisions(transcript_path, sha: str) -> list[dict]:
    """Every parsed Owner decision typed after the first assistant entry that displayed `sha`, in file order."""
    out, seen = [], False
    try:
        lines = Path(transcript_path).read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return []
    for ln in lines:
        try:
            e = json.loads(ln)
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        if not seen:
            seen = e.get("type") == "assistant" and sha in _text_of(e)
            continue
        if _is_owner_typed(e):
            d = parse_approval(e["message"]["content"])
            if d:
                out.append({"uuid": e.get("uuid"), "timestamp": e.get("timestamp"),
                            "text": e["message"]["content"], "decision": d})
    return out


def find_owner_approval(transcript_path, packet_sha_: str) -> dict | None:
    return next((d for d in find_owner_decisions(transcript_path, packet_sha_)
                 if d["decision"]["action"] in ("approve", "modify")), None)


# --- capsule store (append-only) ---------------------------------------------------------------------------
def _rows(root) -> list[dict]:
    p = capital_root(root) / "capsules.jsonl"
    if not p.exists():
        return []
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(ln))
        except ValueError:
            continue
    return out


def _append(root, row: dict) -> dict:
    assert row["state"] in STATES, row["state"]
    d = capital_root(root)
    d.mkdir(parents=True, exist_ok=True)
    with (d / "capsules.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def status(root=None) -> dict:
    latest: dict = {}
    for r in _rows(root):
        latest[(r.get("sha"), r.get("goal"))] = r
    return {"ok": True, "capsules": list(latest.values())}


def _refuse(root, sha, goal, state, reason, **extra) -> dict:
    row = _append(root, {"ts": time.time(), "sha": sha, "goal": goal, "state": state, "reason": reason, **extra})
    return {"ok": False, "applied": False, "state": state, "reason": reason, "row": row}


def _expired(packet: dict, now: float) -> bool:
    exp = packet.get("expires")
    if not exp:
        return True                                        # no expiry on a capital packet is not an approval
    return now > dt.datetime.fromisoformat(exp).timestamp()


def _spend(led) -> tuple[int, dict]:
    g = led._gfold(led._read())
    return sum(g["marks"].values()) + g["open"], g


def apply(packet_path, transcript_path, goal: str, ledger_factory, now: float | None = None, root=None) -> dict:
    now = time.time() if now is None else now
    sha = packet_sha(packet_path)
    packet = json.loads(Path(packet_path).read_text(encoding="utf-8-sig"))
    prog = next((p for p in packet.get("programmes", []) if p.get("goal") == goal), None)
    if prog is None:
        return _refuse(root, sha, goal, "REJECTED", f"goal {goal!r} is not in packet {sha[:12]}")
    rows = _rows(root)
    if any(r.get("goal") == goal and r.get("state") == "REVOKED" for r in rows):
        return _refuse(root, sha, goal, "REJECTED", f"REVOKED: the Owner revoked {goal}")
    if any(r.get("sha") == sha and r.get("goal") == goal and r.get("state") in ("APPLIED", "RECEIPTED") for r in rows):
        return {"ok": True, "applied": False, "state": "APPLIED", "reason": "already applied (idempotent)"}
    if _finalized(rows, sha, goal):
        return {"ok": False, "applied": False, "state": "INVALIDATED", "reason": "packet finally invalidated"}
    appr = next((d for d in find_owner_decisions(transcript_path, sha)
                 if d["decision"]["action"] in ("approve", "modify")
                 and d["decision"].get("goal") in (None, goal)), None)
    if appr is None:
        # not journalled: the hook retries this while the transcript flushes
        return {"ok": False, "applied": False, "state": "REJECTED",
                "reason": "no Owner-typed approval for this packet hash and goal"}
    if _expired(packet, now):
        return _refuse(root, sha, goal, "INVALIDATED", "packet expired", approval=appr["uuid"])
    led = ledger_factory(goal)
    spent, g = _spend(led)
    base = prog["measured_at_packet"]
    if spent > base["settled"] + base["open"] + DRIFT_ALLOWANCE:
        return _refuse(root, sha, goal, "INVALIDATED",
                       f"spend moved: {spent:,} > packet {base['settled'] + base['open']:,} + {DRIFT_ALLOWANCE:,}",
                       approval=appr["uuid"])
    d = appr["decision"]
    ceilings = prog["ceilings"]
    if d["action"] == "modify":
        if d["value"] > ceilings["P95"]:
            return _refuse(root, sha, goal, "REJECTED",
                           f"modify {d['value']:,} exceeds P95 {ceilings['P95']:,}", approval=appr["uuid"])
        ceiling = d["value"]
    else:
        ceiling = ceilings[d.get("tier") or packet.get("default_tier", "P80")]
    if ceiling <= spent:
        return _refuse(root, sha, goal, "REJECTED", f"ceiling {ceiling:,} <= spend {spent:,}", approval=appr["uuid"])
    old = g["programme"]
    out = led.set_programme(ceiling, f"capital:{sha[:12]}:{goal}:{appr['uuid']}", inside_agent=False)
    if not out.get("ok"):
        return _refuse(root, sha, goal, "FAILED_SAFE", str(out.get("reason")), approval=appr["uuid"])
    row = _append(root, {"ts": now, "sha": sha, "goal": goal, "state": "APPLIED", "old_programme": old,
                         "new_programme": ceiling, "delta": ceiling - (old or 0), "approval": appr["uuid"],
                         "approval_ts": appr["timestamp"], "scope": prog.get("scope"),
                         "stop_loss": prog.get("stop_loss"), "excluded": prog.get("excluded"),
                         "invalidators": packet.get("invalidators")})
    return {"ok": True, "applied": True, "state": "APPLIED", "reason": "", "row": row}


def revoke(packet_path, transcript_path, goal: str, ledger_factory, now: float | None = None, root=None) -> dict:
    now = time.time() if now is None else now
    sha = packet_sha(packet_path)
    rows = _rows(root)
    if any(r.get("goal") == goal and r.get("state") == "REVOKED" for r in rows):
        return {"ok": True, "revoked": False, "state": "REVOKED", "reason": "already revoked (idempotent)"}
    rev = next((d for d in find_owner_decisions(transcript_path, sha)
                if d["decision"]["action"] == "revoke" and d["decision"]["goal"] == goal), None)
    if rev is None:
        return _refuse(root, sha, goal, "REJECTED", "no Owner-typed revoke for this goal")
    led = ledger_factory(goal)
    spent, g = _spend(led)
    out = led.set_programme(max(spent, 1), f"capital-revoke:{sha[:12]}:{goal}:{rev['uuid']}", inside_agent=False)
    row = _append(root, {"ts": now, "sha": sha, "goal": goal, "state": "REVOKED", "approval": rev["uuid"],
                         "old_programme": g["programme"], "new_programme": max(spent, 1), "ledger_ok": out.get("ok")})
    return {"ok": bool(out.get("ok")), "revoked": True, "state": "REVOKED", "reason": "", "row": row}


def _finalized(rows, sha, goal) -> bool:
    """A control-plane INVALIDATED row (`invalidate`) is final for its (sha, goal); a drift/expiry row is not."""
    return any(r.get("sha") == sha and r.get("goal") == goal and r.get("state") == "INVALIDATED" and r.get("final")
               for r in rows)


# --- durable receipts (econ-succession S3) -----------------------------------------------------------------
# An approval becomes an immutable OWNER_APPROVED receipt at the moment it is typed, validated THEN (expiry and
# spend drift are judged at approval time, not when a later sweep gets to it). Applying a receipt never
# re-reads the clock against the packet's expiry. Only the hook process and this module write receipts.
def receipts(root=None) -> list[dict]:
    p = capital_root(root) / "receipts.jsonl"
    if not p.exists():
        return []
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(ln))
        except ValueError:
            continue
    return out


def _receipt_id(sha: str, goal: str) -> str:
    return hashlib.sha256(f"{sha}|{goal}".encode()).hexdigest()[:16]


def _issue_receipt(root, packet_path, goal, decision, approval, approval_ts, provenance, ledger_factory, now,
                   session=None) -> dict:
    sha = packet_sha(packet_path)
    packet = json.loads(Path(packet_path).read_text(encoding="utf-8-sig"))
    prog = next((p for p in packet.get("programmes", []) if p.get("goal") == goal), None)
    if prog is None:
        return _refuse(root, sha, goal, "REJECTED", f"goal {goal!r} is not in packet {sha[:12]}")
    rows = _rows(root)
    if any(r.get("goal") == goal and r.get("state") == "REVOKED" for r in rows):
        return _refuse(root, sha, goal, "REJECTED", f"REVOKED: the Owner revoked {goal}")
    if _finalized(rows, sha, goal):
        return {"ok": False, "issued": False, "state": "INVALIDATED", "reason": "packet finally invalidated"}
    rid = _receipt_id(sha, goal)
    have = next((r for r in receipts(root) if r.get("id") == rid), None)
    if have:
        return {"ok": True, "issued": False, "id": rid, "state": "OWNER_APPROVED",
                "reason": "already receipted (idempotent)", "receipt": have}
    if _expired(packet, now):
        return _refuse(root, sha, goal, "INVALIDATED", "packet expired before the approval was recorded",
                       approval=approval)
    spent, _g = _spend(ledger_factory(goal))
    base = prog["measured_at_packet"]
    if spent > base["settled"] + base["open"] + DRIFT_ALLOWANCE:
        return _refuse(root, sha, goal, "INVALIDATED",
                       f"spend moved before the approval: {spent:,} > packet {base['settled'] + base['open']:,}"
                       f" + {DRIFT_ALLOWANCE:,}", approval=approval)
    ceilings = prog["ceilings"]
    if decision["action"] == "modify":
        if decision["value"] > ceilings["P95"]:
            return _refuse(root, sha, goal, "REJECTED",
                           f"modify {decision['value']:,} exceeds P95 {ceilings['P95']:,}", approval=approval)
        ceiling = decision["value"]
    else:
        ceiling = ceilings[decision.get("tier") or packet.get("default_tier", "P80")]
    if ceiling <= spent:
        return _refuse(root, sha, goal, "REJECTED", f"ceiling {ceiling:,} <= spend {spent:,}", approval=approval)
    row = {"id": rid, "ts": now, "state": "OWNER_APPROVED", "sha": sha, "goal": goal, "packet": str(packet_path),
           "tier": decision.get("tier") or packet.get("default_tier", "P80"), "ceiling": ceiling,
           "approval": approval, "approval_ts": approval_ts, "provenance": provenance, "session": session,
           "scope": prog.get("scope"), "stop_loss": prog.get("stop_loss"), "excluded": prog.get("excluded"),
           "invalidators": packet.get("invalidators"), "spend_at_approval": spent}
    d = capital_root(root)
    d.mkdir(parents=True, exist_ok=True)
    with (d / "receipts.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return {"ok": True, "issued": True, "id": rid, "state": "OWNER_APPROVED", "reason": "", "receipt": row}


def record_receipt(packet_path, transcript_path, goal: str, ledger_factory, now: float | None = None,
                   root=None) -> dict:
    """TRANSCRIPT_TYPED: receipt an approval the Owner typed after the packet was displayed (rule (a))."""
    now = time.time() if now is None else now
    sha = packet_sha(packet_path)
    appr = next((d for d in find_owner_decisions(transcript_path, sha)
                 if d["decision"]["action"] in ("approve", "modify")
                 and d["decision"].get("goal") in (None, goal)), None)
    if appr is None:
        return {"ok": False, "issued": False, "state": "REJECTED",
                "reason": "no Owner-typed approval for this packet hash and goal"}
    return _issue_receipt(root, packet_path, goal, appr["decision"], appr["uuid"], appr["timestamp"],
                          "TRANSCRIPT_TYPED", ledger_factory, now)


def _displayed(transcript_path, sha: str) -> bool:
    try:
        for ln in Path(transcript_path).read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if sha in ln:
                e = json.loads(ln)
                if isinstance(e, dict) and e.get("type") == "assistant" and sha in _text_of(e):
                    return True
    except (OSError, ValueError):
        pass
    return False


def record_receipt_from_prompt(prompt, transcript_path, session_id: str, goal: str, ledger_factory,
                               now: float | None = None, root=None, wait: float = 3.0,
                               sleep=time.sleep) -> dict:
    """HOOK_ATTESTED_INTERACTIVE: the pre-model hook passes the prompt being submitted. Admitted only when the
    session's own transcript proves an interactive pane (plan 5.1) and EXACTLY ONE pending packet for `goal`
    was displayed in it and is not already finished. Ambiguity is a refusal, never a guess."""
    now = time.time() if now is None else now
    d = parse_approval(prompt)
    if not d or d["action"] not in ("approve", "modify") or d.get("goal") not in (None, goal):
        return {"ok": False, "issued": False, "reason": "not an approval for this goal"}
    prov = session_provenance(transcript_path)
    if prov != "INTERACTIVE":
        return {"ok": False, "issued": False, "reason": f"session provenance {prov}: only an interactive pane approves"}
    try:
        pend = json.loads((capital_root(root) / "pending.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {"ok": False, "issued": False, "reason": "no pending packets"}
    rows = _rows(root)
    cands = []
    for ent in pend if isinstance(pend, list) else [pend]:
        if goal not in (ent.get("goals") or []):
            continue
        try:
            sha = packet_sha(ent["packet"])
        except (OSError, KeyError):
            continue
        if _displayed(transcript_path, sha) and not _finalized(rows, sha, goal) and not any(
                r.get("sha") == sha and r.get("goal") == goal and r.get("state") in ("APPLIED", "RECEIPTED")
                for r in rows):
            cands.append((ent["packet"], sha))
    if len(cands) != 1:
        return {"ok": False, "issued": False,
                "reason": f"{len(cands)} displayed pending packets for {goal}: exactly one is required"}
    packet_path, sha = cands[0]
    # The prompt argument is only a claim: any process can pass one (review 2026-10-11, HIGH). Admit it only
    # when the session transcript carries the same decision as an Owner-typed entry after the display; the
    # transcript flushes late, so poll briefly and otherwise refuse (the detached sweep applies from the
    # transcript route later).
    deadline = time.time() + wait
    while True:
        typed = next((x for x in find_owner_decisions(transcript_path, sha) if x["decision"] == d), None)
        if typed is not None or time.time() >= deadline:
            break
        sleep(0.25)
    if typed is None:
        return {"ok": False, "issued": False, "reason": "the approval is not yet in the transcript as Owner-typed"}
    return _issue_receipt(root, packet_path, goal, d, typed["uuid"], typed["timestamp"],
                          "HOOK_ATTESTED_INTERACTIVE", ledger_factory, now, session=session_id)


def apply_receipt(packet_path, goal: str, ledger_factory, now: float | None = None, root=None) -> dict:
    """Apply an issued receipt: the packet bytes must still be the approved bytes; expiry and drift are NOT
    re-judged against the clock (they were judged at approval). Idempotent."""
    now = time.time() if now is None else now
    sha = packet_sha(packet_path)
    mine = [r for r in receipts(root) if r.get("goal") == goal and r.get("packet") == str(packet_path)]
    rec = next((r for r in mine if r.get("sha") == sha), None)
    if rec is None:
        why = "packet sha changed since the receipt" if mine else f"no receipt for goal {goal!r} on this packet"
        return {"ok": False, "applied": False, "state": "REJECTED", "reason": why}
    rows = _rows(root)
    if any(r.get("goal") == goal and r.get("state") == "REVOKED" for r in rows):
        return _refuse(root, sha, goal, "REJECTED", f"REVOKED: the Owner revoked {goal}")
    if any(r.get("sha") == sha and r.get("goal") == goal and r.get("state") in ("APPLIED", "RECEIPTED") for r in rows):
        return {"ok": True, "applied": False, "state": "APPLIED", "reason": "already applied (idempotent)"}
    if _finalized(rows, sha, goal):
        return {"ok": False, "applied": False, "state": "INVALIDATED", "reason": "packet finally invalidated"}
    led = ledger_factory(goal)
    spent, g = _spend(led)
    if rec["ceiling"] <= spent:
        return _refuse(root, sha, goal, "REJECTED", f"ceiling {rec['ceiling']:,} <= spend {spent:,}",
                       approval=rec["approval"])
    old = g["programme"]
    out = led.set_programme(rec["ceiling"], f"capital:{sha[:12]}:{goal}:{rec['approval']}", inside_agent=False)
    if not out.get("ok"):
        return _refuse(root, sha, goal, "FAILED_SAFE", str(out.get("reason")), approval=rec["approval"])
    row = _append(root, {"ts": now, "sha": sha, "goal": goal, "state": "APPLIED", "old_programme": old,
                         "new_programme": rec["ceiling"], "delta": rec["ceiling"] - (old or 0),
                         "approval": rec["approval"], "approval_ts": rec["approval_ts"], "receipt": rec["id"],
                         "provenance": rec["provenance"], "scope": rec["scope"], "stop_loss": rec["stop_loss"],
                         "excluded": rec["excluded"], "invalidators": rec["invalidators"]})
    return {"ok": True, "applied": True, "state": "APPLIED", "reason": "", "row": row}


def invalidate(packet_path, goal: str, reason: str, root=None, now: float | None = None) -> dict:
    """Control-plane record that a packet is dead for `goal` (stale before approval, superseded). Final:
    neither apply nor a receipt can resurrect it. Journals; it never touches a programme or a cap."""
    sha = packet_sha(packet_path)
    if _finalized(_rows(root), sha, goal):
        return {"ok": True, "state": "INVALIDATED", "reason": "already invalidated (idempotent)"}
    row = _append(root, {"ts": time.time() if now is None else now, "sha": sha, "goal": goal,
                         "state": "INVALIDATED", "reason": reason, "final": True, "authority": "control-plane"})
    return {"ok": True, "state": "INVALIDATED", "reason": "", "row": row}


def apply_pending(ledger_factory, root=None, timeout: float = 60.0, sleep=time.sleep, now=None) -> list[dict]:
    """Hook leg: retry until the transcript has flushed the Owner entry, then apply every pending goal.
    A goal with a receipt applies from the receipt (no transcript needed); the rest need the Owner entry."""
    base = capital_root(root)
    try:
        pend = json.loads((base / "pending.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []
    try:
        ap = [json.loads(x) for x in (base / "approvals.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    except (OSError, ValueError):
        ap = []
    have = receipts(root)
    if not ap and not have:
        return []
    transcript = ap[-1]["transcript_path"] if ap else None
    deadline, results = time.time() + timeout, []
    for ent in pend if isinstance(pend, list) else [pend]:
        for goal in ent.get("goals", []):
            try:
                cur = packet_sha(ent["packet"])
            except OSError:
                continue
            if any(r.get("goal") == goal and r.get("packet") == str(ent["packet"]) and r.get("sha") == cur
                   for r in have):
                r = apply_receipt(ent["packet"], goal, ledger_factory, now=now, root=root)
                results.append({"goal": goal, **{k: r[k] for k in ("ok", "applied", "reason")}})
                continue
            if transcript is None:
                continue
            while True:
                r = apply(ent["packet"], transcript, goal, ledger_factory, now=now, root=root)
                if r.get("ok") or "no Owner-typed approval" not in r.get("reason", "") or time.time() >= deadline:
                    results.append({"goal": goal, **{k: r[k] for k in ("ok", "applied", "reason")}})
                    break
                sleep(1.0)
    return results
