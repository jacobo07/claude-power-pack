#!/usr/bin/env python
"""tmux_transport -- exact-target continuation delivery for a Claude session inside tmux.

Spec: vault/specs/interactive-context-rollover.md (GEX44 open item: "no Orca / terminal
inbox -> C4 is MANUAL there; needs an exact tmux provider"). This is that provider. It
is the Linux sibling of continuation_transport.py (Orca) and speaks the SAME outcome
vocabulary, imported from there, so a caller branches on one set of words whichever
host the session lives on. It does not edit or replace the Orca path.

Identity, and why each part is needed:

  * ENDPOINT CAPTURE -- called from the session's own hook, so the process reading
    `TMUX` / `TMUX_PANE` IS a descendant of the pane it names. Recorded: the server
    socket, the server pid (from `TMUX`), the pane id (`%N`) and the pane's shell pid.
  * RESOLUTION -- `list-panes -a` must yield exactly one row with that pane id, whose
    pane pid AND server pid still match the capture. A pane id is unique only for one
    server's lifetime: a restarted server hands out `%0` again, and a respawned pane
    keeps its id with a new process. Either would receive input addressed to its
    predecessor, so both are STALE.
  * WRITABLE -- the pane is alive, NOT in a mode (in copy-mode, send-keys drives the
    copy-mode cursor, not the program), and the program in front is an agent. A pane
    whose foreground command is a shell means Claude exited: typing `/kresume` into
    bash is a command in the wrong world, so it refuses.
  * IDLE -- tmux has no tui-idle. The positive evidence used is that the visible pane
    does not change across QUIESCE_SAMPLES captures: Claude's TUI animates a spinner
    while it works, so a busy session cannot hold still. Bounded by IDLE_WAIT_S.
    Measured against a real Claude TUI is OWED; measured against a synthetic busy and
    a synthetic idle pane in tools/test_tmux_transport.py.
  * SEND -- `send-keys -l` (literal: `/clear` must not be read as key names) to the
    pane id, then a separate `Enter`. Re-resolved immediately before the send.
  * RECEIPT -- `accepted` proves bytes reached that pane and nothing more. Consumption
    is a transcript user row carrying the command after the request, exactly as on
    Orca; with no transcript the outcome is TRANSPORT_ACCEPTED_UNCONFIRMED, never
    DELIVERED.

Kill switches: CPP_CONTINUATION_TRANSPORT=off (shared with Orca) or
CPP_TMUX_TRANSPORT=off. Test seam: CPP_TMUX_CLI = JSON list argv prefix for tmux.

CLI:
    python tools/tmux_transport.py capture --session <sid>
    python tools/tmux_transport.py deliver --session <sid> --kind resume|clear|compact
        --text <cmd> [--transcript <path>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import continuation_transport as ct  # noqa: E402  (outcome vocabulary, one set of words)
import gsd_long_run as lr  # noqa: E402  (ledger, transcript readers, state dir)

CLI_TIMEOUT_S = 10
IDLE_WAIT_S = 120
QUIESCE_SAMPLES = 3
QUIESCE_GAP_S = 1.5
CONSUME_WAIT_S = 120
CONSUME_POLL_S = 3
PANE_ID_RE = re.compile(r"^%\d+$")
# The foreground command of a pane that holds a Claude session. A shell here means
# the agent is gone; anything unknown is not evidence of an agent, so it refuses.
# tmux reports the basename of argv[0], NOT the kernel comm. Measured on GEX44
# 2026-09-28 across live Claude processes: argv0 `claude` / `.../bin/claude` for the
# native install (comm there is the versioned file name, `2.1.283`, which would have
# refused every session had this list been built from comm), and `.../claude.exe` for
# the npm install. `node` covers an npm launcher that execs through node.
AGENT_COMMANDS = frozenset({"claude", "claude.exe", "node"})

VIA = "tmux-exact"


# --------------------------------------------------------------------------- tmux cli
def _cli_prefix() -> list[str]:
    override = os.environ.get("CPP_TMUX_CLI")
    if override:
        return list(json.loads(override))
    return ["tmux"]


def tmux(socket: str | None, args: list[str], timeout: float = CLI_TIMEOUT_S) -> tuple[bool, str]:
    """One tmux call. (ok, stdout-or-error-code). Never raises."""
    argv = _cli_prefix() + (["-S", socket] if socket else []) + args
    try:
        p = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "cli_timeout"
    except Exception as exc:
        return False, f"cli_unavailable:{exc.__class__.__name__}"
    if p.returncode != 0:
        return False, f"exit_{p.returncode}:{(p.stderr or '').strip()[:120]}"
    return True, p.stdout


# --------------------------------------------------------------------------- endpoint
def endpoint_path(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "", session_id or "")[:128] or "unknown"
    return lr.state_dir() / f"tmux-endpoint-{safe}.json"


def parse_tmux_env(tmux_var: str, pane_var: str) -> dict | None:
    """Pure: `TMUX=<socket>,<server_pid>,<session_idx>` + `TMUX_PANE=%N`, or None."""
    parts = (tmux_var or "").rsplit(",", 2)
    pane = (pane_var or "").strip()
    if len(parts) != 3 or not parts[0] or not parts[1].isdigit() or not PANE_ID_RE.match(pane):
        return None
    return {"socket": parts[0], "server_pid": int(parts[1]), "pane_id": pane}


def capture_endpoint(session_id: str, env=None) -> dict:
    """Record where THIS process's session lives. Called from the session's own hook."""
    env = os.environ if env is None else env
    parsed = parse_tmux_env(env.get("TMUX", ""), env.get("TMUX_PANE", ""))
    record = {"session_id": session_id, "host": "unsupported", "captured_at": lr._now_iso(),
              "hook_pid": os.getpid()}
    if parsed:
        ok, out = tmux(parsed["socket"], ["display-message", "-p", "-t", parsed["pane_id"],
                                          "#{pane_pid}"])
        pid = out.strip()
        if ok and pid.isdigit():
            record.update(parsed, host="tmux", pane_pid=int(pid))
        else:
            record["reason"] = f"pane pid unreadable: {out[:80]}"
    try:
        path = endpoint_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(record), encoding="utf-8")
        tmp.replace(path)
    except Exception as exc:
        record["write_error"] = exc.__class__.__name__
    return record


def read_endpoint(session_id: str) -> dict | None:
    try:
        data = json.loads(endpoint_path(session_id).read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


# --------------------------------------------------------------------------- resolution
LIST_FORMAT = "#{pane_id}\t#{pane_pid}\t#{pane_dead}\t#{pane_in_mode}\t#{pane_current_command}"


def parse_panes(stdout: str) -> list[dict]:
    rows = []
    for line in (stdout or "").splitlines():
        f = line.split("\t")
        if len(f) != 5:
            continue
        rows.append({"pane_id": f[0], "pane_pid": int(f[1]) if f[1].isdigit() else None,
                     "dead": f[2] == "1", "in_mode": f[3] == "1", "command": f[4]})
    return rows


def resolve(ep: dict, panes: list[dict], server_pid: int | None) -> tuple[str, dict | None]:
    """Pure: the one pane an endpoint names, or the reason there is not one."""
    if not ep or ep.get("host") != "tmux" or not PANE_ID_RE.match(str(ep.get("pane_id") or "")):
        return ct.NO_ENDPOINT, None
    if server_pid != ep.get("server_pid"):
        return ct.STALE, None          # a restarted server reuses pane ids
    hits = [p for p in panes or [] if p.get("pane_id") == ep["pane_id"]]
    if not hits:
        return ct.NOT_FOUND, None
    if len(hits) > 1:
        return ct.AMBIGUOUS, None
    p = hits[0]
    if p.get("pane_pid") != ep.get("pane_pid"):
        return ct.STALE, p             # respawned pane: same id, new occupant
    if p.get("dead") or p.get("in_mode") or p.get("command") not in AGENT_COMMANDS:
        return ct.NOT_WRITABLE, p
    return "OK", p


def server_pid(socket: str) -> tuple[str, int | None]:
    ok, out = tmux(socket, ["display-message", "-p", "#{pid}"])
    if not ok:
        return out, None
    s = out.strip()
    return ("OK", int(s)) if s.isdigit() else ("unparseable", None)


def look(ep: dict) -> tuple[str, dict | None]:
    """Resolve against the live server. Provider failure is not a verdict about the pane."""
    code, spid = server_pid(ep.get("socket") or "")
    if code != "OK":
        return ct.PROVIDER_DOWN, {"provider_error": code}
    ok, out = tmux(ep["socket"], ["list-panes", "-a", "-F", LIST_FORMAT])
    if not ok:
        return ct.PROVIDER_DOWN, {"provider_error": out}
    return resolve(ep, parse_panes(out), spid)


def pane_digest(ep: dict) -> str | None:
    ok, out = tmux(ep["socket"], ["capture-pane", "-p", "-t", ep["pane_id"]])
    return hashlib.sha256(out.encode("utf-8")).hexdigest() if ok else None


def wait_quiescent(ep: dict, sleep=time.sleep, now=time.time) -> bool:
    """True once QUIESCE_SAMPLES consecutive captures are identical, within IDLE_WAIT_S."""
    deadline = now() + IDLE_WAIT_S
    run, last = 0, None
    while now() < deadline:
        d = pane_digest(ep)
        if d is None:
            return False
        run = run + 1 if d == last else 1
        last = d
        if run >= QUIESCE_SAMPLES:
            return True
        sleep(QUIESCE_GAP_S)
    return False


# --------------------------------------------------------------------------- delivery
def _block(session_id: str, cid: str, outcome: str, **why) -> dict:
    lr.ledger_append(session_id, "delivery_blocked", cid=cid, outcome=outcome, via=VIA, **why)
    return {"outcome": outcome, **why}


def deliver(session_id: str, kind: str, text: str, transcript: str = "", cid: str | None = None,
            requested_at: float | None = None, sleep=time.sleep, now=time.time) -> dict:
    """Type one continuation into the session's own pane, with a receipt.

    capture-time endpoint -> resolve -> wait for a still pane -> RE-resolve -> reconcile
    against the transcript -> send-keys -l + Enter -> wait for the transcript to show it.
    Every exit is a ledger row.
    """
    requested_at = now() if requested_at is None else requested_at
    cid = cid or f"{session_id}:{kind}:{int(requested_at)}"
    lr.ledger_append(session_id, "delivery_requested", cid=cid, kind=kind, text=text, via=VIA)

    for switch in ("CPP_CONTINUATION_TRANSPORT", "CPP_TMUX_TRANSPORT"):
        if (os.environ.get(switch) or "").lower() == "off":
            return _block(session_id, cid, ct.DISABLED, switch=switch)
    if not text:
        return _block(session_id, cid, ct.NO_LINE, expected="a command to type")
    ep = read_endpoint(session_id)
    if not ep:
        return _block(session_id, cid, ct.NO_ENDPOINT, reason="no tmux endpoint captured")
    if ep.get("host") != "tmux":
        return _block(session_id, cid, ct.UNSUPPORTED, host=ep.get("host"))
    events = lr.ledger_events(session_id)
    if any(e.get("cid") == cid and e.get("event") in ("resume_confirmed", "compact_confirmed",
                                                        "clear_confirmed") for e in events):
        return {"outcome": ct.ALREADY}
    if sum(1 for e in events if e.get("event") == "transport_accepted"
           and e.get("cid") == cid) >= ct.MAX_ATTEMPTS:
        return _block(session_id, cid, ct.EXHAUSTED, attempts=ct.MAX_ATTEMPTS)

    verdict, pane = look(ep)
    if verdict != "OK":
        return _block(session_id, cid, verdict, pane_id=ep.get("pane_id"), **_why(pane))
    lr.ledger_append(session_id, "target_resolved", cid=cid, pane_id=ep["pane_id"],
                     pane_pid=ep["pane_pid"], via=VIA)

    if not wait_quiescent(ep, sleep=sleep, now=now):
        return _block(session_id, cid, ct.BUSY, pane_id=ep["pane_id"])

    # Re-resolve immediately before the effect: a pane respawned or put into
    # copy-mode while we waited must not receive input addressed to its predecessor.
    verdict, pane = look(ep)
    if verdict != "OK":
        return _block(session_id, cid, verdict, pane_id=ep.get("pane_id"), **_why(pane))
    if transcript and ct._consumed(transcript, text, requested_at):
        lr.ledger_append(session_id, "delivery_reconciled", cid=cid, outcome=ct.ALREADY, via=VIA)
        return {"outcome": ct.ALREADY}

    ok, err = tmux(ep["socket"], ["send-keys", "-t", ep["pane_id"], "-l", "--", text])
    if ok:
        ok, err = tmux(ep["socket"], ["send-keys", "-t", ep["pane_id"], "Enter"])
    if not ok:
        return _block(session_id, cid, ct.REJECTED, pane_id=ep["pane_id"], refused=err)
    lr.ledger_append(session_id, "transport_accepted", cid=cid, pane_id=ep["pane_id"],
                     pane_pid=ep["pane_pid"], bytes=len(text.encode("utf-8")) + 1, via=VIA)

    if not transcript:
        lr.ledger_append(session_id, "delivery_unconfirmed", cid=cid, reason="no transcript", via=VIA)
        return {"outcome": ct.ACCEPTED_UNCONFIRMED, "pane_id": ep["pane_id"]}
    deadline = now() + CONSUME_WAIT_S
    while now() < deadline:
        if ct._consumed(transcript, text, requested_at):
            lr.ledger_append(session_id, f"{kind}_confirmed", cid=cid, command=text, via=VIA)
            return {"outcome": ct.DELIVERED, "pane_id": ep["pane_id"]}
        sleep(CONSUME_POLL_S)
    lr.ledger_append(session_id, "delivery_unconfirmed", cid=cid, pane_id=ep["pane_id"], via=VIA)
    return {"outcome": ct.ACCEPTED_UNCONFIRMED, "pane_id": ep["pane_id"]}


def _why(pane: dict | None) -> dict:
    if not pane:
        return {}
    keys = ("provider_error", "command", "dead", "in_mode", "pane_pid")
    return {k: pane[k] for k in keys if k in pane}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="exact-target continuation delivery over tmux")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture")
    c.add_argument("--session", required=True)
    d = sub.add_parser("deliver")
    d.add_argument("--session", required=True)
    d.add_argument("--kind", choices=("resume", "clear", "compact"), required=True)
    d.add_argument("--text", required=True)
    d.add_argument("--transcript", default="")
    d.add_argument("--cid", default=None)
    args = ap.parse_args(argv)
    if args.cmd == "capture":
        out = capture_endpoint(args.session)
        print(json.dumps(out))
        return 0 if out.get("host") == "tmux" else 1
    out = deliver(args.session, args.kind, args.text, args.transcript, cid=args.cid)
    print(json.dumps(out))
    return 0 if out.get("outcome") in (ct.DELIVERED, ct.ALREADY) else 1


if __name__ == "__main__":
    sys.exit(main())
