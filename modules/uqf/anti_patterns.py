"""UQF Anti-Pattern Detectors.

Source: ECC/Affaan Mustafa MIT
       (rules/common/code-review.md + rules/python/coding-style.md)

AST-based detectors for common code anti-patterns. Each detector is
a pure function (code -> list[AntiPatternHit]) so they can be composed
freely. The registry exposes a `run_all` that runs every detector and
returns a hits-by-detector dict.

These detectors are intended to surface review FINDINGS that pass the
ECC Pre-Report Gate (P01) automatically -- every hit comes with a
file:line citation, the offending snippet, and a concrete fix.
"""
import ast
import re
from dataclasses import dataclass


@dataclass
class AntiPatternHit:
    detector: str
    line: int | None
    snippet: str
    fix: str


def _safe_parse(code: str) -> ast.Module | None:
    try:
        return ast.parse(code)
    except (SyntaxError, ValueError):
        return None


def detect_bare_except(code: str) -> list[AntiPatternHit]:
    """ExceptHandler with `type is None`. ECC rule: never silently
    catch every exception; name what you handle."""
    tree = _safe_parse(code)
    if tree is None:
        return []
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            hits.append(AntiPatternHit(
                detector="detect_bare_except",
                line=node.lineno,
                snippet="except:",
                fix=(
                    "Name the exception type, e.g. "
                    "`except ValueError as e:` or `except OSError as e:`. "
                    "Bare except also catches KeyboardInterrupt and "
                    "SystemExit -- almost never what you want."
                ),
            ))
    return hits


def detect_missing_type_hints(code: str) -> list[AntiPatternHit]:
    """Public functions (not starting with _) without ANY type
    annotation. Internal helpers are exempt."""
    tree = _safe_parse(code)
    if tree is None:
        return []
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name.startswith("_"):
            continue
        # Skip dunder methods (covered by the class contract)
        if node.name.startswith("__"):
            continue
        has_any_annotation = (
            node.returns is not None or
            any(arg.annotation is not None for arg in node.args.args)
        )
        if has_any_annotation:
            continue
        # Skip if @overload or @abstractmethod (interface declarations
        # frequently omit annotations on purpose).
        skip = False
        for dec in node.decorator_list:
            name = getattr(dec, "id", None) or getattr(
                getattr(dec, "attr", None), "id", None) or \
                str(getattr(dec, "attr", ""))
            if name in ("overload", "abstractmethod", "property"):
                skip = True
        if skip:
            continue
        hits.append(AntiPatternHit(
            detector="detect_missing_type_hints",
            line=node.lineno,
            snippet=f"def {node.name}(...): ...",
            fix=(
                f"Add type hints to public function `{node.name}`. "
                f"At minimum annotate the return type."
            ),
        ))
    return hits


def detect_silent_pass_in_except(code: str) -> list[AntiPatternHit]:
    """ExceptHandler whose body is exactly `pass` or `...`."""
    tree = _safe_parse(code)
    if tree is None:
        return []
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if len(node.body) != 1:
            continue
        stmt = node.body[0]
        is_pass = isinstance(stmt, ast.Pass)
        is_ellipsis = (
            isinstance(stmt, ast.Expr) and
            isinstance(stmt.value, ast.Constant) and
            stmt.value.value is Ellipsis
        )
        if is_pass or is_ellipsis:
            hits.append(AntiPatternHit(
                detector="detect_silent_pass_in_except",
                line=node.lineno,
                snippet="except ...: pass",
                fix=(
                    "Silent pass discards every signal. Re-raise, "
                    "log with full context, or convert to a typed "
                    "domain error."
                ),
            ))
    return hits


def detect_magic_numbers(code: str) -> list[AntiPatternHit]:
    """Numeric literals that are NOT in the well-known constant set
    AND NOT being assigned to a UPPERCASE module-level name."""
    KNOWN = {0, 1, -1, 2, 100, 200, 404, 500, 1000, 1024, 60, 24, 365}
    tree = _safe_parse(code)
    if tree is None:
        return []
    # Collect line numbers of UPPERCASE = N assignments (the named
    # constants); we exempt those lines.
    constant_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id.isupper():
                    constant_lines.add(node.lineno)

    hits = []
    seen_keys: set[tuple] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        if not isinstance(node.value, (int, float)):
            continue
        if isinstance(node.value, bool):
            continue
        if node.value in KNOWN:
            continue
        if node.lineno in constant_lines:
            continue
        # Deduplicate by (line, value)
        key = (node.lineno, node.value)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        hits.append(AntiPatternHit(
            detector="detect_magic_numbers",
            line=node.lineno,
            snippet=str(node.value),
            fix=(
                f"Move `{node.value}` to a UPPERCASE module-level "
                f"constant with a descriptive name, or to a config."
            ),
        ))
    return hits


def detect_mutable_defaults(code: str) -> list[AntiPatternHit]:
    """FunctionDef args with a mutable default (list/dict/set/Call)."""
    tree = _safe_parse(code)
    if tree is None:
        return []
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                hits.append(AntiPatternHit(
                    detector="detect_mutable_defaults",
                    line=default.lineno,
                    snippet=ast.unparse(default),
                    fix=(
                        f"Mutable default in `{node.name}` is shared "
                        f"across calls. Use `None` and create the "
                        f"mutable inside the function body."
                    ),
                ))
    return hits


def detect_god_function(code: str, max_lines: int = 50) -> list[AntiPatternHit]:
    """FunctionDef whose body spans more than max_lines."""
    tree = _safe_parse(code)
    if tree is None:
        return []
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.body:
            last = node.body[-1]
            end = getattr(last, "end_lineno", last.lineno)
            span = end - node.lineno + 1
            if span > max_lines:
                hits.append(AntiPatternHit(
                    detector="detect_god_function",
                    line=node.lineno,
                    snippet=f"def {node.name}(...):  ({span} lines)",
                    fix=(
                        f"Split `{node.name}` (~{span} lines) into "
                        f"smaller named functions. ECC threshold: "
                        f"functions < {max_lines} lines."
                    ),
                ))
    return hits


def detect_hardcoded_paths(code: str) -> list[AntiPatternHit]:
    """String literals that look like absolute paths (Windows or
    POSIX home dirs). PP has been bitten by leaked paths before."""
    PATTERNS = (
        re.compile(r"['\"]([A-Za-z]:\\\\?Users\\\\[^'\"]+)['\"]"),
        re.compile(r"['\"](/home/[^/'\"]+/[^'\"]+)['\"]"),
        re.compile(r"['\"](/usr/local/[^'\"]+)['\"]"),
    )
    hits = []
    for lineno, line in enumerate(code.splitlines(), 1):
        # Skip lines that LOOK like documentation or strings inside
        # markdown blocks
        for pat in PATTERNS:
            for m in pat.finditer(line):
                hits.append(AntiPatternHit(
                    detector="detect_hardcoded_paths",
                    line=lineno,
                    snippet=m.group(1),
                    fix=(
                        f"Replace `{m.group(1)}` with a path computed "
                        f"from os.path.expanduser, env var, or config."
                    ),
                ))
                break  # one hit per line per pattern is enough
    return hits


REGISTRY = (
    detect_bare_except,
    detect_silent_pass_in_except,
    detect_missing_type_hints,
    detect_magic_numbers,
    detect_mutable_defaults,
    detect_god_function,
    detect_hardcoded_paths,
)


def run_all(code: str) -> dict[str, list[AntiPatternHit]]:
    """Run every detector against `code`. Returns a dict keyed by
    detector function name, value = list of hits."""
    return {fn.__name__: fn(code) for fn in REGISTRY}


__all__ = [
    "AntiPatternHit",
    "REGISTRY",
    "run_all",
    "detect_bare_except",
    "detect_silent_pass_in_except",
    "detect_missing_type_hints",
    "detect_magic_numbers",
    "detect_mutable_defaults",
    "detect_god_function",
    "detect_hardcoded_paths",
]
