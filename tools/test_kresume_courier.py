#!/usr/bin/env python3
"""V-KRC-* gates for the /kresume courier. Spec: vault/specs/kresume-courier.md.

The successor's SessionStart hook could not be trusted to arm /kresume on a starved host
(stdin never arrived, the hook returned silently). The courier arms from the PREDECESSOR:
it watches the host registry file of the predecessor's own claude.exe until the session id
changes in place, then arms through the one writer. These gates drive the real courier, the
real arm CLI and the real watchdog step; only the registry file and the gate verdict are
fixtures.

Hermetic: HOME, TEMP (the hub log), the ledger, the registry and the daemon dir are private.
The daemon is never launched: its .ps1 is resolved under the private HOME and is absent there.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURIER = Path(os.environ.get("KRC_TEST_COURIER") or ROOT / "tools" / "kresume_courier.py")
AUTOTYPE = Path(os.environ.get("KRC_TEST_AUTOTYPE") or ROOT / "hooks" / "rollover_autotype.js")
WATCHDOG = Path(os.environ.get("KRC_TEST_WATCHDOG")
                or ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py")
CWD = r"C:\p\ProjKRC"

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


class Box:
    """One private world per case: nothing a case writes can reach another case or the host."""

    def __init__(self, capsule=True, certified=False):
        self.root = Path(tempfile.mkdtemp(prefix="krc_"))
        self.home = self.root / "home"
        self.reg = self.root / "sessions"
        self.state = self.root / "state"
        self.tmp = self.root / "tmp"
        self.hooks = self.home / ".claude" / "hooks"
        for d in (self.home, self.reg, self.state, self.tmp, self.hooks):
            d.mkdir(parents=True, exist_ok=True)
        if capsule:
            caps = self.home / ".claude" / "state" / "rollover" / "capsules"
            caps.mkdir(parents=True, exist_ok=True)
            p = caps / "pred-krc.json"
            p.write_text(json.dumps({"session_id": "pred-krc", "cwd": CWD,
                                     "obligations": ["Ship the courier"]}), encoding="utf-8")
            if certified:
                p.with_suffix(".certified").write_text("x", encoding="utf-8")

    def env(self, **extra):
        e = dict(os.environ)
        e.update({"USERPROFILE": str(self.home), "HOME": str(self.home),
                  "TEMP": str(self.tmp), "TMP": str(self.tmp),
                  "AC_DAEMON_DIR": str(self.hooks),
                  "GSD_LONG_RUN_STATE_DIR": str(self.state),
                  "CPP_CLAUDE_SESSIONS_DIR": str(self.reg),
                  "CPP_KRESUME_COURIER_DEADLINE_S": "6",
                  "CPP_KRESUME_COURIER_POLL_S": "0.2",
                  "PYTHONIOENCODING": "utf-8"})
        e.pop("CPP_KRESUME_AUTOTYPE", None)
        e.update(extra)
        return e

    def register(self, pid, sid, proc_start="1000"):
        (self.reg / f"{pid}.json").write_text(json.dumps(
            {"pid": pid, "sessionId": sid, "procStart": proc_start, "cwd": CWD}), encoding="utf-8")

    def flag(self, sid):
        p = self.hooks / f"auto-compact-trigger-{sid}.flag"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def flags(self):
        return sorted(p.name for p in self.hooks.glob("auto-compact-trigger-*.flag"))

    def courier_rows(self):
        led = self.state / "gsd-autorun-ledger.jsonl"
        if not led.exists():
            return []
        rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
        return [r for r in rows if r.get("event") == "kresume_courier"]

    def hub_log(self):
        p = self.tmp / "pp-session-hub.log"
        return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def run_courier(box, pred, swap_to=None, swap_after=1.0, swap_proc="1000", drop=False,
                resolved=True, **env):
    """Run the real courier; optionally rewrite the registry mid-run like a /clear does.
    resolved=True passes the registry file + identity the way the watchdog does at dispatch;
    False makes the courier look the process up itself (the fallback)."""
    extra = ["--registry-file", str(box.reg / "4242.json"), "--identity", "1000"] if resolved else []
    def later():
        time.sleep(swap_after)
        if drop:
            (box.reg / "4242.json").unlink()
        elif swap_to:
            box.register(4242, swap_to, proc_start=swap_proc)
    if swap_to or drop:
        threading.Thread(target=later, daemon=True).start()
    t0 = time.monotonic()
    r = subprocess.run([sys.executable, str(COURIER), "--predecessor", pred, "--cwd", CWD,
                        "--transcript", r"C:\t\proj\%s.jsonl" % pred, *extra],
                       env=box.env(**env), capture_output=True, text=True, timeout=90)
    return r, time.monotonic() - t0


def courier_gates():
    print("the courier: arms the successor from the predecessor's own process")

    # GREEN: the in-place swap /clear produces -> the NEW id is armed, with the capsule's focus.
    b = Box(); b.register(4242, "pred-krc")
    r, _ = run_courier(b, "pred-krc", swap_to="succ-krc")
    body = b.flag("succ-krc") or {}
    rows = b.courier_rows()
    check("V-KRC-ARMS-NEW-SID",
          body.get("session_id") == "succ-krc" and body.get("fresh_line") == "/kresume focus on Ship the courier"
          and body.get("transcript", "").endswith("succ-krc.jsonl"),
          f"flag={body} rc={r.returncode} err={r.stderr[-300:]!r}")
    check("V-KRC-NEVER-ARMS-PREDECESSOR", b.flag("pred-krc") is None, f"flags={b.flags()}")
    check("V-KRC-ONE-OUTCOME-ARMED",
          len(rows) == 1 and rows[0].get("outcome") == "ARMED" and rows[0].get("successor") == "succ-krc"
          and rows[0].get("session_id") == "pred-krc",
          f"rows={rows}")

    # No swap within the deadline: /clear never landed. Named, bounded, nothing armed.
    b = Box(); b.register(4242, "pred-krc")
    r, took = run_courier(b, "pred-krc")
    rows = b.courier_rows()
    check("V-KRC-CLEAR-NEVER-LANDED",
          [x.get("outcome") for x in rows] == ["CLEAR_NEVER_LANDED"] and b.flags() == [],
          f"rows={rows} flags={b.flags()}")
    check("V-KRC-BOUNDED", took < 30, f"took {took:.1f}s against a 6 s deadline")

    # pid reuse: same file, different process. Must not arm a stranger's session.
    b = Box(); b.register(4242, "pred-krc", proc_start="1000")
    run_courier(b, "pred-krc", swap_to="stranger", swap_proc="2000")
    rows = b.courier_rows()
    check("V-KRC-PID-REUSE-REFUSED",
          [x.get("outcome") for x in rows] == ["PROCESS_GONE"] and b.flags() == [],
          f"rows={rows} flags={b.flags()}")

    # The process exits (registry file removed).
    b = Box(); b.register(4242, "pred-krc")
    run_courier(b, "pred-krc", drop=True)
    rows = b.courier_rows()
    check("V-KRC-PROCESS-GONE", [x.get("outcome") for x in rows] == ["PROCESS_GONE"] and b.flags() == [],
          f"rows={rows}")

    # THE RACE this suite found in the first design: on a loaded host the courier starts AFTER
    # /clear has already swapped the id. With the process resolved at dispatch it still arms.
    b = Box(); b.register(4242, "succ-late")
    run_courier(b, "pred-krc")
    rows = b.courier_rows()
    check("V-KRC-LATE-START-STILL-ARMS",
          [x.get("outcome") for x in rows] == ["ARMED"] and b.flag("succ-late") is not None,
          f"rows={rows} flags={b.flags()}")

    # Fallback lookup (no resolved process passed). Its only logic beyond the resolved path is
    # find_process, so that is what is driven -- in-process, setting the ONE key it reads.
    # (A timed swap against a subprocess raced its ~6 s start on a starved host, and wiping
    # os.environ to fake an in-process run broke child creation on Windows: both harness
    # artifacts, neither the production shape.)
    b = Box(); b.register(4242, "someone-else"); b.register(5151, "pred-krc", proc_start="p5151")
    spec = importlib.util.spec_from_file_location("krc_courier_fb", COURIER)
    kc = importlib.util.module_from_spec(spec); spec.loader.exec_module(kc)
    prev = os.environ.get("CPP_CLAUDE_SESSIONS_DIR")
    os.environ["CPP_CLAUDE_SESSIONS_DIR"] = str(b.reg)
    try:
        found = kc.find_process("pred-krc")
        missing = kc.find_process("nobody")
    finally:
        if prev is None:
            os.environ.pop("CPP_CLAUDE_SESSIONS_DIR", None)
        else:
            os.environ["CPP_CLAUDE_SESSIONS_DIR"] = prev
    check("V-KRC-FALLBACK-FINDS-PROCESS",
          found is not None and found[0].name == "5151.json" and found[1] == "p5151" and missing is None,
          f"found={found} missing={missing}")

    # Nothing names the predecessor: refuse at once rather than watch nothing until the deadline.
    # The deadline is 60 s here, so "well under 60" proves it did not wait, whatever start-up costs.
    b = Box(); b.register(4242, "someone-else")
    r, took = run_courier(b, "pred-krc", resolved=False, CPP_KRESUME_COURIER_DEADLINE_S="60")
    rows = b.courier_rows()
    check("V-KRC-NO-REGISTRY-ENTRY",
          [x.get("outcome") for x in rows] == ["NO_REGISTRY_ENTRY"] and b.flags() == [] and took < 30,
          f"rows={rows} took={took:.1f}s against a 60 s deadline")

    # Two live claude.exe holding ONE session id (measured: pids 21620/41256 on c4f1031c). A
    # detached courier has no ancestry to tell them apart: it must refuse by name, never watch
    # the first match (which may be the other pane, and arm /kresume into it after ITS /clear).
    b = Box(); b.register(4242, "pred-krc"); b.register(5151, "pred-krc", proc_start="p5151")
    r, took = run_courier(b, "pred-krc", resolved=False)
    rows = b.courier_rows()
    check("V-KRC-AMBIGUOUS-REFUSED",
          [x.get("outcome") for x in rows] == ["AMBIGUOUS_REGISTRY"]
          and rows[0].get("candidates") == ["4242.json", "5151.json"] and b.flags() == [],
          f"rows={rows} flags={b.flags()} took={took:.1f}s err={r.stderr[-200:]!r}")

    # No unretired capsule for this cwd (already certified): the one writer declines.
    b = Box(certified=True); b.register(4242, "pred-krc")
    run_courier(b, "pred-krc", swap_to="succ-krc")
    rows = b.courier_rows()
    check("V-KRC-NO-CAPSULE-NOT-ARMED",
          [x.get("outcome") for x in rows] == ["NOT_ARMED"] and b.flags() == [], f"rows={rows}")

    # The arm itself cannot run (node absent): retried a bounded number of times, then a
    # named failure -- never a silent pass, never an endless loop.
    b = Box(); b.register(4242, "pred-krc")
    run_courier(b, "pred-krc", swap_to="succ-krc",
                CPP_KRESUME_COURIER_NODE=str(b.root / "no-such-node.exe"))
    rows = b.courier_rows()
    check("V-KRC-ARM-FAILED-RETRIED-AND-NAMED",
          [x.get("outcome") for x in rows] == ["ARM_FAILED"] and rows[0].get("attempts") == 3
          and b.flags() == [],
          f"rows={rows} flags={b.flags()}")

    # Kill switch, shared with the hook path.
    b = Box(); b.register(4242, "pred-krc")
    run_courier(b, "pred-krc", swap_to="succ-krc", CPP_KRESUME_AUTOTYPE="off")
    check("V-KRC-KILL-SWITCH", b.flags() == [], f"flags={b.flags()} rows={b.courier_rows()}")


def run_autotype(box, stdin_text, *args):
    return subprocess.run(["node", str(AUTOTYPE), *args], input=stdin_text, env=box.env(
        PP_HUB_STDIN_BUDGET_MS="1500"), capture_output=True, text=True, timeout=60)


def hook_gates():
    print("the hook path: the starved shape is pinned, and never silent")

    # The 2026-10-01 shape: SessionStart stdin arrives empty. The hook cannot arm (it has no
    # session id) -- that is WHY the courier exists -- but it must say so.
    b = Box()
    run_autotype(b, "")
    check("V-KRC-HOOK-STARVED-ARMS-NOTHING", b.flags() == [], f"flags={b.flags()}")
    check("V-KRC-HOOK-STARVED-IS-LOGGED", "rollover_autotype" in b.hub_log(),
          f"hub log={b.hub_log()[-300:]!r}")

    # Control: with a real payload the hook path still arms (the courier is a second path,
    # not a replacement that quietly disabled the first).
    b = Box()
    payload = json.dumps({"session_id": "succ-hook", "cwd": CWD, "source": "clear",
                          "transcript_path": r"C:\t\succ-hook.jsonl"})
    run_autotype(b, payload)
    check("V-KRC-HOOK-STILL-ARMS", (b.flag("succ-hook") or {}).get("fresh_line", "").startswith("/kresume"),
          f"flags={b.flags()}")

    # The CLI the courier uses is the same writer: same flag shape as the hook path.
    b = Box()
    r = run_autotype(b, "", "--arm", "succ-cli", CWD, r"C:\t\succ-cli.jsonl")
    out = json.loads(r.stdout or "{}") if r.stdout.strip().startswith("{") else {}
    body = b.flag("succ-cli") or {}
    check("V-KRC-CLI-ONE-WRITER",
          out.get("armed") and body.get("kind") == "kresume" and body.get("session_id") == "succ-cli"
          and body.get("fresh_line") == "/kresume focus on Ship the courier",
          f"out={out} flag={body} rc={r.returncode} err={r.stderr[-200:]!r}")


def wiring_gates():
    print("the wiring: the watchdog spawns the courier where it dispatches /clear")
    tmp = Path(tempfile.mkdtemp(prefix="krc_wd_"))
    os.environ.update({"GSD_LONG_RUN_STATE_DIR": str(tmp / "state"),
                       "GSD_LONG_RUN_SESSIONS_DIR": str(tmp / "sessions"),
                       "GSD_AUTORUN_MARKER_DIR": str(tmp / "state"),
                       "CPP_ROLLOVER_STATE_DIR": str(tmp / "rollover"),
                       "CTXWD_HEARTBEAT_LOG": str(tmp / "context-watchdog.log"),
                       "CTXWD_SNAPSHOT_LEDGER": str(tmp / "context_snapshots.jsonl")})
    for d in ("state", "sessions", "rollover"):
        (tmp / d).mkdir()
    sys.path.insert(0, str(WATCHDOG.parent))
    spec = importlib.util.spec_from_file_location("ctxwd_krc", WATCHDOG)
    wd = importlib.util.module_from_spec(spec)
    sys.modules["ctxwd_krc"] = wd
    spec.loader.exec_module(wd)

    spawned, dispatched = [], []
    wd._dispatch_continuation = lambda s_, kind, **k: dispatched.append(kind) or {"route": "terminal-inbox"}
    wd._detached = lambda argv, s_, event, **f: spawned.append((list(map(str, argv)), event)) or True

    reg = tmp / "registry"
    reg.mkdir()
    os.environ["CPP_CLAUDE_SESSIONS_DIR"] = str(reg)

    def step(verdict, own_too=False):
        s = f"krcwd-{uuid.uuid4().hex[:10]}"
        (reg / "777.json").write_text(json.dumps({"pid": 777, "sessionId": s, "procStart": "p777"}),
                                      encoding="utf-8")
        own = reg / f"{os.getpid()}.json"
        if own_too:
            own.write_text(json.dumps({"pid": os.getpid(), "sessionId": s, "procStart": "pown"}),
                           encoding="utf-8")
        else:
            own.unlink(missing_ok=True)
        for f in (wd.ROLLOVER_ASK_FLAG, wd.ROLLOVER_CLEAR_FLAG, wd.ROLLOVER_WAIT_FLAG):
            wd._clear_flag(s, f)
        wd._rollover_gate = lambda s_: {"verdict": verdict, "reasons": [], "rc": 0}
        spawned.clear(); dispatched.clear()
        wd._rollover_step(s, CWD, r"C:\t\x.jsonl", 75.0)
        return s

    def arg(a, k):
        return a[a.index(k) + 1] if k in a else None

    s = step("SAFE_TO_FORGET")
    courier = [a for a, ev in spawned if any(str(x).endswith("kresume_courier.py") for x in a)]
    c = courier[0] if courier else []
    check("V-KRC-WATCHDOG-SPAWNS-COURIER",
          dispatched == ["clear"] and len(courier) == 1 and arg(c, "--predecessor") == s
          and arg(c, "--cwd") == CWD,
          f"dispatched={dispatched} spawned={spawned}")
    check("V-KRC-WATCHDOG-RESOLVES-AT-DISPATCH",
          arg(c, "--registry-file") == str(reg / "777.json") and arg(c, "--identity") == "p777",
          f"argv={c}")
    # Two holders of the session: this process (the watchdog's own ancestry) and pid 777. The
    # watchdog must hand the courier ITS OWN process, not the first match.
    step("SAFE_TO_FORGET", own_too=True)
    courier = [a for a, ev in spawned if any(str(x).endswith("kresume_courier.py") for x in a)]
    c = courier[0] if courier else []
    check("V-KRC-WATCHDOG-PICKS-OWN-PROCESS",
          arg(c, "--registry-file") == str(reg / f"{os.getpid()}.json") and arg(c, "--identity") == "pown",
          f"argv={c}")
    step("REFUSED")
    check("V-KRC-NO-COURIER-WITHOUT-CLEAR", spawned == [] and dispatched == [],
          f"spawned={spawned} dispatched={dispatched}")


def main() -> int:
    for p in (COURIER, AUTOTYPE, WATCHDOG):
        if not p.is_file():
            print(f"HARNESS-FAILED: missing {p}")
            print(f"KRC_PASS=0/0  threshold=all")
            return 2
    courier_gates()
    hook_gates()
    wiring_gates()
    print(f"\nKRC_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 and passes else 1


if __name__ == "__main__":
    sys.exit(main())
