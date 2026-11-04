"""Toolchain adapters behind ONE interface. Public tests use GCC PowerPC (devkitPPC powerpc-eabi-gcc, or powerpc-linux-gnu-gcc).
An mwcc adapter exists but ships no compiler and is never required by a test. m2c and objdiff are external pinned dependencies
(see docs/reconstruction-factory/INSTALL.md): `external_status` reads their presence and version, nothing is vendored."""
import hashlib
import os
import re
import shutil
import subprocess
import tempfile


class AdapterUnavailable(RuntimeError):
    pass


def resolve(cands):
    for c in cands or []:
        p = c if os.path.isabs(c) and os.path.exists(c) else shutil.which(c)
        if p:
            return p
    return None


class Compiled:
    def __init__(self, rc, obj, log, obj_sha256=None, cached=False):
        self.rc, self.obj, self.log, self.obj_sha256, self.cached = rc, obj, log, obj_sha256, cached

    @property
    def ok(self):
        return self.rc == 0 and self.obj is not None


class Adapter:
    id = "abstract"

    def available(self, lang="c"):
        raise NotImplementedError

    def version(self):
        raise NotImplementedError

    def compile(self, text, lang, flags, include_dirs, workdir, name="unit"):
        raise NotImplementedError

    def disasm(self, obj, section):
        raise NotImplementedError


class GccPpcAdapter(Adapter):
    id = "gcc-ppc"

    def __init__(self, cc, cxx=None, objdump=None, cache_dir=None):
        self.cc, self.cxx, self.objdump = resolve(cc), resolve(cxx), resolve(objdump)
        self.cache_dir = cache_dir
        self._ver = None

    @classmethod
    def from_project(cls, project, cache_dir=None):
        tc = project.doc["toolchain"]
        return cls(tc["cc"], tc.get("cxx"), tc["objdump"], cache_dir)

    def available(self, lang="c"):
        return bool((self.cxx if lang == "cxx" else self.cc) and self.objdump)

    def version(self):
        if self._ver is None:
            if not self.cc:
                self._ver = "UNMEASURED"
            else:
                r = subprocess.run([self.cc, "--version"], capture_output=True, text=True)
                self._ver = (r.stdout.splitlines() or ["UNMEASURED"])[0].strip()
        return self._ver

    def key(self, text, lang, flags, include_dirs):
        inc = "".join(open(os.path.join(d, f), "rb").read().hex() for d in include_dirs for f in sorted(os.listdir(d)))
        return hashlib.sha256(("\0".join([self.version(), lang, " ".join(flags), text, hashlib.sha256(inc.encode()).hexdigest()])).encode()).hexdigest()

    def compile(self, text, lang, flags, include_dirs, workdir, name="unit"):
        exe = self.cxx if lang == "cxx" else self.cc
        if not exe:
            raise AdapterUnavailable("no %s compiler resolved" % ("C++" if lang == "cxx" else "C"))
        key = self.key(text, lang, flags, include_dirs)
        if self.cache_dir:
            cp = os.path.join(self.cache_dir, key + ".o")
            if os.path.exists(cp):
                return Compiled(0, cp, "", hashlib.sha256(open(cp, "rb").read()).hexdigest(), cached=True)
        src = os.path.join(workdir, name + (".cpp" if lang == "cxx" else ".c"))
        obj = os.path.join(workdir, name + ".o")
        with open(src, "w", newline="\n") as fh:
            fh.write(text)
        cmd = [exe, "-c", src, "-o", obj] + list(flags) + ["-I" + d for d in include_dirs]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(obj):
            return Compiled(r.returncode or 1, None, r.stderr[-2000:])
        sha = hashlib.sha256(open(obj, "rb").read()).hexdigest()
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
            shutil.copyfile(obj, os.path.join(self.cache_dir, key + ".o"))
        return Compiled(0, obj, r.stderr[-2000:], sha)

    def disasm(self, obj, section):
        r = subprocess.run([self.objdump, "-dr", "-j", section, obj], capture_output=True, text=True)
        return parse_objdump(r.stdout)


_INS = re.compile(r"^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} ){4})\s*(\S+)\s*(.*)$")
_REL = re.compile(r"^\s*([0-9a-f]+):\s+(R_PPC\S+)\s+(\S+)$")


def parse_objdump(text):
    """-> rows [{off, word, op, args, reloc}] in order; a relocation line attaches to the instruction containing its offset."""
    rows = []
    for ln in text.splitlines():
        m = _INS.match(ln)
        if m:
            rows.append({"off": int(m.group(1), 16), "word": m.group(2).replace(" ", ""), "op": m.group(3), "args": m.group(4).split("#")[0].strip(), "reloc": None})
            continue
        m = _REL.match(ln)
        if m and rows:
            rows[-1]["reloc"] = {"type": m.group(2), "sym": m.group(3)}
    return rows


class MwccAdapter(Adapter):
    """Metrowerks-style adapter: construction only. It never ships a compiler and no test requires it; `available` is False unless the
    manifest names an existing executable. Commands are built, not assumed: an unavailable adapter REFUSES, it never returns a pass."""
    id = "mwcc"

    def __init__(self, cc=None, runner=None, objdump=None):
        self.cc, self.runner, self.objdump = resolve(cc), resolve(runner) if runner else None, resolve(objdump)

    def available(self, lang="c"):
        return bool(self.cc)

    def version(self):
        return "UNMEASURED" if not self.cc else "mwcc:" + hashlib.sha256(open(self.cc, "rb").read()).hexdigest()[:12]

    def compile(self, text, lang, flags, include_dirs, workdir, name="unit"):
        if not self.cc:
            raise AdapterUnavailable("mwcc compiler not configured (never shipped with this repository)")
        src, obj = os.path.join(workdir, name + ".c"), os.path.join(workdir, name + ".o")
        open(src, "w", newline="\n").write(text)
        cmd = ([self.runner] if self.runner else []) + [self.cc] + list(flags) + ["-i " + d for d in include_dirs] + ["-c", src, "-o", obj]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(obj):
            return Compiled(r.returncode or 1, None, r.stderr[-2000:])
        return Compiled(0, obj, "", hashlib.sha256(open(obj, "rb").read()).hexdigest())

    def disasm(self, obj, section):
        if not self.objdump:
            raise AdapterUnavailable("no objdump configured")
        r = subprocess.run([self.objdump, "-dr", "-j", section, obj], capture_output=True, text=True)
        return parse_objdump(r.stdout)


def make_adapter(project, cache_dir=None):
    tc = project.doc["toolchain"]
    if tc["adapter"] == "gcc-ppc":
        return GccPpcAdapter.from_project(project, cache_dir)
    return MwccAdapter(tc["cc"], (tc.get("runner") or [None])[0], resolve(tc["objdump"]))


EXTERNAL = {"m2c": {"cmd": ["m2c", "--version"], "pin": None}, "objdiff": {"cmd": ["objdiff-cli", "--version"], "pin": None}}


def external_status(name, pin=None):
    """m2c / objdiff are external pinned dependencies. -> {present, version, pin, pin_ok}. Absent is reported, never faked."""
    spec = EXTERNAL[name]
    exe = shutil.which(spec["cmd"][0])
    if not exe:
        return {"name": name, "present": False, "version": None, "pin": pin, "pin_ok": None}
    r = subprocess.run(spec["cmd"], capture_output=True, text=True)
    ver = (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else None
    return {"name": name, "present": True, "version": ver, "pin": pin, "pin_ok": (pin in ver) if (pin and ver) else None}
