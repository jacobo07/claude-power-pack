#!/usr/bin/env python3
"""
kobi-graphify — Knowledge Graph Generator for Claude Power Pack.

Parses source code into an Obsidian-compatible Markdown vault with [[wikilinks]].
Claude reads INDEX.md (~400 tokens) instead of scanning raw code (~5,000-15,000 tokens).

Usage:
    python kobi_graphify.py --project /path/to/project
    python kobi_graphify.py --project . --sync
    python kobi_graphify.py --project . --languages python,javascript
    python kobi_graphify.py --project . --quiet
"""

import ast
import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VAULT_DIR = "_knowledge_graph"
META_DIR = "_meta"
META_FILE = "graph_meta.json"

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build", ".next",
    ".nuxt", "target", "out", ".gradle", ".idea", ".vscode",
    VAULT_DIR, ".eggs", "site-packages", ".cache",
}

SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Pipfile.lock", "poetry.lock",
}

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".ex": "elixir",
    ".exs": "elixir",
    ".rb": "ruby",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
}

MAX_FILE_SIZE = 512 * 1024  # 512 KB — skip huge generated files

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class MethodInfo:
    name: str
    lines: str  # e.g. "52-78"
    visibility: str  # public/private/protected
    summary: str
    params: list[str] = field(default_factory=list)
    returns: str = ""
    is_async: bool = False
    decorators: list[str] = field(default_factory=list)


@dataclass
class GraphNode:
    """Base node in the knowledge graph."""
    node_id: str          # Unique ID, used as filename
    name: str             # Display name
    node_type: str        # module, class, function, dependency
    file_path: str        # Relative path to source file
    language: str
    line_start: int = 0
    line_end: int = 0
    summary: str = ""
    imports: list[str] = field(default_factory=list)       # outbound module refs
    dependencies: list[str] = field(default_factory=list)  # [[wikilink]] targets
    used_by: list[str] = field(default_factory=list)       # inbound [[wikilink]] sources
    methods: list[MethodInfo] = field(default_factory=list)
    inherits: list[str] = field(default_factory=list)
    implements: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    business_rules: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def safe_filename(name: str) -> str:
    """Convert a path/name to a filesystem-safe vault filename."""
    # Replace path separators with double dashes
    name = name.replace("/", "--").replace("\\", "--")
    # Remove or replace other unsafe chars
    name = re.sub(r"[<>:\"|?*]", "", name)
    # Strip leading/trailing dots and spaces
    name = name.strip(". ")
    return name


def file_hash(path: Path) -> str:
    """SHA256 hash of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def estimate_tokens(text: str) -> int:
    """Rough token estimate: words * 1.33."""
    return int(len(text.split()) * 1.33)


def relative_path(file_path: Path, project_dir: Path) -> str:
    """Get relative path as forward-slash string."""
    try:
        return str(file_path.relative_to(project_dir)).replace("\\", "/")
    except ValueError:
        return str(file_path).replace("\\", "/")


def make_node_id(rel_path: str, name: str, node_type: str) -> str:
    """Generate a unique node ID for vault filenames."""
    base = rel_path.rsplit(".", 1)[0]  # strip extension
    if node_type == "module":
        return f"modules/{safe_filename(base)}"
    elif node_type == "class":
        return f"classes/{safe_filename(name)}"
    elif node_type == "function":
        return f"functions/{safe_filename(name)}"
    elif node_type == "dependency":
        return f"dependencies/{safe_filename(name)}"
    return f"modules/{safe_filename(base)}"


# ---------------------------------------------------------------------------
# Python Parser (AST-based — gold standard)
# ---------------------------------------------------------------------------

class PythonParser:
    """Parse Python files using the ast module."""

    def parse(self, file_path: Path, project_dir: Path) -> list[GraphNode]:
        """Parse a Python file and return graph nodes."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return []

        rel = relative_path(file_path, project_dir)
        lines = source.splitlines()
        nodes: list[GraphNode] = []

        # Module node
        module_node = GraphNode(
            node_id=make_node_id(rel, file_path.stem, "module"),
            name=file_path.stem,
            node_type="module",
            file_path=rel,
            language="python",
            line_start=1,
            line_end=len(lines),
            summary=self._extract_module_docstring(tree),
            imports=self._extract_imports(tree),
            exports=self._extract_exports(tree),
        )

        # Extract top-level classes and functions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                cls_node = self._parse_class(node, rel, lines)
                cls_node.dependencies.append(f"[[{module_node.node_id}]]")
                module_node.exports.append(node.name)
                nodes.append(cls_node)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_") or node.name == "__main__":
                    fn_node = self._parse_function(node, rel, lines, top_level=True)
                    fn_node.dependencies.append(f"[[{module_node.node_id}]]")
                    module_node.exports.append(node.name)
                    nodes.append(fn_node)

        # Extract business rules (assertions, raises, constants)
        module_node.business_rules = self._extract_business_rules(tree, lines)
        nodes.insert(0, module_node)
        return nodes

    def _extract_module_docstring(self, tree: ast.Module) -> str:
        """Extract module-level docstring."""
        ds = ast.get_docstring(tree)
        if ds:
            # First sentence only
            first = ds.split("\n")[0].strip()
            return first[:120]
        return ""

    def _extract_imports(self, tree: ast.Module) -> list[str]:
        """Extract import statements as module references."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return sorted(set(imports))

    def _extract_exports(self, tree: ast.Module) -> list[str]:
        """Extract __all__ or top-level definitions."""
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            return [
                                elt.value for elt in node.value.elts
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                            ]
        return []

    def _parse_class(self, node: ast.ClassDef, rel_path: str, lines: list[str]) -> GraphNode:
        """Parse a class definition into a GraphNode."""
        end_line = self._get_end_line(node)
        docstring = ast.get_docstring(node) or ""
        summary = docstring.split("\n")[0].strip()[:120] if docstring else ""

        # Inheritance
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))

        # Methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._parse_method_info(item, lines))

        # Decorators
        decorators = [self._decorator_name(d) for d in node.decorator_list]

        return GraphNode(
            node_id=make_node_id(rel_path, node.name, "class"),
            name=node.name,
            node_type="class",
            file_path=rel_path,
            language="python",
            line_start=node.lineno,
            line_end=end_line,
            summary=summary,
            methods=methods,
            inherits=bases,
            decorators=decorators,
        )

    def _parse_function(self, node, rel_path: str, lines: list[str],
                        top_level: bool = False) -> GraphNode:
        """Parse a top-level function into a GraphNode."""
        end_line = self._get_end_line(node)
        docstring = ast.get_docstring(node) or ""
        summary = docstring.split("\n")[0].strip()[:120] if docstring else ""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        decorators = [self._decorator_name(d) for d in node.decorator_list]

        # Parameters
        params = []
        for arg in node.args.args:
            if arg.arg != "self" and arg.arg != "cls":
                annotation = ""
                if arg.annotation:
                    try:
                        annotation = f": {ast.unparse(arg.annotation)}"
                    except Exception:
                        pass
                params.append(f"{arg.arg}{annotation}")

        # Return type
        returns = ""
        if node.returns:
            try:
                returns = ast.unparse(node.returns)
            except Exception:
                pass

        return GraphNode(
            node_id=make_node_id(rel_path, node.name, "function"),
            name=node.name,
            node_type="function",
            file_path=rel_path,
            language="python",
            line_start=node.lineno,
            line_end=end_line,
            summary=summary,
            decorators=decorators,
            extra={
                "params": params,
                "returns": returns,
                "is_async": is_async,
            },
        )

    def _parse_method_info(self, node, lines: list[str]) -> MethodInfo:
        """Parse a method inside a class into MethodInfo."""
        end_line = self._get_end_line(node)
        docstring = ast.get_docstring(node) or ""
        summary = docstring.split("\n")[0].strip()[:80] if docstring else ""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        decorators = [self._decorator_name(d) for d in node.decorator_list]

        # Visibility heuristic
        if node.name.startswith("__") and node.name.endswith("__"):
            visibility = "dunder"
        elif node.name.startswith("_"):
            visibility = "private"
        else:
            visibility = "public"

        params = []
        for arg in node.args.args:
            if arg.arg not in ("self", "cls"):
                params.append(arg.arg)

        returns = ""
        if node.returns:
            try:
                returns = ast.unparse(node.returns)
            except Exception:
                pass

        return MethodInfo(
            name=node.name,
            lines=f"{node.lineno}-{end_line}",
            visibility=visibility,
            summary=summary,
            params=params,
            returns=returns,
            is_async=is_async,
            decorators=decorators,
        )

    def _extract_business_rules(self, tree: ast.Module, lines: list[str]) -> list[str]:
        """Extract business rules from assertions, raises, and constants."""
        rules = []
        for node in ast.walk(tree):
            # Assertions with messages
            if isinstance(node, ast.Assert) and node.msg:
                try:
                    msg = ast.unparse(node.msg)
                    rules.append(f"Assert: {msg} (line {node.lineno})")
                except Exception:
                    pass
            # Raise with string messages
            elif isinstance(node, ast.Raise) and node.exc:
                try:
                    text = ast.unparse(node.exc)
                    if len(text) < 100:
                        rules.append(f"Raises: {text} (line {node.lineno})")
                except Exception:
                    pass
            # Module-level constants (ALL_CAPS assignments)
            elif isinstance(node, ast.Assign) and hasattr(node, "lineno"):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper() and len(target.id) > 2:
                        try:
                            val = ast.unparse(node.value)
                            if len(val) < 80:
                                rules.append(f"Const: {target.id} = {val} (line {node.lineno})")
                        except Exception:
                            pass
        return rules[:20]  # Cap to avoid bloat

    def _get_end_line(self, node) -> int:
        """Get the last line of an AST node."""
        if hasattr(node, "end_lineno") and node.end_lineno:
            return node.end_lineno
        # Fallback: walk children for max lineno
        max_line = node.lineno
        for child in ast.walk(node):
            if hasattr(child, "lineno") and child.lineno:
                max_line = max(max_line, child.lineno)
        return max_line

    def _decorator_name(self, node) -> str:
        """Extract decorator name from AST node."""
        try:
            return ast.unparse(node)
        except Exception:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return node.attr
            return "?"


# ---------------------------------------------------------------------------
# JavaScript/TypeScript Parser (Regex-based heuristic)
# ---------------------------------------------------------------------------

class JavaScriptParser:
    """Parse JavaScript/TypeScript files using regex patterns."""

    # Class patterns
    RE_CLASS = re.compile(
        r"^(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)"
        r"(?:\s+extends\s+([\w.]+))?"
        r"(?:\s+implements\s+([\w.,\s]+))?",
        re.MULTILINE,
    )
    # Function/method patterns
    RE_FUNCTION = re.compile(
        r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
        re.MULTILINE,
    )
    RE_ARROW_EXPORT = re.compile(
        r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(",
        re.MULTILINE,
    )
    RE_METHOD = re.compile(
        r"^\s+(?:async\s+)?(?:static\s+)?(?:get\s+|set\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*\S+\s*)?\{",
        re.MULTILINE,
    )
    # Import patterns
    RE_IMPORT_FROM = re.compile(
        r"import\s+(?:(?:\{[^}]*\}|[\w*]+)\s+from\s+)?['\"]([^'\"]+)['\"]",
    )
    RE_REQUIRE = re.compile(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)")

    # TypeScript extras
    RE_INTERFACE = re.compile(
        r"^(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+([\w.,\s]+))?",
        re.MULTILINE,
    )
    RE_TYPE_ALIAS = re.compile(
        r"^(?:export\s+)?type\s+(\w+)\s*=",
        re.MULTILINE,
    )

    def __init__(self, language: str = "javascript"):
        self.language = language

    def parse(self, file_path: Path, project_dir: Path) -> list[GraphNode]:
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        rel = relative_path(file_path, project_dir)
        lines = source.splitlines()
        nodes: list[GraphNode] = []

        # Module node
        imports = self._extract_imports(source)
        module_node = GraphNode(
            node_id=make_node_id(rel, file_path.stem, "module"),
            name=file_path.stem,
            node_type="module",
            file_path=rel,
            language=self.language,
            line_start=1,
            line_end=len(lines),
            summary=self._extract_first_comment(source),
            imports=imports,
        )

        # Classes
        for m in self.RE_CLASS.finditer(source):
            cls_name = m.group(1)
            extends = m.group(2) or ""
            implements = [x.strip() for x in (m.group(3) or "").split(",") if x.strip()]
            line_num = source[:m.start()].count("\n") + 1

            # Find methods in class body
            methods = self._extract_class_methods(source, m.start(), lines)

            cls_node = GraphNode(
                node_id=make_node_id(rel, cls_name, "class"),
                name=cls_name,
                node_type="class",
                file_path=rel,
                language=self.language,
                line_start=line_num,
                summary="",
                methods=methods,
                inherits=[extends] if extends else [],
                implements=implements,
                dependencies=[f"[[{module_node.node_id}]]"],
            )
            module_node.exports.append(cls_name)
            nodes.append(cls_node)

        # Standalone functions
        for m in self.RE_FUNCTION.finditer(source):
            fn_name = m.group(1)
            line_num = source[:m.start()].count("\n") + 1
            is_async = "async" in m.group(0)

            fn_node = GraphNode(
                node_id=make_node_id(rel, fn_name, "function"),
                name=fn_name,
                node_type="function",
                file_path=rel,
                language=self.language,
                line_start=line_num,
                dependencies=[f"[[{module_node.node_id}]]"],
                extra={"is_async": is_async},
            )
            module_node.exports.append(fn_name)
            nodes.append(fn_node)

        # Arrow function exports
        for m in self.RE_ARROW_EXPORT.finditer(source):
            fn_name = m.group(1)
            line_num = source[:m.start()].count("\n") + 1

            fn_node = GraphNode(
                node_id=make_node_id(rel, fn_name, "function"),
                name=fn_name,
                node_type="function",
                file_path=rel,
                language=self.language,
                line_start=line_num,
                dependencies=[f"[[{module_node.node_id}]]"],
            )
            module_node.exports.append(fn_name)
            nodes.append(fn_node)

        # TypeScript interfaces and type aliases
        if self.language == "typescript":
            for m in self.RE_INTERFACE.finditer(source):
                iface_name = m.group(1)
                extends_list = [x.strip() for x in (m.group(2) or "").split(",") if x.strip()]
                line_num = source[:m.start()].count("\n") + 1

                iface_node = GraphNode(
                    node_id=make_node_id(rel, iface_name, "class"),
                    name=iface_name,
                    node_type="class",
                    file_path=rel,
                    language=self.language,
                    line_start=line_num,
                    inherits=extends_list,
                    extra={"kind": "interface"},
                    dependencies=[f"[[{module_node.node_id}]]"],
                )
                module_node.exports.append(iface_name)
                nodes.append(iface_node)

            for m in self.RE_TYPE_ALIAS.finditer(source):
                type_name = m.group(1)
                line_num = source[:m.start()].count("\n") + 1
                module_node.exports.append(type_name)

        nodes.insert(0, module_node)
        return nodes

    def _extract_imports(self, source: str) -> list[str]:
        imports = set()
        for m in self.RE_IMPORT_FROM.finditer(source):
            imports.add(m.group(1))
        for m in self.RE_REQUIRE.finditer(source):
            imports.add(m.group(1))
        return sorted(imports)

    def _extract_first_comment(self, source: str) -> str:
        """Extract first JSDoc or line comment as summary."""
        # JSDoc
        m = re.match(r"\s*/\*\*\s*\n?\s*\*?\s*(.+?)(?:\n|\*/)", source)
        if m:
            return m.group(1).strip()[:120]
        # Single-line comment at top
        m = re.match(r"\s*//\s*(.+)", source)
        if m:
            return m.group(1).strip()[:120]
        return ""

    def _extract_class_methods(self, source: str, class_start: int,
                                lines: list[str]) -> list[MethodInfo]:
        """Extract methods from a class body using regex."""
        methods = []
        # Find the opening brace
        brace_pos = source.find("{", class_start)
        if brace_pos == -1:
            return methods

        # Scan for methods within ~500 lines
        search_end = min(len(source), brace_pos + 20000)
        region = source[brace_pos:search_end]

        for m in self.RE_METHOD.finditer(region):
            name = m.group(1)
            if name in ("if", "for", "while", "switch", "catch", "constructor"):
                if name != "constructor":
                    continue
            line_num = source[:brace_pos + m.start()].count("\n") + 1
            is_async = "async" in m.group(0)

            visibility = "public"
            if name.startswith("#") or name.startswith("_"):
                visibility = "private"

            methods.append(MethodInfo(
                name=name,
                lines=str(line_num),
                visibility=visibility,
                summary="",
                is_async=is_async,
            ))

        return methods


# ---------------------------------------------------------------------------
# Java Parser (Regex-based heuristic)
# ---------------------------------------------------------------------------

class JavaParser:
    """Parse Java files using regex patterns."""

    RE_PACKAGE = re.compile(r"^package\s+([\w.]+)\s*;", re.MULTILINE)
    RE_IMPORT = re.compile(r"^import\s+(?:static\s+)?([\w.]+)\s*;", re.MULTILINE)
    RE_CLASS = re.compile(
        r"^(?:public\s+|private\s+|protected\s+)?(?:abstract\s+)?(?:final\s+)?"
        r"(?:class|interface|enum|record)\s+(\w+)"
        r"(?:<[^>]+>)?"
        r"(?:\s+extends\s+([\w.<>,\s]+))?"
        r"(?:\s+implements\s+([\w.<>,\s]+))?",
        re.MULTILINE,
    )
    RE_METHOD = re.compile(
        r"^\s+(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?"
        r"(?:abstract\s+)?(?:<[\w<>,?\s]+>\s+)?"
        r"([\w<>\[\],?\s]+)\s+(\w+)\s*\(([^)]*)\)",
        re.MULTILINE,
    )
    RE_ANNOTATION = re.compile(r"^\s*@(\w+)", re.MULTILINE)

    def parse(self, file_path: Path, project_dir: Path) -> list[GraphNode]:
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        rel = relative_path(file_path, project_dir)
        lines = source.splitlines()
        nodes: list[GraphNode] = []

        # Imports
        imports = sorted(set(m.group(1) for m in self.RE_IMPORT.finditer(source)))

        # Package
        pkg_match = self.RE_PACKAGE.search(source)
        package = pkg_match.group(1) if pkg_match else ""

        # Module node
        module_node = GraphNode(
            node_id=make_node_id(rel, file_path.stem, "module"),
            name=file_path.stem,
            node_type="module",
            file_path=rel,
            language="java",
            line_start=1,
            line_end=len(lines),
            imports=imports,
            extra={"package": package},
        )

        # Classes/interfaces/enums
        for m in self.RE_CLASS.finditer(source):
            cls_name = m.group(1)
            extends_raw = m.group(2) or ""
            implements_raw = m.group(3) or ""
            line_num = source[:m.start()].count("\n") + 1

            # Parse extends/implements (strip generics for link matching)
            extends = [x.strip().split("<")[0] for x in extends_raw.split(",") if x.strip()]
            implements = [x.strip().split("<")[0] for x in implements_raw.split(",") if x.strip()]

            # Extract methods
            methods = self._extract_methods(source, m.start(), lines)

            # Detect annotations above class
            decorators = []
            pre_lines = source[:m.start()].splitlines()
            for pl in reversed(pre_lines[-5:]):
                ann = self.RE_ANNOTATION.match(pl)
                if ann:
                    decorators.append(ann.group(1))

            cls_node = GraphNode(
                node_id=make_node_id(rel, cls_name, "class"),
                name=cls_name,
                node_type="class",
                file_path=rel,
                language="java",
                line_start=line_num,
                methods=methods,
                inherits=extends,
                implements=implements,
                decorators=list(reversed(decorators)),
                dependencies=[f"[[{module_node.node_id}]]"],
            )
            module_node.exports.append(cls_name)
            nodes.append(cls_node)

        nodes.insert(0, module_node)
        return nodes

    def _extract_methods(self, source: str, class_start: int,
                          lines: list[str]) -> list[MethodInfo]:
        methods = []
        brace_pos = source.find("{", class_start)
        if brace_pos == -1:
            return methods

        search_end = min(len(source), brace_pos + 30000)
        region = source[brace_pos:search_end]

        for m in self.RE_METHOD.finditer(region):
            return_type = m.group(1).strip()
            name = m.group(2)
            params_raw = m.group(3).strip()
            line_num = source[:brace_pos + m.start()].count("\n") + 1

            # Determine visibility from match
            full_match = m.group(0).strip()
            if full_match.startswith("private"):
                visibility = "private"
            elif full_match.startswith("protected"):
                visibility = "protected"
            else:
                visibility = "public"

            params = [p.strip().split()[-1] for p in params_raw.split(",") if p.strip()] if params_raw else []

            methods.append(MethodInfo(
                name=name,
                lines=str(line_num),
                visibility=visibility,
                summary="",
                params=params,
                returns=return_type,
            ))

        return methods


# ---------------------------------------------------------------------------
# Generic Parser (Fallback — imports + function signatures)
# ---------------------------------------------------------------------------

class GenericParser:
    """Fallback parser for unsupported languages. Extracts imports and function-like signatures."""

    RE_IMPORT = re.compile(
        r"^(?:import|require|include|use|from|#include)\s+[\"'<]?([^\s\"'>]+)",
        re.MULTILINE,
    )
    RE_FUNCTION = re.compile(
        r"^(?:pub\s+|export\s+)?(?:async\s+)?(?:def|fn|func|fun|sub|function)\s+(\w+)",
        re.MULTILINE,
    )

    def __init__(self, language: str = "unknown"):
        self.language = language

    def parse(self, file_path: Path, project_dir: Path) -> list[GraphNode]:
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        rel = relative_path(file_path, project_dir)
        lines = source.splitlines()

        imports = sorted(set(m.group(1) for m in self.RE_IMPORT.finditer(source)))

        module_node = GraphNode(
            node_id=make_node_id(rel, file_path.stem, "module"),
            name=file_path.stem,
            node_type="module",
            file_path=rel,
            language=self.language,
            line_start=1,
            line_end=len(lines),
            imports=imports,
        )

        nodes = [module_node]

        # Extract functions
        for m in self.RE_FUNCTION.finditer(source):
            fn_name = m.group(1)
            line_num = source[:m.start()].count("\n") + 1

            fn_node = GraphNode(
                node_id=make_node_id(rel, fn_name, "function"),
                name=fn_name,
                node_type="function",
                file_path=rel,
                language=self.language,
                line_start=line_num,
                dependencies=[f"[[{module_node.node_id}]]"],
            )
            module_node.exports.append(fn_name)
            nodes.append(fn_node)

        return nodes


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def render_node_md(node: GraphNode) -> str:
    """Render a GraphNode as an Obsidian-compatible Markdown file."""
    parts = []

    # YAML frontmatter
    parts.append("---")
    parts.append(f"type: {node.node_type}")
    parts.append(f"name: {node.name}")
    parts.append(f"file: {node.file_path}")
    parts.append(f"language: {node.language}")
    if node.line_start and node.line_end:
        parts.append(f"lines: {node.line_start}-{node.line_end}")
    parts.append("---")
    parts.append("")

    # Title + summary
    parts.append(f"# {node.name}")
    if node.summary:
        parts.append(f"> {node.summary}")
    parts.append("")

    # Inheritance
    if node.inherits:
        links = ", ".join(f"[[classes/{safe_filename(b)}|{b}]]" for b in node.inherits)
        parts.append(f"**Inherits:** {links}")
        parts.append("")

    # Implements
    if node.implements:
        links = ", ".join(f"[[classes/{safe_filename(i)}|{i}]]" for i in node.implements)
        parts.append(f"**Implements:** {links}")
        parts.append("")

    # Decorators
    if node.decorators:
        parts.append(f"**Decorators:** {', '.join(f'`@{d}`' for d in node.decorators)}")
        parts.append("")

    # Function-specific: params & returns
    if node.node_type == "function" and node.extra:
        params = node.extra.get("params", [])
        returns = node.extra.get("returns", "")
        is_async = node.extra.get("is_async", False)
        prefix = "async " if is_async else ""
        sig = f"`{prefix}def {node.name}({', '.join(params)})"
        if returns:
            sig += f" -> {returns}"
        sig += "`"
        parts.append(f"**Signature:** {sig}")
        parts.append("")

    # Methods table
    if node.methods:
        public_methods = [m for m in node.methods if m.visibility != "private"]
        if public_methods:
            parts.append("## Methods")
            parts.append("| Method | Lines | Summary |")
            parts.append("|--------|-------|---------|")
            for m in public_methods:
                prefix = "async " if m.is_async else ""
                parts.append(f"| `{prefix}{m.name}({', '.join(m.params)})` | {m.lines} | {m.summary} |")
            parts.append("")

    # Imports
    if node.imports:
        parts.append("## Imports")
        for imp in node.imports:
            parts.append(f"- `{imp}`")
        parts.append("")

    # Exports
    if node.exports and node.node_type == "module":
        parts.append("## Exports")
        for exp in node.exports:
            parts.append(f"- `{exp}`")
        parts.append("")

    # Dependencies (wikilinks)
    if node.dependencies:
        parts.append("## Dependencies")
        for dep in node.dependencies:
            parts.append(f"- {dep}")
        parts.append("")

    # Used By (wikilinks — populated during link resolution)
    if node.used_by:
        parts.append("## Used By")
        for ref in node.used_by:
            parts.append(f"- {ref}")
        parts.append("")

    # Business rules
    if node.business_rules:
        parts.append("## Business Rules")
        for rule in node.business_rules:
            parts.append(f"- {rule}")
        parts.append("")

    return "\n".join(parts)


def render_index_md(nodes: list[GraphNode], project_name: str, project_dir: str) -> str:
    """Render the master INDEX.md for the vault."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Stats
    modules = [n for n in nodes if n.node_type == "module"]
    classes = [n for n in nodes if n.node_type == "class"]
    functions = [n for n in nodes if n.node_type == "function"]
    deps = [n for n in nodes if n.node_type == "dependency"]

    parts = []
    parts.append(f"# Knowledge Graph: {project_name}")
    parts.append(f"Generated: {now} | Files: {len(modules)} | Classes: {len(classes)} | Functions: {len(functions)}")
    parts.append("")

    # Quick Nav
    parts.append("## Quick Nav")
    parts.append("- [[architecture/DEPENDENCY_GRAPH]] — Who imports whom")
    parts.append("- [[architecture/CLASS_HIERARCHY]] — Inheritance trees")
    parts.append("- [[architecture/ENTRY_POINTS]] — Where execution starts")
    if any(n.business_rules for n in nodes):
        parts.append("- [[architecture/BUSINESS_RULES]] — Domain constraints")
    parts.append("")

    # Modules by directory
    if modules:
        parts.append("## Modules")
        # Sort by path for grouping
        sorted_mods = sorted(modules, key=lambda n: n.file_path)
        for node in sorted_mods:
            inbound = len(node.used_by)
            suffix = f" ({inbound} refs)" if inbound > 0 else ""
            summary_text = f" — {node.summary}" if node.summary else ""
            parts.append(f"- [[{node.node_id}|{node.file_path}]]{summary_text}{suffix}")
        parts.append("")

    # Classes
    if classes:
        parts.append("## Classes")
        sorted_cls = sorted(classes, key=lambda n: len(n.used_by), reverse=True)
        for node in sorted_cls:
            inbound = len(node.used_by)
            suffix = f" ({inbound} refs)" if inbound > 0 else ""
            summary_text = f" — {node.summary}" if node.summary else ""
            base = f" extends {', '.join(node.inherits)}" if node.inherits else ""
            parts.append(f"- [[{node.node_id}|{node.name}]]{base}{summary_text}{suffix}")
        parts.append("")

    # Top standalone functions (max 20 to keep index lean)
    if functions:
        parts.append("## Functions")
        sorted_fns = sorted(functions, key=lambda n: len(n.used_by), reverse=True)
        for node in sorted_fns[:20]:
            summary_text = f" — {node.summary}" if node.summary else ""
            parts.append(f"- [[{node.node_id}|{node.name}]]{summary_text}")
        if len(functions) > 20:
            parts.append(f"- _...and {len(functions) - 20} more_")
        parts.append("")

    # External dependencies (if any)
    if deps:
        parts.append("## External Dependencies")
        for node in sorted(deps, key=lambda n: n.name):
            parts.append(f"- [[{node.node_id}|{node.name}]]")
        parts.append("")

    # Hot spots — most connected nodes
    all_by_refs = sorted(nodes, key=lambda n: len(n.used_by) + len(n.dependencies), reverse=True)
    hotspots = [n for n in all_by_refs if len(n.used_by) + len(n.dependencies) > 2][:10]
    if hotspots:
        parts.append("## Hot Spots (most connected)")
        for node in hotspots:
            parts.append(f"- [[{node.node_id}|{node.name}]] — {len(node.used_by)} inbound, {len(node.dependencies)} outbound")
        parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Link Resolver
# ---------------------------------------------------------------------------

def resolve_links(nodes: list[GraphNode]) -> None:
    """
    Resolve import references into bidirectional wikilinks.
    Matches import names to module/class/function node names.
    """
    # Build lookup: name -> node_id
    name_to_id: dict[str, str] = {}
    for node in nodes:
        name_to_id[node.name] = node.node_id
        # Also map by full module path for Python imports
        if node.node_type == "module":
            # Map dotted path: e.g. "src.utils.helpers" -> node_id
            dotted = node.file_path.replace("/", ".").rsplit(".", 1)[0]
            name_to_id[dotted] = node.node_id

    # Resolve imports -> dependencies (wikilinks)
    for node in nodes:
        for imp in node.imports:
            # Try exact match first, then last segment
            target_id = name_to_id.get(imp)
            if not target_id:
                last_segment = imp.rsplit(".", 1)[-1]
                target_id = name_to_id.get(last_segment)

            if target_id and target_id != node.node_id:
                link = f"[[{target_id}]]"
                if link not in node.dependencies:
                    node.dependencies.append(link)

    # Build reverse links (used_by)
    id_to_node: dict[str, GraphNode] = {n.node_id: n for n in nodes}
    for node in nodes:
        for dep_link in node.dependencies:
            # Extract node_id from [[node_id]]
            match = re.match(r"\[\[([^\]|]+)", dep_link)
            if match:
                target_id = match.group(1)
                target = id_to_node.get(target_id)
                if target and target.node_id != node.node_id:
                    back_link = f"[[{node.node_id}|{node.name}]]"
                    if back_link not in target.used_by:
                        target.used_by.append(back_link)


# ---------------------------------------------------------------------------
# Graph Builder (Orchestrator)
# ---------------------------------------------------------------------------

class GraphBuilder:
    """Orchestrates file discovery, parsing, linking, and vault generation."""

    def __init__(self, project_dir: str, languages: Optional[list[str]] = None,
                 quiet: bool = False):
        self.project_dir = Path(project_dir).resolve()
        self.languages = languages  # None = all supported
        self.quiet = quiet
        self.nodes: list[GraphNode] = []
        self.parsers = {
            "python": PythonParser(),
            "javascript": JavaScriptParser("javascript"),
            "typescript": JavaScriptParser("typescript"),
            "java": JavaParser(),
            "go": GenericParser("go"),
            "rust": GenericParser("rust"),
            "elixir": GenericParser("elixir"),
            "ruby": GenericParser("ruby"),
            "c": GenericParser("c"),
            "cpp": GenericParser("cpp"),
            "csharp": GenericParser("csharp"),
            "php": GenericParser("php"),
        }

    def log(self, msg: str) -> None:
        if not self.quiet:
            print(msg, file=sys.stderr)

    def scan(self) -> None:
        """Discover and parse all source files."""
        self.nodes = []
        files = self._discover_files()
        self.log(f"[graphify] Found {len(files)} source files")

        for file_path in files:
            lang = LANGUAGE_MAP.get(file_path.suffix, "")
            if not lang:
                continue
            if self.languages and lang not in self.languages:
                continue

            parser = self.parsers.get(lang)
            if not parser:
                continue

            try:
                file_nodes = parser.parse(file_path, self.project_dir)
                self.nodes.extend(file_nodes)
            except Exception as e:
                self.log(f"[graphify] WARN: Failed to parse {file_path}: {e}")

        self.log(f"[graphify] Extracted {len(self.nodes)} nodes")

        # Resolve links
        resolve_links(self.nodes)
        self.log("[graphify] Links resolved")

    def write_vault(self) -> dict:
        """Write all nodes to the vault directory. Returns stats."""
        vault_path = self.project_dir / VAULT_DIR
        meta_path = vault_path / META_DIR

        # Create directory structure
        for subdir in ["modules", "classes", "functions", "dependencies", "architecture", META_DIR]:
            (vault_path / subdir).mkdir(parents=True, exist_ok=True)

        # Write node files
        files_written = 0
        for node in self.nodes:
            node_path = vault_path / f"{node.node_id}.md"
            node_path.parent.mkdir(parents=True, exist_ok=True)
            content = render_node_md(node)
            node_path.write_text(content, encoding="utf-8")
            files_written += 1

        # Write INDEX.md
        project_name = self.project_dir.name
        index_content = render_index_md(self.nodes, project_name, str(self.project_dir))
        (vault_path / "INDEX.md").write_text(index_content, encoding="utf-8")

        # Write architecture views
        self._write_architecture_views(vault_path)

        # Write metadata
        meta = self._build_metadata()
        (meta_path / META_FILE).write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )

        # Stats
        index_tokens = estimate_tokens(index_content)
        avg_node_tokens = 0
        if self.nodes:
            total_tokens = sum(estimate_tokens(render_node_md(n)) for n in self.nodes)
            avg_node_tokens = total_tokens // len(self.nodes)

        stats = {
            "files_written": files_written + 1,  # +1 for INDEX.md
            "nodes": len(self.nodes),
            "index_tokens": index_tokens,
            "avg_node_tokens": avg_node_tokens,
            "vault_path": str(vault_path),
        }

        self.log(f"[graphify] Vault written: {stats['files_written']} files")
        self.log(f"[graphify] INDEX.md: ~{index_tokens} tokens")
        self.log(f"[graphify] Avg node: ~{avg_node_tokens} tokens")

        return stats

    def _discover_files(self) -> list[Path]:
        """Walk project directory and collect source files."""
        files = []
        for root, dirs, filenames in os.walk(self.project_dir):
            # Prune skip directories in-place
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

            for name in filenames:
                if name in SKIP_FILES:
                    continue
                fp = Path(root) / name
                if fp.suffix not in LANGUAGE_MAP:
                    continue
                # Skip large files
                try:
                    if fp.stat().st_size > MAX_FILE_SIZE:
                        continue
                except OSError:
                    continue
                files.append(fp)

        return sorted(files)

    def _build_metadata(self) -> dict:
        """Build metadata for incremental sync."""
        file_hashes = {}
        for node in self.nodes:
            if node.node_type == "module":
                fp = self.project_dir / node.file_path
                if fp.exists():
                    file_hashes[node.file_path] = file_hash(fp)

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project_dir": str(self.project_dir),
            "file_hashes": file_hashes,
            "node_count": len(self.nodes),
            "languages": list(set(n.language for n in self.nodes)),
        }

    def sync(self) -> dict:
        """Incremental sync — only re-parse files whose hash changed."""
        vault_path = self.project_dir / VAULT_DIR
        meta_path = vault_path / META_DIR / META_FILE

        # If no prior vault exists, fall back to full scan
        if not meta_path.exists():
            self.log("[graphify] No existing vault found. Running full scan.")
            self.scan()
            return self.write_vault()

        # Load previous metadata
        try:
            old_meta = json.loads(meta_path.read_text(encoding="utf-8"))
            old_hashes = old_meta.get("file_hashes", {})
        except (json.JSONDecodeError, OSError):
            self.log("[graphify] Corrupt metadata. Running full scan.")
            self.scan()
            return self.write_vault()

        # Discover current files and compute hashes
        files = self._discover_files()
        current_hashes: dict[str, str] = {}
        file_by_rel: dict[str, Path] = {}
        for fp in files:
            lang = LANGUAGE_MAP.get(fp.suffix, "")
            if not lang:
                continue
            if self.languages and lang not in self.languages:
                continue
            rel = relative_path(fp, self.project_dir)
            current_hashes[rel] = file_hash(fp)
            file_by_rel[rel] = fp

        # Diff: changed, added, removed
        changed = []
        added = []
        for rel, h in current_hashes.items():
            if rel not in old_hashes:
                added.append(rel)
            elif old_hashes[rel] != h:
                changed.append(rel)
        removed = [rel for rel in old_hashes if rel not in current_hashes]

        if not changed and not added and not removed:
            self.log("[graphify] No changes detected. Vault is up to date.")
            return {
                "files_written": 0,
                "nodes": old_meta.get("node_count", 0),
                "changed": 0,
                "added": 0,
                "removed": 0,
                "vault_path": str(vault_path),
            }

        self.log(f"[graphify] Sync: {len(changed)} changed, {len(added)} added, {len(removed)} removed")

        # Re-parse changed and added files
        re_parse_rels = set(changed + added)
        new_nodes: list[GraphNode] = []
        for rel in re_parse_rels:
            fp = file_by_rel.get(rel)
            if not fp:
                continue
            lang = LANGUAGE_MAP.get(fp.suffix, "")
            parser = self.parsers.get(lang)
            if not parser:
                continue
            try:
                file_nodes = parser.parse(fp, self.project_dir)
                new_nodes.extend(file_nodes)
            except Exception as e:
                self.log(f"[graphify] WARN: Failed to parse {fp}: {e}")

        # Load existing nodes from vault for unchanged files
        unchanged_rels = set(current_hashes.keys()) - re_parse_rels
        for rel in unchanged_rels:
            fp = file_by_rel.get(rel)
            if not fp:
                continue
            lang = LANGUAGE_MAP.get(fp.suffix, "")
            parser = self.parsers.get(lang)
            if not parser:
                continue
            try:
                file_nodes = parser.parse(fp, self.project_dir)
                new_nodes.extend(file_nodes)
            except Exception:
                pass

        self.nodes = new_nodes

        # Remove vault files for deleted source files
        for rel in removed:
            node_id = make_node_id(rel.rsplit(".", 1)[0], Path(rel).stem, "module")
            md_path = vault_path / f"{node_id}.md"
            if md_path.exists():
                md_path.unlink()
                self.log(f"[graphify] Removed: {node_id}.md")

        # Resolve links and write
        resolve_links(self.nodes)
        stats = self.write_vault()
        stats["changed"] = len(changed)
        stats["added"] = len(added)
        stats["removed"] = len(removed)
        return stats

    def _write_architecture_views(self, vault_path: Path) -> None:
        """Generate architecture/ aggregate view files."""
        arch_dir = vault_path / "architecture"

        # DEPENDENCY_GRAPH.md
        dep_lines = ["# Dependency Graph", "",
                      "Module-to-module import relationships.", ""]
        modules = [n for n in self.nodes if n.node_type == "module"]
        for mod in sorted(modules, key=lambda n: n.file_path):
            if mod.dependencies:
                dep_lines.append(f"## [[{mod.node_id}|{mod.name}]]")
                for dep in mod.dependencies:
                    dep_lines.append(f"  - → {dep}")
                dep_lines.append("")
        (arch_dir / "DEPENDENCY_GRAPH.md").write_text("\n".join(dep_lines), encoding="utf-8")

        # CLASS_HIERARCHY.md
        cls_lines = ["# Class Hierarchy", "",
                      "Inheritance and implementation relationships.", ""]
        classes = [n for n in self.nodes if n.node_type == "class"]
        for cls in sorted(classes, key=lambda n: n.name):
            base = f" extends {', '.join(cls.inherits)}" if cls.inherits else ""
            impl = f" implements {', '.join(cls.implements)}" if cls.implements else ""
            cls_lines.append(f"- [[{cls.node_id}|{cls.name}]]{base}{impl}")
        cls_lines.append("")
        (arch_dir / "CLASS_HIERARCHY.md").write_text("\n".join(cls_lines), encoding="utf-8")

        # ENTRY_POINTS.md
        entry_lines = ["# Entry Points", "",
                        "Main execution entry points and CLI handlers.", ""]
        for node in self.nodes:
            if node.node_type == "function" and node.name in ("main", "__main__"):
                entry_lines.append(f"- [[{node.node_id}|{node.name}]] in `{node.file_path}`")
            elif node.node_type == "module":
                # Check for if __name__ == "__main__" pattern
                fp = self.project_dir / node.file_path
                if fp.exists():
                    try:
                        content = fp.read_text(encoding="utf-8", errors="replace")
                        if '__name__' in content and '__main__' in content:
                            entry_lines.append(f"- [[{node.node_id}|{node.name}]] — has `if __name__ == '__main__'`")
                    except OSError:
                        pass
        entry_lines.append("")
        (arch_dir / "ENTRY_POINTS.md").write_text("\n".join(entry_lines), encoding="utf-8")

        # BUSINESS_RULES.md
        rules_lines = ["# Business Rules", "",
                         "Extracted constraints, assertions, and domain invariants.", ""]
        for node in self.nodes:
            if node.business_rules:
                rules_lines.append(f"## [[{node.node_id}|{node.name}]]")
                for rule in node.business_rules:
                    rules_lines.append(f"- {rule}")
                rules_lines.append("")
        (arch_dir / "BUSINESS_RULES.md").write_text("\n".join(rules_lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="kobi-graphify — Generate a Knowledge Graph vault from source code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--project", "-p", required=True,
        help="Path to project directory to scan",
    )
    parser.add_argument(
        "--languages", "-l", default=None,
        help="Comma-separated list of languages to parse (e.g., python,javascript)",
    )
    parser.add_argument(
        "--sync", "-s", action="store_true",
        help="Incremental sync — only re-parse changed files",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suppress progress messages",
    )

    args = parser.parse_args()

    languages = None
    if args.languages:
        languages = [lang.strip().lower() for lang in args.languages.split(",")]

    builder = GraphBuilder(
        project_dir=args.project,
        languages=languages,
        quiet=args.quiet,
    )

    if args.sync:
        stats = builder.sync()
    else:
        builder.scan()
        stats = builder.write_vault()

    # Print summary to stdout (machine-readable)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
