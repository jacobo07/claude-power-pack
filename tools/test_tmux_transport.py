#!/usr/bin/env python
"""Gate for tools/tmux_transport.py -- exact-target delivery into a tmux pane.

Two halves, and the second is the one that counts:

  PURE -- env parsing, pane parsing and every resolve() branch, driven from both poles.
          Runs on any host.
  LIVE -- a REAL tmux server on a private socket (never the default one, which may
          hold a person's sessions). The agent in the pane is a stand-in literally
          named `claude` that appends a transcript user row per line it reads, in the
          shape gsd_long_run.user_issued_command_since parses -- so DELIVERED is judged
          by the same reader production uses, not by this file. The endpoint is
          captured FROM INSIDE the pane by the real CLI, as a hook would.

A host without tmux reports LIVE=UNJUDGED and exits 0 unless --require-live, which the
done-gate uses on GEX44. UNJUDGED is not a pass; the summary line says which it was.

What this gate cannot prove: that a real Claude TUI holds still when idle and moves
when busy. The quiescence signal is proven here against a static and an animating
stand-in; the real-TUI measurement is owed on the first real crossing.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

passes = fails = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {name}")
    else:
        fails += 1
        print(f"  FAIL {name}: {detail}")


# --------------------------------------------------------------------------- pure
def pure(tt, ct) -> None:
    env = tt.parse_tmux_env("/tmp/tmux-1000/default,4242,0", "%7")
    check("V-TMUX-ENV-PARSES", env == {"socket": "/tmp/tmux-1000/default", "server_pid": 4242,
                                        "pane_id": "%7"}, repr(env))
    # A socket path containing a comma must still split from the RIGHT.
    env2 = tt.parse_tmux_env("/tmp/a,b/sock,99,1", "%0")
    check("V-TMUX-ENV-COMMA-IN-SOCKET", bool(env2) and env2["socket"] == "/tmp/a,b/sock", repr(env2))
    bad = [tt.parse_tmux_env("", "%1"), tt.parse_tmux_env("/s,1,0", ""),
           tt.parse_tmux_env("/s,x,0", "%1"), tt.parse_tmux_env("/s,1,0", "7")]
    check("V-TMUX-ENV-REFUSES-MALFORMED", bad == [None] * 4, repr(bad))

    rows = tt.parse_panes("%1\t100\t0\t0\tclaude\n%2\t200\t1\t0\tclaude\njunk\n")
    check("V-TMUX-PANES-PARSE", len(rows) == 2 and rows[1]["dead"] and rows[0]["pane_pid"] == 100,
          repr(rows))

    ep = {"host": "tmux", "socket": "/s", "server_pid": 9, "pane_id": "%1", "pane_pid": 100}
    live = {"pane_id": "%1", "pane_pid": 100, "dead": False, "in_mode": False, "command": "claude"}
    R = lambda panes, spid=9, e=ep: tt.resolve(e, panes, spid)[0]  # noqa: E731
    check("V-TMUX-RESOLVE-OK", R([live]) == "OK")
    # The npm install's argv0 basename, measured on GEX44; the native one is `claude`.
    check("V-TMUX-RESOLVE-NPM-AND-NODE-OK", R([{**live, "command": "claude.exe"}]) == "OK"
          and R([{**live, "command": "node"}]) == "OK")
    # The kernel comm of a native install is the version file name. It is NOT what
    # tmux reports, and the list must not grow to admit it on a misreading.
    check("V-TMUX-RESOLVE-COMM-IS-NOT-ARGV0", R([{**live, "command": "2.1.283"}]) == ct.NOT_WRITABLE)
    check("V-TMUX-RESOLVE-NOT-FOUND", R([{**live, "pane_id": "%2"}]) == ct.NOT_FOUND)
    check("V-TMUX-RESOLVE-AMBIGUOUS", R([live, live]) == ct.AMBIGUOUS)
    check("V-TMUX-RESOLVE-RESPAWN-STALE", R([{**live, "pane_pid": 101}]) == ct.STALE)
    # Server restart alone: same pane id, same pane pid, different server. Isolates the
    # server clause, which the live drill cannot, because a restart also moves pane_pid.
    check("V-TMUX-RESOLVE-SERVER-RESTART-STALE", R([live], spid=10) == ct.STALE)
    check("V-TMUX-RESOLVE-DEAD", R([{**live, "dead": True}]) == ct.NOT_WRITABLE)
    check("V-TMUX-RESOLVE-COPY-MODE", R([{**live, "in_mode": True}]) == ct.NOT_WRITABLE)
    check("V-TMUX-RESOLVE-SHELL-IS-NOT-AGENT", R([{**live, "command": "bash"}]) == ct.NOT_WRITABLE)
    check("V-TMUX-RESOLVE-NO-ENDPOINT",
          R([live], e={**ep, "host": "unsupported"}) == ct.NO_ENDPOINT
          and R([live], e={**ep, "pane_id": "7"}) == ct.NO_ENDPOINT)


# --------------------------------------------------------------------------- live
FAKE_AGENT = r'''#!/usr/bin/env python3
import datetime, json, os, sys, threading, time
tr = os.environ["FAKE_TRANSCRIPT"]
if os.environ.get("FAKE_BUSY") == "1":
    def spin():
        n = 0
        while True:
            n += 1
            sys.stdout.write(f"\rworking {n}"); sys.stdout.flush(); time.sleep(0.3)
    threading.Thread(target=spin, daemon=True).start()
for line in sys.stdin:
    row = {"type": "user", "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "message": {"role": "user", "content": line.rstrip("\n")}}
    with open(tr, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
'''


class Box:
    """A private tmux server. Everything it creates lives under one temp dir."""

    def __init__(self, root: Path):
        self.root, self.sock = root, str(root / "sock")
        # tmux names a pane by the basename of argv[0]. A shebang script's argv[0]
        # is its INTERPRETER (measured: the first live run saw `python3` and the
        # precondition refused). So the stand-in runs the interpreter through a
        # symlink called `claude`, which is also the shape a real native launch has.
        (root / "bin").mkdir()
        script = root / "bin" / "agent.py"
        script.write_text(FAKE_AGENT, encoding="utf-8")
        link = root / "bin" / "claude"
        link.symlink_to(os.path.realpath(sys.executable))
        self.agent = f"{link} {script}"
        self.state = root / "state"
        self.state.mkdir()

    def t(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(["tmux", "-S", self.sock, *args], capture_output=True, text=True)

    def start(self, name: str, sid: str, tail: str, busy: bool = False) -> Path:
        """One session whose shell captures its own endpoint, then execs `tail`."""
        transcript = self.root / f"{name}.jsonl"
        transcript.touch()
        cap = (f"{sys.executable} {HERE / 'tmux_transport.py'} capture --session {sid} "
               f"> {self.root / (name + '.cap')} 2>&1; exec {tail}")
        envs = [f"GSD_LONG_RUN_STATE_DIR={self.state}", f"FAKE_TRANSCRIPT={transcript}",
                f"FAKE_BUSY={'1' if busy else '0'}", "PYTHONDONTWRITEBYTECODE=1"]
        args = ["new-session", "-d", "-s", name, "-x", "100", "-y", "20"]
        for e in envs:
            args += ["-e", e]
        r = self.t(*args, "sh", "-c", cap)
        if r.returncode != 0:
            raise RuntimeError(f"new-session {name}: {r.stderr}")
        # Bounded by the CONDITION, not a sleep: the capture runs inside the pane and
        # finishes asynchronously. Measured: a pane whose tail is `sh` already reports
        # `sh` while the capture is still running, so waiting on the foreground name
        # delivered before any endpoint existed and read as TARGET_UNKNOWN.
        capfile, end = self.root / f"{name}.cap", time.time() + 15
        while time.time() < end and not (capfile.is_file() and capfile.read_text().strip()):
            time.sleep(0.2)
        return transcript

    def pane(self, name: str) -> dict:
        r = self.t("list-panes", "-t", name, "-F", "#{pane_id}\t#{pane_pid}\t#{pane_current_command}")
        f = (r.stdout.strip().splitlines() or [""])[0].split("\t")
        return {"pane_id": f[0], "pane_pid": f[1] if len(f) > 1 else "",
                "command": f[2] if len(f) > 2 else ""}

    def wait_command(self, name: str, want: str, bound: float = 10.0) -> str:
        """Bounded by the CONDITION: the exec into the agent is asynchronous."""
        end, got = time.time() + bound, ""
        while time.time() < end:
            got = self.pane(name)["command"]
            if got == want:
                return got
            time.sleep(0.2)
        return got

    def close(self) -> None:
        self.t("kill-server")


def rows(transcript: Path, text: str) -> int:
    try:
        return sum(1 for ln in transcript.read_text(encoding="utf-8").splitlines() if text in ln)
    except OSError:
        return -1


def live(tt, ct) -> str:
    if not shutil.which("tmux") or os.name == "nt":
        return "UNJUDGED (no tmux on this host)"
    root = Path(tempfile.mkdtemp(prefix="tmuxgate-"))
    box = Box(root)
    os.environ["GSD_LONG_RUN_STATE_DIR"] = str(box.state)
    tt.IDLE_WAIT_S, tt.QUIESCE_GAP_S, tt.CONSUME_WAIT_S, tt.CONSUME_POLL_S = 8, 0.5, 10, 0.5
    try:
        return _live(tt, ct, box)
    finally:
        box.close()
        os.environ.pop("GSD_LONG_RUN_STATE_DIR", None)


def _live(tt, ct, box: Box) -> str:
    before = fails
    verdict = _live_checks(tt, ct, box)
    # PROVEN only when every live check held. The first version returned PROVEN
    # unconditionally and printed LIVE=PROVEN beside a live FAIL.
    return verdict if verdict != "PROVEN" or fails == before else "FAILED"


def _live_checks(tt, ct, box: Box) -> str:
    # --- A: the ordinary path, idle agent, endpoint captured from inside the pane
    tr = box.start("a", "sid-a", str(box.agent))
    got = box.wait_command("a", "claude")
    if got != "claude":
        # Precondition, not a finding: without an agent-named foreground the whole
        # drill measures the allow-list, not delivery.
        check("V-TMUX-LIVE-HARNESS-AGENT-NAMED", False, f"foreground is {got!r}, not 'claude'")
        return "HARNESS"
    cap = json.loads((box.root / "a.cap").read_text(encoding="utf-8").strip().splitlines()[-1])
    p = box.pane("a")
    check("V-TMUX-LIVE-CAPTURE-FROM-INSIDE",
          cap.get("host") == "tmux" and cap.get("pane_id") == p["pane_id"]
          and str(cap.get("pane_pid")) == p["pane_pid"], f"cap={cap} pane={p}")

    t0 = time.time()
    out = tt.deliver("sid-a", "clear", "/clear", str(tr), cid="a-1")
    check("V-TMUX-LIVE-DELIVERED", out.get("outcome") == ct.DELIVERED and rows(tr, "/clear") == 1,
          f"{out} rows={rows(tr, '/clear')}")
    check("V-TMUX-LIVE-LITERAL", "/clear" in tr.read_text(encoding="utf-8"), "bytes not literal")
    again = tt.deliver("sid-a", "clear", "/clear", str(tr), cid="a-1", requested_at=t0)
    check("V-TMUX-LIVE-ALREADY-NOT-RETYPED", again.get("outcome") == ct.ALREADY
          and rows(tr, "/clear") == 1, f"{again} rows={rows(tr, '/clear')}")

    # --- kill switch: nothing typed
    os.environ["CPP_TMUX_TRANSPORT"] = "off"
    try:
        off = tt.deliver("sid-a", "resume", "/kresume", str(tr), cid="a-off")
    finally:
        os.environ.pop("CPP_TMUX_TRANSPORT")
    check("V-TMUX-LIVE-KILL-SWITCH", off.get("outcome") == ct.DISABLED and rows(tr, "/kresume") == 0,
          f"{off}")

    # --- copy-mode: send-keys would drive the cursor, so it must refuse; then the
    # control: leave copy-mode and the same pane accepts.
    box.t("copy-mode", "-t", "a")
    cm = tt.deliver("sid-a", "resume", "/kresume", str(tr), cid="a-cm")
    check("V-TMUX-LIVE-COPY-MODE-REFUSED", cm.get("outcome") == ct.NOT_WRITABLE
          and rows(tr, "/kresume") == 0, f"{cm}")
    box.t("send-keys", "-t", "a", "-X", "cancel")
    ok = tt.deliver("sid-a", "resume", "/kresume", str(tr), cid="a-cm2")
    check("V-TMUX-LIVE-COPY-MODE-CONTROL", ok.get("outcome") == ct.DELIVERED
          and rows(tr, "/kresume") == 1, f"{ok}")

    # --- busy: an animating pane is not idle, and nothing is typed into it
    trb = box.start("b", "sid-b", str(box.agent), busy=True)
    box.wait_command("b", "claude")
    busy = tt.deliver("sid-b", "clear", "/clear", str(trb), cid="b-1")
    check("V-TMUX-LIVE-BUSY-REFUSED", busy.get("outcome") == ct.BUSY and rows(trb, "/clear") == 0,
          f"{busy}")

    # --- the agent exited: a shell in front is not an agent
    box.start("c", "sid-c", "sh")
    box.wait_command("c", "sh")
    sh = tt.deliver("sid-c", "resume", "/kresume", "", cid="c-1")
    check("V-TMUX-LIVE-SHELL-REFUSED", sh.get("outcome") == ct.NOT_WRITABLE, f"{sh}")

    # --- respawn: same pane id, new occupant -> STALE, and nothing reaches the new one
    tr_before = rows(tr, "/after-respawn")
    box.t("respawn-pane", "-k", "-t", "a", str(box.agent))
    box.wait_command("a", "claude")
    rs = tt.deliver("sid-a", "resume", "/after-respawn", str(tr), cid="a-rs")
    check("V-TMUX-LIVE-RESPAWN-STALE", rs.get("outcome") == ct.STALE
          and rows(tr, "/after-respawn") == tr_before, f"{rs}")

    # --- gone: the pane no longer exists
    box.t("kill-session", "-t", "b")
    gone = tt.deliver("sid-b", "clear", "/clear", str(trb), cid="b-2")
    check("V-TMUX-LIVE-GONE-NOT-FOUND", gone.get("outcome") == ct.NOT_FOUND, f"{gone}")

    # --- server down: provider failure, never a verdict about the pane
    box.close()
    down = tt.deliver("sid-a", "resume", "/kresume", str(tr), cid="a-down")
    check("V-TMUX-LIVE-SERVER-DOWN", down.get("outcome") == ct.PROVIDER_DOWN, f"{down}")

    # --- every exit left a ledger row
    ev = [e.get("event") for e in __import__("gsd_long_run").ledger_events("sid-a")]
    check("V-TMUX-LIVE-LEDGER", ev.count("delivery_blocked") >= 4 and "clear_confirmed" in ev
          and "resume_confirmed" in ev, repr(ev[-12:]))
    return "PROVEN"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-live", action="store_true")
    args = ap.parse_args(argv)
    import tmux_transport as tt
    import continuation_transport as ct
    print("PURE")
    pure(tt, ct)
    print("LIVE")
    verdict = live(tt, ct)
    if args.require_live and verdict != "PROVEN":
        check("V-TMUX-LIVE-REQUIRED", False, verdict)
    print(f"\nTMUX_TRANSPORT_PASS={passes}/{passes + fails}  LIVE={verdict}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
