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


# Calls whose cost scales with the whole corpus rather than with the
# arguments handed in. Deliberately narrow: a name that merely sounds
# expensive is not evidence, and a detector that fires on `get_x()` teaches
# reviewers to ignore it.
#
# `read_text` and `run` were tried here and removed: reading ONE file or
# spawning ONE process is per-target cost, and including them produced 15
# hits that were not this defect. A detector that cries wolf teaches
# reviewers to skip it, which is worse than not shipping it.
_GLOBAL_COST = re.compile(
    r"^(?:.*\.)?(?:rglob|walk|iterdir|listdir|glob|"
    r"build_\w*map|_build_\w*map|load_all|scan_all|index_all|\w+_all)$")

# Detectors and tests legitimately carry the vocabulary they detect; the
# incrementality detector matched its OWN name on the first run.
_ANALYTICAL = re.compile(r"^(?:detect_|test_|_?probe_|main$)")

# A parameter naming a SUBSET of the work. If one of these is present the
# function is claiming to be incremental.
_SUBSET_PARAMS = frozenset({
    "paths", "files", "items", "subset", "ids", "changed", "touched",
    "rels", "targets", "keys", "names", "only",
})

# `delta` was tried here and removed: a function named compute_delta scans
# in order to FIND the delta -- scanning is its job, not a broken promise.
_INCREMENTAL_NAME = re.compile(
    r"(?:refresh|incremental|partial|targeted|scoped)", re.I)


def _is_absence_test(node: ast.AST) -> bool:
    """`not x`, `x is None`, or a boolean combination of those.

    A fast-path guard tests for ABSENT input. `if args.dry_run: return`
    also exits early but is a deliberate flag check placed after setup, and
    treating it as a fast path made cmd_migrate() the detector's only hit
    on its first run -- a false positive that would have taught reviewers
    to ignore the whole check.
    """
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return True
    if isinstance(node, ast.Compare):
        return any(isinstance(c, ast.Constant) and c.value is None
                   for c in node.comparators)
    if isinstance(node, ast.BoolOp):
        return all(_is_absence_test(v) for v in node.values)
    return False


def _guard_returns(stmt: ast.stmt) -> bool:
    """An `if ...: return/raise` with no else -- an early-exit guard."""
    if not isinstance(stmt, ast.If) or stmt.orelse:
        return False
    return any(isinstance(s, (ast.Return, ast.Raise)) for s in stmt.body)


def _names_in(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _calls_in(node: ast.AST) -> list[ast.Call]:
    return [n for n in ast.walk(node) if isinstance(n, ast.Call)]


def _call_name(call: ast.Call) -> str:
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def detect_widened_fast_path(code: str) -> list[AntiPatternHit]:
    """Corpus-scale work placed BEFORE an input-absence guard.

    Origin: `cascade.evaluate()` returned on an empty error before touching
    the event store. Widening its input contract to accept a structured key
    moved the store parse above that guard, so EVERY dispatch paid for it
    even with nothing to match -- 30 ms to 123 ms on the path that runs on
    every prompt. The guard still existed and still read correctly; it had
    simply stopped covering the common case.

    Flags a function that HAS an early-exit guard testing only its own
    parameters, where an expensive call precedes that guard. The guard is
    the proof the author intended a fast path; the ordering is the defect.
    """
    tree = _safe_parse(code)
    if tree is None:
        return []
    hits = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        params = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
        if not params:
            continue
        for i, stmt in enumerate(fn.body):
            if not _guard_returns(stmt):
                continue
            # Only an INPUT-absence guard counts: its condition must rest
            # solely on parameters, not on state the function computed.
            cond = _names_in(stmt.test)
            if not cond or not cond.issubset(params):
                continue
            if not _is_absence_test(stmt.test):
                continue
            for earlier in fn.body[:i]:
                for call in _calls_in(earlier):
                    name = _call_name(call)
                    if name and _GLOBAL_COST.match(name):
                        hits.append(AntiPatternHit(
                            detector="detect_widened_fast_path",
                            line=getattr(call, "lineno", fn.lineno),
                            snippet=f"{name}(...) before guard in {fn.name}()",
                            fix=(
                                f"Move `{name}(...)` BELOW the "
                                f"`if ...: return` guard in {fn.name}(). The "
                                "guard proves a fast path was intended; work "
                                "above it is paid on every no-input call. "
                                "Widening an input contract must not widen "
                                "the no-input path."
                            ),
                        ))
                        break
            break
    return hits


def detect_false_incrementality(code: str) -> list[AntiPatternHit]:
    """A function that takes a subset and then does global-scale work.

    Origin: `audit_cache.refresh_paths()` accepted the exact files to
    refresh and then called `build_stem_map()`, which walks the entire
    project. Refreshing ONE file cost 3016 ms -- nearly the full rebuild it
    existed to avoid. The loop was incremental; the operation was not.

    INCREMENTALITY IS AN END-TO-END COST PROPERTY, NOT A LOCAL LOOP ONE.
    """
    tree = _safe_parse(code)
    if tree is None:
        return []
    hits = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if _ANALYTICAL.match(fn.name):
            continue
        params = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
        claims = bool(params & _SUBSET_PARAMS) or bool(
            _INCREMENTAL_NAME.search(fn.name))
        if not claims:
            continue
        for call in _calls_in(fn):
            name = _call_name(call)
            if not name or not _GLOBAL_COST.match(name):
                continue
            # A call parameterised BY the subset is the incremental case.
            if _names_in(call) & (params & _SUBSET_PARAMS):
                continue
            hits.append(AntiPatternHit(
                detector="detect_false_incrementality",
                line=getattr(call, "lineno", fn.lineno),
                snippet=f"{name}(...) in {fn.name}()",
                fix=(
                    f"{fn.name}() presents itself as incremental but calls "
                    f"`{name}(...)`, whose cost is the whole corpus and does "
                    "not shrink with the subset. Measure the fixed cost, not "
                    "the loop: persist or cache the global part, or pass the "
                    "subset into it."
                ),
            ))
            break
    return hits


REGISTRY = (
    detect_bare_except,
    detect_silent_pass_in_except,
    detect_missing_type_hints,
    detect_magic_numbers,
    detect_mutable_defaults,
    detect_god_function,
    detect_hardcoded_paths,
    detect_widened_fast_path,
    detect_false_incrementality,
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
