#!/usr/bin/env python3
"""V-gates for modules/craif/adapter_conformance.py.

The load-bearing tests here are the NEGATIVE ones. A conformance checker that has
only ever been observed to pass is indistinguishable from one that cannot fail, and
the estate has already paid for that mistake twice -- a kill switch whose router
named a section present in zero files, and a trigger class carrying zero rules.
Each defect class therefore gets a fixture that provokes it.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.craif.adapter_conformance import (  # noqa: E402
    CONFORMING,
    NONCONFORMING,
    CatalogueError,
    discover_packages,
    discover_schema,
    run,
)

_PASS = 0
_FAIL = 0


def _ok(gate: str, evidence: str) -> None:
    global _PASS
    _PASS += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _FAIL
    _FAIL += 1
    print(f"  [FAIL] {gate}: {diag}")


_SCHEMA = ("Schema per package: **Owner** · **Mechanism Strengthened** · "
           "**Missing Adapter/Contract** · **Done-Gate**\n\n")


def _pkg(n: int, title: str, owner: str, *, drop: str = "", empty: str = "") -> str:
    rows = {
        "Owner": owner,
        "Mechanism strengthened": "some mechanism.",
        "Missing adapter/contract": "some gap.",
        "Done-gate": "some gate.",
    }
    if drop:
        rows.pop(drop, None)
    if empty:
        rows[empty] = ""
    body = "".join(f"**{k}**: {v}\n\n" for k, v in rows.items())
    return f"## {n}. {title}\n\n{body}---\n\n"


def _write(tmp: Path, text: str) -> Path:
    p = tmp / "CAT.md"
    p.write_text(text, encoding="utf-8")
    return p


def main() -> int:
    print("=== V-CRAIF-ADAPTER gates ===")

    # --- The real catalogue: discovery, not a hand-written expectation ---------
    verdicts = run(root=_ROOT)
    n = len(verdicts)
    if n >= 8:
        _ok("V-CRAIF-ADAPTER-DISCOVER",
            f"{n} seams discovered from the document's own headings")
    else:
        _fail("V-CRAIF-ADAPTER-DISCOVER", f"expected >=8 seams, discovered {n}")

    cat = (_ROOT / "vault/knowledge_base/craif/"
           "CRAIF_D2A_REINFORCEMENT_PACKAGES.md").read_text(encoding="utf-8-sig")
    schema = discover_schema(cat)
    if len(schema) >= 8 and any(s.lower().startswith("owner") for s in schema):
        _ok("V-CRAIF-ADAPTER-SCHEMA",
            f"{len(schema)} fields read from the catalogue's own schema sentence")
    else:
        _fail("V-CRAIF-ADAPTER-SCHEMA", f"schema discovered as {schema}")

    if len(discover_packages(cat)) == n:
        _ok("V-CRAIF-ADAPTER-STABLE", f"package discovery reproducible at {n}")
    else:
        _fail("V-CRAIF-ADAPTER-STABLE", "package count differs between calls")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "modules").mkdir()
        (tmp / "modules" / "real.py").write_text("x = 1\n", encoding="utf-8")

        # --- NEGATIVE 1: a field the schema requires is absent ----------------
        p = _write(tmp, _SCHEMA + _pkg(1, "Gap", "`modules/real.py`",
                                       drop="Missing adapter/contract"))
        v = run(root=tmp, catalogue=p)[0]
        if v.verdict == NONCONFORMING and v.missing_fields:
            _ok("V-CRAIF-ADAPTER-MISSING-FIELD",
                f"caught {v.missing_fields}")
        else:
            _fail("V-CRAIF-ADAPTER-MISSING-FIELD",
                  f"a package missing a schema field scored {v.verdict}")

        # --- NEGATIVE 2: field declared but carries nothing -------------------
        p = _write(tmp, _SCHEMA + _pkg(1, "Empty", "`modules/real.py`",
                                       empty="Done-gate"))
        v = run(root=tmp, catalogue=p)[0]
        if v.verdict == NONCONFORMING and v.empty_fields:
            _ok("V-CRAIF-ADAPTER-EMPTY-FIELD", f"caught {v.empty_fields}")
        else:
            _fail("V-CRAIF-ADAPTER-EMPTY-FIELD",
                  f"an empty declared field scored {v.verdict}")

        # --- NEGATIVE 3: Owner names a path that is not on disk ---------------
        p = _write(tmp, _SCHEMA + _pkg(1, "Moved", "`modules/vanished.py`"))
        v = run(root=tmp, catalogue=p)[0]
        if v.verdict == NONCONFORMING and v.missing_paths == ["modules/vanished.py"]:
            _ok("V-CRAIF-ADAPTER-DEAD-OWNER", "caught modules/vanished.py")
        else:
            _fail("V-CRAIF-ADAPTER-DEAD-OWNER",
                  f"a dead Owner path scored {v.verdict} / {v.missing_paths}")

        # --- NEGATIVE 4: Owner is prose, so nothing is verifiable -------------
        p = _write(tmp, _SCHEMA + _pkg(1, "Prose", "the JIT skill loader and SKILL.md"))
        v = run(root=tmp, catalogue=p)[0]
        if v.verdict == NONCONFORMING and v.unverifiable_owner:
            _ok("V-CRAIF-ADAPTER-PROSE-OWNER",
                "an Owner naming no repo path is a defect, not a silent pass")
        else:
            _fail("V-CRAIF-ADAPTER-PROSE-OWNER",
                  f"a prose Owner scored {v.verdict}")

        # --- POSITIVE: a fully conforming seam still passes -------------------
        p = _write(tmp, _SCHEMA + _pkg(1, "Good", "`modules/real.py`"))
        v = run(root=tmp, catalogue=p)[0]
        if v.verdict == CONFORMING and not v.reasons:
            _ok("V-CRAIF-ADAPTER-POSITIVE", "a complete seam scores CONFORMING")
        else:
            _fail("V-CRAIF-ADAPTER-POSITIVE",
                  f"a complete seam scored {v.verdict}: {v.reasons}")

        # --- FAIL-LOUD 1: no schema sentence -> error, never a pass -----------
        p = _write(tmp, _pkg(1, "NoSchema", "`modules/real.py`"))
        try:
            run(root=tmp, catalogue=p)
            _fail("V-CRAIF-ADAPTER-NO-SCHEMA",
                  "a document with no schema sentence returned verdicts")
        except CatalogueError:
            _ok("V-CRAIF-ADAPTER-NO-SCHEMA",
                "empty vocabulary raises instead of reporting a clean run")

        # --- FAIL-LOUD 2: schema but zero packages -> error, never 0/0 -------
        p = _write(tmp, _SCHEMA)
        try:
            run(root=tmp, catalogue=p)
            _fail("V-CRAIF-ADAPTER-NO-PACKAGES", "zero packages returned a pass")
        except CatalogueError:
            _ok("V-CRAIF-ADAPTER-NO-PACKAGES",
                "0 discovered seams raises rather than scoring 0/0 clean")

        # --- FAIL-LOUD 3: catalogue absent ------------------------------------
        try:
            run(root=tmp, catalogue=tmp / "absent.md")
            _fail("V-CRAIF-ADAPTER-ABSENT", "a missing catalogue returned verdicts")
        except CatalogueError:
            _ok("V-CRAIF-ADAPTER-ABSENT", "a missing catalogue raises")

    total = _PASS + _FAIL
    print(f"\nCRAIF_ADAPTER_PASS={_PASS}/{total}  threshold={total}/{total}")
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
