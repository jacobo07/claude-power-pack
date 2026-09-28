"""Record every write a Python process makes under the REAL ~/.claude.

Loaded only when a runner prepends this directory to PYTHONPATH and sets
CPP_STATE_AUDIT_LOG. Python children inherit both, so a test that shells out to
a CLI is observed too. Node children are NOT observed (stated limit).

The real root comes from CPP_STATE_AUDIT_ROOT, fixed by the runner before the
test starts, so a test that repoints USERPROFILE cannot move the target it is
being judged against.
"""
import os
import sys
import threading

_LOG = os.environ.get("CPP_STATE_AUDIT_LOG")
_ROOT = os.environ.get("CPP_STATE_AUDIT_ROOT")

if _LOG and _ROOT:
    _root = os.path.normcase(os.path.abspath(_ROOT)).rstrip("\\/") + os.sep
    _busy = threading.local()

    def _under(p):
        try:
            p = os.fspath(p)
            if isinstance(p, bytes):
                p = p.decode("utf-8", "replace")
            return os.path.normcase(os.path.abspath(p)).startswith(_root)
        except Exception:  # unrepresentable path: not ours to judge
            return False

    def _record(kind, path):
        if getattr(_busy, "on", False):
            return
        _busy.on = True
        try:
            fd = os.open(_LOG, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
            try:
                os.write(fd, f"{os.getpid()}\t{kind}\t{os.fspath(path)}\n".encode("utf-8", "replace"))
            finally:
                os.close(fd)
        finally:
            _busy.on = False

    def _writes(mode, flags):
        if isinstance(mode, str):
            return any(c in mode for c in "wax+")
        if isinstance(flags, int):
            return bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC))
        return False

    def _hook(event, args):
        if getattr(_busy, "on", False):
            return
        try:
            if event == "open":
                path, mode, flags = (list(args) + [None, None, None])[:3]
                if isinstance(path, int) or path is None:
                    return
                if _writes(mode, flags) and _under(path):
                    _record("open", path)
            elif event in ("os.rename", "os.replace"):
                if _under(args[1]):
                    _record(event, args[1])
            elif event in ("os.remove", "os.rmdir", "os.mkdir", "shutil.rmtree"):
                if _under(args[0]):
                    _record(event, args[0])
        except Exception:  # the auditor must never change the subject's behaviour
            return

    sys.addaudithook(_hook)
