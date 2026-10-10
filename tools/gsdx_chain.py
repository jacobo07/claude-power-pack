"""Deterministic successor arming for one programme (zero model): receipt -> next unit, inside the envelope.

    python tools/gsdx_chain.py tick [--chain PATH] [--dry-run]

chain.json: {"goal", "root", "envelope", "units": [{"id", "packet", "route", "receipt", "after", "wait": [paths]}]}
- `after` is the id of the unit whose receipt must say DONE first (null = first unit). A unit's optional `accept` list
  names more statuses; DONE_WITH_LIMITS is accepted everywhere when the JSON receipt has gate_rc 0 and named `limits`.
- `wait` paths must all exist (an event another programme produces, e.g. its install receipt).
One tick arms at most ONE unit, and none while any non-terminal mission holds the programme root (one writer).
A unit whose mission ended without a DONE receipt is never re-armed here: the steward and a residual own that.
Every decision is one JSON row in ~/.claude/state/gsdx-chain.jsonl. Kill switch: CPP_GSDX_CHAIN=off.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHAIN = ROOT / "vault" / "specs" / "gsdx-factory" / "chain.json"
LIVE = Path.home() / ".claude" / "skills" / "claude-power-pack" / "tools"
PY = sys.executable
TERMINAL = {"COMPLETED", "HALTED", "ORPHANED"}


def receipt_status(path: Path) -> str | None:
    """DONE / PARTIAL / FAILED / ... from a JSON `status` or a Markdown `Status:` line; None when absent."""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        s = str(json.loads(text).get("status", ""))
    except (ValueError, AttributeError):
        m = re.search(r"^\s*Status:\s*\**\s*([A-Z_]+)", text, re.M)
        s = m.group(1) if m else ""
    m = re.match(r"\s*([A-Z_]+)", s)
    return m.group(1) if m else "UNREADABLE"


def limits_accepted(path: Path) -> bool:
    """DONE_WITH_LIMITS counts as done by default only when the JSON receipt proves its gate passed (gate_rc 0) and
    names its limits (non-empty `limits` list). Free text, a failed gate or unnamed limits still stop the chain."""
    if not path.exists():
        return False
    try:
        r = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    except ValueError:
        return False
    if not isinstance(r, dict) or str(r.get("status", "")).split()[:1] != ["DONE_WITH_LIMITS"]:
        return False
    limits = r.get("limits")
    return r.get("gate_rc") == 0 and isinstance(limits, list) and any(str(x).strip() for x in limits)


def _norm(p) -> str:
    return str(p).replace("/", "\\").rstrip("\\").lower()


def decide(chain: dict, missions: list[dict], goal_used: int, route_target) -> dict:
    """Pure decision: what this tick should do. route_target(path) -> int."""
    units = chain["units"]
    roots = {_norm(chain["root"])} | {_norm(u["cwd"]) for u in units if u.get("cwd")}
    held = [m for m in missions if _norm(m.get("cwd", "")) in roots and m.get("state") not in TERMINAL]
    by_packet = {}
    for m in missions:
        p = (m.get("wu_packet") or {}).get("path")
        if p:
            by_packet.setdefault(_norm(p), []).append(m)
    status = {u["id"]: receipt_status(Path(u["receipt"])) for u in units}
    accept = {u["id"]: set(u.get("accept") or ["DONE"]) for u in units}   # a unit may accept more than DONE, by name
    done = {uid for uid, s in status.items() if s in accept[uid]}
    done |= {u["id"] for u in units if limits_accepted(Path(u["receipt"]))}   # K6: proven gate + named limits
    for u in units:
        if u["id"] in done:
            continue
        ms = by_packet.get(_norm(u["packet"]), [])
        refused = [m for m in ms if m.get("state") == "PREPARED"
                   and str((m.get("owner_hold") or {}).get("reason", "")).startswith("arm-chain failed")]
        if refused:   # a failed arm leaves a held record: surface it, never read it as "running"
            return {"action": "arm_refused", "unit": u["id"], "mission_id": refused[0]["mission_id"],
                    "why": refused[0]["owner_hold"]["reason"][:300]}
        if any(m.get("state") not in TERMINAL for m in ms):
            return {"action": "running", "unit": u["id"]}
        if ms:
            return {"action": "stopped_without_done", "unit": u["id"], "receipt": status[u["id"]],
                    "reason": "steward / residual owns it; never re-armed by the chain"}
        if u.get("after") and u["after"] not in done:
            return {"action": "wait_predecessor", "unit": u["id"], "after": u["after"], "receipt": status.get(u["after"])}
        missing = [w for w in u.get("wait", []) if not Path(w).exists()]
        if missing:
            return {"action": "wait_event", "unit": u["id"], "missing": missing}
        if held:
            return {"action": "wait_writer", "unit": u["id"], "held_by": [m["mission_id"] for m in held]}
        need = route_target(u["route"])
        if goal_used + need > int(chain["envelope"]):
            return {"action": "refuse_envelope", "unit": u["id"], "used": goal_used, "need": need,
                    "envelope": chain["envelope"]}
        return {"action": "arm", "unit": u["id"], "need": need}
    return {"action": "complete"}


def _route_target(path) -> int:
    return int(json.loads(Path(path).read_text(encoding="utf-8-sig"))["envelope"]["target"])


def _live_state(goal: str) -> tuple[list, int]:
    sys.path.insert(0, str(LIVE))
    import gsd_mission as gm  # noqa: E402
    import mission_spend as ms  # noqa: E402
    led = ms._goal_ledger(goal)
    g = led._gfold(led._read())
    return gm._scan()[0], int(g["total_used"])    # envelope arithmetic is lifetime spend, not the current lease's


def _route_stop(path) -> int:
    env = json.loads(Path(path).read_text(encoding="utf-8-sig"))["envelope"]
    return int(env.get("stop") or env["target"])


def _live_ledger(goal: str):
    sys.path.insert(0, str(LIVE))
    import mission_spend as ms  # noqa: E402
    return ms._goal_ledger(goal)


def _open_lease(led, goal: str, unit: dict) -> dict | None:
    """OCA: with a programme on the ledger, each unit arms under its own lease (idempotent by goal:unit). Returns
    None when there is no programme (behaviour unchanged) or the lease is open; a refusal row otherwise."""
    g = led._gfold(led._read())
    if g["programme"] is None:
        return None
    out = led.lease_open(succession_id=f"{goal}:{unit['id']}", cap=_route_stop(unit["route"]),
                         prev_lease=g["leases"][-1]["id"])
    if out.get("ok"):
        return None
    why = str(out.get("reason", ""))
    return {"action": "refuse_authority" if why.startswith("AUTHORITY_REQUIRED") else "lease_refused",
            "unit": unit["id"], "why": why[:300]}


def _arm(chain: dict, u: dict) -> dict:
    cmd = [PY, str(LIVE / "gsd_mission.py"), "arm-chain", "--cwd", u.get("cwd") or chain["root"], "--command", "/gsd-autonomous",
           "--wu-packet", u["packet"], "--token-estimate", str(_route_target(u["route"])), "--route", u["route"],
           "--max-cycles", "2", "--permission-mode", "auto", "--rollover-protocol", "capsule-v2"]
    p = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=300, stdin=subprocess.DEVNULL)
    out = p.stdout.strip()
    try:
        res = json.loads(out[out.index("{"):])
    except ValueError:
        res = {"ok": False, "raw": out[-300:]}
    return {"rc": p.returncode, **res, "stderr": p.stderr.strip()[-300:]}


def to_settle(chain: dict, missions: list[dict], open_sids: set) -> list[str]:
    """Session ids of TERMINAL missions of this chain's units that still hold an open goal reservation.
    A worker that finished WITH a receipt is not the steward's case (it acts only without one), so nobody else
    closes its lease: the chain does, at transcript-measured spend (goal-settle refuses blind)."""
    packets = {_norm(u["packet"]) for u in chain["units"]}
    out = []
    for m in missions:
        if m.get("state") in TERMINAL and _norm((m.get("wu_packet") or {}).get("path", "")) in packets:
            sids = [(m.get("owner") or {}).get("session_id")] + [p.get("session_id") for p in m.get("previous_owners") or []
                                                                 if isinstance(p, dict)]
            out += [s for s in sids if s and s in open_sids and s not in out]
    return out


def _live_settle(goal: str, missions: list[dict], chain: dict) -> list[dict]:
    import mission_spend as ms  # noqa: E402 -- _live_state put LIVE on sys.path
    led = ms._goal_ledger(goal)
    g = led._gfold(led._read())
    open_sids = {r["sid"] for r in g["res"].values() if r.get("hold")}
    done = []
    for sid in to_settle(chain, missions, open_sids):
        try:
            r = ms.goal_settle(goal, sid)
            done.append({"sid": sid[:8], "ok": r.get("ok"), "closed": len(r.get("closed", [])), "reason": r.get("reason", "")})
        except Exception as e:  # noqa: BLE001 -- one bad row must not stop arming; it is reported
            done.append({"sid": sid[:8], "ok": False, "reason": f"{type(e).__name__}: {e}"[:200]})
    return done


def tick(chain_path: Path, dry_run: bool = False, state=None, armer=None, settler=None, ledger=None) -> dict:
    if os.environ.get("CPP_GSDX_CHAIN", "").lower() == "off":
        return {"action": "off"}
    chain = json.loads(chain_path.read_text(encoding="utf-8-sig"))
    missions, used = state() if state else _live_state(chain["goal"])
    settled = []
    if not dry_run:
        settled = (settler or (lambda: _live_settle(chain["goal"], missions, chain)))() if (settler or state is None) else []
    row = decide(chain, missions, used, _route_target)
    if settled:
        row["settled"] = settled
    if row["action"] == "arm" and not dry_run:
        unit = next(u for u in chain["units"] if u["id"] == row["unit"])
        led = ledger if ledger is not None else (_live_ledger(chain["goal"]) if state is None else None)
        refusal = _open_lease(led, chain["goal"], unit) if led is not None else None
        if refusal:
            row = refusal
        else:
            row["armed"] = (armer or _arm)(chain, unit)
    row.update({"at": time.time(), "goal": chain["goal"], "used": used, "dry_run": dry_run})
    log = Path.home() / ".claude" / "state" / "gsdx-chain.jsonl"
    if not dry_run and state is None:
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    return row


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "tick":
        print(__doc__)
        return 2
    path = Path(argv[argv.index("--chain") + 1]) if "--chain" in argv else DEFAULT_CHAIN
    row = tick(path, dry_run="--dry-run" in argv)
    print(json.dumps(row))
    return 0 if row["action"] != "arm" or (row.get("armed") or {}).get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
