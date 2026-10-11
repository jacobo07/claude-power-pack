"""Deterministic successor arming for one programme (zero model): receipt -> next unit, inside the envelope.

    python tools/gsdx_chain.py tick [--chain PATH] [--dry-run]

chain.json: {"goal", "root", "envelope", "units": [{"id", "packet", "route", "receipt", "after", "wait": [paths]}]}
- `after` is the id of the unit whose receipt must say DONE first (null = first unit). A unit's optional `accept` list
  names more statuses; DONE_WITH_LIMITS is accepted everywhere when the JSON receipt has gate_rc 0 and named `limits`.
- `wait` paths must all exist (an event another programme produces, e.g. its install receipt).
One tick arms at most ONE unit, and none while any non-terminal mission holds the programme root (one writer).
A unit whose missions ended without a DONE receipt is re-armed ONLY as a bounded residual: the chain (or the unit)
sets `max_residuals` (default 0 = never, the old behaviour), the steward must have written `<packet>.residual.md`
for the LATEST stopped mission, and each residual climbs one rung of `route_ladder` (a stop that cut the worker
short is not cured by the same route). Past the bound the unit is `residual_exhausted`: the Owner decides.
Every decision is one JSON row in ~/.claude/state/gsdx-chain.jsonl. Kill switch: CPP_GSDX_CHAIN=off.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHAIN = ROOT / "vault" / "specs" / "gsdx-factory" / "chain.json"
LIVE = Path.home() / ".claude" / "skills" / "claude-power-pack" / "tools"
PY = sys.executable
TERMINAL = {"COMPLETED", "HALTED", "ORPHANED"}


sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipt_judge import NOT_CLOSED, receipt_status  # noqa: E402,F401 -- the one reading every layer shares (APR-1, EWC K5)


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


RESIDUAL = ".residual.md"


def _klass(ms: list, status, ref) -> str:
    if ref is not None:
        return "FALSE_DONE"
    if status in NOT_CLOSED and status is not None:
        return "UNCLOSED_RECEIPT"
    latest = max(ms, key=lambda m: float(m.get("created_at") or 0))
    if status is None and latest.get("state") == "COMPLETED":
        return "NO_RECEIPT"
    return "WORKER_STOPPED"


def _residual(chain: dict, u: dict, ms: list[dict], by_packet: dict, status=None, ref=None) -> dict:
    """All of the unit's missions are terminal without a DONE: a bounded residual arm, or the reason there is none."""
    res = Path(u["packet"] + RESIDUAL)
    # a lineage renewal (renewed_from) continues the same residual on its own budget; only fresh arms count
    n = len([m for m in by_packet.get(_norm(res), []) if not m.get("renewed_from")])
    cap = int(u.get("max_residuals", chain.get("max_residuals", 0)))
    klass = _klass(ms, status, ref)
    base = {"unit": u["id"], "attempts": len(ms), "residuals": n, "max_residuals": cap, "class": klass}
    if ref is not None:
        base["evidence"] = u["receipt"] + REFUSAL
    elif _current(u, SEAL) is not None:
        base["evidence"] = u["receipt"] + SEAL
    if cap <= 0:
        return {"action": "stopped_without_done", **base, "reason": "max_residuals 0: the Owner arms a residual"}
    if n >= cap:
        return {"action": "residual_exhausted", **base, "reason": "bounded residual re-arm used up; Owner decides"}
    latest = max(ms, key=lambda m: float(m.get("created_at") or 0))
    text = res.read_text(encoding="utf-8-sig", errors="replace") if res.exists() else ""
    ladder = list(chain.get("route_ladder") or [])
    norm = [_norm(r) for r in ladder]
    route = u["route"]
    fps = (ref or {}).get("fingerprints") or []
    repeated = len(fps) >= 2 and fps[-1] == fps[-2]
    idx = norm.index(_norm(route)) if _norm(route) in norm else None
    if repeated and (idx is None or idx + n >= len(ladder) - 1):   # same failure on the top rung (or no ladder)
        return {"action": "human_gate", **base, "why": "same failure on every rung",
                "evidence": [u["receipt"] + REFUSAL, str(res)]}
    if klass == "FALSE_DONE":     # no steward exists for a COMPLETED mission: the finalizer wrote the residual
        if latest["mission_id"] not in text:
            return {"action": "wait_finalizer", **base, "latest": latest["mission_id"]}
    elif not (latest.get("steward") or {}).get("done") or latest["mission_id"] not in text:
        return {"action": "wait_steward", **base, "latest": latest["mission_id"]}
    if idx is not None:
        route = ladder[min(idx + 1 + n + (1 if repeated else 0), len(ladder) - 1)]
    return {"action": "arm", **base, "residual": n + 1, "packet": str(res), "route": route,
            "after_mission": latest["mission_id"]}


# ---- APR-2: machine seal, false-DONE refusal, residual classes -------------------------------------------------
SEAL, REFUSAL, GATE = ".seal.json", ".refusal.json", ".gate.json"


def _sha(path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def _jload(path) -> dict | None:
    try:
        o = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        return o if isinstance(o, dict) else None
    except (OSError, ValueError):
        return None


def _wr(path, obj) -> None:
    Path(path).write_text(json.dumps(obj, indent=1), encoding="utf-8")


def _current(u: dict, kind: str) -> dict | None:
    """The seal/refusal that belongs to the receipt as it is NOW (same sha256; None == absent receipt)."""
    o = _jload(u["receipt"] + kind)
    return o if o is not None and o.get("receipt_sha256") == _sha(u["receipt"]) else None


def _run_gate(argv, cwd, timeout) -> tuple:
    try:
        p = subprocess.run(list(argv), cwd=cwd, capture_output=True, text=True, errors="replace", timeout=timeout,
                           stdin=subprocess.DEVNULL)
        return p.returncode, (p.stdout + p.stderr)[-400:]
    except subprocess.TimeoutExpired:
        return -1, "gate timeout"
    except OSError as e:
        return -1, f"gate could not start: {e}"[:400]


_WIN_GIT = r"C:\Program Files\Git\cmd\git.exe"
_GIT = "git" if shutil.which("git") or not os.path.exists(_WIN_GIT) else _WIN_GIT    # bare git is off PATH under the task


def _git(cwd, *args) -> str:
    try:
        p = subprocess.run([_GIT, "-C", str(cwd), *args], capture_output=True, text=True, errors="replace", timeout=60,
                           stdin=subprocess.DEVNULL)
        return p.stdout.strip() if p.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _fingerprint(gates: list, reason: str) -> str:
    bad = [(g["argv"], g["rc"], g["tail"]) for g in gates if g["rc"] != 0] or [reason]
    return hashlib.sha256(json.dumps(bad, sort_keys=True).encode()).hexdigest()


def _by_packet(missions: list) -> dict:
    out = {}
    for m in missions:
        p = (m.get("wu_packet") or {}).get("path")
        if p:
            out.setdefault(_norm(p), []).append(m)
    return out


def _unit_ms(u: dict, by_packet: dict) -> list:
    return by_packet.get(_norm(u["packet"]), []) + by_packet.get(_norm(u["packet"] + RESIDUAL), [])


def _write_residual(u: dict, ms: list, ref: dict) -> None:
    """FALSE_DONE has no steward (its mission COMPLETED with a closed receipt): the finalizer writes the residual."""
    latest = max(ms, key=lambda m: float(m.get("created_at") or 0))
    res = Path(u["packet"] + RESIDUAL)
    if res.exists() and latest["mission_id"] in res.read_text(encoding="utf-8-sig", errors="replace"):
        return
    pk = Path(u["packet"])
    base = pk.read_text(encoding="utf-8-sig", errors="replace") if pk.exists() else ""
    tails = "\n".join(f"- `{' '.join(map(str, g['argv']))}` rc={g['rc']}: {g['tail'].strip()[-300:]}"
                      for g in ref.get("gates", []) if g["rc"] != 0) or f"- {ref.get('reason', '')}"
    res.write_text(f"{base}\n\n## Residual\n\nThe previous worker (mission {latest['mission_id']}) wrote Status: DONE but "
                   f"the unit's declared acceptance FAILED, so the receipt is refused (FALSE_DONE).\n"
                   f"Refusal: {u['receipt'] + REFUSAL}\nFailing gates:\n{tails}\n"
                   f"Fix the cause, make the gates pass, then close the receipt.\n", encoding="utf-8")


def finalize_unit(chain: dict, u: dict, ms: list, runner=None, git=None, force: bool = False) -> dict | None:
    """Zero-model finalizer for ONE unit with `acceptance`. Returns a row when it did something, else None."""
    acc = u.get("acceptance")
    if not acc:
        return None
    receipt = u["receipt"]
    status = receipt_status(Path(receipt))
    if not force:
        if ms and any(m.get("state") not in TERMINAL for m in ms):
            return None
        if not ms and status is None:
            return None
    done_claim = status in set(u.get("accept") or ["DONE"])
    if not (status in NOT_CLOSED or done_claim):
        return None           # an explicit BLOCKED_HUMAN / FAILED is the worker's verdict; nothing to seal or refuse
    cwd = acc.get("cwd") or u.get("cwd") or chain["root"]
    gitf = git or (lambda *a: _git(cwd, *a))
    head = gitf("rev-parse", "HEAD") or "nogit"
    sha = _sha(receipt)
    cache = _jload(receipt + GATE)
    ran = not (cache and cache.get("sha") == sha and cache.get("head") == head)
    if not ran:
        passed, gates, commits, reason = cache["passed"], cache["gates"], cache["commits"], cache.get("reason", "")
    else:
        gates, reason = [], ""
        for argv in acc.get("gates") or []:
            rc, tail = (runner or _run_gate)(argv, cwd, int(acc.get("timeout_s", 600)))
            gates.append({"argv": list(argv), "rc": rc, "tail": tail})
        t0 = min((float(m.get("created_at") or 0) for m in ms), default=0)
        since = [f"--since={time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime(t0))}"] if t0 else []
        commits = [c for c in gitf("log", *since, "--format=%H", "-n", "50").splitlines() if c]
        missing = [f for f in acc.get("files") or [] if not (Path(cwd) / f).exists()]
        bad = [g for g in gates if g["rc"] != 0]
        if any(g["tail"] == "gate timeout" for g in bad):
            reason = "gate timeout"
        elif bad:
            reason = "gate failed"
        elif missing:
            reason = f"missing files: {missing}"
        elif acc.get("require_commit") and not commits:
            reason = "no commit since the unit started"
        elif not (acc.get("gates") or acc.get("files") or acc.get("require_commit")):
            reason = "acceptance declares no check"      # an empty contract proves nothing: never seal on it
        passed = not reason
        _wr(receipt + GATE, {"sha": sha, "head": head, "passed": passed, "gates": gates, "commits": commits,
                             "reason": reason})
    rec = {"unit": u["id"], "sealed_by": "gsdx_chain.finalize", "receipt_status": status, "receipt_sha256": sha,
           "gates": gates, "commits": commits, "head": head, "at": time.time()}
    if passed and status in NOT_CLOSED:
        if _current(u, SEAL) is None:
            _wr(receipt + SEAL, {**rec, "verdict": "DONE"})
            return {"unit": u["id"], "finalized": "sealed"}
        return None
    if passed:      # done claim with passing evidence: any older refusal is superseded
        Path(receipt + REFUSAL).unlink(missing_ok=True)
        return None
    if done_claim:
        old = _jload(receipt + REFUSAL)
        fp = _fingerprint(gates, reason)
        fps = list((old or {}).get("fingerprints") or [])
        if old is None or old.get("receipt_sha256") != sha or old.get("head") != head:
            fps.append(fp)
        ref = {**rec, "verdict": "FALSE_DONE", "reason": reason, "fingerprint": fp, "fingerprints": fps}
        if ran or old is None:
            _wr(receipt + REFUSAL, ref)
        Path(receipt + SEAL).unlink(missing_ok=True)
        if ms:
            _write_residual(u, ms, ref)
        return {"unit": u["id"], "finalized": "refused", "reason": reason}
    return None


def finalize(chain: dict, missions: list, runner=None, git=None) -> list:
    bp = _by_packet(missions)
    out = []
    for u in chain["units"]:
        try:
            r = finalize_unit(chain, u, _unit_ms(u, bp), runner, git)
        except Exception as e:  # noqa: BLE001 -- one unit's evidence must not stop the tick
            r = {"unit": u["id"], "finalized": "error", "reason": f"{type(e).__name__}: {e}"[:200]}
        if r:
            out.append(r)
    return out


def try_seal(packet, missions=None, runner=None, git=None) -> dict:
    """For APR-3: finalize the one unit that owns `packet` (found via chain*.json beside it) before a halt-continue."""
    pk = str(packet)
    pk = pk[:-len(RESIDUAL)] if pk.endswith(RESIDUAL) else pk
    for cp in sorted(Path(pk).resolve().parent.glob("chain*.json")):
        chain = _jload(cp)
        u = next((x for x in (chain or {}).get("units", []) if _norm(x.get("packet", "")) == _norm(pk)), None)
        if u is None:
            continue
        if not u.get("acceptance"):
            return {"sealed": False, "unit": u["id"], "reason": "no acceptance block"}
        if missions is None:
            missions = _live_state(chain["goal"])[0]
        r = finalize_unit(chain, u, _unit_ms(u, _by_packet(missions)), runner, git, force=True)
        seal = _current(u, SEAL)
        return {"sealed": seal is not None, "unit": u["id"], "seal": u["receipt"] + SEAL if seal else None,
                "result": (r or {}).get("finalized")}
    return {"sealed": False, "reason": "packet not found in any chain.json beside it"}


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
    refusal = {u["id"]: _current(u, REFUSAL) for u in units if u.get("acceptance")}
    sealed = {u["id"] for u in units if u.get("acceptance") and _current(u, SEAL) is not None}
    done = {uid for uid, s in status.items() if s in accept[uid] and refusal.get(uid) is None} | sealed
    done |= {u["id"] for u in units if limits_accepted(Path(u["receipt"])) and refusal.get(u["id"]) is None}   # K6: proven gate + named limits
    for u in units:
        if u["id"] in done:
            continue
        ms = by_packet.get(_norm(u["packet"]), []) + by_packet.get(_norm(u["packet"] + RESIDUAL), [])
        refused = [m for m in ms if m.get("state") == "PREPARED"
                   and str((m.get("owner_hold") or {}).get("reason", "")).startswith("arm-chain failed")]
        if refused:   # a failed arm leaves a held record: surface it, never read it as "running"
            return {"action": "arm_refused", "unit": u["id"], "mission_id": refused[0]["mission_id"],
                    "why": refused[0]["owner_hold"]["reason"][:300]}
        if any(m.get("state") not in TERMINAL for m in ms):
            return {"action": "running", "unit": u["id"]}
        if ms:
            row = _residual(chain, u, ms, by_packet, status[u["id"]], refusal.get(u["id"]))
            if row["action"] != "arm":
                return {**row, "receipt": "FALSE_DONE" if refusal.get(u["id"]) else status[u["id"]]}
            if held:
                return {"action": "wait_writer", "unit": u["id"], "held_by": [m["mission_id"] for m in held]}
            need = route_target(row["route"])
            if goal_used + need > int(chain["envelope"]):
                return {"action": "refuse_envelope", "unit": u["id"], "used": goal_used, "need": need,
                        "envelope": chain["envelope"], "residual": row["residual"]}
            return {**row, "need": need, **({"receipt": "FALSE_DONE"} if row.get("class") == "FALSE_DONE" else {})}
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
    out = led.lease_open(succession_id=f"{goal}:{unit.get('succession') or unit['id']}", cap=_route_stop(unit["route"]),
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


SILENT = {"stopped_without_done", "residual_exhausted", "arm_refused", "refuse_envelope", "human_gate",
          "pause_budget", "wait_steward"}
DEFAULT_SILENCE_S, DEFAULT_WAIT_TIMEOUT_S, LOCK_S = 1800, 21600, 5.0


def _state_dir() -> Path:
    return Path(os.environ.get("CPP_GSDX_CHAIN_STATE") or (Path.home() / ".claude" / "state"))


def _log_path() -> Path:
    return _state_dir() / "gsdx-chain.jsonl"


def _history(goal: str, limit: int = 400) -> list:
    out = []
    try:
        for ln in _log_path().read_text(encoding="utf-8", errors="replace").splitlines()[-limit * 4:]:
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if isinstance(r, dict) and r.get("goal") == goal:
                out.append(r)
    except OSError:
        pass
    return out[-limit:]


def _alert(row: dict) -> None:
    """The existing steward sink. Keyed `chain_goal`, not `goal`: R2 reads `goal` as a forgotten-goal incident."""
    p = _state_dir() / "steward-incidents.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    detail = {k: row[k] for k in ("why", "reason", "missing", "need", "forecast") if k in row}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "chain_alert", "chain_goal": row["goal"], "action": row["action"],
                            "unit": row.get("unit"), "at": row["at"], "detail": detail}) + "\n")


def silence_check(chain: dict, row: dict, history: list, now: float) -> bool:
    """True when this row has been the chain's standing answer for longer than its window and no alert was raised
    for (goal, action, unit) yet. A running mission is never silent; wait_event is, past wait_timeout_s."""
    act = row.get("action")
    if act == "wait_event":
        limit = float(chain.get("wait_timeout_s", DEFAULT_WAIT_TIMEOUT_S))
    elif act in SILENT:
        limit = float(chain.get("silence_s", DEFAULT_SILENCE_S))
    else:
        return False
    key = (act, row.get("unit"))
    since = now
    for h in reversed(history):
        if (h.get("action"), h.get("unit")) != key:
            break
        since = float(h.get("at") or since)
    if now - since <= limit:
        return False
    return not any(h.get("alerted") and (h.get("action"), h.get("unit")) == key for h in history)


def _done_ids(chain: dict) -> set:
    done = set()
    for u in chain["units"]:
        refused = bool(u.get("acceptance")) and _current(u, REFUSAL) is not None
        st = receipt_status(Path(u["receipt"]))
        if (st in set(u.get("accept") or ["DONE"]) and not refused) or \
                (u.get("acceptance") and _current(u, SEAL) is not None) or \
                (limits_accepted(Path(u["receipt"])) and not refused):
            done.add(u["id"])
    return done


def forecast(chain: dict, measured: dict, route_target) -> dict:
    """forecast = sum over not-done units of route target x overrun; overrun = measured spend of done units /
    their route targets (floor 1.0); no measurement -> overrun 1.0, basis 'unmeasured'."""
    done = _done_ids(chain)
    num = den = 0
    for u in chain["units"]:
        if u["id"] in done and measured.get(u["id"]):
            num += int(measured[u["id"]])
            den += route_target(u["route"])
    overrun = max(1.0, num / den) if den else 1.0
    remaining = [u for u in chain["units"] if u["id"] not in done]
    total = int(sum(route_target(u["route"]) for u in remaining) * overrun)
    return {"forecast": total, "overrun": round(overrun, 3), "basis": "measured" if den else "unmeasured",
            "units_left": [u["id"] for u in remaining]}


def _live_measured(goal: str) -> dict:
    """Per-unit measured spend from the goal ledger: lease succession_id `<goal>:<unit>[:rN]` -> settled tokens."""
    led = _live_ledger(goal)
    out = {}
    for ls in led._gfold(led._read())["leases"]:
        sid = ls.get("succession_id") or ""
        if sid.startswith(goal + ":"):
            uid = sid.split(":")[1]
            out[uid] = out.get(uid, 0) + int(ls.get("settled", 0)) + int(ls.get("rsettled", 0))
    return out


def _armed_for(missions: list, packet: str) -> list:
    bp = _by_packet(missions)
    return [m for m in bp.get(_norm(packet), []) + bp.get(_norm(packet + RESIDUAL), []) if m.get("state") not in TERMINAL]


def tick(chain_path: Path, dry_run: bool = False, state=None, armer=None, settler=None, ledger=None,
         gate_runner=None, git=None, trigger: str = "watchdog", lock_s: float = LOCK_S, measured=None, history=None,
         alerter=None, now=None) -> dict:
    """One decision, under ONE exclusive per-goal lock (watchdog, event and manual ticks all queue on it)."""
    if os.environ.get("CPP_GSDX_CHAIN", "").lower() == "off":
        return {"action": "off"}
    chain = json.loads(chain_path.read_text(encoding="utf-8-sig"))
    kw = dict(dry_run=dry_run, state=state, armer=armer, settler=settler, ledger=ledger, gate_runner=gate_runner, git=git,
              trigger=trigger, measured=measured, history=history, alerter=alerter, now=now)
    if dry_run:
        return _tick_locked(chain, **kw)
    sys.path.insert(0, str(ROOT))
    from modules.lease.store import Exclusive  # noqa: E402
    lockdir = _state_dir()
    lockdir.mkdir(parents=True, exist_ok=True)
    try:
        with Exclusive(lockdir / f"gsdx-chain-{chain['goal']}.lock", lock_s):
            return _tick_locked(chain, **kw)
    except TimeoutError:
        row = {"action": "skipped_locked", "at": time.time(), "goal": chain["goal"], "trigger": trigger, "dry_run": False}
        if state is None:
            with _log_path().open("a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
        return row


def _tick_locked(chain: dict, dry_run, state, armer, settler, ledger, gate_runner, git, trigger, measured, history,
                 alerter, now) -> dict:
    missions, used = state() if state else _live_state(chain["goal"])
    settled = []
    if not dry_run:
        settled = (settler or (lambda: _live_settle(chain["goal"], missions, chain)))() if (settler or state is None) else []
    finalized = [] if dry_run else finalize(chain, missions, gate_runner, git)
    row = decide(chain, missions, used, _route_target)
    if finalized:
        row["finalized"] = finalized
    if settled:
        row["settled"] = settled
    if row["action"] == "arm":
        if callable(measured):
            meas = measured()
        elif measured is not None:
            meas = measured
        else:
            meas = _live_measured(chain["goal"]) if state is None else {}
        fc = forecast(chain, meas, _route_target)
        row["forecast"], row["overrun"], row["forecast_basis"] = fc["forecast"], fc["overrun"], fc["basis"]
        if used + fc["forecast"] > int(chain["envelope"]):
            row = {"action": "pause_budget", "unit": row["unit"], "used": used, "forecast": fc["forecast"],
                   "overrun": fc["overrun"], "basis": fc["basis"], "envelope": chain["envelope"],
                   "units_left": fc["units_left"], **({"finalized": finalized} if finalized else {})}
    if row["action"] == "arm" and not dry_run:
        unit = next(u for u in chain["units"] if u["id"] == row["unit"])
        if row.get("residual"):   # same unit, the steward's residual packet, one rung up, its own lease
            unit = dict(unit, packet=row["packet"], route=row["route"], succession=f"{unit['id']}:r{row['residual']}")
        fresh = (state() if state else _live_state(chain["goal"]))[0]    # re-read under the lock, right before the arm
        dup = _armed_for(fresh, unit["packet"]) or _armed_for(fresh, unit["packet"] + RESIDUAL)
        if dup:
            row = {"action": "running", "unit": row["unit"], "note": "already armed (re-read under lock)",
                   "mission_id": dup[0]["mission_id"]}
        else:
            led = ledger if ledger is not None else (_live_ledger(chain["goal"]) if state is None else None)
            refusal = _open_lease(led, chain["goal"], unit) if led is not None else None
            if refusal:
                row = refusal
            else:
                try:
                    row["armed"] = (armer or _arm)(chain, unit)
                except Exception as e:  # noqa: BLE001 -- the next tick re-reads missions and sees what the armer made
                    row["armed"] = {"ok": False, "raised": f"{type(e).__name__}: {e}"[:200]}
    t = time.time() if now is None else now
    row.update({"at": t, "goal": chain["goal"], "used": used, "dry_run": dry_run, "trigger": trigger})
    if not dry_run:
        hist = history if history is not None else (_history(chain["goal"]) if state is None else [])
        if silence_check(chain, row, hist, t):
            sink = alerter or (_alert if state is None else None)
            if sink:
                sink(row)
            row["alerted"] = True
    if not dry_run and state is None:
        log = _log_path()
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    return row


# ---- APR-3: event path --------------------------------------------------------------------------------------------
def discover_chains(packet, programs_dir=None) -> list:
    """chain.json files (under <live checkout>/vault/programs/*/) that own `packet` or its .residual.md.
    An unreadable chain.json is returned as (path, error) so the caller records a row."""
    pk = str(packet)
    pk = pk[:-len(RESIDUAL)] if pk.endswith(RESIDUAL) else pk
    base = Path(programs_dir) if programs_dir else LIVE.parent / "vault" / "programs"
    found = []
    for cp in sorted(base.glob("*/chain.json")):
        try:
            c = json.loads(cp.read_text(encoding="utf-8-sig"))
            if any(_norm(u.get("packet", "")) == _norm(pk) for u in c.get("units", [])):
                found.append(cp)
        except (OSError, ValueError, AttributeError) as e:
            found.append((cp, f"{type(e).__name__}: {e}"[:160]))
    return found


def tick_for_packet(packet, programs_dir=None, budget_s: float = 540.0, ticker=None, **kw) -> list:
    """Event-driven advance: tick every chain that owns `packet`. Never raises (an exception is a row); bounded by
    `budget_s` (the sweep stage has 600 s); off with CPP_GSDX_CHAIN_EVENT=off."""
    if os.environ.get("CPP_GSDX_CHAIN_EVENT", "").lower() == "off":
        return []
    t0 = time.monotonic()
    rows = []
    try:
        found = discover_chains(packet, programs_dir)
    except Exception as e:  # noqa: BLE001
        return [{"action": "event_error", "trigger": "event", "error": f"{type(e).__name__}: {e}"[:200]}]
    for cp in found:
        if isinstance(cp, tuple):
            rows.append({"action": "event_error", "trigger": "event", "chain": str(cp[0]), "error": cp[1]})
            continue
        if time.monotonic() - t0 > budget_s:
            rows.append({"action": "event_skipped_budget", "trigger": "event", "chain": str(cp)})
            continue
        try:
            rows.append({**(ticker or tick)(cp, trigger="event", **kw), "chain": str(cp)})
        except Exception as e:  # noqa: BLE001
            rows.append({"action": "event_error", "trigger": "event", "chain": str(cp), "error": f"{type(e).__name__}: {e}"[:200]})
    return rows


# ---- APR-3: health ------------------------------------------------------------------------------------------------
def foreign_bindings(chain: dict, missions: list, open_sids: dict) -> list:
    """Sessions holding open reservations on the goal that own none of the chain's missions (read-only)."""
    packets = {_norm(u["packet"]) for u in chain["units"]} | {_norm(u["packet"] + RESIDUAL) for u in chain["units"]}
    own = set()
    for m in missions:
        if _norm((m.get("wu_packet") or {}).get("path", "")) in packets:
            own |= {(m.get("owner") or {}).get("session_id"), m.get("worker")}
            own |= {p.get("session_id") for p in m.get("previous_owners") or [] if isinstance(p, dict)}
    return [{"sid": s[:8], "hold": h} for s, h in sorted(open_sids.items()) if s not in own]


def status(chain_path: Path, state=None, history=None, measured=None, open_sids=None, git=None, now=None) -> dict:
    """Plain-JSON health of one programme; no model."""
    chain = json.loads(Path(chain_path).read_text(encoding="utf-8-sig"))
    now = time.time() if now is None else now
    missions, used = state() if state else _live_state(chain["goal"])
    row = decide(chain, missions, used, _route_target)
    hist = history if history is not None else _history(chain["goal"])
    bp = _by_packet(missions)
    done = _done_ids(chain)
    units = []
    for u in chain["units"]:
        ms = _unit_ms(u, bp)
        latest = max(ms, key=lambda m: float(m.get("created_at") or 0)) if ms else None
        units.append({"id": u["id"], "done": u["id"] in done, "mission": latest and latest["mission_id"],
                      "state": latest and latest.get("state")})
    marks = []
    for u in chain["units"]:
        for k in ("", SEAL):
            try:
                marks.append(Path(u["receipt"] + k).stat().st_mtime)
            except OSError:
                pass
    marks += [float(h["at"]) for h in hist if h.get("action") == "arm" and h.get("at")]
    gitf = git or (lambda *a: _git(chain["root"], *a))
    ct = gitf("log", "-1", "--format=%ct")
    if ct.strip().isdigit():
        marks.append(float(ct))
    last = hist[-1] if hist else None
    since = now
    for h in reversed(hist):
        if (h.get("action"), h.get("unit")) != (last.get("action"), last.get("unit")):
            break
        since = float(h.get("at") or since)
    meas = (measured() if callable(measured) else measured) if measured is not None else _live_measured(chain["goal"])
    fc = forecast(chain, meas or {}, _route_target)
    nxt = {"running": "terminal transition of the running mission (event tick)",
           "wait_event": f"files: {row.get('missing')}", "wait_predecessor": f"receipt of {row.get('after')}",
           "wait_steward": "steward residual packet", "wait_finalizer": "finalizer residual packet",
           "wait_writer": f"mission(s) {row.get('held_by')} to end", "arm": "this tick arms",
           "complete": None}.get(row["action"], "owner action")
    if open_sids is None:
        try:
            led = _live_ledger(chain["goal"])
            open_sids = {r["sid"]: r["hold"] for r in led._gfold(led._read())["res"].values() if r.get("hold")}
        except Exception:  # noqa: BLE001
            open_sids = {}
    return {"goal": chain["goal"], "current_unit": row.get("unit"), "decision": row["action"], "units": units,
            "last_progress_at": max(marks) if marks else None,
            "last_action": last and {"action": last.get("action"), "unit": last.get("unit"), "trigger": last.get("trigger"),
                                     "since": since, "age_s": round(now - since)},
            "recovery": {k: row[k] for k in ("class", "residuals", "max_residuals", "attempts") if k in row} or None,
            "human_gate": row if row["action"] == "human_gate" else None,
            "envelope": {"total": int(chain["envelope"]), "used": used, "forecast": fc["forecast"],
                         "overrun": fc["overrun"], "basis": fc["basis"], "remaining": int(chain["envelope"]) - used},
            "next_expected_event": nxt,
            "foreign_bindings": foreign_bindings(chain, missions, open_sids)}


def main(argv: list[str]) -> int:
    if argv and argv[0] == "status":
        if "--all" in argv:
            paths = sorted((LIVE.parent / "vault" / "programs").glob("*/chain.json"))
        else:
            paths = [Path(argv[argv.index("--chain") + 1]) if "--chain" in argv else DEFAULT_CHAIN]
        out = []
        for p in paths:
            try:
                out.append({"chain": str(p), **status(p)})
            except Exception as e:  # noqa: BLE001
                out.append({"chain": str(p), "error": f"{type(e).__name__}: {e}"[:200]})
        print(json.dumps(out if "--all" in argv else out[0], indent=1))
        return 0
    if not argv or argv[0] != "tick":
        print(__doc__)
        return 2
    path = Path(argv[argv.index("--chain") + 1]) if "--chain" in argv else DEFAULT_CHAIN
    row = tick(path, dry_run="--dry-run" in argv)
    print(json.dumps(row))
    return 0 if row["action"] != "arm" or (row.get("armed") or {}).get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
