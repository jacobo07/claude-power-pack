#!/usr/bin/env python
"""V-MSH-* gates for spec vault/specs/mission-self-heal.md (tools/mission_remedies.py + its gsd_mission wiring).

Origin (measured 2026-11-08/09, KobiiCraft survivalsmp-spawn on GEX44): a mission HALTED on "Workspace not trusted",
blocked 3 epochs on an approval dialog for a Windows-only MCP server, then held 21 h on a line-ending-only phantom
diff. The sweep detected all three and nothing acted or told anyone.

Real git repositories and real JSON files in a temp dir.
Run: python tools/test_mission_self_heal.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

STATE = tempfile.mkdtemp(prefix="msh-state-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = STATE
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(STATE) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = STATE
CFG = tempfile.mkdtemp(prefix="msh-cfg-")
os.environ["CLAUDE_CONFIG_DIR"] = CFG
os.environ.pop("CPP_MISSION_SELF_HEAL", None)

import gsd_mission as gm  # noqa: E402
import gsd_long_run as lr  # noqa: E402
import mission_remedies as mr  # noqa: E402

GIT = os.environ.get("CPP_GIT_EXE") or r"C:\Program Files\Git\cmd\git.exe"
if not Path(GIT).exists():
    GIT = "git"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t"}
CRLF = b"alpha\r\nbeta\r\n"
results: list[tuple[str, bool, str]] = []


def check(gate: str, cond: bool, msg: str) -> None:
    results.append((gate, bool(cond), msg))
    print(f"[{'PASS' if cond else 'FAIL'}] {gate}: {msg}")


def git(path, *args) -> str:
    r = subprocess.run([GIT, "-C", str(path), *args], capture_output=True, text=True, env=ENV, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"git {args}: {r.stderr}")
    return r.stdout.strip()


def phantom_repo(touch_in_work: bool = False):
    """cwd on `program` with a `-text` CRLF blob under `text eol=lf`; worktree `wt` one commit ahead."""
    root = Path(tempfile.mkdtemp(prefix="msh-repo-"))
    cwd, wt = root / "repo", root / "wt"
    cwd.mkdir()
    git(cwd, "init", "-q", "-b", "program")
    git(cwd, "config", "core.autocrlf", "false")
    (cwd / "seed.txt").write_text("seed", encoding="utf-8")
    (cwd / "doc.md").write_bytes(CRLF)
    git(cwd, "add", "seed.txt", "doc.md")
    git(cwd, "commit", "-q", "-m", "seed with a CRLF blob")
    (cwd / ".gitattributes").write_text("doc.md text eol=lf\n", encoding="utf-8")
    git(cwd, "add", ".gitattributes")
    git(cwd, "commit", "-q", "-m", "attributes say text eol=lf")
    git(cwd, "worktree", "add", "-q", "-b", "work", str(wt))
    (wt / "work.txt").write_text("worker output", encoding="utf-8")
    if touch_in_work:
        (wt / "doc.md").write_bytes(b"alpha\nbeta\ngamma\n")
        git(wt, "add", "doc.md")
    git(wt, "add", "work.txt")
    git(wt, "commit", "-q", "-m", "worker commit")
    # A fresh stat, as in a fresh clone: git re-hashes the file and re-normalises it.
    os.utime(cwd / "doc.md", None)
    return cwd, wt


# ------------------------------------------------------------- phantom dirt
cwd, wt = phantom_repo()
dirty_before = git(cwd, "status", "--porcelain", "--untracked-files=no")
r = gm.align_cwd(str(cwd), str(wt))
check("V-MSH-FIXTURE", "doc.md" in dirty_before, f"fixture reproduces the phantom: porcelain={dirty_before!r}")
check("V-MSH-PHANTOM", r["status"] == "fast_forwarded" and r.get("phantom") == ["doc.md"]
      and git(cwd, "rev-parse", "HEAD") == git(wt, "rev-parse", "HEAD")
      and (cwd / "doc.md").read_bytes() == CRLF, f"{r['status']} phantom={r.get('phantom')}")

cwd, wt = phantom_repo()
(cwd / "doc.md").write_bytes(CRLF + b"a real edit\r\n")
head = git(cwd, "rev-parse", "HEAD")
r = gm.align_cwd(str(cwd), str(wt))
check("V-MSH-REAL-DIRTY", r["status"] == "behind_dirty" and git(cwd, "rev-parse", "HEAD") == head
      and (cwd / "doc.md").read_bytes().endswith(b"a real edit\r\n"), f"{r['status']}, edit intact")

cwd, wt = phantom_repo(touch_in_work=True)
direct = mr.phantom_dirty(lambda p, *a: subprocess.run([GIT, "-C", str(p), *a], capture_output=True, text=True,
                                                       env=ENV, timeout=60),
                          str(cwd), git(cwd, "rev-parse", "HEAD"), git(wt, "rev-parse", "HEAD"))
r = gm.align_cwd(str(cwd), str(wt))
check("V-MSH-PHANTOM-TOUCHED", direct is None and r["status"] == "behind_dirty" and "phantom" not in r,
      f"condition (b) itself refuses (direct={direct}); align={r['status']}")

# Review M1: a real edit on a non-ASCII path beside the phantom must not be read as phantom (quoted-path trap).
cwd, wt = phantom_repo()
uni = cwd / "café.md"
uni.write_text("original\n", encoding="utf-8")
git(cwd, "add", "café.md")
git(cwd, "commit", "-q", "-m", "non-ascii path")
git(wt, "merge", "-q", "--no-edit", "program")
(wt / "more.txt").write_text("x", encoding="utf-8")
git(wt, "add", "more.txt")
git(wt, "commit", "-q", "-m", "more work")
uni.write_text("original\nREAL EDIT\n", encoding="utf-8")
os.utime(cwd / "doc.md", None)
head = git(cwd, "rev-parse", "HEAD")
r = gm.align_cwd(str(cwd), str(wt))
check("V-MSH-NONASCII-REAL", r["status"] == "behind_dirty" and git(cwd, "rev-parse", "HEAD") == head
      and "REAL EDIT" in uni.read_text(encoding="utf-8"), f"{r['status']} (real edit on café.md kept the hold)")

# Review M1: a staged change whose worktree matches HEAD is still a change.
cwd, wt = phantom_repo()
(cwd / "seed.txt").write_text("staged change", encoding="utf-8")
git(cwd, "add", "seed.txt")
(cwd / "seed.txt").write_text("seed", encoding="utf-8")
os.utime(cwd / "doc.md", None)
r = gm.align_cwd(str(cwd), str(wt))
check("V-MSH-STAGED", r["status"] == "behind_dirty", f"{r['status']} (staged change kept the hold)")

os.environ["CPP_MISSION_SELF_HEAL"] = "off"
cwd, wt = phantom_repo()
r = gm.align_cwd(str(cwd), str(wt))
check("V-MSH-OFF-ALIGN", r["status"] == "behind_dirty", f"kill switch -> {r['status']}")
os.environ.pop("CPP_MISSION_SELF_HEAL")

# ------------------------------------------------------------- preflight
claude_json = Path(CFG) / ".claude.json"
roots = Path(STATE) / "mission-self-heal.json"
missions = Path(tempfile.mkdtemp(prefix="msh-missions-"))
inside = missions / "m1"
inside.mkdir()
outside = Path(tempfile.mkdtemp(prefix="msh-outside-"))
BASE = {"numStartups": 7, "projects": {"/elsewhere": {"hasTrustDialogAccepted": True, "x": [1, 2]}}, "oauth": {"k": "v"}}


def reset_cfg():
    claude_json.write_text(json.dumps(BASE), encoding="utf-8")


def proj(cwd_path):
    cfg = json.loads(claude_json.read_text(encoding="utf-8"))
    return cfg, cfg["projects"].get(mr._project_key(cfg, str(cwd_path)), {})


rows: list[tuple] = []
led = lambda event, **kw: rows.append((event, kw))  # noqa: E731

reset_cfg()
roots.write_text(json.dumps({"trust_roots": [str(missions)]}), encoding="utf-8")
mr.preflight({"mission_id": "m-t1", "cwd": str(inside)}, ledger=led)
cfg, p = proj(inside)
others_kept = (cfg["numStartups"] == 7 and cfg["oauth"] == {"k": "v"}
               and cfg["projects"]["/elsewhere"] == BASE["projects"]["/elsewhere"])
check("V-MSH-TRUST", p.get("hasTrustDialogAccepted") is True and others_kept
      and any(e == "remedy_applied" and k["kind"] == "trust" for e, k in rows), f"trust set, other keys kept={others_kept}")

reset_cfg()
before = claude_json.read_bytes()
rows.clear()
mr.preflight({"mission_id": "m-t2", "cwd": str(outside)}, ledger=led)
check("V-MSH-TRUST-OUTSIDE", claude_json.read_bytes() == before
      and any(e == "remedy_refused" and k["kind"] == "trust" for e, k in rows), "outside the roots: file byte-equal")

roots.unlink()
rows.clear()
mr.preflight({"mission_id": "m-t3", "cwd": str(inside)}, ledger=led)
check("V-MSH-TRUST-NOROOTS", claude_json.read_bytes() == before, "no roots file: trust never written")

reset_cfg()
roots.write_text(json.dumps({"trust_roots": [str(missions)]}), encoding="utf-8")
(inside / ".mcp.json").write_text(json.dumps({"mcpServers": {
    "codex": {"command": r"C:\Users\nobody\codex-missing\codex.exe" if os.name == "nt" else "/nonexistent/codex.exe"},
    "py": {"command": sys.executable},
    "remote": {"type": "http", "url": "https://example.invalid/mcp"},
    "expanded": {"command": "${HOME}/bin/tool"}}}), encoding="utf-8")
rows.clear()
sent: list[str] = []
mr.preflight({"mission_id": "m-t4", "cwd": str(inside)}, ledger=led, notifier=lambda t: sent.append(t) or "sent")
local_settings = inside / ".claude" / "settings.local.json"
loc = json.loads(local_settings.read_text(encoding="utf-8")) if local_settings.is_file() else {}
refused = [k for e, k in rows if e == "remedy_refused" and k["kind"] == "mcp"]
check("V-MSH-MCP", loc.get("disabledMcpjsonServers") == ["codex"]
      and bool(refused) and sorted(refused[0]["servers"]) == ["expanded", "py", "remote"] and len(sent) == 1,
      f"local disabled={loc.get('disabledMcpjsonServers')} awaiting={refused[0]['servers'] if refused else None} "
      f"notified={len(sent)} (URL and ${{...}} servers never rejected)")

# The CLI rewrites ~/.claude.json from memory (measured 3x on GEX44): the decision must survive that.
claude_json.write_text(json.dumps(BASE), encoding="utf-8")
rows.clear()
mr.preflight({"mission_id": "m-t4b", "cwd": str(inside)}, ledger=led, notifier=lambda t: "sent")
check("V-MSH-MCP-DURABLE", not [k for e, k in rows if e == "remedy_applied" and k["kind"] == "mcp"],
      "after ~/.claude.json is clobbered, the local-settings decision stands: no re-apply")

os.environ["CPP_MISSION_SELF_HEAL"] = "off"
reset_cfg()
before = claude_json.read_bytes()
out = mr.preflight({"mission_id": "m-t5", "cwd": str(inside)})
check("V-MSH-OFF-PREFLIGHT", out == [] and claude_json.read_bytes() == before, "kill switch: nothing written")
os.environ.pop("CPP_MISSION_SELF_HEAL")

# Review L3: a filesystem-root entry would trust every path; it is ignored.
reset_cfg()
before = claude_json.read_bytes()
roots.write_text(json.dumps({"trust_roots": ["/", "C:\\", ""]}), encoding="utf-8")
(inside / ".mcp.json").unlink()
mr.preflight({"mission_id": "m-t6", "cwd": str(outside)}, ledger=led)
check("V-MSH-ROOT-SLASH", mr.trust_roots() == [] and claude_json.read_bytes() == before, "'/', 'C:\\' and '' ignored")

# ------------------------------------------------------------- notification
calls: list[str] = []
a = mr.notify_incident("m-n1", "launch held: x", "held", notifier=lambda t: calls.append(t) or "sent")
b = mr.notify_incident("m-n1", "launch held: x", "held", notifier=lambda t: calls.append(t) or "sent")
c = mr.notify_incident("m-n1", "other key", "held", notifier=lambda t: calls.append(t) or "sent")
check("V-MSH-NOTIFY", len(calls) == 2 and a == "sent" and b is None and c == "sent", f"calls={len(calls)} (once per key)")

# Review M4: a failed channel is retried, bounded; a later success stops the retries.
tries: list[str] = []
for _ in range(5):
    mr.notify_incident("m-n2", "k", "held", notifier=lambda t: tries.append(t) or "telegram failed: URLError")
fails_ev = [e for e in lr.ledger_events("m-n2") if e.get("event") == "incident_notify_failed"]
check("V-MSH-NOTIFY-RETRY-CAP", len(tries) == mr.NOTIFY_MAX_ATTEMPTS and len(fails_ev) == mr.NOTIFY_MAX_ATTEMPTS
      and not [e for e in lr.ledger_events("m-n2") if e.get("event") == "incident_notified"],
      f"attempts={len(tries)} failed rows={len(fails_ev)}, never marked delivered")
late: list[str] = []
mr.notify_incident("m-n3", "k", "held", notifier=lambda t: late.append(t) or "no channel configured")
mr.notify_incident("m-n3", "k", "held", notifier=lambda t: late.append(t) or "telegram 200")
mr.notify_incident("m-n3", "k", "held", notifier=lambda t: late.append(t) or "telegram 200")
check("V-MSH-NOTIFY-RECOVER", len(late) == 2, f"unconfigured then delivered: {len(late)} attempts, then silent")

os.environ["CPP_MISSION_SELF_HEAL"] = "off"
off_calls: list[str] = []
check("V-MSH-OFF-NOTIFY", mr.notify_incident("m-n4", "k", "x", notifier=lambda t: off_calls.append(t) or "sent") is None
      and not off_calls, "kill switch: no notification")
os.environ.pop("CPP_MISSION_SELF_HEAL")

# Wiring: a real liveness incident reaches the notifier path and is ledgered.
gm_mid = "m-wire1"
seen: list[str] = []
orig = mr.notify_incident
mr.notify_incident = lambda mid, key, why, **kw: seen.append(key) or orig(mid, key, why, notifier=lambda t: "sent")
try:
    gm._note_liveness_incident(gm_mid, "launch held: wired", "held for the wiring gate")
finally:
    mr.notify_incident = orig
ev = [e for e in lr.ledger_events(gm_mid) if e.get("event") == "incident_notified"]
check("V-MSH-WIRED-INCIDENT", seen == ["launch held: wired"] and len(ev) == 1, f"notify reached, ledger rows={len(ev)}")

failed = [g for g, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} PASS" + (f"  FAILED: {failed}" if failed else ""))
sys.exit(1 if failed else 0)
