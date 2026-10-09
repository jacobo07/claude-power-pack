"""S4: can a slim-t2 worker run a packet with tools + the session budget guard?

Builds argv with the worktree's own gsd_mission.slim_argv (production path), declares a session budget so
the guard is live, launches with cwd = worktree (child only), then measures from the transcript and the
guard's own state. Prints one JSON verdict. Usage: s4_probe.py <worktree> <out.json>
"""
import json, shutil, subprocess, sys, time, uuid
from pathlib import Path

wt = Path(sys.argv[1]); out = Path(sys.argv[2])
sys.path.insert(0, str(wt / "tools"))
import gsd_mission as gm          # noqa: E402  (worktree copy, the code a factory worker would launch)
import mission_spend as ms        # noqa: E402

GIT = r"C:\Program Files\Git\cmd\git.exe"
# negative control: `s4_probe.py <wt> <out> deny` -> stop below one call, separate probe file; expect a deny
DENY = len(sys.argv) > 3 and sys.argv[3] == "deny"
probe = "vault/specs/gsdx-factory/s4-probe-deny.txt" if DENY else "vault/specs/gsdx-factory/s4-probe.txt"
packet = f"""Work tree: {wt}. Never use Set-Location or cd; use absolute paths and git -C.
1. Read {wt}\\vault\\specs\\gsdx-factory\\dispositions.json and count the entries of its "obligations".
2. Write {wt}\\{probe.replace('/', chr(92))} with exactly one line: S4 slim-t2 probe: obligations=<count>
3. With the PowerShell tool run: & '{GIT}' -C '{wt}' add -- {probe}; & '{GIT}' -C '{wt}' commit -q -m 's4: slim-t2 probe artifact' -- {probe}; & '{GIT}' -C '{wt}' log -1 --format=%h
4. Reply with the short commit hash only."""

sid = str(uuid.uuid4())
rec = {"allowed_tools": ["Read", "Grep", "Glob", "Edit", "Write", "PowerShell"], "model": "sonnet"}
exe = shutil.which("claude") or "claude"
argv = gm.slim_argv(rec, packet, exe, "slim-t2", session_id=sid)
ms.declare(sid, *((5_000, 5_000, 5_000) if DENY else (150_000, 250_000, 400_000)), calls_estimate=8, extra={"feasibility": {"skipped": True,
           "reason": "S4 probe: feasibility projects this pane's floor, not slim-t2's"}})

t0 = time.time()
r = subprocess.run(argv, cwd=str(wt), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=540)
wall = round(time.time() - t0, 1)
res = {"sid": sid, "rc": r.returncode, "wall_s": wall, "argv_flags": [a for a in argv[1:-1]]}
try:
    j = json.loads(r.stdout)
    res["result"] = {k: j.get(k) for k in ("subtype", "is_error", "num_turns", "result", "total_cost_usd", "usage")}
except ValueError:
    res["stdout_tail"] = r.stdout[-1500:]
res["stderr_tail"] = r.stderr[-1500:]

t = ms.find_transcript(sid, ms.projects_root())
res["transcript"] = str(t) if t else None
if t:
    res["tokens"] = ms.session_tokens(t)
    first = None
    for line in open(t, encoding="utf-8", errors="replace"):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        u = ((row.get("message") or {}).get("usage") or {}) if isinstance(row, dict) else {}
        if row.get("type") == "assistant" and u:
            first = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
            break
    res["first_call_context"] = first
state = sorted(p.name for p in ms.state_dir().glob(f"*{sid}*"))
res["guard_state_files"] = state
for name in state:
    if name != ms.budget_path(sid).name:
        try:
            res.setdefault("guard_state", {})[name] = json.loads((ms.state_dir() / name).read_text(encoding="utf-8"))
        except ValueError:
            pass
g = subprocess.run([GIT, "-C", str(wt), "log", "-1", "--format=%h %s", "--", probe], capture_output=True, text=True)
res["probe_commit"] = g.stdout.strip()
res["probe_file"] = (wt / probe).read_text(encoding="utf-8").strip() if (wt / probe).exists() else None
out.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
print(json.dumps({k: res.get(k) for k in ("sid", "rc", "wall_s", "first_call_context", "probe_commit", "probe_file")}))
