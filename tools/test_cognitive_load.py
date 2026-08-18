"""V-gates for the cognitive-load lens (UPAC residue R3)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

from modules.cognitive_load import (  # noqa: E402
    UNMEASURED_SIGNALS, measure, undeclared_entry_points,
)

_passes = 0
_fails = 0


def _ok(gate: str, ev: str) -> None:
    global _passes
    _passes += 1
    print(f"[PASS] {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global _fails
    _fails += 1
    print(f"[FAIL] {gate}: {ev}")


def _pkg(root: Path, name: str, init: str, extra: dict | None = None) -> None:
    d = root / "modules" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "__init__.py").write_text(init, encoding="utf-8")
    for fn, body in (extra or {}).items():
        (d / fn).write_text(body, encoding="utf-8")


def t_all_wins_over_defs() -> None:
    """__all__ is the author's own statement of the surface. Honouring it is the
    difference between measuring what is exported and what happens to be defined."""
    gate = "V-CL-ALL-WINS"
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _pkg(root, "declared",
             '"""doc."""\n__all__ = ["a", "b"]\n'
             "def a():\n    pass\ndef b():\n    pass\n"
             "def c():\n    pass\ndef e():\n    pass\n")
        rows = measure(root)
    row = next((r for r in rows if r["unit"] == "declared"), None)
    if row and row["own_public_symbols"] == 2:
        _ok(gate, "__all__ of 2 wins over 4 defined public names")
    else:
        _fail(gate, f"own_public_symbols={row['own_public_symbols'] if row else None}")


def t_entry_point_detection() -> None:
    gate = "V-CL-ENTRY-POINT"
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _pkg(root, "withdoc", '"""I say where to start."""\n')
        _pkg(root, "withall", '__all__ = ["x"]\nx = 1\n')
        _pkg(root, "silent", "x = 1\n")
        rows = measure(root)
    undeclared = set(undeclared_entry_points(rows))
    if undeclared == {"silent"}:
        _ok(gate, "docstring OR __all__ counts as declared; the silent package is "
                  "the only one flagged")
    else:
        _fail(gate, f"undeclared={sorted(undeclared)}")


def t_upstream_surface_counted() -> None:
    """Context cost must grow with what upstream EXPORTS, not merely with edge
    count -- depending on a unit that exports 40 names costs more than depending
    on one that exports 2."""
    gate = "V-CL-UPSTREAM-SURFACE"
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        wide = '"""wide."""\n__all__ = %s\n' % str([f"n{i}" for i in range(20)])
        _pkg(root, "wide", wide)
        _pkg(root, "narrow", '"""narrow."""\n__all__ = ["only"]\n')
        _pkg(root, "consumer_wide", '"""c."""\n',
             {"core.py": "from modules.wide import n0\n"})
        _pkg(root, "consumer_narrow", '"""c."""\n',
             {"core.py": "from modules.narrow import only\n"})
        rows = {r["unit"]: r for r in measure(root)}
    cw = rows.get("consumer_wide", {})
    cn = rows.get("consumer_narrow", {})
    if cw.get("upstream_surface") == 20 and cn.get("upstream_surface") == 1 \
            and cw.get("context_cost", 0) > cn.get("context_cost", 0):
        _ok(gate, f"upstream surface 20 vs 1 -> cost {cw['context_cost']} vs "
                  f"{cn['context_cost']}; edge count alone would tie them")
    else:
        _fail(gate, f"wide={cw.get('upstream_surface')} "
                    f"narrow={cn.get('upstream_surface')}")


def t_no_second_import_graph() -> None:
    """Two import graphs in one estate would be two sources of truth for the same
    fact, and the second to drift would be silently wrong."""
    gate = "V-CL-SHARED-GRAPH"
    src = (PP / "modules" / "cognitive_load" / "load.py").read_text(
        encoding="utf-8", errors="replace")
    imports_shared = (
        "from modules.architecture_horizon.horizon import build_graph" in src)
    # Assert the precise thing: this module must not DEFINE a graph builder.
    # The first cut also flagged any use of `ast.ImportFrom`, which appears
    # legitimately in _public_symbols to count names an __init__ re-exports --
    # a false positive that condemned surface counting as graph building.
    builds_own = ("def build_graph" in src or "def _build_graph" in src
                  or "def dependents" in src)
    if imports_shared and not builds_own:
        _ok(gate, "the dependency graph is imported from architecture_horizon; "
                  "this module defines no second builder")
    else:
        _fail(gate, f"imports_shared={imports_shared} builds_own={builds_own}")


def t_no_uqf_overlap() -> None:
    """modules/uqf owns file-local defects. A second opinion on an owned question
    is duplication, so the boundary is asserted mechanically, not promised."""
    gate = "V-CL-NO-UQF-OVERLAP"
    src = (PP / "modules" / "cognitive_load" / "load.py").read_text(
        encoding="utf-8", errors="replace")
    # Detector CONCEPTS uqf owns. Present in the non-duplication note as prose;
    # what must be absent is any computation of them.
    forbidden = ["detect_bare_except", "detect_missing_type_hints",
                 "detect_silent_pass_in_except", "detect_magic_numbers",
                 "detect_mutable_defaults", "detect_god_function",
                 "detect_hardcoded_paths", "modules.uqf", "from .uqf"]
    hits = [f for f in forbidden if f in src]
    if not hits:
        _ok(gate, f"none of the {len(forbidden)} uqf detectors is computed or "
                  "imported here")
    else:
        _fail(gate, f"overlaps uqf: {hits}")


def t_unmeasured_declared() -> None:
    gate = "V-CL-UNMEASURED-DECLARED"
    required = {"setup_time", "feedback_latency", "error_message_quality",
                "debugging_affordances"}
    missing = required - set(UNMEASURED_SIGNALS)
    unreasoned = [k for k, v in UNMEASURED_SIGNALS.items() if not str(v).strip()]
    if not missing and not unreasoned:
        _ok(gate, f"{len(UNMEASURED_SIGNALS)} signals declared unmeasured, each "
                  "with a reason")
    else:
        _fail(gate, f"missing={sorted(missing)} unreasoned={unreasoned}")


def t_measures_real_repo() -> None:
    gate = "V-CL-DISCOVERS"
    rows = measure(PP)
    undeclared = undeclared_entry_points(rows)
    if len(rows) > 50 and rows and rows[0]["context_cost"] > 0:
        _ok(gate, f"{len(rows)} units; highest cost {rows[0]['unit']}="
                  f"{rows[0]['context_cost']}; {len(undeclared)} unit(s) declare "
                  "no entry point")
    else:
        _fail(gate, f"units={len(rows)}")


def main() -> int:
    for t in (t_all_wins_over_defs,
              t_entry_point_detection,
              t_upstream_surface_counted,
              t_no_second_import_graph,
              t_no_uqf_overlap,
              t_unmeasured_declared,
              t_measures_real_repo):
        t()
    total = _passes + _fails
    verdict = "PASS" if _fails == 0 else "FAIL"
    print(f"CL_PASS={_passes}/{total}  threshold={total}/{total}  VERDICT={verdict}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
