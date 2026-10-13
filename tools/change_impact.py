"""Which V-gate suites does this change reach? (assimilation item 27, genesis-change-impact -> WRAP)

The narrow-oracle doctrine says run the suites whose domain is the change, not the whole estate.
That needs a dependency graph, and the one planned for this (the audit cache's `depends_on`) was
measured unusable on 2026-09-28: it resolves references by filename STEM, so a tool "depends on" a
Markdown file named tools.md inside a worktree copy of a vendored server, and only 8 of 25 test
suites with an obviously named subject list that subject. The vendored analyzer reads a missing
edge as "no dependency", so that graph would have answered "no suite affected" for most changes --
a false green, not a gap.

So the graph is built here from what the code does:
  * the AST of every Python file's imports, resolved the way this repo's sys.path resolves them
    (tools/ is on the path for tools and their tests; the root for `modules.*`);
  * every literal `tools/....py` / `modules/....py` path a file names -- many suites drive their
    subject as a subprocess and never import it.
Non-Python files are not in the graph, so a change to one is an explicit `unmatched-change` gap
from the vendored analyzer (through the one bridge), never a silent "nothing affected".

    python tools/change_impact.py --changed tools/rollover.py [--changed ...]
    python tools/change_impact.py --since HEAD~1
exit 0 coverage complete · 3 gaps listed (suites named are still the ones to run) · 2 bridge down
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.external_assimilation import node_bridge as nb  # noqa: E402

SCOPES = ("tools", "modules", "hooks", "lib")
_LITERAL = re.compile(r"(?<![\w/])((?:tools|modules|hooks|lib)/[\w./-]+\.py)\b")
FLOOR = 50  # a sweep that found fewer Python files has stopped seeing code


def _py_files(root: Path) -> list[str]:
    out = []
    for scope in SCOPES:
        base = root / scope
        if base.is_dir():
            out += [p.relative_to(root).as_posix() for p in base.rglob("*.py")
                    if "__pycache__" not in p.parts and "vendor" not in p.parts]
    return sorted(out)


def _resolve(name: str, known: set[str]) -> str | None:
    parts = name.split(".")
    for cand in (f"tools/{parts[0]}.py", "/".join(parts) + ".py", "/".join(parts) + "/__init__.py"):
        if cand in known:
            return cand
    return None


def edges_of(root: Path, rel: str, known: set[str]) -> set[str]:
    path = root / rel
    try:
        text = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(text)
    except (OSError, SyntaxError, ValueError):
        return set()
    pkg = Path(rel).parent.as_posix().replace("/", ".")
    deps: set[str] = set()
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = pkg.split(".")[: len(pkg.split(".")) - (node.level - 1)]
                mod = ".".join([*base, *(node.module.split(".") if node.module else [])])
            else:
                mod = node.module or ""
            names = [mod] + [f"{mod}.{a.name}" for a in node.names]
        for n in names:
            hit = _resolve(n, known)
            if hit and hit != rel:
                deps.add(hit)
    for lit in _LITERAL.findall(text):
        if lit in known and lit != rel:
            deps.add(lit)
    return deps


def manifest(root: Path) -> dict:
    files = _py_files(root)
    known = set(files)
    entries = [{"path": f, "kind": "test" if Path(f).name.startswith("test_") else "file",
                "dependsOn": sorted(edges_of(root, f, known))} for f in files]
    return {"schemaVersion": 1, "entries": entries}


def analyze(root: Path, changed: list[str]) -> dict:
    m = manifest(root)
    if len(m["entries"]) < FLOOR:
        return {"unjudged": True, "gaps": [{"type": "sweep-floor", "found": len(m["entries"]), "floor": FLOOR}]}
    r = nb.call("changeImpact", "analyzeChangeImpact", [m, [c.replace("\\", "/") for c in changed]], timeout=60)
    if not r.ok:
        return {"unjudged": True, "gaps": [{"type": "bridge", "error": f"{r.outcome}: {r.error}"}]}
    return r.value


def js_named_test(rel: str, root: Path) -> str | None:
    """hooks/<name>.js -> tools/test_<name>.py by name (hyphens as underscores) when that suite exists."""
    stem = Path(rel).stem.replace("-", "_")
    cand = f"tools/test_{stem}.py"
    return cand if (root / cand).is_file() else None


HUB_FRACTION = 0.25  # a path whose closure exceeds this share of all suites is a HUB, not local


def hub_report(closure: dict, root: Path | None = None, fraction: float = HUB_FRACTION) -> dict:
    """{"total": n, "hubs": {path: n_suites}, "leaf": [paths]} -- hub = per-path suites > fraction of all suites."""
    root = Path(root) if root else ROOT
    total = len(list((root / "tools").glob("test_*.py")))
    hubs = {p: len(v) for p, v in closure["per_path"].items() if total and len(v) > fraction * total}
    return {"total": total, "fraction": fraction, "hubs": hubs,
            "leaf": [p for p in closure["per_path"] if p not in hubs]}


def affected_closure(paths: list[str], root: Path | None = None, analyzer=None) -> dict:
    """Per-path proof closure. {"tests": [cmd], "per_path": {p: [cmd]}, "unmapped": [p], "unjudged": bool, "gaps": []}.
    A path is unmapped when no test is reached from it (a test file reaches itself). Unjudged = no answer, never green."""
    root = Path(root) if root else ROOT
    analyzer = analyzer or analyze
    per_path: dict[str, list[str]] = {}
    gaps: list = []
    for p in paths:
        p = p.replace("\\", "/")
        if p.endswith(".js") and p.startswith("hooks/"):
            named = js_named_test(p, root)
            if named:
                per_path[p] = [f"python {named}"]
                continue
        res = analyzer(root, [p])
        if res.get("unjudged"):
            return {"tests": [], "per_path": per_path, "unmapped": [], "unjudged": True, "gaps": res.get("gaps", [])}
        ts = sorted(set(res["affected"]["test"]))
        if Path(p).name.startswith("test_") and p.endswith(".py") and p not in ts:
            ts.append(p)
        per_path[p] = [f"python {t}" for t in ts]
        gaps += res.get("gaps", [])
    tests = sorted({c for v in per_path.values() for c in v})
    return {"tests": tests, "per_path": per_path, "unmapped": [p for p, v in per_path.items() if not v],
            "unjudged": False, "gaps": gaps}


def affected_tests(paths: list[str], root: Path | None = None) -> list[str]:
    """Declared-test commands (`python tools/test_x.py`) for the changed paths; [] when unjudged."""
    return affected_closure(paths, root)["tests"]


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--changed", action="append", default=[])
    ap.add_argument("--since")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    changed = list(a.changed)
    if a.since:
        g = r"C:\Program Files\Git\cmd\git.exe" if Path(r"C:\Program Files\Git\cmd\git.exe").exists() else "git"
        out = subprocess.run([g, "-C", str(root), "diff", "--name-only", a.since], capture_output=True, text=True)
        changed += [x for x in out.stdout.splitlines() if x.strip()]
    res = analyze(root, changed)
    if res.get("unjudged"):
        print(f"UNJUDGED {res['gaps']}")
        return 2
    tests = res["affected"]["test"]
    print(f"suites to run ({len(tests)}):")
    for t in tests:
        print(f"  python {t}")
    for gap in res["gaps"]:
        print(f"  gap  {gap['type']}: {gap.get('path', '')}")
    return 0 if res["coverageComplete"] else 3


if __name__ == "__main__":
    sys.exit(main())
