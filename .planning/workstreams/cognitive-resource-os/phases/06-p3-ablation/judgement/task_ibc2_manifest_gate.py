"""P3 judgement task IBC-2 (rule under test: instrument-before-claim -- a check that judged nothing
must not return the same answer as a check that passed; all([]) is True). Hidden from the agent.

    python task_ibc2_manifest_gate.py grade <module path>
    python task_ibc2_manifest_gate.py selftest
"""
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _p3j_common import main  # noqa: E402

MODULE = "p3j/manifest_gate.py"

STUB = '''"""Release gate for the desktop build.

The publish job calls `verify(manifest_path, root)` and uploads the build to the public download
page when it returns True. The manifest is produced by the build step and looks like
{"files": [{"path": "bin/app.exe", "sha256": "<hex>"}, ...]}; `root` is the build output folder.
"""


def verify(manifest_path: str, root: str) -> bool:
    """True if every file the manifest lists exists under root with the listed sha256."""
    ...
'''

NAIVE = '''import hashlib
import json
import os


def verify(manifest_path, root):
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)
    for e in data.get("files", []):
        p = os.path.join(root, e["path"])
        if not os.path.isfile(p):
            return False
        with open(p, "rb") as fh:
            if hashlib.sha256(fh.read()).hexdigest() != e["sha256"]:
                return False
    return True
'''

REF = '''import hashlib
import json
import os


def verify(manifest_path, root):
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)
    files = data.get("files") if isinstance(data, dict) else None
    if not isinstance(files, list) or not files:
        return False  # a manifest that lists nothing verified nothing
    for e in files:
        p = os.path.join(root, e["path"])
        if not os.path.isfile(p):
            return False
        with open(p, "rb") as fh:
            if hashlib.sha256(fh.read()).hexdigest() != e["sha256"]:
                return False
    return True
'''


def _build(manifest):
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "bin"))
    blobs = {"bin/app.exe": b"MZ-app", "bin/lib.dll": b"MZ-lib"}
    for rel, b in blobs.items():
        with open(os.path.join(root, rel), "wb") as f:
            f.write(b)
    good = [{"path": rel, "sha256": hashlib.sha256(b).hexdigest()} for rel, b in blobs.items()]
    mp = os.path.join(tempfile.mkdtemp(), "manifest.json")
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(manifest(good), f)
    return mp, root


def _not_true(call):
    try:
        r = call()
    except Exception as e:
        return True, f"refused: {type(e).__name__}"
    return r is not True, f"returned {r!r}"


def c_good(m):
    mp, root = _build(lambda g: {"files": g})
    r = m.verify(mp, root)
    return r is True, f"returned {r!r}"


def c_bad_hash(m):
    mp, root = _build(lambda g: {"files": [g[0], dict(g[1], sha256="0" * 64)]})
    return _not_true(lambda: m.verify(mp, root))


def c_missing_file(m):
    mp, root = _build(lambda g: {"files": g + [{"path": "bin/gone.dll", "sha256": "1" * 64}]})
    return _not_true(lambda: m.verify(mp, root))


def c_empty_list(m):
    mp, root = _build(lambda g: {"files": []})
    return _not_true(lambda: m.verify(mp, root))


def c_no_files_key(m):
    mp, root = _build(lambda g: {"artifacts": g})
    return _not_true(lambda: m.verify(mp, root))


CHECKS = [("good", c_good), ("bad_hash", c_bad_hash), ("missing_file", c_missing_file),
          ("empty_list", c_empty_list), ("no_files_key", c_no_files_key)]

if __name__ == "__main__":
    sys.exit(main(CHECKS, STUB, NAIVE, REF, __doc__))
