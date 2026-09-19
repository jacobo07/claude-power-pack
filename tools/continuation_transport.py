#!/usr/bin/env python
"""continuation_transport -- deliver a continuation to the EXACT session that owns it.

Spec: vault/specs/exact-target-continuation.md (C2, C3, C5).

Why this exists. On 2026-09-18 the autonomous resume for session 8178f7d0 was
"delivered" by a SendKeys daemon that typed `/d1-continue` into whichever Cursor
window had focus. The session lived in an Orca terminal, so it received nothing;
two commands landed in no Claude transcript at all. Focus is presentation, not
identity.

The identity this module uses:

  * ENDPOINT CAPTURE -- every Stop of a session with an autorun marker records
    that process's own `ORCA_PANE_KEY` (`tabId:leafId`). The hook is a child of
    the Claude process, so the key names ITS terminal, and a replaced worker
    rebinds itself on its first Stop.
  * RESOLUTION -- Orca `terminal list` must yield EXACTLY one terminal with that
    tabId+leafId, connected, writable, not orphaned. Anything else refuses.
  * SEND -- `terminal send --terminal <handle>` only. Without `--terminal` the
    Orca CLI falls back to the ACTIVE terminal, which is the foreground trap
    again, so every call names its handle.
  * RECEIPT -- `accepted` proves bytes reached that PTY and nothing more.
    Consumption is a transcript user row carrying the command after the
    request; only that becomes `resume_confirmed`.

There is no foreground fallback. A host without an exact provider (Cursor
terminals are indistinguishable from Win32) is EXACT_SESSION_ROUTING_UNSUPPORTED
and the continuation stays manual, which is honest.

Kill switch: CPP_CONTINUATION_TRANSPORT=off -> every delivery is blocked
(manual). Test seam: CPP_ORCA_CLI = JSON list argv prefix for the Orca CLI.

CLI:
    python tools/continuation_transport.py deliver --session <sid> --kind resume|compact
        [--text <cmd>] [--expect-prefix /compact] [--transcript <path>]
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
import gsd_long_run as lr  # noqa: E402  (ledger, transcript readers, state dir)

ORCA_CLI_DEFAULT = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "OrcaX" / "resources" \
    / "app.asar.unpacked" / "out" / "cli" / "index.js"
NODE_DEFAULT = Path(r"C:\Program Files\nodejs\node.exe")

CLI_TIMEOUT_S = 45
# The FIRST Orca CLI call of a freshly spawned worker pays a cold Electron/node
# start. Measured 2026-09-19 on this host at 551 MB free, same instant, same
# command (`terminal list --json`, all three returning ok):
#     cold 101,628 ms  |  warm 7,272 ms  |  warm 7,268 ms
# CLI_TIMEOUT_S was sized against the warm path (6.4x headroom) and is blind to
# the cold one (0.44x -- a guaranteed loss). Since `spawn_delivery` starts a new
# process per delivery, the first call is ALWAYS cold, so the transport failed
# most reliably on the one attempt a crossing gets: session de7f3c91 lost both
# its compact (46 s) and, 40 minutes later, its resume (50 s) to exactly this.
#
# This is a budget, not a raised ceiling. A cold start is a known fixed cost and
# is paid once and explicitly; CLI_TIMEOUT_S stays tight so that genuine
# slowness is still caught on every subsequent call.
COLD_START_BUDGET_S = 180
IDLE_WAIT_MS = 120_000
CONSUME_WAIT_S = 120
CONSUME_POLL_S = 3
MAX_ATTEMPTS = 2
_UUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
PANE_KEY_RE = re.compile(rf"^([^:\s]+):({_UUID})$")

# Outcomes. Disjoint on purpose: "could not ask" is never "refused", and
# neither is ever reported as delivered.
DELIVERED = "DELIVERED_AND_CONSUMED"
ACCEPTED_UNCONFIRMED = "TRANSPORT_ACCEPTED_UNCONFIRMED"
ALREADY = "ALREADY_CONSUMED"
UNSUPPORTED = "EXACT_SESSION_ROUTING_UNSUPPORTED"
DISABLED = "BLOCKED_TRANSPORT_DISABLED"
NO_ENDPOINT = "TARGET_UNKNOWN"
NOT_FOUND = "TARGET_NOT_FOUND"
AMBIGUOUS = "TARGET_AMBIGUOUS"
STALE = "STALE_TARGET"
NOT_WRITABLE = "TARGET_NOT_WRITABLE"
PROVIDER_DOWN = "BLOCKED_BY_DELIVERY_PROVIDER"
BUSY = "TARGET_NOT_IDLE"
REJECTED = "DELIVERY_REJECTED"
NO_LINE = "EXPECTED_LINE_MISSING"
EXHAUSTED = "ATTEMPTS_EXHAUSTED"


# --------------------------------------------------------------------------- endpoint
def endpoint_path(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "", session_id or "")[:128] or "unknown"
    return lr.state_dir() / f"continuation-endpoint-{safe}.json"


def capture_endpoint(session_id: str, env=None) -> dict:
    """Record where THIS process's session lives. Called from the session's own hook."""
    env = os.environ if env is None else env
    key = (env.get("ORCA_PANE_KEY") or "").strip()
    host = "orca" if PANE_KEY_RE.match(key) else "unsupported"
    record = {"session_id": session_id, "host": host, "pane_key": key if host == "orca" else None,
              "captured_at": lr._now_iso(), "hook_pid": os.getpid()}
    try:
        path = endpoint_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(record), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass
    return record


def read_endpoint(session_id: str) -> dict | None:
    try:
        data = json.loads(endpoint_path(session_id).read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def resolve(pane_key: str, terminals: list) -> tuple[str, dict | None]:
    """Pure: the one terminal a pane key names, or the reason there is not one."""
    m = PANE_KEY_RE.match(pane_key or "")
    if not m:
        return NO_ENDPOINT, None
    tab, leaf = m.group(1), m.group(2).lower()
    hits = [t for t in terminals or [] if isinstance(t, dict)
            and t.get("tabId") == tab and str(t.get("leafId") or "").lower() == leaf]
    if not hits:
        return NOT_FOUND, None
    if len(hits) > 1:
        return AMBIGUOUS, None
    t = hits[0]
    if t.get("orphaned"):
        return STALE, t
    if not t.get("connected") or not t.get("writable"):
        return NOT_WRITABLE, t
    return "OK", t


# --------------------------------------------------------------------------- orca cli
def _cli_prefix() -> list[str]:
    override = os.environ.get("CPP_ORCA_CLI")
    if override:
        return list(json.loads(override))
    return [str(NODE_DEFAULT), str(ORCA_CLI_DEFAULT)]


_WARM = False


def _reset_warm() -> None:
    """Forget that the cold start was paid. For gates; never called in production."""
    global _WARM
    _WARM = False


def orca(args: list[str], timeout: float | None = None) -> dict:
    """Run one Orca CLI call. Returns the JSON envelope, or {"ok": False, "error": {...}}.

    `timeout=None` means "decide": the cold budget until this process has
    actually run the CLI once, the tight warm ceiling thereafter. An explicit
    timeout from the caller is always honoured unchanged -- the tui-idle wait
    sets its own, and it must not be widened by this.
    """
    global _WARM
    if timeout is None:
        timeout = CLI_TIMEOUT_S if _WARM else COLD_START_BUDGET_S
    try:
        p = subprocess.run(_cli_prefix() + args + ["--json"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout,
                           creationflags=0x08000000 if os.name == "nt" else 0)
    except subprocess.TimeoutExpired:
        # Warm even on a timeout: the dominant cold cost is the interpreter and
        # asar image reaching the OS file cache, and a killed process leaves
        # that paid. This is what makes the retry in list_terminals() cheap.
        _WARM = True
        return {"ok": False, "error": {"code": "cli_timeout", "message": f"{args[:2]} > {timeout}s"}}
    except Exception as exc:
        return {"ok": False, "error": {"code": "cli_unavailable", "message": exc.__class__.__name__}}
    # The CLI ran to completion, so the cold cost is paid whatever it answered.
    _WARM = True
    try:
        env = json.loads(p.stdout or "")
    except Exception:
        return {"ok": False, "error": {"code": "cli_unparseable", "message": (p.stdout or p.stderr)[:200]}}
    return env if isinstance(env, dict) else {"ok": False, "error": {"code": "cli_unparseable"}}


def list_terminals() -> tuple[str, list]:
    """The first CLI call of a delivery, so the one that pays any cold start.

    A `cli_timeout` here is retried EXACTLY once. By the retry the interpreter
    and asar image are cached, so the second call runs on the warm path (7.3 s
    measured against a 45 s ceiling) -- which is why one retry is enough and a
    loop would be superstition. Only cli_timeout is retried: a provider that
    answered `runtime_unavailable` has told us something true, and repeating
    the question does not make it less true.
    """
    env = orca(["terminal", "list"])
    if (env.get("error") or {}).get("code") == "cli_timeout":
        env = orca(["terminal", "list"])
    if not env.get("ok"):
        return (env.get("error") or {}).get("code") or "unknown", []
    return "OK", list(((env.get("result") or {}).get("terminals")) or [])


# --------------------------------------------------------------------------- delivery
def _ledger(session_id: str, event: str, **fields) -> None:
    lr.ledger_append(session_id, event, **fields)


def _attempts(session_id: str, cid: str) -> int:
    return sum(1 for e in lr.ledger_events(session_id)
               if e.get("event") == "transport_accepted" and e.get("cid") == cid)


def _consumed(transcript: str, text: str, since: float) -> bool:
    return bool(transcript) and lr.user_issued_command_since(Path(transcript), text, since)


def _block(session_id: str, cid: str, outcome: str, **why) -> dict:
    _ledger(session_id, "delivery_blocked", cid=cid, outcome=outcome, **why)
    return {"outcome": outcome, **why}


def deliver(session_id: str, kind: str, text: str | None = None, expect_prefix: str | None = None,
            transcript: str = "", cid: str | None = None, requested_at: float | None = None,
            sleep=time.sleep, now=time.time) -> dict:
    """Deliver one continuation to the session's own terminal, with a receipt.

    Order matters and is the whole point: capture-time endpoint -> resolve ->
    wait for the agent to be idle -> RE-resolve (incarnation must not move) ->
    reconcile against the transcript -> send with --terminal -> wait for the
    transcript to show consumption. Every exit is a ledger row.
    """
    requested_at = now() if requested_at is None else requested_at
    cid = cid or f"{session_id}:{kind}:{int(requested_at)}"
    _ledger(session_id, "delivery_requested", cid=cid, kind=kind, text=text,
            expect_prefix=expect_prefix)

    if (os.environ.get("CPP_CONTINUATION_TRANSPORT") or "").lower() == "off":
        return _block(session_id, cid, DISABLED)
    ep = read_endpoint(session_id)
    if not ep:
        return _block(session_id, cid, NO_ENDPOINT, reason="no endpoint captured for this session")
    if ep.get("host") != "orca":
        return _block(session_id, cid, UNSUPPORTED, host=ep.get("host"))
    # One logical continuation, many transport attempts: a cid already
    # confirmed is done, and a cid that has spent its attempts stops.
    if any(e.get("cid") == cid and e.get("event") in ("resume_confirmed", "compact_confirmed")
           for e in lr.ledger_events(session_id)):
        return {"outcome": ALREADY}
    if _attempts(session_id, cid) >= MAX_ATTEMPTS:
        return _block(session_id, cid, EXHAUSTED, attempts=MAX_ATTEMPTS)

    code, terms = list_terminals()
    if code != "OK":
        return _block(session_id, cid, PROVIDER_DOWN, provider_error=code)
    verdict, target = resolve(ep["pane_key"], terms)
    if verdict != "OK":
        return _block(session_id, cid, verdict, pane_key=ep["pane_key"])
    handle, incarnation = target["handle"], target.get("incarnationId")
    _ledger(session_id, "target_resolved", cid=cid, handle=handle, incarnation=incarnation,
            pty=target.get("ptyId"), pane_key=ep["pane_key"])

    waited = orca(["terminal", "wait", "--terminal", handle, "--for", "tui-idle",
                   "--timeout-ms", str(IDLE_WAIT_MS)], timeout=IDLE_WAIT_MS / 1000 + 15)
    if not waited.get("ok") or not ((waited.get("result") or {}).get("wait") or {}).get("satisfied"):
        return _block(session_id, cid, BUSY, handle=handle,
                      provider_error=(waited.get("error") or {}).get("code"))

    # Re-resolve immediately before the effect: a terminal replaced while we
    # waited must not receive input addressed to its predecessor.
    code, terms = list_terminals()
    if code != "OK":
        return _block(session_id, cid, PROVIDER_DOWN, provider_error=code)
    verdict, again = resolve(ep["pane_key"], terms)
    if verdict != "OK":
        return _block(session_id, cid, verdict, pane_key=ep["pane_key"])
    if again["handle"] != handle or again.get("incarnationId") != incarnation:
        return _block(session_id, cid, STALE, handle=handle, was=incarnation,
                      now=again.get("incarnationId"))

    if kind == "compact":
        line = lr.last_line(lr.last_assistant_text(Path(transcript))) if transcript else ""
        if not expect_prefix or not line.startswith(expect_prefix):
            return _block(session_id, cid, NO_LINE, expected=expect_prefix, got=line[:80])
        text = line
    if not text:
        return _block(session_id, cid, NO_LINE, expected="a resume command")
    if _consumed(transcript, text, requested_at):
        _ledger(session_id, "delivery_reconciled", cid=cid, outcome=ALREADY)
        return {"outcome": ALREADY}

    sent = orca(["terminal", "send", "--terminal", handle, "--text", text, "--enter"])
    send = (sent.get("result") or {}).get("send") or {}
    if not sent.get("ok") or not send.get("accepted"):
        return _block(session_id, cid, REJECTED, handle=handle,
                      refused=send.get("refusedReason") or (sent.get("error") or {}).get("code"))
    _ledger(session_id, "transport_accepted", cid=cid, handle=handle, incarnation=incarnation,
            bytes=send.get("bytesWritten"))

    deadline = now() + CONSUME_WAIT_S
    while now() < deadline:
        if _consumed(transcript, text, requested_at):
            _ledger(session_id, "resume_confirmed" if kind == "resume" else "compact_confirmed",
                    cid=cid, command=text, via="orca-exact")
            return {"outcome": DELIVERED, "handle": handle}
        sleep(CONSUME_POLL_S)
    _ledger(session_id, "delivery_unconfirmed", cid=cid, handle=handle)
    return {"outcome": ACCEPTED_UNCONFIRMED, "handle": handle}


def job_path(cid: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", cid)[:180]
    return lr.state_dir() / "continuation-jobs" / f"{safe}.json"


def write_job(session_id: str, kind: str, text: str | None, expect_prefix: str | None,
              transcript: str, cid: str) -> Path:
    """The pending continuation, durable. It survives a worker that never starts."""
    path = job_path(cid)
    path.parent.mkdir(parents=True, exist_ok=True)
    job = {"session_id": session_id, "kind": kind, "text": text, "expect_prefix": expect_prefix,
           "transcript": transcript or "", "cid": cid, "requested_at": time.time()}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(job), encoding="utf-8")
    tmp.replace(path)
    return path


def run_job(path: Path) -> dict:
    job = json.loads(Path(path).read_text(encoding="utf-8"))
    out = deliver(job["session_id"], job["kind"], job.get("text"), job.get("expect_prefix"),
                  job.get("transcript") or "", cid=job["cid"], requested_at=job.get("requested_at"))
    if out.get("outcome") in (DELIVERED, ALREADY, ACCEPTED_UNCONFIRMED):
        Path(path).unlink(missing_ok=True)
    return out


def spawn_delivery(session_id: str, kind: str, text: str | None, expect_prefix: str | None,
                   transcript: str, cid: str) -> bool:
    """Persist the job, then run it detached (the Orca CLI costs seconds; a Stop hook has a budget).

    The spawn is `cmd /c start "" /B` because a detached Popen straight from a
    Python Stop hook silently no-ops on this host (context-watchdog.py, measured
    2026-05-20). Only the job path is passed: it is space-free, while transcript
    paths ("Cursor Projects") and command text are not, and cmd would re-split them.
    """
    try:
        path = write_job(session_id, kind, text, expect_prefix, transcript, cid)
    except Exception:
        return False
    if os.environ.get("GSD_LONG_RUN_NO_SPAWN") == "1":
        return False
    try:
        subprocess.Popen(["cmd.exe", "/c", "start", "", "/B", sys.executable,
                          str(Path(__file__).resolve()), "run-job", "--job", str(path)],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, creationflags=0x08000000)
        return True
    except Exception:
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="exact-target continuation delivery")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("deliver")
    d.add_argument("--session", required=True)
    d.add_argument("--kind", choices=("resume", "compact"), required=True)
    d.add_argument("--text", default=None)
    d.add_argument("--expect-prefix", default=None)
    d.add_argument("--transcript", default="")
    d.add_argument("--cid", default=None)
    j = sub.add_parser("run-job")
    j.add_argument("--job", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "run-job":
        out = run_job(Path(args.job))
    else:
        out = deliver(args.session, args.kind, args.text, args.expect_prefix, args.transcript,
                      cid=args.cid)
    print(json.dumps(out))
    return 0 if out.get("outcome") in (DELIVERED, ALREADY) else 1


if __name__ == "__main__":
    sys.exit(main())
