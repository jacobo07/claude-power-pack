"""Dispatch-key liveness: a registered handler is not an invoked handler.

`reachability.py` answers "does anything reach this module?" and states the doctrine this
file extends (lines 29-32): the safe direction is over-reporting, and anything unproven is
ORPHAN or UNKNOWN, never REACHABLE. A dispatch table breaks that guarantee without
breaking any rule the scanner can see. The handler is registered, the module is imported,
the import edge is real -- and the key is never supplied, so the code never runs.

Measured 2026-08-25. `cascade_prevention/engine.py` registers seven surface detectors.
`liveness_report.md:209` classes `cascade_prevention/predictive` LIVE, "reached from
modules/cascade_prevention/engine", which is true. The only automatic caller in the estate
is `hooks/cascade_check_bash.js:28`, `detect('bash', ...)`. A sweep for `detect('<surface>')`
found `session` and `context` only inside tests, `deploy` in a manual tool, and `edit`,
`commit`, `task` with no callers at all. Six of seven detectors had never run.

The same insight is already sealed one layer down, in `reachability.py:78-85`: a file
merely sitting in `hooks/` is not necessarily invoked by anything, so a hook counts as a
live seed only if the dispatcher's own registries name it. That reasoning was bounded to
the hook layer. This carries it to a module's internal dispatch table, which is the same
mistake at a different scale.

Deliberately a REPORTER, not a gate. A dict of callables is a legitimate and common
idiom, and plenty of tables are driven by computed keys this analysis cannot follow --
so a NEVER_SUPPLIED row means "no literal caller was found", which is a prompt to look,
never a proof of death. Over-reporting is the safe direction; blocking on it would not be.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

SUPPLIED = "SUPPLIED"
NEVER_SUPPLIED = "NEVER_SUPPLIED"

# A table with one or two entries is usually a small mapping, not a dispatch surface,
# and scanning them produces far more noise than signal.
MIN_TABLE_ENTRIES = 3

# Enough suppliers to show a key is genuinely reached; the full list is noise in a report.
MAX_SUPPLIERS_SHOWN = 4

_SKIP_DIRS = {"__pycache__", "node_modules", ".git", "vendor", "backups",
              "_quarantine", "_audit_cache", "_logs", "_knowledge_graph"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def dispatch_tables(py_path: Path) -> list[tuple[str, dict, list]]:
    """Module-level str->callable dicts, as (table_name, {key: handler}, [dispatcher_fns]).

    Two constraints, both learned by running this against its own founding case.

    A value must resolve to something CALLABLE defined in this module -- a `def`, a
    lambda, or an attribute access. Accepting bare names made `_KIND_TIER = {'skill-card':
    WARM, ...}` look like a dispatch surface, when WARM is a tier constant and the dict is
    ordinary data.

    A table is only a dispatch surface if some function actually indexes it. That
    function's name is what callers write, so it is returned alongside: without it the
    caller search degenerates into "does this word appear in quotes anywhere", which for a
    key like 'session' matches hundreds of unrelated lines.
    """
    try:
        src = py_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except (OSError, SyntaxError, ValueError):
        return []

    funcs = {n.name for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    out: list[tuple[str, dict, list]] = []
    for node in tree.body:                       # module level only
        target, value = None, None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        if not isinstance(target, ast.Name) or not isinstance(value, ast.Dict):
            continue
        if len(value.keys) < MIN_TABLE_ENTRIES:
            continue
        pairs: dict[str, str] = {}
        ok = True
        for k, v in zip(value.keys, value.values):
            if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                ok = False
                break
            if isinstance(v, ast.Name) and v.id in funcs:
                pairs[k.value] = v.id
            elif isinstance(v, ast.Lambda):
                pairs[k.value] = "<lambda>"
            else:
                ok = False
                break
        if not (ok and pairs):
            continue
        dispatchers = _dispatchers_for(tree, target.id)
        if dispatchers:
            out.append((target.id, pairs, dispatchers))
    return out


def _dispatchers_for(tree: ast.AST, table: str) -> list[str]:
    """Functions that index `table` -- TABLE[x] or TABLE.get(x). These are what callers call."""
    found: list[str] = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for n in ast.walk(fn):
            hit = (
                (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                 and n.value.id == table)
                or (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "get" and isinstance(n.func.value, ast.Name)
                    and n.func.value.id == table)
            )
            if hit:
                found.append(fn.name)
                break
    return found


def _searchable_files(repo_root: Path) -> list[Path]:
    """Files that could supply a key: live surfaces and non-test source."""
    files: list[Path] = []
    for sub in ("hooks", "commands", "tools", "modules", "agents", "skills"):
        base = repo_root / sub
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.is_dir() or any(d in p.parts for d in _SKIP_DIRS):
                continue
            if p.suffix.lower() in (".py", ".js", ".md", ".json", ".ps1"):
                files.append(p)
    return files


def scan(repo_root: Path | None = None) -> list[dict]:
    """Every dispatch-table key, and whether any file outside its own module supplies it.

    A key is SUPPLIED when it appears as a quoted literal somewhere else. Tests are
    excluded on purpose: a key that only a test supplies is exactly the FPO case, where
    the suite exercised a path production never took.
    """
    root = repo_root or _repo_root()
    corpus: list[tuple[Path, str]] = []
    for p in _searchable_files(root):
        name = p.name.lower()
        if name.startswith("test_") or name.endswith(".test.js"):
            continue
        try:
            corpus.append((p, p.read_text(encoding="utf-8", errors="replace")))
        except OSError:
            continue

    rows: list[dict] = []
    for py in sorted((root / "modules").rglob("*.py")):
        if any(d in py.parts for d in _SKIP_DIRS) or py.name.startswith("test_"):
            continue
        for table, pairs, dispatchers in dispatch_tables(py):
            # Match the key only in CALL position -- dispatcher('key') -- never as a bare
            # quoted word. 'session' as a loose literal appears in hundreds of unrelated
            # lines, which silently marked every detector SUPPLIED and made the scanner
            # miss the case it was written for.
            call = "|".join(re.escape(d) for d in sorted(set(dispatchers)))
            for key, handler in sorted(pairs.items()):
                pat = re.compile(
                    r"(?:" + call + r")\s*\(\s*['\"]" + re.escape(key) + r"['\"]")
                suppliers = [
                    str(p.relative_to(root)).replace("\\", "/")
                    for p, text in corpus
                    if p != py and pat.search(text)
                ]
                rows.append({
                    "module": str(py.relative_to(root)).replace("\\", "/"),
                    "table": table,
                    "key": key,
                    "handler": handler,
                    "dispatchers": sorted(set(dispatchers)),
                    "suppliers": suppliers[:MAX_SUPPLIERS_SHOWN],
                    "status": SUPPLIED if suppliers else NEVER_SUPPLIED,
                })
    return rows


def gaps(repo_root: Path | None = None) -> list[dict]:
    return [r for r in scan(repo_root) if r["status"] == NEVER_SUPPLIED]


def render(rows: list[dict]) -> str:
    missing = [r for r in rows if r["status"] == NEVER_SUPPLIED]
    lines = [
        f"dispatch keys: {len(rows)}   never supplied: {len(missing)}",
        "",
        "A NEVER_SUPPLIED key means no file outside the defining module calls its",
        "dispatcher with that key as a literal. Test files are excluded on purpose: a key",
        "only a test supplies is the case this scanner exists for. Computed keys are",
        "invisible here, so treat a row as a question, not a verdict.",
        "",
    ]
    for r in missing:
        via = "/".join(r.get("dispatchers") or []) or "?"
        lines.append(f"  {r['module']}  {r['table']}[{r['key']!r}] -> {r['handler']}"
                     f"   (via {via}())")
    return "\n".join(lines)


def main(argv: list | None = None) -> int:
    rows = scan()
    print(render(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
