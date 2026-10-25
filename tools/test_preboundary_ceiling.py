"""V-PREB-* gates: the session breaker must deny BEFORE the call that would cross `stop`.

Origin: vault/plans/gsdx-factory-2-gen2-econ-plan-20261025.md section 4 (H0). hooks/session_budget_guard.js
judged `st.tokens > budget.stop` over the calls ALREADY made, so the call that crossed the stop was
always admitted: a 3M envelope ended at 4.31M. The fix denies when processed + next call + the
closeout reserve would cross stop. Kill switch: CPP_PREBOUNDARY=off restores the old comparison.

The replay fixture (tools/fixtures/preboundary_4f881648_usage.json) is usage only, no content: one
row per unique message id of session 4f881648, with the tool names it called. It is replayed through
the guard's own advance()/judge(). A control replays the same rows with the kill switch on and must
OVERSHOOT, so the ceiling assertion is shown able to fail.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
sys.path.insert(0, str(HERE))
import mission_spend as ms  # noqa: E402

GUARD = PP / "hooks" / "session_budget_guard.js"
FIXTURE = HERE / "fixtures" / "preboundary_4f881648_usage.json"
NODE = shutil.which("node") or "node"
SID = "preb-test-0001"
STOP = 3_000_000

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


REPLAY = r"""
const fs = require('fs');
const g = require(process.argv[1]);
const rows = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const tx = process.argv[3];
const b = { target: 2500000, warn: 2800000, stop: 3000000, noprogress_calls: 1e9 };
fs.writeFileSync(tx, '');
const st = g.fresh(null);
let admitted = 0, denied = null, gated = 0;
for (const r of rows) {
  if (r.tools.length) {
    gated += 1;
    const v = g.judge(b, st);
    const h = v && v.hookSpecificOutput;
    if (h && h.permissionDecision === 'deny') { denied = { at: gated, tokens: st.tokens, reason: h.permissionDecisionReason }; break; }
  }
  const content = r.tools.length ? r.tools.map(n => ({ type: 'tool_use', name: n, input: {} })) : [{ type: 'text', text: 'x' }];
  fs.appendFileSync(tx, JSON.stringify({ type: 'assistant', uuid: 'u-' + r.id,
    message: { id: r.id, model: 'm', content, usage: r.usage } }) + '\n');
  g.advance(st, tx);
  admitted = st.tokens;
}
process.stdout.write(JSON.stringify({ admitted, denied, gated }));
"""


def replay(guard, **env):
    tx = Path(tempfile.mkdtemp(prefix="preb_")) / "t.jsonl"
    p = subprocess.run([NODE, "-e", REPLAY, str(guard), str(FIXTURE), str(tx)], capture_output=True, text=True,
                       env=dict(os.environ, **env), timeout=120)
    if p.returncode != 0:
        return {"admitted": -1, "denied": None, "err": p.stderr[-300:]}
    return json.loads(p.stdout)


def row(mid, n, tools=(), ts="2026-10-25T10:00:00.000Z"):
    content = [{"type": "tool_use", "name": t, "input": {}} for t in tools] or [{"type": "text", "text": "x"}]
    return json.dumps({"type": "assistant", "timestamp": ts, "uuid": "u-" + mid, "message": {
        "id": mid, "model": "m", "content": content,
        "usage": {"input_tokens": n, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}}}) + "\n"


RUNNER = r"""
const g = require(process.argv[1]);
let raw = ''; process.stdin.on('data', d => raw += d).on('end', () => {
  process.stdout.write(JSON.stringify({ out: g.decide(JSON.parse(raw)) }));
});
"""


class Box:
    def __init__(self, stop=3000, closeout_calls=None):
        self.root = Path(tempfile.mkdtemp(prefix="preb_box_"))
        self.state = self.root / "state"
        self.state.mkdir()
        self.tx = self.root / "t.jsonl"
        self.tx.write_text("", encoding="utf-8")
        old = os.environ.get("GSD_LONG_RUN_STATE_DIR")
        os.environ["GSD_LONG_RUN_STATE_DIR"] = str(self.state)
        try:
            kw = dict(target=stop // 2, warn=stop * 2 // 3, stop=stop, noprogress_calls=10**9)
            if closeout_calls is not None:
                kw["closeout_calls"] = closeout_calls
            ms.declare(SID, **kw)
        finally:
            if old is None:
                os.environ.pop("GSD_LONG_RUN_STATE_DIR")
            else:
                os.environ["GSD_LONG_RUN_STATE_DIR"] = old

    def append(self, text):
        with open(self.tx, "a", encoding="utf-8") as fh:
            fh.write(text)

    def call(self, tool="Bash", ti=None, **env):
        ev = {"session_id": SID, "tool_name": tool, "tool_input": ti or {"command": "echo hi"},
              "transcript_path": str(self.tx)}
        e = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(self.state), **env)
        for k in ("CPP_SESSION_BUDGET", "CPP_GOAL"):
            e.pop(k, None)
        p = subprocess.run([NODE, "-e", RUNNER, str(GUARD)], input=json.dumps(ev), capture_output=True,
                           text=True, env=e, timeout=60)
        if p.returncode != 0:
            return "CRASH", p.stderr[-200:]
        out = json.loads(p.stdout)["out"]
        h = (out or {}).get("hookSpecificOutput") or {}
        k = "deny" if h.get("permissionDecision") == "deny" else ("advise" if h.get("additionalContext") else "allow")
        return k, h.get("permissionDecisionReason") or h.get("additionalContext") or ""


def main():
    # Replay of the real session's usage through advance()/judge(): the ceiling holds.
    r = replay(GUARD)
    check("V-PREB-REPLAY-CEILING", 0 < r["admitted"] <= STOP and r["denied"] is not None,
          f"admitted {r['admitted']:,} <= stop {STOP:,}; first deny at gated call {r['denied'] and r['denied']['at']} "
          f"{r.get('err', '')}")
    # Control: the old comparison (switch off) over the same rows overshoots, so the gate above can fail.
    c = replay(GUARD, CPP_PREBOUNDARY="off")
    check("V-PREB-REPLAY-CONTROL", c["admitted"] > STOP,
          f"CPP_PREBOUNDARY=off admits {c['admitted']:,} > stop {STOP:,} (the old overshoot)")
    check("V-PREB-WORDING", bool(r["denied"]) and r["denied"]["reason"].startswith("SESSION BUDGET BREAKER --"),
          f"deny reason: {(r['denied'] or {}).get('reason', '')[:90]!r}")
    # Paid inside stop: what was admitted plus the closeout calls at the mean recent size fits under stop.
    rows = json.loads(FIXTURE.read_text(encoding="utf-8"))
    sizes = [sum(x["usage"].values()) for x in rows]
    n = next((i + 1 for i in range(len(sizes)) if sum(sizes[:i + 1]) == r["admitted"]), 0)
    tail = sizes[max(n - 3, 0):n]
    nxt = max(sizes[n - 1], sum(tail) / len(tail)) if n else 0
    # The denied call is not spent, so what is left to pay is the 4 closeout calls.
    check("V-PREB-CLOSEOUT-FITS", n > 0 and r["admitted"] + 4 * nxt <= STOP,
          f"admitted {r['admitted']:,} ({n} calls) + 4 closeout calls at ~{int(nxt):,} = {int(r['admitted'] + 4 * nxt):,} <= {STOP:,}")

    # decide() path on a small envelope: stop 3000, 400 per call, default closeout 4 calls.
    b = Box()
    b.append(row("a", 400, ["Read"]))
    k0, _ = b.call()
    check("V-PREB-QUIET-EARLY", k0 == "allow", f"400 of stop 3000 -> {k0}")
    for i in range(4):
        b.append(row(f"x{i}", 400, ["Read"]))
    k1, why = b.call()
    check("V-PREB-DENY-BEFORE-CROSS", k1 == "deny" and "SESSION BUDGET BREAKER --" in why,
          f"2000 processed + next 400 + 4 closeout x 400 > 3000 -> {k1}")
    k2, _ = b.call(CPP_PREBOUNDARY="off")
    check("V-PREB-KILL", k2 != "deny", f"CPP_PREBOUNDARY=off at 2000/3000 -> {k2}")

    # The closeout allowance still lets a tripped session write its receipt (and nothing else).
    k3, why3 = b.call("Write", {"file_path": str(b.root / "WU-X-receipt.md")})
    check("V-PREB-CLOSEOUT-RECEIPT", k3 == "advise" and "closeout call" in why3,
          f"receipt write after a pre-boundary deny -> {k3}")
    k4, _ = b.call("Write", {"file_path": str(b.root / "other.py")})
    check("V-PREB-CLOSEOUT-ONLY", k4 == "deny", f"non-closeout write after a pre-boundary deny -> {k4}")

    print(f"PREB_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
