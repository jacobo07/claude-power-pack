#!/usr/bin/env python3
"""V-ONB-* / V-UNA-* -- by-type onboarding, and the unattended compound driver.

Two features that shipped together on 2026-09-01 and share one failure mode:
both act on EVERY project without being asked, so both are only safe if their
selection is right. A wrong selector here is not a bug in one repo, it is a
wrong action in all of them.

  V-ONB-*  zero-command-bootstrap onboards BY PROJECT TYPE
           (PR-PP-ONBOARDING-BY-PROJECT-TYPE-001). A repo carrying its own
           governance substrate has opted out; stamping ours over it is a
           second law system in one tree, not onboarding.

  V-UNA-*  compound_unattended selects on the MARKER, never on raw files.
           The first dry-run returned 3 candidates, all marker=false -- the
           driver and the --unattended policy it invokes disagreed on what
           "ready" meant, so every run would have been wasted agent sessions.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PP_ROOT / "tools"))

_NODE = os.environ.get("NODE_EXE") or "node"
_HOOK = _PP_ROOT / "hooks" / "zero-command-bootstrap.js"

import compound_unattended as cu  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate}  {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate}  {diagnostic}")


def _make_repo(root: Path, *, fork: str = "", manifest: str = "package.json"):
    root.mkdir(parents=True, exist_ok=True)
    (root / ".git").mkdir(exist_ok=True)
    (root / manifest).write_text('{"name":"t"}', encoding="utf-8")
    if fork:
        (root / fork).mkdir(exist_ok=True)
    return root


def _run_hook(cwd: Path) -> None:
    payload = json.dumps({"cwd": str(cwd).replace("\\", "/"),
                          "session_id": "test"})
    subprocess.run([_NODE, str(_HOOK)], input=payload, capture_output=True,
                   text=True, timeout=30)


def main() -> int:
    print("== V-ONB / V-UNA gates ==")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # ---- V-ONB-STUBS-PLAIN-REPO ---------------------------------------
        plain = _make_repo(tmp / "plain")
        _run_hook(plain)
        cap_file = plain / ".pp-capabilities"
        stubbed = (plain / ".specify" / "memory" / "constitution.md").is_file()
        if stubbed and cap_file.is_file():
            caps = json.loads(cap_file.read_text(encoding="utf-8"))
            if "speckit-constitution" in caps["capabilities"]:
                _ok("V-ONB-STUBS-PLAIN-REPO",
                    f"stubbed + recorded {len(caps['capabilities'])} capabilities")
            else:
                _fail("V-ONB-STUBS-PLAIN-REPO", f"capability not recorded: {caps}")
        else:
            _fail("V-ONB-STUBS-PLAIN-REPO",
                  f"stubbed={stubbed} capabilities_file={cap_file.is_file()}")

        # ---- V-ONB-RESPECTS-FORK ------------------------------------------
        # KobiiSports Resort forked deliberately (.ksr_vault). Its ~75 absent
        # modules are correct, not a coverage gap.
        for marker in (".ksr_vault", ".governance"):
            forked = _make_repo(tmp / f"forked{marker}", fork=marker)
            _run_hook(forked)
            if (forked / ".specify" / "memory" / "constitution.md").is_file():
                _fail("V-ONB-RESPECTS-FORK",
                      f"stubbed over a repo carrying {marker}")
                break
        else:
            _ok("V-ONB-RESPECTS-FORK",
                "no stub written over .ksr_vault or .governance")

        # ---- V-ONB-DECLINE-IS-RECORDED ------------------------------------
        # A decline must be legible as a DECISION, or the next coverage audit
        # reads a healthy fork as missing coverage.
        forked = tmp / "forked.ksr_vault"
        caps = json.loads((forked / ".pp-capabilities").read_text(encoding="utf-8"))
        declined = [d["capability"] for d in caps.get("declined", [])]
        if "speckit-constitution" in declined and caps["capabilities"]:
            _ok("V-ONB-DECLINE-IS-RECORDED",
                f"declined={declined}, still got {len(caps['capabilities'])} universal")
        else:
            _fail("V-ONB-DECLINE-IS-RECORDED", f"got {caps}")

        # ---- V-ONB-LATCH-NOT-OVERLOADED -----------------------------------
        # The capability record must NOT live in .pp-onboarded: that file is
        # the hook's idempotency latch, and a payload there makes the hook a
        # permanent no-op in every repo it touches.
        latch = json.loads((plain / ".pp-onboarded").read_text(encoding="utf-8"))
        if "capabilities" not in latch and "actions" in latch:
            _ok("V-ONB-LATCH-NOT-OVERLOADED",
                ".pp-onboarded stays a latch; capabilities live separately")
        else:
            _fail("V-ONB-LATCH-NOT-OVERLOADED",
                  f"latch carries a capability payload: {list(latch)}")

        # ---- V-UNA-SELECTS-ON-MARKER --------------------------------------
        ready = _make_repo(tmp / "ready")
        (ready / "LEARNINGS_PENDING.md").write_text("x", encoding="utf-8")
        loading = _make_repo(tmp / "loading")
        cache = loading / ".claude" / "cache" / "learnings"
        cache.mkdir(parents=True, exist_ok=True)
        for i in range(4):
            (cache / f"l{i}.md").write_text("x", encoding="utf-8")

        real = cu.pending_learnings
        try:
            # Substitute discovery, not the selection logic under test.
            import indexer  # noqa: F401  (imported by cu.candidates)
            saved = sys.modules["indexer"].active_repos
            sys.modules["indexer"].active_repos = lambda *a, **k: [
                str(ready), str(loading)]
            todo, filling = cu.candidates(10)
            sys.modules["indexer"].active_repos = saved

            todo_names = [Path(t["repo"]).name for t in todo]
            fill_names = [Path(f["repo"]).name for f in filling]
            if todo_names == ["ready"] and fill_names == ["loading"]:
                _ok("V-UNA-SELECTS-ON-MARKER",
                    "marker -> run; 4 unconsumed files -> filling, not run")
            else:
                _fail("V-UNA-SELECTS-ON-MARKER",
                      f"run={todo_names} filling={fill_names}")

            # ---- V-UNA-FILLING-IS-VISIBLE ---------------------------------
            # A loading pipeline must not report as bare idleness -- a producer
            # firing into an empty sink looked healthy here for 80 days once.
            if filling and filling[0]["files"] == 4:
                _ok("V-UNA-FILLING-IS-VISIBLE",
                    "near-misses reported with their file counts")
            else:
                _fail("V-UNA-FILLING-IS-VISIBLE", f"filling={filling}")
        except Exception as e:  # noqa: BLE001
            _fail("V-UNA-SELECTS-ON-MARKER", f"harness error: {e}")
            _fail("V-UNA-FILLING-IS-VISIBLE", "not reached")
        finally:
            cu.pending_learnings = real

    # ---- V-UNA-LOCK-IS-EXCLUSIVE -----------------------------------------
    # Two timers, or a timer racing an interactive run, must not both advance
    # the cursor.
    first = cu.acquire_lock()
    second = cu.acquire_lock()
    if first:
        cu.release_lock()
    if first and not second:
        _ok("V-UNA-LOCK-IS-EXCLUSIVE", "second acquirer refused while held")
    else:
        _fail("V-UNA-LOCK-IS-EXCLUSIVE", f"first={first} second={second}")

    # ---- V-UNA-POLICY-IS-DOCUMENTED --------------------------------------
    # The driver passes --unattended; if the command does not define it, the
    # headless run inherits AskUserQuestion and hangs with nobody to answer.
    body = (_PP_ROOT / "commands" / "compound.md").read_text(encoding="utf-8")
    needed = ["--unattended", "AskUserQuestion is unavailable",
              "origin: unattended-compound"]
    missing = [n for n in needed if n not in body]
    if not missing:
        _ok("V-UNA-POLICY-IS-DOCUMENTED",
            "flag, no-ask rule and provenance stamp all present")
    else:
        _fail("V-UNA-POLICY-IS-DOCUMENTED", f"missing from compound.md: {missing}")

    total = _passes + _fails
    print(f"ONB_UNA_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
