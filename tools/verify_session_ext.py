"""verify_session_ext.py -- done-gate for the Session-Preservation + PP Sessions build.

Verifies the static / on-disk artifacts. UI gates (panel renders, no
'History restored', <3s refresh) are inherently post-reload and Owner-observed;
they are reported as PENDING, never fake-passed (no-classified-FAILs doctrine).

Run: python tools/verify_session_ext.py
Exit 0 iff every checkable V-gate passes.
"""
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
STATE = os.path.join(HOME, ".claude", "state")
PROJ = os.path.join(HOME, ".claude", "projects")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(REPO, "extension")

passes = 0
fails = 0
pending = []


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"  OK   {gate}: {ev}")


def _fail(gate, why):
    global fails
    fails += 1
    print(f"  FAIL {gate}: {why}")


def _pending(gate, why):
    pending.append(gate)
    print(f"  PEND {gate}: {why} (post-reload, Owner-observed)")


def encode_cwd(cwd):
    return re.sub(r"[^a-zA-Z0-9]", "-", cwd)


# --- load pane_map.json ---
pm_path = os.path.join(STATE, "pane_map.json")
try:
    with open(pm_path, "r", encoding="utf-8-sig") as f:
        pm = json.load(f)
    panes = pm.get("panes", [])
    _ok("V-PANEMAP-VALID", f"{len(panes)} panes, counts={pm.get('counts')}")
except Exception as e:
    _fail("V-PANEMAP-VALID", f"cannot load pane_map.json: {e}")
    panes = []

# --- no empty required fields ---
empties = [p.get("sessionId", "?") for p in panes
           if not (p.get("repo") and p.get("cwd") and p.get("sessionId") and p.get("resumeCmd") and p.get("status"))]
if panes and not empties:
    _ok("V-PANEMAP-NO-EMPTY", f"all {len(panes)} panes have repo/cwd/sessionId/resumeCmd/status")
elif not panes:
    _fail("V-PANEMAP-NO-EMPTY", "no panes to check")
else:
    _fail("V-PANEMAP-NO-EMPTY", f"{len(empties)} panes with empty fields")

# --- RESUMABLE panes: exact resume + transcript on disk ---
bad = []
for p in panes:
    if p.get("status") in ("RESUMABLE", "OLD"):
        want = f"kclaude --resume {p['sessionId']}"
        jsonl = os.path.join(PROJ, encode_cwd(p["cwd"]), p["sessionId"] + ".jsonl")
        if p.get("resumeCmd") != want or not os.path.isfile(jsonl):
            bad.append(p["sessionId"][:8])
res_count = sum(1 for p in panes if p.get("status") in ("RESUMABLE", "OLD"))
if res_count and not bad:
    _ok("V-PANEMAP-RESUME-EXACT", f"all {res_count} resumable panes: exact --resume + transcript on disk")
elif not res_count:
    _fail("V-PANEMAP-RESUME-EXACT", "no resumable panes found")
else:
    _fail("V-PANEMAP-RESUME-EXACT", f"mismatch/missing transcript: {bad}")

# --- never invents ids: STALE must be plain claude ---
invented = [p["sessionId"][:8] for p in panes
            if p.get("status") == "STALE" and "--resume" in (p.get("resumeCmd") or "")]
stale_count = sum(1 for p in panes if p.get("status") == "STALE")
if not invented:
    _ok("V-PANEMAP-NO-INVENT", f"all {stale_count} STALE panes degrade to plain 'claude' (no invented resume)")
else:
    _fail("V-PANEMAP-NO-INVENT", f"STALE panes with --resume (invented): {invented}")

# --- extension files present ---
need = ["package.json", "src/extension.js", "README.md", "LICENSE.txt", "media/icon.svg", ".vscodeignore"]
missing = [n for n in need if not os.path.isfile(os.path.join(EXT, n.replace("/", os.sep)))]
if not missing:
    _ok("V-EXT-FILES", f"all {len(need)} extension files present")
else:
    _fail("V-EXT-FILES", f"missing: {missing}")

# --- package.json valid + wires view + commands ---
try:
    with open(os.path.join(EXT, "package.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    c = manifest.get("contributes", {})
    has_view = "ppSessions" in c.get("viewsContainers", {}).get("activitybar", [{}])[0].get("id", "") or \
        any(v.get("id") == "ppSessionsView" for v in c.get("views", {}).get("ppSessions", []))
    cmds = {x["command"] for x in c.get("commands", [])}
    need_cmds = {"ppSessions.refresh", "ppSessions.resume", "ppSessions.copyResume", "ppSessions.openMap"}
    if manifest.get("main") and has_view and need_cmds <= cmds:
        _ok("V-EXT-MANIFEST", f"main+view+{len(need_cmds)} commands wired")
    else:
        _fail("V-EXT-MANIFEST", f"view={has_view} cmds_ok={need_cmds <= cmds}")
except Exception as e:
    _fail("V-EXT-MANIFEST", f"package.json invalid: {e}")

# --- vsix built with forward-slash entries + root manifest ---
import zipfile
vsix = os.path.join(REPO, "pp-sessions.vsix")
try:
    with zipfile.ZipFile(vsix) as z:
        names = z.namelist()
    has_manifest = "extension.vsixmanifest" in names
    has_pkg = "extension/package.json" in names
    no_backslash = not any("\\" in n for n in names)
    if has_manifest and has_pkg and no_backslash:
        _ok("V-VSIX-STRUCT", f"{len(names)} entries, forward-slash, manifest+package.json present")
    else:
        _fail("V-VSIX-STRUCT", f"manifest={has_manifest} pkg={has_pkg} fwdslash={no_backslash}")
except Exception as e:
    _fail("V-VSIX-STRUCT", f"cannot open vsix: {e}")

# --- post-reload, Owner-observed gates ---
_pending("V-PANEL-SHOWS-PANES", "panel renders only after Cursor reload activates the extension")
_pending("V-NO-HISTORY-RESTORED", "observable only by reloading and watching each pane")
_pending("V-SNAPSHOT-REFRESH", "FileSystemWatcher latency measurable only with the extension live")

total = passes + fails
print(f"\nSESSION_EXT_PASS={passes}/{total}  pending(post-reload)={len(pending)}  threshold={total}/{total}")
sys.exit(0 if fails == 0 else 1)
