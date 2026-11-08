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
    return (e.get("type") == "user" and (e.get("origin") or {}).get("kind") == "human"
            and e.get("promptSource") in OWNER_PROMPT_SOURCES and isinstance(c, str) and not e.get("isMeta"))


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


def approval_transcripts(ap: list[dict]) -> list[str]:
    """Transcripts an apply must search: the last row's (a sweep row names the pane to search) and the last
    approval row's. Other panes append sweep rows every few seconds, so reading only the last row missed an
    approval made seconds earlier (ctx-rent-a2 2026-10-24: cost-collapse and cp50-c1 corrections)."""
    last = next((a for a in reversed(ap) if a.get("kind") == "approval"), None)
    out = [ap[-1]["transcript_path"]]
    if last is not None and last["transcript_path"] not in out:
        out.append(last["transcript_path"])
    return out


def apply_pending(ledger_factory, root=None, timeout: float = 60.0, sleep=time.sleep, now=None) -> list[dict]:
    """Hook leg: retry until the transcript has flushed the Owner entry, then apply every pending goal."""
    base = capital_root(root)
    try:
        pend = json.loads((base / "pending.json").read_text(encoding="utf-8-sig"))
        ap = [json.loads(x) for x in (base / "approvals.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    except (OSError, ValueError):
        return []
    if not ap:
        return []
    transcripts = approval_transcripts(ap)
    deadline, results = time.time() + timeout, []
    for ent in pend if isinstance(pend, list) else [pend]:
        for goal in ent.get("goals", []):
            while True:
                for t in transcripts:
                    r = apply(ent["packet"], t, goal, ledger_factory, now=now, root=root)
                    if "no Owner-typed approval" not in r.get("reason", ""):
                        break
                if r.get("ok") or "no Owner-typed approval" not in r.get("reason", "") or time.time() >= deadline:
                    results.append({"goal": goal, **{k: r[k] for k in ("ok", "applied", "reason")}})
                    break
                sleep(1.0)
    return results
