"""Control-plane P&L, CONTROL_PLANE_TOKEN_INCIDENT detector and C2-RESUMPTION generator (cpx R2).

Coordinator tokens are processed tokens of the pane that plans and arms; worker tokens are the
missions' own. The incident is an ABSOLUTE breach (coordinator > cap), never a ratio: a ratio
reads fine while both sides are tiny, and D22/D23 showed the breach is the money."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_COORD_CAP = 1_500_000  # D22/D23 promoted: coordinate from a fresh pane, ~1.5M cap.
INCIDENT = "CONTROL_PLANE_TOKEN_INCIDENT"


def pnl(rows: list[dict]) -> list[dict]:
    """rows: {goal, coordinator_tokens, worker_tokens[, cap]} -> one P&L row per goal."""
    out = []
    for r in rows:
        c, w = int(r.get("coordinator_tokens") or 0), int(r.get("worker_tokens") or 0)
        out.append({"goal": r["goal"], "coordinator": c, "workers": w, "total": c + w,
                    "control_share": round(c / (c + w), 4) if c + w else 0.0,
                    "cap": int(r.get("cap") or DEFAULT_COORD_CAP)})
    return out


def detect(rows: list[dict]) -> list[dict]:
    """Incidents: every goal whose coordinator tokens exceed its cap. Never raises on a bad row:
    an unreadable row is reported as UNMEASURABLE (unmeasurable must not read as healthy)."""
    found = []
    for r in rows:
        try:
            p = pnl([r])[0]
        except (KeyError, TypeError, ValueError) as exc:
            found.append({"goal": (r or {}).get("goal") if isinstance(r, dict) else None,
                          "verdict": "UNMEASURABLE", "error": f"{exc.__class__.__name__}: {exc}"[:120]})
            continue
        if p["coordinator"] > p["cap"]:
            found.append({**p, "verdict": INCIDENT, "over_cap": p["coordinator"] - p["cap"]})
    return found


def filter_mission(rows: list[dict], mission: str | None) -> list[dict]:
    """`status --mission`: only that mission's row (exact id or unambiguous prefix)."""
    if not mission:
        return rows
    return [r for r in rows if str(r.get("mission_id", "")).startswith(mission)]


def collect_state(goal: dict, receipt_dir: Path) -> dict:
    """State from facts: the goal dict (cap/used/root/branch/missions/next) and receipt Status lines."""
    receipts = {}
    for p in sorted(Path(receipt_dir).glob("*-receipt.md")):
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        st = next((re.sub(r"^Status:\s*", "", ln) for ln in lines[:6] if ln.startswith("Status:")), "UNKNOWN")
        receipts[p.name] = st
    return {**goal, "receipts": receipts}


def render_resumption(s: dict) -> str:
    cap, used = int(s["cap"]), int(s["used"])
    L = [f"# RESUMPTION -- {s['goal']} -- GENERATED from state (do not hand-edit)", "",
         f"Identity. Goal {s['goal']}, cap {cap:,}, used {used:,}, remaining {cap - used:,}, "
         f"host {s.get('host', '?')}, root {s.get('root', '?')}.",
         f"Repo {s.get('repo', '?')} (branch {s.get('branch', '?')}). Plan: {s.get('plan', '?')}.", ""]
    c = s.get("coordinator_tokens")
    if c is not None:
        w = int(s.get("worker_tokens") or 0)
        inc = detect([{"goal": s["goal"], "coordinator_tokens": c, "worker_tokens": w,
                       "cap": s.get("coordinator_cap", DEFAULT_COORD_CAP)}])
        L += [f"Control plane: coordinator {int(c):,} vs workers {w:,}. "
              + (f"{INCIDENT}: coordinate from a fresh pane, arm and end." if inc else "Within cap."), ""]
    L.append("Missions:")
    L += [f"- {m['id']}: {m['state']}" for m in s.get("missions", [])] or ["- none"]
    L += ["", "Receipts:"]
    L += [f"- {k}: {v}" for k, v in s["receipts"].items()] or ["- none"]
    L += ["", "Next actions:"]
    L += [f"{i}. {a}" for i, a in enumerate(s.get("next", []), 1)] or ["1. none recorded"]
    L += ["", "Start: run the generator again; never coordinate from a long-context pane.", ""]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("detect")
    d.add_argument("--rows", required=True, help="JSON file: list of {goal,coordinator_tokens,worker_tokens,cap}")
    g = sub.add_parser("resume")
    g.add_argument("--state", required=True, help="JSON file with goal state")
    g.add_argument("--receipts", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "detect":
        rows = json.loads(Path(a.rows).read_text(encoding="utf-8-sig"))
        print(json.dumps({"pnl": pnl(rows), "incidents": detect(rows)}, indent=2))
        return 2 if detect(rows) else 0
    st = collect_state(json.loads(Path(a.state).read_text(encoding="utf-8-sig")), Path(a.receipts))
    sys.stdout.write(render_resumption(st))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
