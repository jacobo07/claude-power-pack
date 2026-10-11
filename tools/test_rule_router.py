"""V-RR-* gates for tools/rule_router.py (rule router: unit -> deferred-backlog D-rows)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools.rule_router as rr  # noqa: E402

PASSES: list[str] = []
FAILS: list[str] = []

BACKLOG = "".join(
    f"## D{n} \u2014 title {n}\n\nbody line a {n}\nbody line b {n}\n\n" for n in (20, 21, 22, 23, 24, 25, 26, 27)
)


def check(name: str, ok: bool, ev: str = "") -> None:
    (PASSES if ok else FAILS).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  {ev}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="rr_"))
    bl = tmp / "deferred-backlog.md"
    bl.write_text(BACKLOG, encoding="utf-8")
    log = tmp / "rr.log"

    rows = rr.route({"goal": "cp50-c2", "unit": "C2c"}, backlog=bl, log=log)
    ids = [r["id"] for r in rows]
    check("V-RR-SURFACE", ids == ["D21", "D22", "D23", "D24", "D26"], str(ids))
    check("V-RR-BOUNDED", all("body line a" in r["text"] and "title" in r["text"] for r in rows)
          and not any("D25" in r["text"] or "D27" in r["text"] for r in rows), "row text stops at next heading")
    check("V-RR-ROOT-KEY", [r["id"] for r in rr.route({"root": r"C:\x\wt_cp50_c2"}, backlog=bl, log=log)] == ids,
          "root path keys the same set")

    none = rr.route({"goal": "ukai", "unit": "U1"}, backlog=bl, log=log)
    check("V-RR-UNRELATED", none == [], str(none))

    try:
        gone = rr.route({"goal": "cp50-c2"}, backlog=tmp / "missing.md", log=log)
    except Exception as e:  # a raise is a gate failure, not a crash
        gone = e
    check("V-RR-MISSING-SOFT", gone == [], f"got {gone!r}")
    check("V-RR-MISSING-LOGGED", log.exists() and "missing" in log.read_text(encoding="utf-8"), "log line written")

    partial = tmp / "partial.md"
    partial.write_text("## D22 \u2014 only\nx\n", encoding="utf-8")
    got = [r["id"] for r in rr.route({"goal": "cp50-c2"}, backlog=partial, log=log)]
    check("V-RR-ROW-ABSENT-LOGGED", got == ["D22"] and "D21" in log.read_text(encoding="utf-8"), str(got))

    print(f"RR_PASS={len(PASSES)}/{len(PASSES) + len(FAILS)}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
