#!/usr/bin/env python3
"""recon_public_gate: refuse DERIVED CONTENT in the public Reconstruction Factory.

Spec: vault/specs/reconstruction-factory-general.md (section Shape, tools/recon_public_gate.py). Exit 0 = clean, 1 = violations, 2 = usage/UNMEASURED.

Classes (each one is driven at both poles in tools/test_recon_public_gate.py):
  ADDR     a function label or address of a commercial image: fn_80xxxxxx / lbl_ / sub_ / FUN_ / func_ followed by an 80xxxxxx address, or 0x80xxxxxx
  BLOB     a binary image or opaque archive: .dol .elf .iso .wbfs .rvz .gcm .rel .gz .zst .xz .bz2 .7z .zip .bin .o .a, or content that is not text
           (ELF/gzip/zstd/xz/bz2/zip magic, NUL bytes, invalid UTF-8)
  PATH     a private-evidence path component: evidence/ .local/ , or a recon_fabric fixtures path
  DISASM   PowerPC disassembly that was not produced from fixtures/synthetic (4+ instruction lines in a file outside that directory)
  TITLE    a private title / binary name / sha pin. The denylist is held as SHA-256 hashes of lowercase tokens (words and adjacent-word joins,
           and 32+ hex runs), so this file itself contains no such name. Extend it WITHOUT plaintext with --deny-file (one sha256 per line) or
           the RECON_GATE_DENY environment variable (comma-separated sha256). The built-in list is a floor, not the full private list.
Scope: default = the paths this work owns (SCOPE below); --all scans every tracked/untracked-not-ignored file; --range A..B scans every file
changed in that range as stored at B, plus the commit messages. A violation anywhere in scope is a refusal: there is no allowlist of files.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

SCOPE = ("modules/reconstruction_factory", "fixtures/synthetic", "tools/recon_public_gate.py", "tools/test_recon_public_gate.py",
         "tools/test_reconstruction_factory.py", "vault/programs/reconstruction-factory", "vault/specs/reconstruction-factory-general.md",
         "docs/reconstruction-factory", "recon.toml")

BUILTIN_DENY = frozenset((
    "f1996a7cda48bca0dc87f700b183266eed3a770330d924fb1507b3036e37b0ff",
    "1bce16970eaf867c874b6f9ebe22ca8b214794b98d7884f549e5eecec5e9cfa7",
    "480641793a81d461767d41bd230981fe072a395b60e8e354dd0c326846c67316",
    "b2d6c4e5d741e2cfe4881e778113ca799533c7ae01181882b7a1203fe4c44be8"))

BLOB_EXT = (".dol", ".elf", ".iso", ".wbfs", ".rvz", ".gcm", ".rel", ".gz", ".tgz", ".zst", ".xz", ".bz2", ".7z", ".zip", ".bin", ".o", ".a", ".so", ".nfs")
BLOB_MAGIC = (b"\x7fELF", b"\x1f\x8b", b"\x28\xb5\x2f\xfd", b"\xfd7zXZ\x00", b"BZh", b"PK\x03\x04", b"WBFS", b"RVZ\x01")
PATH_BAD = re.compile(r"(^|/)(evidence|\.local)(/|$)|(^|/)recon_fabric/fixtures(/|$)")
ADDR_RE = re.compile(r"\b(?:fn|lbl|sub|FUN|func|unk|dat)_80[0-9a-fA-F]{6}\b|\b0x80[0-9a-fA-F]{6}\b")
PPC_OPS = ("lwz", "stw", "lis", "addi", "addis", "mflr", "mtlr", "blr", "stwu", "lfs", "stfs", "lbz", "stb", "lhz", "sth", "cmpwi", "cmplwi", "cmpw", "bne", "beq",
           "bl", "mr", "li", "ori", "rlwinm", "srawi", "slwi", "extsh", "extsb", "mtctr", "bctr", "bctrl", "fadds", "fmuls", "lfd", "stfd", "stmw", "lmw")
DISASM_RE = re.compile(r"^\s*(?:[0-9a-f]+:\s+(?:[0-9a-f]{2} ){4}\s*)?(%s)\s+(?:r\d+|f\d+|-?\d+|0x[0-9a-f]+)[,\s(]" % "|".join(PPC_OPS), re.M)
OBJDUMP_LINE = re.compile(r"^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2} ){4}\s*\S+", re.M)
WORD = re.compile(r"[A-Za-z0-9]+")
HEX_RUN = re.compile(r"\b[0-9a-fA-F]{32,128}\b")
SYNTH = "fixtures/synthetic/"


def deny_set(deny_file=None):
    s = set(BUILTIN_DENY)
    for part in (os.environ.get("RECON_GATE_DENY", "").split(",") if os.environ.get("RECON_GATE_DENY") else []):
        if part.strip():
            s.add(part.strip().lower())
    if deny_file:
        with open(deny_file, encoding="utf-8") as fh:
            s.update(x.strip().lower() for x in fh if x.strip() and not x.startswith("#"))
    return s


def h(tok):
    return hashlib.sha256(tok.encode()).hexdigest()


def title_hits(text, deny):
    """Hashed-token scan: words, adjacent-word joins and long hex runs. Returns the count only (never the matched text)."""
    n = 0
    words = [w.lower() for w in WORD.findall(text)]
    for i, w in enumerate(words):
        if h(w) in deny:
            n += 1
        if i + 1 < len(words) and h(w + words[i + 1]) in deny:
            n += 1
    for m in HEX_RUN.findall(text):
        if h(m.lower()) in deny:
            n += 1
    return n


def scan_blob(path, data):
    out = []
    if path.lower().endswith(BLOB_EXT):
        out.append(("BLOB", "extension"))
    if data[:8].startswith(BLOB_MAGIC) or any(data.startswith(m) for m in BLOB_MAGIC):
        out.append(("BLOB", "magic"))
    elif b"\x00" in data[:4096]:
        out.append(("BLOB", "nul-bytes"))
    else:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            out.append(("BLOB", "not-utf8"))
    return out


def scan_file(path, data, deny):
    """-> list of (class, detail, line|None). `path` is repo-relative with '/' separators. Never returns the offending text."""
    v = []
    if PATH_BAD.search(path):
        v.append(("PATH", "private-evidence path", None))
    if title_hits(path.replace("/", " ").replace("_", " ").replace("-", " ").replace(".", " "), deny):
        v.append(("TITLE", "denylisted token in path", None))
    for cls, why in scan_blob(path, data):
        v.append((cls, why, None))
    if any(c == "BLOB" for c, _, _ in v) and (data[:4] in BLOB_MAGIC or b"\x00" in data[:4096]):
        return v                                           # binary: nothing meaningful to text-scan
    try:
        text = data.decode("utf-8", "replace")
    except Exception:
        return v
    for i, ln in enumerate(text.splitlines(), 1):
        if ADDR_RE.search(ln):
            v.append(("ADDR", "address/label of an image", i))
    if not path.startswith(SYNTH):
        nlines = len(DISASM_RE.findall(text)) + len(OBJDUMP_LINE.findall(text))
        if nlines >= 4:
            v.append(("DISASM", "%d disassembly-shaped lines outside fixtures/synthetic" % nlines, None))
    if title_hits(text, deny):
        v.append(("TITLE", "denylisted token in content", None))
    return v


def git(root, *args, text=True):
    r = subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=text)
    if r.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args[:2]), (r.stderr if text else r.stderr.decode())[:200]))
    return r.stdout


def in_scope(rel, scope):
    return any(rel == s or rel.startswith(s.rstrip("/") + "/") for s in scope)


def list_tree(root, scope, everything):
    names = git(root, "ls-files", "-co", "--exclude-standard", "-z").split("\0")
    return sorted(n for n in names if n and (everything or in_scope(n, scope)) and os.path.isfile(os.path.join(root, n)))


def scan_tree(root, scope, everything, deny):
    res = []
    for rel in list_tree(root, scope, everything):
        with open(os.path.join(root, rel), "rb") as fh:
            data = fh.read()
        for cls, why, ln in scan_file(rel, data, deny):
            res.append({"file": rel, "class": cls, "detail": why, "line": ln})
    return res


def scan_range(root, rng, deny):
    res = []
    end = rng.split("..")[-1] or "HEAD"
    changed = [x for x in git(root, "diff", "--name-only", "--diff-filter=AM", "-z", rng).split("\0") if x]
    deleted_binary_check = [x for x in git(root, "diff", "--name-only", "-z", rng).split("\0") if x]
    for rel in sorted(set(changed)):
        data = subprocess.run(["git", "-C", root, "show", "%s:%s" % (end, rel)], capture_output=True).stdout
        for cls, why, ln in scan_file(rel, data, deny):
            res.append({"file": rel, "class": cls, "detail": why, "line": ln})
    for rel in sorted(set(deleted_binary_check) - set(changed)):
        pass                                                # a deletion introduces no content
    for sha in git(root, "rev-list", rng).split():
        msg = git(root, "show", "-s", "--format=%B", sha)
        for cls, why, ln in scan_file("COMMIT:" + sha[:10], msg.encode(), deny):
            if cls in ("ADDR", "TITLE"):
                res.append({"file": "COMMIT:" + sha[:10], "class": cls, "detail": why, "line": ln})
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--all", action="store_true", help="scan every tracked/untracked-not-ignored file, not just this work's scope")
    ap.add_argument("--range", help="scan files changed in a commit range (A..B) and its commit messages")
    ap.add_argument("--deny-file", help="extra sha256 denylist (one hash per line)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        deny = deny_set(a.deny_file)
        res = scan_range(a.root, a.range, deny) if a.range else scan_tree(a.root, SCOPE, a.all, deny)
    except (RuntimeError, OSError) as e:
        print("RECON_PUBLIC_GATE UNMEASURED: %s" % e)
        return 2
    by = {}
    for r in res:
        by[r["class"]] = by.get(r["class"], 0) + 1
    if a.json:
        print(json.dumps({"clean": not res, "violations": res, "by_class": by}, indent=1, sort_keys=True))
    else:
        for r in res:
            print("%s %s%s %s" % (r["class"], r["file"], (":%d" % r["line"]) if r["line"] else "", r["detail"]))
        print("RECON_PUBLIC_GATE %s (%s)" % ("CLEAN" if not res else "VIOLATIONS", json.dumps(by, sort_keys=True)))
    return 0 if not res else 1


if __name__ == "__main__":
    sys.exit(main())
