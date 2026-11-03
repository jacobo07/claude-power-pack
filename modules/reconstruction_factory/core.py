"""Factory: builds target objects from the reference sources with the manifest recipe, compiles candidate source in a CLEAN directory per
compile, and judges it. Every path, tool, flag and function list comes from the Project manifest (recon.toml)."""
import os
import tempfile

from . import judge as J
from .manifest import Project
from .toolchain import make_adapter


class FactoryError(RuntimeError):
    pass


class Factory:
    def __init__(self, project, adapter=None, cache_dir=None, workdir=None):
        self.project = project if isinstance(project, Project) else Project(project)
        self.adapter = adapter or make_adapter(self.project, cache_dir)
        self._own = None
        if workdir is None:
            self._own = tempfile.TemporaryDirectory(prefix="rf-")
            workdir = self._own.name
        self.workdir = workdir
        self._targets = {}
        self._n = 0

    def close(self):
        if self._own:
            self._own.cleanup()
            self._own = None

    def _clean_dir(self, tag):
        self._n += 1
        d = os.path.join(self.workdir, "%s-%d" % (tag, self._n))
        os.makedirs(d)
        return d

    def read_source(self, fn, kind="ref"):
        with open(self.project.source_path(fn, kind), "r") as fh:
            return fh.read()

    def flags_for(self, fn, variant=None):
        f = self.project.functions[fn]
        return self.project.flags(f["recipe"], f["lang"], variant)

    def compile_text(self, fn, text, variant=None, flags=None):
        f = self.project.functions[fn]
        d = self._clean_dir("c")
        return self.adapter.compile(text, f["lang"], flags if flags is not None else self.flags_for(fn, variant), self.project.include_dirs, d, name=fn)

    def target(self, fn):
        """Target object of a function: prebuilt target_dir/<fn>.o if the manifest names one, else the ref source compiled with the pinned recipe."""
        if fn in self._targets:
            return self._targets[fn]
        td = self.project.doc["corpus"].get("target_dir")
        if td and os.path.exists(os.path.join(self.project.p(td), fn + ".o")):
            p = os.path.join(self.project.p(td), fn + ".o")
        else:
            c = self.compile_text(fn, self.read_source(fn, "ref"))
            if not c.ok:
                raise FactoryError("target for %s does not compile: %s" % (fn, c.log))
            p = c.obj
        self._targets[fn] = p
        return p

    def judge_text(self, fn, text, variant=None, flags=None):
        """-> (judge result, Compiled). A compile failure is compiles=False/exact=None, never a mismatch."""
        c = self.compile_text(fn, text, variant, flags)
        if not c.ok:
            return {"compiles": False, "exact": None, "pct": None, "symbols": [], "reasons": ["COMPILE_FAILED"], "log": c.log}, c
        return J.judge(self.target(fn), c.obj, self.project.functions[fn]["symbols"]), c

    def judge_obj(self, fn, obj):
        return J.judge(self.target(fn), obj, self.project.functions[fn]["symbols"])
