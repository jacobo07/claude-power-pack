"""V-HBPATH-* -- the gsd_x heartbeat resolves its file at CALL time (code review WR-07).

`modules/gsd_x/heartbeat.py` used to bind `_STATE` / `HEARTBEAT` once, at import.
`modules/gsd_x/cli.py` imports it and `cli.main()` records a heartbeat on every
judgement, so any suite that swapped HOME (or CLAUDE_STATE_DIR) AFTER the module
was imported still wrote the REAL ~/.claude/state/gsd-x-heartbeat.json and bumped
its production counters. The fix resolves the path per call; these gates prove

  * a CLAUDE_STATE_DIR or HOME/USERPROFILE swapped after import is honoured;
  * for the real HOME layout the path is exactly what the import-time formula
    produced (CLAUDE_STATE_DIR first, else <home>/.claude/state), so the live
    UserPromptSubmit hook's behaviour is unchanged;
  * fail-open stays absolute: an unwritable state dir, or a process with no
    resolvable home at all (which used to RAISE at import), costs nothing;
  * `heartbeat.HEARTBEAT` still resolves for any reader that used it.

The module is imported after CLAUDE_STATE_DIR points at a temp "decoy", so even
against the unfixed module no gate here can write the real heartbeat.

Run: python tools/test_gsd_x_heartbeat_path.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

_PASS = 0
_FAIL = 0
EXPECTED = 7
_HOME_KEYS = ("HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "CLAUDE_STATE_DIR")


def _check(gate, cond, evidence, diagnostic):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-34s %s" % (gate, evidence))
    else:
        _FAIL += 1
        print("  FAIL %-34s %s" % (gate, diagnostic))


def _judgements(path):
    try:
        return int(json.loads(Path(path).read_text(encoding="utf-8")).get("judgements", 0))
    except (OSError, ValueError):
        return 0


def _record(hb):
    return hb.record("LIGHT", by_floor=True, abstained=False, informative=False,
                     reason="path-gate")


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="hbpath_")
    saved = {k: os.environ.get(k) for k in _HOME_KEYS}
    try:
        print("V-HBPATH gates (heartbeat path resolved at call time)")
        decoy = os.path.join(tmp, "decoy")
        os.environ["CLAUDE_STATE_DIR"] = decoy
        from modules.gsd_x import heartbeat as hb          # bound (if at all) to the decoy

        path_fn = getattr(hb, "heartbeat_path", None)

        # 1 -- CLAUDE_STATE_DIR swapped after import is honoured, each swap on its own
        a, b = os.path.join(tmp, "a"), os.path.join(tmp, "b")
        os.environ["CLAUDE_STATE_DIR"] = a
        ok_a = _record(hb)
        os.environ["CLAUDE_STATE_DIR"] = b
        ok_b = _record(hb)
        ja = _judgements(os.path.join(a, "gsd-x-heartbeat.json"))
        jb = _judgements(os.path.join(b, "gsd-x-heartbeat.json"))
        _check("V-HBPATH-CALL-TIME-ENV",
               ok_a and ok_b and ja == 1 and jb == 1
               and _judgements(os.path.join(decoy, "gsd-x-heartbeat.json")) == 0,
               "record() after an env swap writes to the NEW state dir (a=1, b=1, "
               "decoy untouched)",
               "ok=%s/%s a=%d b=%d decoy=%d (the import-time binding wrote elsewhere)"
               % (ok_a, ok_b, ja, jb,
                  _judgements(os.path.join(decoy, "gsd-x-heartbeat.json"))))

        # 2 -- HOME/USERPROFILE swapped after import is honoured (no CLAUDE_STATE_DIR)
        os.environ.pop("CLAUDE_STATE_DIR", None)
        h1, h2 = os.path.join(tmp, "h1"), os.path.join(tmp, "h2")
        for h in (h1, h2):
            os.makedirs(h)
        os.environ.update(HOME=h1, USERPROFILE=h1)
        ok_1 = _record(hb)
        os.environ.update(HOME=h2, USERPROFILE=h2)
        ok_2 = _record(hb)
        j1 = _judgements(os.path.join(h1, ".claude", "state", "gsd-x-heartbeat.json"))
        j2 = _judgements(os.path.join(h2, ".claude", "state", "gsd-x-heartbeat.json"))
        _check("V-HBPATH-CALL-TIME-HOME", ok_1 and ok_2 and j1 == 1 and j2 == 1,
               "record() after a HOME swap writes under the NEW <home>/.claude/state "
               "(h1=1, h2=1)",
               "ok=%s/%s h1=%d h2=%d (the import-time binding ignored the swap)"
               % (ok_1, ok_2, j1, j2))

        # 3 -- the live layout is exactly the old import-time formula
        os.environ.update(HOME=h1, USERPROFILE=h1)
        want_home = Path.home() / ".claude" / "state" / "gsd-x-heartbeat.json"
        got_home = path_fn() if callable(path_fn) else None
        os.environ["CLAUDE_STATE_DIR"] = a
        want_env = Path(a) / "gsd-x-heartbeat.json"
        got_env = path_fn() if callable(path_fn) else None
        _check("V-HBPATH-LIVE-LAYOUT-IDENTICAL",
               got_home == want_home and got_env == want_env,
               "no env -> <home>/.claude/state/gsd-x-heartbeat.json; CLAUDE_STATE_DIR "
               "wins when set: the same two answers the import-time formula gave",
               "no-env got=%s want=%s; env got=%s want=%s"
               % (got_home, want_home, got_env, want_env))

        # 3b -- and for the REAL home (read only; nothing is written)
        for k in _HOME_KEYS:
            if saved[k] is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = saved[k]
        real_expected = (Path(saved["CLAUDE_STATE_DIR"]) if saved["CLAUDE_STATE_DIR"]
                         else Path.home() / ".claude" / "state") / "gsd-x-heartbeat.json"
        _check("V-HBPATH-REAL-HOME-IDENTICAL",
               callable(path_fn) and path_fn() == real_expected,
               "under the process's own environment the path is %s (unchanged "
               "behaviour for the live hook; nothing written)" % real_expected,
               "heartbeat_path=%s want=%s" % (path_fn() if callable(path_fn) else None,
                                              real_expected))

        # 4 -- fail-open: an unwritable state dir
        blocker = os.path.join(tmp, "blocker")
        Path(blocker).write_text("a file, not a directory", encoding="utf-8")
        os.environ["CLAUDE_STATE_DIR"] = os.path.join(blocker, "state")
        try:
            wrote = _record(hb)
            state = hb.read()
            failed_open = wrote is False and state.get("judgements") == 0
        except Exception as exc:  # noqa: BLE001 -- the gate names it
            failed_open, state = False, "%s: %s" % (type(exc).__name__, exc)
        _check("V-HBPATH-FAIL-OPEN-UNWRITABLE", failed_open,
               "an unwritable state dir -> record() False, read() empty, nothing raised",
               "wrote=%s state=%s" % (None, state))

        # 5 -- fail-open: a process with NO resolvable home (raised at import before)
        env = {k: v for k, v in os.environ.items() if k not in _HOME_KEYS}
        env["PYTHONPATH"] = _PP_ROOT
        code = ("import modules.gsd_x.heartbeat as h;"
                "print(h.record('LIGHT', by_floor=True, abstained=False, informative=False));"
                "print(h.read().get('judgements'))")
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                              env=env, cwd=tmp, timeout=60)
        _check("V-HBPATH-FAIL-OPEN-NO-HOME",
               proc.returncode == 0 and proc.stdout.split() == ["False", "0"],
               "importing and recording with no HOME/USERPROFILE/CLAUDE_STATE_DIR exits 0 "
               "(record False, read empty)",
               "rc=%s out=%r err=%r" % (proc.returncode, proc.stdout, proc.stderr[-200:]))

        # 6 -- the old module attribute still resolves
        os.environ["CLAUDE_STATE_DIR"] = a
        attr = getattr(hb, "HEARTBEAT", None)
        _check("V-HBPATH-ATTR-COMPAT",
               callable(path_fn) and attr == path_fn() == Path(a) / "gsd-x-heartbeat.json",
               "heartbeat.HEARTBEAT still resolves, to the call-time path",
               "HEARTBEAT=%r heartbeat_path=%r" % (attr, path_fn() if callable(path_fn) else None))

        print()
        print("GSD_X_HEARTBEAT_PATH_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, EXPECTED, EXPECTED))
        return 0 if _FAIL == 0 and _PASS == EXPECTED else 1
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
