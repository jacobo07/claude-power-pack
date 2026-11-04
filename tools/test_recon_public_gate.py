#!/usr/bin/env python3
"""V-RFG-*: tools/recon_public_gate.py driven at BOTH poles. Each derived-content class has a planted violation that must be caught and a
clean look-alike that must pass; `--drills` disables one class at a time and the matching gate must go red."""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import recon_public_gate as G
from modules.reconstruction_factory.gatekit import Kit, patched

kit = Kit("test_recon_public_gate")


def run_gate(args):
    """In-process, so a drill that patches the gate module reaches the code under test."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = G.main(args)
    return rc, buf.getvalue()


class _R:
    def __init__(self, rc, out):
        self.returncode, self.stdout = rc, out
W = "modules/reconstruction_factory/"


class Ctx:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="rfg-")
        self.n = 0

    def close(self):
        self.tmp.cleanup()

    def repo(self, files, msg="work"):
        self.n += 1
        d = os.path.join(self.tmp.name, "r%d" % self.n)
        os.makedirs(d)
        sh = lambda *a: subprocess.run(["git", "-C", d] + list(a), capture_output=True, check=True)
        sh("init", "-q")
        sh("config", "user.email", "t@t")
        sh("config", "user.name", "t")
        sh("commit", "-q", "--allow-empty", "-m", "base")
        base = subprocess.run(["git", "-C", d, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        for p, data in files.items():
            fp = os.path.join(d, p)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "wb") as fh:
                fh.write(data if isinstance(data, bytes) else data.encode())
        sh("add", "-A")
        sh("commit", "-q", "-m", msg)
        return d, base

    def gate(self, files, msg="work", extra=()):
        d, base = self.repo(files, msg)
        rc, out = run_gate(["--root", d, "--json"] + list(extra))
        return rc, json.loads(out), d, base


def caught(ctx, files, cls, **kw):
    rc, out, _, _ = ctx.gate(files, **kw)
    assert rc == 1 and out["by_class"].get(cls), "class %s not caught: rc=%s %s" % (cls, rc, out["by_class"])


def clean(ctx, files, **kw):
    rc, out, _, _ = ctx.gate(files, **kw)
    assert rc == 0 and not out["violations"], "false positive: %s" % out["violations"]


def off(name):
    return lambda: patched(G, name, re.compile("(?!x)x"))


ADDR_TXT = "int x = 1; /* " + "fn_" + "80" + "3a4b5c" + " */\n"
HEXADDR = "p = " + "0x" + "80" + "123456" + ";\n"
DIS = "".join("   %x:\t%s \t%s\n" % (4 * i, "38 60 00 00", op) for i, op in enumerate(["li      r3,0", "lwz     r3,4(r3)", "stw     r3,8(r1)", "blr"]))
TITLE_WORD = "".join(chr(c) for c in (116, 101, 110, 110, 105, 115))      # assembled so this file carries no denylisted token


@kit.gate("V-RFG-ADDR", drill=off("ADDR_RE"))
def _(ctx):
    caught(ctx, {W + "a.py": ADDR_TXT}, "ADDR")
    caught(ctx, {W + "b.py": HEXADDR}, "ADDR")
    clean(ctx, {W + "ok.py": "base = 0x1000\nfn_alpha = 3\nlabel_80 = 1\n"})


def _blob_drill():
    return patched(G, "scan_blob", lambda p, d: [])


@kit.gate("V-RFG-BLOB", drill=_blob_drill)
def _(ctx):
    caught(ctx, {"fixtures/synthetic/a.dol": b"hello"}, "BLOB")
    caught(ctx, {"fixtures/synthetic/b.txt": b"\x7fELF\x01\x02\x01\x00" + b"\0" * 20}, "BLOB")
    caught(ctx, {"fixtures/synthetic/c.dat": b"\x1f\x8b\x08\x00opaque-gzip-body"}, "BLOB")
    caught(ctx, {"fixtures/synthetic/d.txt": b"\xff\xfe\xfa binary \xc3\x28"}, "BLOB")
    clean(ctx, {"fixtures/synthetic/e.c": "int f(void) { return 1; }\n", "modules/reconstruction_factory/x.py": "print(1)\n"})


@kit.gate("V-RFG-PATH", drill=lambda: patched(G, "PATH_BAD", re.compile("(?!x)x")))
def _(ctx):
    caught(ctx, {"fixtures/synthetic/evidence/x.txt": "notes\n"}, "PATH")
    caught(ctx, {"fixtures/synthetic/.local/y.txt": "notes\n"}, "PATH")
    caught(ctx, {"fixtures/synthetic/recon_fabric/fixtures/z.txt": "n\n"}, "PATH")
    clean(ctx, {"fixtures/synthetic/evidences_of_style.txt": "n\n", "fixtures/synthetic/src/local.c": "int a;\n"})


@contextlib.contextmanager
def _no_disasm():
    with patched(G, "DISASM_RE", re.compile("(?!x)x")), patched(G, "OBJDUMP_LINE", re.compile("(?!x)x")):
        yield


@kit.gate("V-RFG-DISASM", drill=_no_disasm)
def _(ctx):
    caught(ctx, {W + "dump.txt": DIS}, "DISASM")
    clean(ctx, {"fixtures/synthetic/dump.txt": DIS})                 # disassembly OF the synthetic corpus is allowed
    clean(ctx, {W + "doc.md": "The prologue uses `mflr` and `stw` to save the link register.\n"})


@kit.gate("V-RFG-TITLE", drill=lambda: patched(G, "BUILTIN_DENY", frozenset()))
def _(ctx):
    caught(ctx, {W + "t.md": "A port of the %s game.\n" % TITLE_WORD}, "TITLE")
    caught(ctx, {W + "t_%s.md" % TITLE_WORD: "x\n"}, "TITLE")
    clean(ctx, {W + "t.md": "A port of a generic game.\n"})


@kit.gate("V-RFG-DENYFILE", drill=lambda: patched(G, "deny_set", lambda f=None: set(G.BUILTIN_DENY)))
def _(ctx):
    with tempfile.NamedTemporaryFile("w", suffix=".deny", delete=False) as fh:
        fh.write("# extra\n" + G.h("zorbl") + "\n")
        path = fh.name
    try:
        caught(ctx, {W + "z.md": "the zorbl binary\n"}, "TITLE", extra=["--deny-file", path])
        clean(ctx, {W + "z.md": "the zorbl binary\n"})                  # without the file the word is not denied
    finally:
        os.unlink(path)


@kit.gate("V-RFG-RANGE", drill=lambda: patched(G, "scan_range", lambda *a: []))
def _(ctx):
    d, base = ctx.repo({W + "r.py": ADDR_TXT, "outside/readme.md": "x\n"})
    r = _R(*run_gate(["--root", d, "--range", base + "..HEAD", "--json"]))
    out = json.loads(r.stdout)
    assert r.returncode == 1 and out["by_class"].get("ADDR"), out
    # the commit message is part of the range
    d2, base2 = ctx.repo({W + "ok.py": "x = 1\n"}, msg="port of %s" % TITLE_WORD)
    r = _R(*run_gate(["--root", d2, "--range", base2 + "..HEAD", "--json"]))
    assert r.returncode == 1 and json.loads(r.stdout)["by_class"].get("TITLE"), r.stdout
    # a clean range is clean
    d3, base3 = ctx.repo({W + "ok.py": "x = 1\n"}, msg="fine")
    r = _R(*run_gate(["--root", d3, "--range", base3 + "..HEAD"]))
    assert r.returncode == 0, r.stdout


@kit.gate("V-RFG-SCOPE", drill=lambda: patched(G, "SCOPE", ("nothing-matches/",)))
def _(ctx):
    rc, out, _, _ = ctx.gate({"elsewhere/a.py": ADDR_TXT})                     # out of scope: not scanned by default
    assert rc == 0, out
    rc, out, _, _ = ctx.gate({"elsewhere/a.py": ADDR_TXT}, extra=["--all"])
    assert rc == 1 and out["by_class"].get("ADDR"), out
    rc, out, _, _ = ctx.gate({W + "a.py": ADDR_TXT})                           # in scope: caught
    assert rc == 1, out


@kit.gate("V-RFG-NOTEXT-LEAK", drill=lambda: patched(G, "scan_file", lambda p, d, deny: [("ADDR", "x" + d.decode("utf-8", "replace"), 1)]))
def _(ctx):
    rc, out, _, _ = ctx.gate({W + "a.py": ADDR_TXT})
    blob = json.dumps(out)
    assert "3a4b5c" not in blob and rc == 1, "the report must not echo the offending text"


@kit.gate("V-RFG-USAGE-UNMEASURED", drill=lambda: patched(G, "git", lambda *a, **k: "")) 
def _(ctx):
    with tempfile.TemporaryDirectory() as d:                                   # not a git repo: UNMEASURED (2), never clean
        r = _R(*run_gate(["--root", d]))
        assert r.returncode == 2 and "UNMEASURED" in r.stdout, (r.returncode, r.stdout)


@kit.gate("V-RFG-REPO-CLEAN", drill=lambda: patched(G, "ADDR_RE", re.compile(r"."))) 
def _(ctx):
    r = _R(*run_gate(["--root", ROOT]))
    assert r.returncode == 0, r.stdout[-600:]


if __name__ == "__main__":
    sys.exit(kit.main(Ctx))
