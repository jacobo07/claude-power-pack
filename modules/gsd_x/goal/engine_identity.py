#!/usr/bin/env python3
"""The identity of the code the sweep would run: a digest of its import closure.

The autonomy record says "the judge and chaos suites were green on THIS code".
It used to name the repository HEAD. In a shared tree HEAD moves every few
minutes (median 7.6 min, measured 2026-10-02) for files the engine never
imports, so a record went stale before the next five-minute sweep could use it:
a precondition that is never satisfiable is a capability the product does not
have.

So the record names the engine itself. The closure is DISCOVERED, never listed
by hand: start from every module of the goal package, its CLI and the required
suites, and follow every import statement (function-level ones included -- the
engine imports ``repo_identity`` and ``secret_firewall`` lazily) plus every
``*.py`` path literal (scripts run by path). Each file is hashed with line
endings normalised, because a CRLF checkout of the same code is the same code
(goal-spine finding B1). A missing seed yields "" -- UNKNOWN, which matches
nothing.

What the digest does not cover: the interpreter, git, the environment, and any
import spelled dynamically. The HEAD pin did not cover the first three either.
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

PREFIX = "engine:"
GOAL_PKG = Path("modules") / "gsd_x" / "goal"
CLI = Path("tools") / "gsd_x_goal.py"


def _seeds(pp_root: Path, suites: tuple[str, ...]) -> list[Path] | None:
    pkg = pp_root / GOAL_PKG
    fixed = [pp_root / CLI, *[pp_root / "tools" / s for s in suites]]
    if not pkg.is_dir() or not all(p.is_file() for p in fixed):
        return None
    return sorted(pkg.rglob("*.py")) + fixed


def _module_files(root: Path, dotted: str) -> list[Path]:
    """Files executed by importing ``dotted`` from ``root``: each package
    ``__init__`` on the way plus the module or package itself."""
    parts = dotted.split(".")
    out: list[Path] = []
    for i in range(1, len(parts) + 1):
        base = root.joinpath(*parts[:i])
        if (base / "__init__.py").is_file():
            out.append(base / "__init__.py")
        elif base.with_suffix(".py").is_file():
            out.append(base.with_suffix(".py"))
            break
        elif base.is_dir():
            continue  # namespace package: `modules/` itself has no __init__.py
        else:
            break
    return out


def _package_of(pp_root: Path, f: Path) -> list[str]:
    try:
        rel = f.relative_to(pp_root)
    except ValueError:
        return []
    return list(rel.parent.parts)


def _imports(pp_root: Path, f: Path) -> set[Path]:
    try:
        tree = ast.parse(f.read_bytes(), filename=str(f))
    except (OSError, SyntaxError, ValueError):
        return set()
    roots = (pp_root, pp_root / "tools")
    found: set[Path] = set()

    def add(dotted: str) -> None:
        for r in roots:
            found.update(_module_files(r, dotted))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                pkg = _package_of(pp_root, f)
                if node.level > 1:
                    pkg = pkg[: len(pkg) - (node.level - 1)]
                base = ".".join(pkg + ([node.module] if node.module else []))
                if not base:
                    continue
                found.update(_module_files(pp_root, base))
                for alias in node.names:
                    found.update(_module_files(pp_root, f"{base}.{alias.name}"))
            elif node.module:
                add(node.module)
                for alias in node.names:
                    add(f"{node.module}.{alias.name}")
        elif isinstance(node, ast.Call) and node.args:
            # __import__("x"), importlib.import_module("x"), a local _tools_import("x"):
            # a module named by a literal is still an import (providers/long_run.py).
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            arg = node.args[0]
            if ("import" in name.lower() and isinstance(arg, ast.Constant)
                    and isinstance(arg.value, str)):
                add(arg.value)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value.strip()
            if v.endswith(".py") and "\n" not in v and len(v) < 260:
                for cand in (pp_root / v, f.parent / v, pp_root / "tools" / Path(v).name):
                    if cand.is_file():
                        found.add(cand)
                        break
    root_res = pp_root.resolve()
    return {p.resolve() for p in found if p.resolve().is_relative_to(root_res)}


def engine_closure(pp_root: Path, suites: tuple[str, ...] | None = None) -> list[str]:
    """Repo-relative POSIX paths of every file in the engine's closure, sorted."""
    if suites is None:
        from .sweep import REQUIRED_SUITES as suites  # noqa: PLC0415
    pp_root = Path(pp_root).resolve()
    seeds = _seeds(pp_root, suites)
    if seeds is None:
        return []
    seen: set[Path] = set()
    todo = [s.resolve() for s in seeds]
    while todo:
        f = todo.pop()
        if f in seen:
            continue
        seen.add(f)
        todo.extend(p for p in _imports(pp_root, f) if p not in seen)
    return sorted(p.relative_to(pp_root).as_posix() for p in seen)


def engine_identity(pp_root: Path, suites: tuple[str, ...] | None = None) -> str:
    """``engine:<sha256>`` over the closure, or "" when it cannot be computed."""
    pp_root = Path(pp_root).resolve()
    files = engine_closure(pp_root, suites)
    if not files:
        return ""
    h = hashlib.sha256()
    for rel in files:
        try:
            data = (pp_root / rel).read_bytes().replace(b"\r\n", b"\n")
        except OSError:
            return ""
        h.update(rel.encode("utf-8") + b"\0" + hashlib.sha256(data).digest())
    return PREFIX + h.hexdigest()
