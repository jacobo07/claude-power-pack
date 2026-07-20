"""test_tab_order.py -- hermetic V-gates for tab-order capture + pane_map overlay.

V-TAB-ORDER-WRITTEN       : extension/src/tab_order.js --selftest proves the writer
                            transform emits label+group_index+tab_index+sidPrefix
                            in stable visual order.
V-PANE-MAP-USES-TAB-ORDER : build_pane_map.ps1 with a tab_order.json present orders
                            panes by real tab position, overriding lastActivity.
V-FALLBACK-LAST-ACTIVE    : same build with NO tab_order.json falls back to
                            most-recent-first (prior behavior intact).

Fully hermetic: builds into a throwaway temp StateDir/ProjBase; never touches
~/.claude/state. Run: python tools/test_tab_order.py  (exit 0 iff all pass).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TAB_ORDER_JS = os.path.join(REPO, "extension", "src", "tab_order.js")
BUILD_PS1 = os.path.join(HERE, "build_pane_map.ps1")

passes = 0
fails = 0


def _ok(g, ev):
    global passes
    passes += 1
    print(f"  OK   {g}: {ev}")


def _fail(g, why):
    global fails
    fails += 1
    print(f"  FAIL {g}: {why}")


def enc(cwd):
    return re.sub(r"[^a-zA-Z0-9]", "-", cwd)


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def write_transcript(path, cwd, topic, ts_iso):
    line = json.dumps(
        {
            "type": "user",
            "cwd": cwd,
            "message": {"role": "user", "content": topic},
            "timestamp": ts_iso,
        }
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(line + "\n")


def run_build(state_dir, proj_base):
    cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", BUILD_PS1,
        "-StateDir", state_dir, "-ProjBase", proj_base,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"build_pane_map failed: {r.stderr or r.stdout}")
    with open(os.path.join(state_dir, "pane_map.json"), "r", encoding="utf-8-sig") as f:
        return json.load(f)


# ---- V-TAB-ORDER-WRITTEN (writer transform, node self-test) ----
try:
    r = subprocess.run(["node", TAB_ORDER_JS, "--selftest"], capture_output=True, text=True)
    if r.returncode == 0 and "TAB_ORDER_SELFTEST=PASS" in r.stdout:
        _ok("V-TAB-ORDER-WRITTEN",
            "tab_order.js --selftest: label+group_index+tab_index+sidPrefix emitted, order stable")
    else:
        _fail("V-TAB-ORDER-WRITTEN",
              f"selftest rc={r.returncode} out={r.stdout.strip()[:200]} err={r.stderr.strip()[:200]}")
except FileNotFoundError:
    _fail("V-TAB-ORDER-WRITTEN", "node not found on PATH")

# ---- hermetic fixture for the two build gates ----
root = tempfile.mkdtemp(prefix="pp_taborder_")
try:
    state = os.path.join(root, "state")
    os.makedirs(state)
    proj = os.path.join(root, "proj")
    os.makedirs(proj)
    now = datetime.now(timezone.utc)
    # 3 panes; A newest .. C oldest by mtime (== lastActivity)
    fixtures = [
        ("aaaaaaaa-1111-1111-1111-111111111111", "paneA", 0),
        ("bbbbbbbb-2222-2222-2222-222222222222", "paneB", 1),
        ("cccccccc-3333-3333-3333-333333333333", "paneC", 2),
    ]
    for sid, name, hours_old in fixtures:
        cwd = os.path.join(root, name)
        os.makedirs(cwd)
        pd = os.path.join(proj, enc(cwd))
        os.makedirs(pd)
        jl = os.path.join(pd, sid + ".jsonl")
        ts = now - timedelta(hours=hours_old)
        write_transcript(jl, cwd, f"topic sentinel {name}", iso(ts))
        os.utime(jl, (ts.timestamp(), ts.timestamp()))

    # ---- V-FALLBACK-LAST-ACTIVE (no tab_order.json) ----
    data = run_build(state, proj)
    got = [p["sessionId"][:8] for p in data.get("panes", [])]
    if got == ["aaaaaaaa", "bbbbbbbb", "cccccccc"]:
        _ok("V-FALLBACK-LAST-ACTIVE", f"no tab_order.json -> recent-first {got}")
    else:
        _fail("V-FALLBACK-LAST-ACTIVE", f"expected A,B,C recent-first; got {got}")

    # ---- V-PANE-MAP-USES-TAB-ORDER (tab_order.json present, visual order C,A,B) ----
    tab_order = {
        "generatedAt": iso(now),
        "source": "vscode.window.tabGroups",
        "tabs": [
            {"label": "paneC cccccccc", "group_index": 0, "tab_index": 0,
             "is_active": True, "is_terminal": True, "sidPrefix": "cccccccc"},
            {"label": "paneA aaaaaaaa", "group_index": 0, "tab_index": 1,
             "is_active": False, "is_terminal": True, "sidPrefix": "aaaaaaaa"},
            {"label": "paneB bbbbbbbb", "group_index": 0, "tab_index": 2,
             "is_active": False, "is_terminal": True, "sidPrefix": "bbbbbbbb"},
        ],
    }
    with open(os.path.join(state, "tab_order.json"), "w", encoding="utf-8") as f:
        json.dump(tab_order, f)
    data2 = run_build(state, proj)
    got2 = [p["sessionId"][:8] for p in data2.get("panes", [])]
    if got2 == ["cccccccc", "aaaaaaaa", "bbbbbbbb"]:
        _ok("V-PANE-MAP-USES-TAB-ORDER",
            f"tab order C,A,B honored -> {got2} (overrides recent-first A,B,C)")
    else:
        _fail("V-PANE-MAP-USES-TAB-ORDER", f"expected C,A,B; got {got2}")
finally:
    shutil.rmtree(root, ignore_errors=True)

total = passes + fails
print(f"\nTAB_ORDER_PASS={passes}/{total}  threshold={total}/{total}")
def test_gate():
    """Expose the V-gate result to pytest (see test_compact_rescue.py)."""
    assert fails == 0, f"{fails} V-gate failure(s)"


if __name__ == "__main__":
    sys.exit(0 if fails == 0 else 1)
