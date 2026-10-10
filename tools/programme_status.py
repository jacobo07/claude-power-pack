"""Programme status: a deterministic projection from durable state only (zero model).

    python tools/programme_status.py [--chain PATH] [--json] [--notify]

Sources: chain.json, unit receipts, mission records (injected loader), the goal ledger/spend view, git HEAD.
Cost is O(units + current state): per-session rows, history and transcripts are never emitted (spend is measured
by mission_spend.programme_spend, the one place allowed to read transcripts). Output size is bounded by
construction (every free text is clipped, lists are capped), so history growth cannot change it.
Missing state is UNKNOWN, never zero. Notification: only a material event (done / blocked / authority edge), once.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsdx_chain as gc  # noqa: E402

UNKNOWN = "UNKNOWN"
CLIP = 200
MAX_ITEMS = 8
BLOCKING = {"held", "arm_refused", "refuse_envelope", "stopped_without_done", "wait_event"}
AUTHORITY = {"arm_refused", "refuse_envelope", "held"}
NOTIFY_STATE = Path.home() / ".claude" / "state" / "programme-status-notified.json"


def _clip(s, n=CLIP):
    return str(s)[:n]


def _git_head(root: str) -> str:
    try:
        p = subprocess.run([r"C:\Program Files\Git\cmd\git.exe", "-C", root, "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL)
        return p.stdout.strip() or UNKNOWN
    except (OSError, subprocess.SubprocessError):
        return UNKNOWN


def _load_missions(goal: str):
    try:
        return gc._live_state(goal)
    except Exception:  # noqa: BLE001 -- unreadable live state is UNKNOWN, not "no missions"
        return None, None


def _spend(goal: str):
    try:
        import mission_spend as ms
        s = ms.programme_spend(goal)
    except Exception as ex:  # noqa: BLE001
        return {"settled": UNKNOWN, "reserved": UNKNOWN, "unknown": UNKNOWN, "available": UNKNOWN,
                "telemetry_ok": False, "why": _clip(f"{type(ex).__name__}: {ex}", 120)}
    if not s.get("ok"):
        return {"settled": UNKNOWN, "reserved": UNKNOWN, "unknown": UNKNOWN, "available": UNKNOWN,
                "telemetry_ok": False, "why": _clip(s.get("reason", "not ok"), 120)}
    return {k: s[k] for k in ("settled", "reserved", "unknown", "available", "available_certain", "telemetry_ok")}


def _target(path) -> object:
    try:
        return gc._route_target(path)
    except (OSError, ValueError, KeyError, TypeError):
        return UNKNOWN


def project(chain_path: Path, *, missions=None, goal_used=None, spend=None, head=None, now=None) -> dict:
    """The status record. missions/goal_used/spend/head are injectable; None means "load it"."""
    chain_path = Path(chain_path)
    chain = json.loads(chain_path.read_text(encoding="utf-8-sig"))
    units = chain["units"]
    goal = chain.get("goal", UNKNOWN)
    if chain.get("enabled") is False or chain.get("parked"):
        base_state = "parked"
    else:
        base_state = None
    if missions is None:
        missions, goal_used = _load_missions(goal)
    live_ok = missions is not None
    spend = spend if spend is not None else _spend(goal)
    head = head if head is not None else _git_head(chain.get("root", "."))

    receipts = {u["id"]: gc.receipt_status(Path(u["receipt"])) for u in units}
    done_ids = [u["id"] for u in units if receipts[u["id"]] == "DONE" or gc.limits_accepted(Path(u["receipt"]))]
    last = None
    for u in units:
        if u["id"] in done_ids:
            try:
                t = Path(u["receipt"]).stat().st_mtime
            except OSError:
                t = 0
            if last is None or t >= last[1]:
                last = (u["id"], t)
    if live_ok:
        d = gc.decide(chain, missions, int(goal_used or 0), _target)
    else:
        d = {"action": UNKNOWN, "why": "live mission/ledger state unreadable"}
    action = d["action"]
    unit = next((u for u in units if u["id"] == d.get("unit")), None)
    blocked_receipt = [(uid, s) for uid, s in receipts.items() if s and s.startswith("BLOCKED")]
    if base_state:
        state = base_state
    elif action == "complete":
        state = "done"
    elif blocked_receipt or action in BLOCKING:
        state = "blocked"
    elif action == UNKNOWN:
        state = UNKNOWN
    elif action == "running":
        state = "running"
    else:
        state = "waiting" if action.startswith("wait") else "armable"
    worker = UNKNOWN
    if unit and live_ok:
        pk = gc._norm(unit["packet"])
        ms_ = [m for m in missions if gc._norm((m.get("wu_packet") or {}).get("path", "")) == pk]
        ms_ = [m for m in ms_ if m.get("state") not in gc.TERMINAL] or ms_[-1:]
        if ms_:
            worker = _clip(f"{ms_[-1].get('mission_id')}:{ms_[-1].get('state')}", 80)
        else:
            worker = "none"
    blocker = None
    if blocked_receipt:
        blocker = _clip(f"{blocked_receipt[0][0]} receipt {blocked_receipt[0][1]}")
    elif state in ("blocked", UNKNOWN):
        blocker = _clip(d.get("why") or d.get("reason") or d.get("missing") or action)
    resid = sum(1 for u in units if Path(u["packet"] + ".residual.md").exists())
    pending = [u["id"] for u in units if u["id"] not in done_ids]
    forecast = _target(unit["route"]) if unit and unit.get("route") else None
    st = {
        "goal": goal, "state": state, "action": action,
        "current_unit": d.get("unit") if d.get("unit") else None,
        "worker": worker,
        "last_verified_transition": {"unit": last[0], "receipt": "DONE",
                                     "at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(last[1]))} if last else None,
        "spend": spend, "envelope": chain.get("envelope"),
        "forecast_next_unit": forecast,
        "blocker": blocker,
        "next_eligible_transition": _clip(f"{action}:{d.get('unit')}" if d.get("unit") else action, 80),
        "debt": {"units_pending": len(pending), "pending_ids": pending[:MAX_ITEMS], "residuals": resid},
        "git_head": head, "done_units": len(done_ids), "total_units": len(units),
    }
    st["handoff"] = render_handoff(st)
    return st


def render_handoff(st: dict) -> str:
    sp = st["spend"]
    lv = st["last_verified_transition"]
    lines = [
        "HANDOFF",
        f"goal: {st['goal']} | state: {st['state']} | head: {st['git_head']}",
        f"unit: {st['current_unit']} | worker: {st['worker']} | next: {st['next_eligible_transition']}",
        f"last verified: {lv['unit'] + ' ' + lv['receipt'] + ' @ ' + lv['at'] if lv else 'none'}",
        f"spend settled={sp.get('settled')} reserved={sp.get('reserved')} unknown={sp.get('unknown')} "
        f"available={sp.get('available')} (envelope {st['envelope']}) forecast_next={st['forecast_next_unit']}",
        f"blocker: {st['blocker'] or 'none'}",
        f"debt: {st['debt']['units_pending']} units pending {','.join(st['debt']['pending_ids'])}; "
        f"residuals {st['debt']['residuals']}",
    ]
    return "\n".join(lines)


def material_event(st: dict):
    """Done, blocked, or an authority edge (held/refused/envelope, telemetry failure). Anything else: None."""
    if st["state"] == "done":
        return "programme_done"
    if st["state"] == "blocked":
        return "authority_edge" if st["action"] in AUTHORITY else "blocked"
    if st["spend"].get("telemetry_ok") is False:
        return "authority_edge"
    return None


def notify(st: dict, state_path: Path | None = None):
    """Return the event text once per (event, unit); a repeat of the same event returns None. No model, O(1)."""
    ev = material_event(st)
    p = state_path or NOTIFY_STATE
    try:
        prev = json.loads(p.read_text(encoding="utf-8-sig")).get(st["goal"])
    except (OSError, ValueError):
        prev = None
    key = f"{ev}:{st['current_unit']}" if ev else None
    if key == prev:
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        data = {}
    data[st["goal"]] = key
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data), encoding="utf-8")
    return f"{ev}: {st['goal']} unit={st['current_unit']} {st['blocker'] or ''}".strip() if ev else None


def main(argv: list[str]) -> int:
    chain = Path(argv[argv.index("--chain") + 1]) if "--chain" in argv else \
        Path(__file__).resolve().parents[1] / "vault" / "programs" / "autonomy" / "chain.json"
    st = project(chain)
    if "--notify" in argv:
        msg = notify(st)
        if msg:
            print(msg)
        return 0
    print(json.dumps(st) if "--json" in argv else st["handoff"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
