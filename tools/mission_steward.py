#!/usr/bin/env python
"""Mission steward (WU-S1): a stopped worker is settled, salvaged and handed on, deterministically.

Zero model. Run at the end of every `gsd_mission.supervise()` pass. It never arms, admits or launches
(that is spend authority): it SETTLES the dead owner's holds, writes a PARTIAL receipt (never the canonical
path), extracts refused tool inputs, and PROPOSES a residual packet.

  R1 stopped worker   state HALTED|BLOCKED, owner not alive, wu_packet + goal set, canonical receipt absent
  R2 forgotten goal   a goal with budget left and no live, un-held mission for 30 min -> one incident / 24 h
  R3 unarmed successor a receipt or packet names a successor packet no mission carries -> a row

Every effect is a step recorded on the mission as `steward: {...}` through `transition` (state unchanged),
and the record is re-read before each step, so a repeated or restarted pass does nothing twice.
Kill switch: CPP_MISSION_STEWARD=off.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

FORGOTTEN_AFTER_S = 30 * 60
INCIDENT_EVERY_S = 24 * 3600
BREAKER = "SESSION BUDGET BREAKER"
_SUCC_RE = re.compile(r"^successor(?:_packet)?:[ \t]*(\S.*?)[ \t]*$", re.MULTILINE)
STEPS = ("settled", "partial", "salvage", "residual")


def _off() -> bool:
    return (os.environ.get("CPP_MISSION_STEWARD") or "").strip().lower() in ("off", "0", "false")


def _gm():
    import gsd_mission
    return gsd_mission


def _ms():
    import mission_spend
    return mission_spend


def _atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def spend_goal_for(cwd: str, index: dict) -> str | None:
    ms = _ms()
    c = ms._norm(cwd or ".")
    for goal, e in sorted(index.items()):
        for r in e.get("roots", []):
            r = ms._norm(r)
            if c == r or c.startswith(r + os.sep):
                return goal
    return None


# --------------------------------------------------------------------------- transcript
def read_transcript(path: Path) -> dict:
    """Model calls (deduped by message.id), tool calls, and the refused tool_use inputs."""
    seen, uses, results = set(), {}, {}
    model_calls = tool_calls = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            m = r.get("message") if isinstance(r, dict) else None
            if not isinstance(m, dict):
                continue
            content = m.get("content")
            if r.get("type") == "assistant" and isinstance(content, list):
                mid = m.get("id") or r.get("uuid")
                if m.get("usage") and m.get("model") != "<synthetic>" and mid not in seen:
                    seen.add(mid)
                    model_calls += 1
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        tool_calls += 1
                        uses[b.get("id")] = {"name": b.get("name"), "input": b.get("input")}
            elif r.get("type") == "user" and isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error"):
                        c = b.get("content")
                        if isinstance(c, list):
                            c = " ".join(str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in c)
                        if BREAKER in str(c):
                            results[b.get("tool_use_id")] = str(c)[:300]
    refused = [{"tool_use_id": t, "tool": uses[t]["name"], "input": uses[t]["input"], "error": e}
               for t, e in results.items() if t in uses]
    return {"model_calls": model_calls, "tool_calls": tool_calls, "refused": refused}


def _git_log(tree: str, since: float) -> list[str]:
    g = os.environ.get("CPP_GIT_EXE") or r"C:\Program Files\Git\cmd\git.exe"
    try:
        p = subprocess.run([g, "-C", tree, "log", f"--since=@{int(since)}", "--format=%h %s"],
                           capture_output=True, text=True, timeout=30)
        return [x for x in p.stdout.splitlines() if x.strip()] if p.returncode == 0 else []
    except Exception:  # noqa: BLE001 -- the log is evidence, not a precondition
        return []


# --------------------------------------------------------------------------- R1
def _step(gm, mid: str, rec: dict, name: str, value, steward: dict) -> dict:
    new = {**steward, name: value}
    return gm.transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                         event=f"steward_{name}", steward=new)


def _r1(gm, rec: dict, now: float, *, ledger_for, transcript_for, dry_run: bool, index: dict) -> dict:
    mid = rec["mission_id"]
    row = {"mission_id": mid, "state": rec["state"], "epoch": rec["epoch"], "rule": "R1", "action": "none"}
    st = (rec.get("steward") or {})
    if st.get("done"):
        return None
    sid = (rec.get("owner") or {}).get("session_id")
    receipt = gm.packet_receipt_path(rec)
    if receipt and Path(receipt).exists():
        return None                       # the canonical receipt is the worker's own close: untouched
    g0 = rec.get("goal")
    goal = (g0 if isinstance(g0, str) and g0 else None) or spend_goal_for(rec.get("cwd"), index)
    if not goal:
        row.update(action="UNKNOWN", reason="no spend goal is bound to this mission's cwd: nothing settled")
        return row
    tp = transcript_for(sid)
    if tp is None:
        row.update(action="UNKNOWN", reason=f"no transcript for {sid}: nothing settled")
        return row
    if dry_run:
        row.update(action="would_steward", goal=goal)
        return row
    pkt = Path(rec["wu_packet"]["path"])
    tree, _ = gm.packet_gate_dir(rec)
    tree = tree or rec["cwd"]
    ms = _ms()
    # Only spend made after the goal was declared is the goal's. Measured 2026-10-09, cp50-c1: without
    # this, four recon-factory sessions that had stopped before the goal existed were settled into it
    # (7,534,629 tokens) and the first C1 call was refused over a cap C1 had not touched.
    since = (index.get(goal) or {}).get("since")
    tok = ms.session_tokens(tp, since)
    tr = read_transcript(tp)
    # re-read before each step: the record is the memory, never this pass's earlier copy
    fresh = gm.load(mid) or rec
    st = dict(fresh.get("steward") or {})
    if not st.get("settled"):
        out = ledger_for(goal).settle_stopped(sid, int(tok["tokens"]), f"steward:{mid}")
        fresh = _step(gm, mid, fresh, "settled", {"goal": goal, "sid": sid, "measured": int(tok["tokens"]),
                                                   "since": since, "closed": out.get("closed", []), "at": now}, st)
        row["settled"] = int(tok["tokens"])
    fresh = gm.load(mid) or fresh
    st = dict(fresh.get("steward") or {})
    partial = Path(receipt + ".partial.json") if receipt else Path(str(pkt) + ".partial.json")
    if not st.get("partial"):
        adm_at = float((rec.get("admission") or {}).get("at") or rec.get("created_at") or 0)
        body = {"mission_id": mid, "session": sid, "goal": goal, "status": "PARTIAL", "canonical": False,
                "tokens": tok["tokens"], "tool_calls": tr["tool_calls"], "model_calls": tr["model_calls"],
                "commits": _git_log(tree, adm_at), "refused_calls": len(tr["refused"]),
                "salvage": [f"vault/specs/salvage/{mid}/{x['tool_use_id']}.json" for x in tr["refused"]]}
        _atomic(partial, json.dumps(body, indent=1, sort_keys=True).encode("utf-8"))
        fresh = _step(gm, mid, fresh, "partial", str(partial), st)
        row["partial"] = str(partial)
    fresh = gm.load(mid) or fresh
    st = dict(fresh.get("steward") or {})
    sdir = Path(tree) / "vault" / "specs" / "salvage" / mid
    if not st.get("salvage"):
        files = []
        for x in tr["refused"]:
            f = sdir / f"{x['tool_use_id']}.json"
            _atomic(f, json.dumps(x["input"], indent=1, ensure_ascii=False).encode("utf-8"))
            files.append(str(f))
        fresh = _step(gm, mid, fresh, "salvage", files, st)
        row["salvaged"] = len(files)
    fresh = gm.load(mid) or fresh
    st = dict(fresh.get("steward") or {})
    residual = Path(str(pkt) + ".residual.md")
    if not st.get("residual"):
        text = pkt.read_text(encoding="utf-8-sig", errors="replace") if pkt.exists() else ""
        add = ("\n\n## Residual\n"
               f"Proposed by the steward for stopped mission {mid} (PROPOSAL ONLY: arming it needs the "
               "Owner/coordinator).\n"
               f"- Partial receipt: {partial}\n"
               f"- RESUMPTION_FILE: {Path(tree) / 'RESUMPTION_FILE.md'}\n"
               f"- Salvage: {sdir}\n")
        _atomic(residual, (text + add).encode("utf-8"))
        fresh = _step(gm, mid, fresh, "residual", str(residual), st)
        row["residual"] = str(residual)
    fresh = gm.load(mid) or fresh
    st = dict(fresh.get("steward") or {})
    if not st.get("done"):
        _step(gm, mid, fresh, "done", True, st)
    row["action"] = "steward_settled" if "settled" in row else "steward_completed"
    return row


# --------------------------------------------------------------------------- R2
def _r2(missions: list[dict], now: float, *, ledger_for, dry_run: bool, index: dict) -> list[dict]:
    gm = _gm()
    path = gm.lr.state_dir() / "steward-incidents.jsonl"
    last: dict[str, float] = {}
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(ln)
                last[e["goal"]] = max(last.get(e["goal"], 0), float(e["at"]))
            except (ValueError, KeyError, TypeError):
                continue
    except OSError:
        pass
    rows = []
    for goal in sorted(index):
        covered = False
        for m in missions:
            if spend_goal_for(m.get("cwd"), {goal: index[goal]}) != goal:
                continue
            if m.get("owner_hold"):
                covered = True            # a deliberate hold is never forgotten
            elif m["state"] not in gm.TERMINAL and now - float(m.get("updated_at") or 0) <= FORGOTTEN_AFTER_S:
                covered = True
        if covered:
            continue
        try:
            rem = ledger_for(goal).status().get("remaining")
        except Exception:  # noqa: BLE001
            continue
        if not rem or rem <= 0 or now - last.get(goal, 0) < INCIDENT_EVERY_S:
            continue
        row = {"mission_id": None, "rule": "R2", "action": "forgotten_goal", "goal": goal, "remaining": rem}
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"goal": goal, "at": now, "remaining": rem}) + "\n")
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- R3
def _r3(missions: list[dict]) -> list[dict]:
    gm = _gm()
    armed = set()
    for m in missions:
        p = (m.get("wu_packet") or {}).get("path")
        if p:
            armed.add(os.path.normcase(os.path.abspath(p)))
    rows = []
    for m in missions:
        pkt = (m.get("wu_packet") or {}).get("path")
        if not pkt:
            continue
        texts = [gm._packet_text(m) or ""]
        receipt = gm.packet_receipt_path(m)
        if receipt and Path(receipt).exists():
            try:
                texts.append(Path(receipt).read_text(encoding="utf-8-sig", errors="replace"))
            except OSError:
                pass
        tree, _ = gm.packet_gate_dir(m)
        base = Path(tree or m["cwd"])
        for t in texts:
            for ref in _SUCC_RE.findall(t) + re.findall(r'"successor(?:_packet)?"\s*:\s*"([^"]+)"', t):
                p = Path(ref)
                full = os.path.normcase(os.path.abspath(p if p.is_absolute() else base / p))
                if full not in armed:
                    rows.append({"mission_id": m["mission_id"], "rule": "R3", "action": "successor_unarmed",
                                 "successor": ref})
    seen, out = set(), []
    for r in rows:
        k = (r["mission_id"], r["successor"])
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


# --------------------------------------------------------------------------- entry
def steward_pass(missions: list[dict], now: float, *, sessions=None, pid_alive=None, dry_run: bool = False,
                 ledger_for=None, transcript_for=None) -> list[dict]:
    if _off():
        return []
    gm, ms = _gm(), _ms()
    pid_alive = pid_alive or gm.lr._pid_alive
    ledger_for = ledger_for or ms._goal_ledger
    transcript_for = transcript_for or (lambda sid: ms.find_transcript(sid) if sid else None)
    index = ms.read_index()
    rows = []
    for m in missions:
        if m["state"] not in (gm.COMPLETED, gm.HALTED, gm.BLOCKED) or not m.get("wu_packet"):
            continue
        if m["state"] == gm.COMPLETED and not spend_goal_for(m.get("cwd"), index):
            continue                      # a finished mission bound to no goal has nothing to settle
        verdict = gm.liveness(m.get("owner"), sessions, pid_alive)[0]
        if verdict in (gm.LIVE, gm.WAITING_HUMAN):
            continue
        if not (m.get("owner") or {}).get("session_id"):
            continue
        fresh = gm.load(m["mission_id"]) or m
        r1 = _r1(gm, fresh, now, ledger_for=ledger_for, transcript_for=transcript_for,
                 dry_run=dry_run, index=index)
        if r1:
            rows.append(r1)
    rows += _r2(missions, now, ledger_for=ledger_for, dry_run=dry_run, index=index)
    rows += _r3(missions)
    return rows
