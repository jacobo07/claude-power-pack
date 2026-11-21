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
DEFAULT_CEILING_X = 3.0             # Owner 2026-11-21 "x3" (was 2x, 2026-11-16): grow to 3x authority, commits-gated


def enabled() -> bool:
    return (os.environ.get("CPP_MISSION_AUTO_TOPUP") or "").strip().lower() != "off"


def default_enabled() -> bool:
    return (os.environ.get("CPP_MISSION_TOPUP_DEFAULT") or "").strip().lower() != "off"


def ceiling_x() -> float:
    try:
        x = float(os.environ.get("CPP_MISSION_TOPUP_CEILING_X") or DEFAULT_CEILING_X)
    except ValueError:
        x = DEFAULT_CEILING_X
    return max(1.0, x)


def default_terms(authority: int, step: int | None = None) -> dict:
    """{ceiling, step, max_topups} for the 2x default: the steps that fit between authority and ceiling."""
    ceiling = int(authority * ceiling_x())
    room = max(0, ceiling - authority)
    stp = min(step or DEFAULT_PHASE_TOKENS, room) if room else (step or DEFAULT_PHASE_TOKENS)
    return {"ceiling": ceiling, "step": stp, "max_topups": (-(-room // stp)) if room else 0}


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
    if pol.get("ceiling") and int(rec.get("authority_tokens") or 0) >= int(pol["ceiling"]):
        return {"action": "refuse", "why": f"ceiling reached ({int(pol['ceiling']):,}); beyond it is the Owner's"}
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


def toast_enabled() -> bool:
    """On by default on Windows. A redirected state dir (GSD_LONG_RUN_STATE_DIR: every suite, never the live sweep)
    is a test run, which must not toast the Owner's desktop unless it asks with CPP_MISSION_NOTIFY_TOAST=on."""
    v = (os.environ.get("CPP_MISSION_NOTIFY_TOAST") or "").strip().lower()
    if os.name != "nt" or v in ("off", "0", "false"):
        return False
    return v == "on" or not os.environ.get("GSD_LONG_RUN_STATE_DIR")


_TOAST_PS = (
    "$ErrorActionPreference='Stop';"
    "[void][Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime];"
    "[void][Windows.Data.Xml.Dom.XmlDocument,Windows.Data.Xml.Dom.XmlDocument,ContentType=WindowsRuntime];"
    "$t=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($env:CPP_TOAST_TEXT));"
    "$x=New-Object Windows.Data.Xml.Dom.XmlDocument;"
    "$x.LoadXml('<toast duration=\"long\"><visual><binding template=\"ToastGeneric\"><text>Misiones PP</text>"
    "<text></text></binding></visual></toast>');"
    "$x.GetElementsByTagName('text').Item(1).InnerText=$t;"
    "$n=[Windows.UI.Notifications.ToastNotification]::new($x);"
    "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
    "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe').Show($n)")


def toast(text: str) -> str:
    """Windows toast (spec mission-unattended-continuity B): stays in the Action Center while the Owner is away.
    CREATE_NO_WINDOW: a sweep must never flash a console (console-popup rule). The text travels in an env var as
    base64, never inside the command line. Returns 'toast shown' or a failure string; never raises."""
    import base64
    try:
        env = {**os.environ, "CPP_TOAST_TEXT": base64.b64encode(text[:600].encode("utf-8")).decode("ascii")}
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", _TOAST_PS],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, env=env,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception as exc:  # noqa: BLE001 -- recorded by the caller as not delivered
        return f"toast failed: {type(exc).__name__}"
    return "toast shown" if r.returncode == 0 else f"toast failed: rc {r.returncode} {(r.stderr or '').strip()[:80]}"


def notify(text: str, sender=None, toaster=None) -> str:
    """Telegram when configured, else a Windows toast; returns what happened, never raises."""
    if sender is not None:
        return sender(text)
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        if toaster is not None:
            return toaster(text)
        return toast(text) if toast_enabled() else "no channel configured"
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
    if verdict["action"] == "grant" and not dry_run:
        try:   # CCN-3 weekly account ceiling (Owner Q2 = enforce 85%), checked before the grant is written
            import account_governor as _ag
            _code, _verdict, _why, _ = _ag.check(_ag.DEFAULT_STATE, "topup")
        except Exception as exc:  # noqa: BLE001 -- the governor fails open
            _code = 0
            gm.lr.ledger_append(mid, "account_governor_error", mission_id=mid, why=f"{type(exc).__name__}: {exc}"[:300])
        if _code == 3:
            verdict = {"action": "refuse", "why": _why}
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
        to = cur + int(pol["step"])
        if pol.get("ceiling"):
            to = min(to, int(pol["ceiling"]))   # the last step is clipped: never above the ceiling
        grant = {"n": len(pol.get("grants") or []) + 1, "at": now, "hold_set_at": hold_at, "from": cur,
                 "to": to, "head": prog["head"], "spent": _spent(rec), "why": verdict["why"]}
        # Written BEFORE the effect: a pass that dies after this line is completed (never re-granted) next pass.
        pol.setdefault("grants", []).append(grant)
        pol["last_head"] = prog["head"]
        save_policy(pol)
        gm.lr.ledger_append(mid, "authority_auto_topup", mission_id=mid, **{k: grant[k] for k in
                                                                         ("n", "from", "to", "head", "spent")})
    out["result"] = _complete(mid, pol["grants"][-1], decide_fn, now)
    return out


def adopt_defaults(now: float | None = None) -> list[str]:
    """Give the 2x default policy to every live mission parked on its authority trip that has no policy (addendum
    2026-11-16). Base = the head its binding recorded at arm, so only work done since arm counts as progress."""
    if not default_enabled():
        return []
    now = time.time() if now is None else now
    adopted = []
    for rec in gm.all_missions():
        mid = rec.get("mission_id")
        auth = int(rec.get("authority_tokens") or 0)
        if (not mid or rec.get("state") in gm.TERMINAL or not is_authority_trip(rec) or auth <= 0
                or policy_path(mid).exists()):
            continue
        terms = default_terms(auth)
        base = (rec.get("binding") or {}).get("head")
        if not base and rec.get("created_at"):   # never bound: the root's last commit at arm time
            out = _git(mb.execution_root(rec), "rev-list", "-1", f"--before=@{int(rec['created_at'])}", "HEAD")
            base = out.strip() if out else None
        pol = {"schema": SCHEMA, "mission_id": mid, "grants": [], "authority": auth, "set_at": now,
               "reason": f"default policy (Owner 2026-11-16): ceiling {ceiling_x():g}x authority, commits-gated",
               "last_head": base, "default": True, **terms}
        save_policy(pol)
        gm.lr.ledger_append(mid, "authority_topup_policy", mission_id=mid, authority=auth, default=True, **terms)
        adopted.append(mid)
    return adopted


def sweep(*, now: float | None = None, decide_fn=None, sender=None, dry_run: bool = False) -> list[dict]:
    if not enabled():
        return [{"action": "none", "why": "CPP_MISSION_AUTO_TOPUP=off"}]
    res = []
    if not dry_run:
        try:
            adopt_defaults(now)
        except Exception as exc:  # noqa: BLE001 -- adoption failure must not stop the explicit policies
            res.append({"action": "error", "why": f"adopt_defaults: {type(exc).__name__}: {exc}"[:300]})
    for p in sorted(Path(gm.lr.state_dir()).glob("mission-topup-m-*.json")):
        mid = p.stem[len("mission-topup-"):]
        try:
            res.append(sweep_one(mid, now=now, decide_fn=decide_fn, sender=sender, dry_run=dry_run))
        except Exception as exc:  # noqa: BLE001 -- one mission's failure must not stop the others
            gm.lr.ledger_append(mid, "authority_auto_topup_error", mission_id=mid,
                                error=f"{type(exc).__name__}: {exc}"[:300])
            res.append({"mission": mid, "action": "error", "why": f"{type(exc).__name__}: {exc}"[:300]})
    return res


def budget(mid: str, authority, topups: int | None, step, reason: str = "", now: float | None = None,
           ceiling=None) -> dict:
    """topups=None derives them from the ceiling (default 2x authority); an explicit topups keeps the old
    behaviour, bounded only by an explicit ceiling."""
    now = time.time() if now is None else now
    rec = gm.load(mid)
    if rec is None:
        raise gm.MissionError(f"no mission {mid}")
    if topups is not None and topups < 0:
        raise ValueError("--topups must be >= 0")
    auth, stp = parse_tokens(authority), parse_tokens(step)
    ceil_tokens = parse_tokens(ceiling) if ceiling is not None else None
    if ceil_tokens is not None and ceil_tokens < auth:
        raise ValueError("--ceiling must be >= --authority")
    if topups is None:
        terms = default_terms(auth, stp)
        if ceil_tokens is not None:
            room = ceil_tokens - auth
            terms = {"ceiling": ceil_tokens, "step": min(stp, room) if room else stp,
                     "max_topups": (-(-room // min(stp, room))) if room else 0}
    else:
        terms = {"ceiling": ceil_tokens, "step": stp, "max_topups": int(topups)}
    gm.set_authority(mid, tokens=auth, now=now, reason=reason or "Owner budget at arm (mission-auto-topup)")
    pol = load_policy(mid) or {"schema": SCHEMA, "mission_id": mid, "grants": []}
    topups, stp = terms["max_topups"], terms["step"]
    pol.update({"authority": auth, "max_topups": int(topups), "step": stp, "ceiling": terms["ceiling"],
                "set_at": now, "reason": reason, "last_head": head_of(mb.execution_root(rec))})
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
    b.add_argument("--topups", type=int, default=None,
                   help="explicit count; omitted = derived from the ceiling (default 2x authority)")
    b.add_argument("--ceiling", default=None, help="hard authority ceiling for auto top-ups, e.g. 240M")
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
        pol = budget(a.mission, a.authority, a.topups, a.step, a.reason, ceiling=a.ceiling)
        ceil = f"{pol['ceiling']:,}" if pol.get("ceiling") else "none"
        print(f"BUDGET SET mission={a.mission} authority={pol['authority']:,} topups={pol['max_topups']} "
              f"step={pol['step']:,} ceiling={ceil} base_head={str(pol['last_head'])[:8]}")
    elif a.cmd == "suggest":
        r = suggest(a.cwd, a.phases)
        print(f"SUGGEST phases={r['phases']} ({r['basis']}) x {r['rate']:,} = authority {r['authority']:,}; "
              f"run: mission_topup.py budget --mission <id> --authority {r['authority'] // 1_000_000}M "
              f"--step {r['step'] // 1_000_000}M  (top-ups derived: ceiling {ceiling_x():g}x)")
    elif a.cmd == "sweep":
        for r in sweep(dry_run=a.dry_run):
            if r.get("action") not in ("none",):
                print(f"TOPUP {r.get('mission')} {r['action']}: {r['why']} {r.get('result') or r.get('notify') or ''}")
    elif a.cmd == "status":
        print(json.dumps(load_policy(a.mission), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
