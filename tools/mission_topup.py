#!/usr/bin/env python
"""Mission auto top-up (spec vault/specs/mission-auto-topup.md).

A mission armed overnight should not wait seven hours on a budget stop while it is producing commits, and should
not spend without limit either. The Owner declares, at arm time, an authority plus N top-ups of a fixed step. The
5-minute sweep grants one step when the mission is parked on its mission-authority trip AND the execution root has
non-bookkeeping commits since the last grant. Anything else stays held, recorded, and is surfaced once.

    mission_topup.py budget  --mission M --authority 120M --topups 3 --step 40M [--reason TEXT]
    mission_topup.py suggest --cwd REPO
    mission_topup.py sweep   [--dry-run]
    mission_topup.py status  --mission M

Kill switch: CPP_MISSION_AUTO_TOPUP=off (sweep does nothing).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402
import mission_binding as mb  # noqa: E402

SCHEMA = "mission-topup/1"
AUTHORITY_TRIP = "cost breaker (mission authority)"
DEFAULT_PHASE_TOKENS = 40_000_000   # measured: 154M / 4 phases, Credit Score Engine, 2026-10-15
BOOKKEEPING_PREFIX = ".planning/"


def enabled() -> bool:
    return (os.environ.get("CPP_MISSION_AUTO_TOPUP") or "").strip().lower() != "off"


def policy_path(mission_id: str) -> Path:
    return Path(gm.lr.state_dir()) / f"mission-topup-{mission_id}.json"


def load_policy(mission_id: str) -> dict | None:
    p = policy_path(mission_id)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def save_policy(pol: dict) -> None:
    p = policy_path(pol["mission_id"])
    tmp = p.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(pol, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def parse_tokens(text) -> int:
    """'40M' / '1.5M' / '800K' / '40000000' -> int. Refuses anything else."""
    s = str(text).strip().upper().replace("_", "").replace(",", "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([KMG]?)", s)
    if not m:
        raise ValueError(f"not a token count: {text!r}")
    mult = {"": 1, "K": 1_000, "M": 1_000_000, "G": 1_000_000_000}[m.group(2)]
    n = int(float(m.group(1)) * mult)
    if n <= 0:
        raise ValueError(f"token count must be positive: {text!r}")
    return n


def _git(wd: str, *args: str) -> str | None:
    g = gm.resolve_exe("git") or "git"
    try:
        r = subprocess.run([g, "-C", wd, *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=30)
    except Exception:  # noqa: BLE001 -- unmeasured is its own answer
        return None
    return r.stdout if r.returncode == 0 else None


def head_of(wd: str) -> str | None:
    out = _git(wd, "rev-parse", "HEAD")
    return out.strip() if out else None


def progress_since(wd: str, base: str | None) -> dict:
    """{measured, progress, commits, paths}. Progress = commits after `base` whose diff touches a path outside
    `.planning/`. An unknown base or an unreadable root is unmeasured, never 'no progress'."""
    head = head_of(wd)
    if not head or not base:
        return {"measured": False, "progress": False, "head": head, "why": "root or base unreadable"}
    log = _git(wd, "rev-list", f"{base}..HEAD")
    names = _git(wd, "diff", "--name-only", base, "HEAD")
    if log is None or names is None:
        return {"measured": False, "progress": False, "head": head, "why": f"base {base[:8]} not in history"}
    commits = [c for c in log.split() if c]
    paths = [p for p in names.splitlines() if p.strip() and not p.startswith(BOOKKEEPING_PREFIX)]
    return {"measured": True, "progress": bool(commits) and bool(paths), "head": head,
            "commits": len(commits), "paths": len(paths)}


def is_authority_trip(rec: dict) -> bool:
    hold = rec.get("owner_hold") or {}
    return hold.get("kind") == "cost" and AUTHORITY_TRIP in (hold.get("reason") or "")


def judge(rec: dict | None, pol: dict, prog: dict) -> dict:
    """Pure: {action: none|grant|resume|refuse, why}. `resume` completes a grant already written for this hold."""
    if rec is None or rec.get("state") in gm.TERMINAL:
        return {"action": "none", "why": "mission gone or terminal"}
    if not is_authority_trip(rec):
        return {"action": "none", "why": "no mission-authority cost hold"}
    hold_at = (rec.get("owner_hold") or {}).get("set_at")
    grants = pol.get("grants") or []
    if grants and grants[-1].get("hold_set_at") == hold_at:
        return {"action": "resume", "why": "grant already written for this hold"}
    if len(grants) >= int(pol["max_topups"]):
        return {"action": "refuse", "why": f"top-ups exhausted ({len(grants)}/{pol['max_topups']})"}
    if not prog.get("measured"):
        return {"action": "refuse", "why": f"progress unmeasured: {prog.get('why')}"}
    if not prog.get("progress"):
        return {"action": "refuse", "why": (f"no progress since {str(pol.get('last_head'))[:8]}: "
                                            f"{prog.get('commits', 0)} commit(s), {prog.get('paths', 0)} "
                                            "non-bookkeeping path(s)")}
    return {"action": "grant", "why": f"{prog['commits']} commit(s) touching {prog['paths']} path(s)"}


def _spent(rec: dict) -> int | None:
    try:
        import mission_spend as ms
        return ms.processed_tokens(rec)
    except Exception:  # noqa: BLE001 -- unmeasured spend is recorded as None, not 0
        return None


def notify(text: str, sender=None) -> str:
    """Telegram when configured; returns what happened, never raises."""
    if sender is not None:
        return sender(text)
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return "no channel configured"
    try:
        import urllib.parse
        import urllib.request
        data = urllib.parse.urlencode({"chat_id": chat, "text": text[:3900]}).encode()
        with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=15) as r:
            return f"telegram {r.status}"
    except Exception as exc:  # noqa: BLE001 -- recorded by the caller
        return f"telegram failed: {type(exc).__name__}"


def _complete(mid: str, grant: dict, decide_fn, now: float) -> str:
    """Raise authority to the grant (idempotent), release the hold, wake the worker with a decision."""
    rec = gm.load(mid)
    if int(rec.get("authority_tokens") or 0) < grant["to"]:
        gm.set_authority(mid, tokens=grant["to"], now=now,
                         reason=f"auto top-up {grant['n']} under Owner policy (spec mission-auto-topup)")
    if gm.load(mid).get("owner_hold"):
        gm.release_owner_hold(mid, now=now)
    text = (f"Auto top-up {grant['n']} granted under the Owner's pre-authorised policy: authority "
            f"{grant['from']:,} -> {grant['to']:,} processed tokens, because {grant['why']}. Continue the "
            "milestone where you stopped; every other constraint is unchanged.")
    out = decide_fn(mid, text, decision_id=f"TOPUP{grant['n']}")
    return f"woke={out.get('woke') if isinstance(out, dict) else out}"


def sweep_one(mid: str, *, now: float | None = None, decide_fn=None, sender=None, dry_run: bool = False) -> dict:
    now = time.time() if now is None else now
    decide_fn = decide_fn or gm.deliver_decision
    pol = load_policy(mid)
    if pol is None:
        return {"mission": mid, "action": "none", "why": "no policy"}
    rec = gm.load(mid)
    prog = progress_since(mb.execution_root(rec), pol.get("last_head")) if rec else {"measured": False}
    verdict = judge(rec, pol, prog)
    out = {"mission": mid, **verdict}
    if dry_run or verdict["action"] == "none":
        return out
    hold_at = rec["owner_hold"].get("set_at")
    if verdict["action"] == "refuse":
        if pol.get("notified_hold_set_at") != hold_at:
            msg = (f"Mission {mid} is parked on its budget and was NOT topped up: {verdict['why']}. "
                   f"Authority {int(rec.get('authority_tokens') or 0):,}. "
                   f"Raise it with: gsd_mission.py authority --mission {mid} --tokens N "
                   f"--owner-turn <session>:<timestamp>, then release.")
            pol["notified_hold_set_at"] = hold_at
            pol["last_refusal"] = {"at": now, "why": verdict["why"], "notify": notify(msg, sender)}
            save_policy(pol)
            gm.lr.ledger_append(mid, "authority_auto_topup_refused", mission_id=mid, why=verdict["why"],
                                notify=pol["last_refusal"]["notify"])
        out["notify"] = (pol.get("last_refusal") or {}).get("notify")
        return out
    if verdict["action"] == "grant":
        cur = int(rec.get("authority_tokens") or 0)
        grant = {"n": len(pol.get("grants") or []) + 1, "at": now, "hold_set_at": hold_at, "from": cur,
                 "to": cur + int(pol["step"]), "head": prog["head"], "spent": _spent(rec), "why": verdict["why"]}
        # Written BEFORE the effect: a pass that dies after this line is completed (never re-granted) next pass.
        pol.setdefault("grants", []).append(grant)
        pol["last_head"] = prog["head"]
        save_policy(pol)
        gm.lr.ledger_append(mid, "authority_auto_topup", mission_id=mid, **{k: grant[k] for k in
                                                                         ("n", "from", "to", "head", "spent")})
    out["result"] = _complete(mid, pol["grants"][-1], decide_fn, now)
    return out


def sweep(*, now: float | None = None, decide_fn=None, sender=None, dry_run: bool = False) -> list[dict]:
    if not enabled():
        return [{"action": "none", "why": "CPP_MISSION_AUTO_TOPUP=off"}]
    res = []
    for p in sorted(Path(gm.lr.state_dir()).glob("mission-topup-m-*.json")):
        mid = p.stem[len("mission-topup-"):]
        try:
            res.append(sweep_one(mid, now=now, decide_fn=decide_fn, sender=sender, dry_run=dry_run))
        except Exception as exc:  # noqa: BLE001 -- one mission's failure must not stop the others
            gm.lr.ledger_append(mid, "authority_auto_topup_error", mission_id=mid,
                                error=f"{type(exc).__name__}: {exc}"[:300])
            res.append({"mission": mid, "action": "error", "why": f"{type(exc).__name__}: {exc}"[:300]})
    return res


def budget(mid: str, authority, topups: int, step, reason: str = "", now: float | None = None) -> dict:
    now = time.time() if now is None else now
    rec = gm.load(mid)
    if rec is None:
        raise gm.MissionError(f"no mission {mid}")
    if topups < 0:
        raise ValueError("--topups must be >= 0")
    auth, stp = parse_tokens(authority), parse_tokens(step)
    gm.set_authority(mid, tokens=auth, now=now, reason=reason or "Owner budget at arm (mission-auto-topup)")
    pol = load_policy(mid) or {"schema": SCHEMA, "mission_id": mid, "grants": []}
    pol.update({"authority": auth, "max_topups": int(topups), "step": stp, "set_at": now, "reason": reason,
                "last_head": head_of(mb.execution_root(rec))})
    save_policy(pol)
    gm.lr.ledger_append(mid, "authority_topup_policy", mission_id=mid, authority=auth, max_topups=topups, step=stp)
    return pol


def open_phases(repo: str) -> int | None:
    """Unchecked phase lines in .planning/ROADMAP.md (`- [ ] **Phase N`); None when there is no roadmap."""
    p = Path(repo) / ".planning" / "ROADMAP.md"
    if not p.is_file():
        return None
    return len(re.findall(r"^\s*-\s*\[ \]\s*\**\s*Phase\b", p.read_text(encoding="utf-8", errors="replace"),
                          flags=re.M | re.I))


def suggest(repo: str, phases: int | None = None) -> dict:
    rate = parse_tokens(os.environ.get("CPP_MISSION_PHASE_TOKENS") or DEFAULT_PHASE_TOKENS)
    n = phases if phases is not None else open_phases(repo)
    basis = "ROADMAP.md open phases" if phases is None and n is not None else "given"
    if n is None:
        n, basis = 3, "no ROADMAP.md: assumed 3 phases"
    auth = max(1, n) * rate
    return {"phases": n, "basis": basis, "rate": rate, "authority": auth, "topups": 3, "step": rate}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("budget")
    b.add_argument("--mission", required=True)
    b.add_argument("--authority", required=True)
    b.add_argument("--topups", type=int, default=3)
    b.add_argument("--step", default="40M")
    b.add_argument("--reason", default="")
    s = sub.add_parser("suggest")
    s.add_argument("--cwd", default=".")
    s.add_argument("--phases", type=int)
    w = sub.add_parser("sweep")
    w.add_argument("--dry-run", action="store_true")
    t = sub.add_parser("status")
    t.add_argument("--mission", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "budget":
        pol = budget(a.mission, a.authority, a.topups, a.step, a.reason)
        print(f"BUDGET SET mission={a.mission} authority={pol['authority']:,} topups={pol['max_topups']} "
              f"step={pol['step']:,} base_head={str(pol['last_head'])[:8]}")
    elif a.cmd == "suggest":
        r = suggest(a.cwd, a.phases)
        print(f"SUGGEST phases={r['phases']} ({r['basis']}) x {r['rate']:,} = authority {r['authority']:,}; "
              f"run: mission_topup.py budget --mission <id> --authority {r['authority'] // 1_000_000}M "
              f"--topups {r['topups']} --step {r['step'] // 1_000_000}M")
    elif a.cmd == "sweep":
        for r in sweep(dry_run=a.dry_run):
            if r.get("action") not in ("none",):
                print(f"TOPUP {r.get('mission')} {r['action']}: {r['why']} {r.get('result') or r.get('notify') or ''}")
    elif a.cmd == "status":
        print(json.dumps(load_policy(a.mission), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
