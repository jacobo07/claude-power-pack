"""WU3 dependency packets (TOK-18 gen2, tranche context-runtime S5) -- offline, no live mutant.

Three projections of the source a historical unit needed, all built through tools/source_packet.py
(never a second builder):
  current     the unit's card plus every repo file the card names, at the builder's default limits
              (what a worker is handed today)
  naive trim  the same file list, raw bytes concatenated in card order, cut at the dependency
              projection's byte size (same budget, no dependency awareness)
  dependency  the files the unit's own commits changed, plus their direct imports and literal
              repo paths, at whole-file limits

Critical pages are an ORACLE taken from history: the .py files the unit's commits changed. The
dependency projection is seeded from that oracle, so it answers "can a packet carry what the work
touched", not "would a planner have found it beforehand". A packet is judged per critical page:
ADMIT (every page whole) . PAGE (a page is missing or cut but readable on disk: fault it in) .
DEOPT (a page is blocked, unreadable, or the builder could not answer: fall back to direct reads).
There is no silent pass: a page that is not whole is never ADMIT.

    python tools/wu3_packets.py [--json]
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import source_packet as sp  # noqa: E402

GIT = r"C:\Program Files\Git\cmd\git.exe"
UNITS = {
    "WU1": {"commits": ["0f07a3d7", "b67f5d8f"], "card": "vault/plans/tok18-tranche-context-runtime-2026-10-06.md"},
    "WU2": {"commits": ["4eea7a8c"], "card": "vault/programs/cognitive-economy/gen2/evidence/tranche/WU2-packet.md"},
}
WHOLE = {"maxExcerptBytes": 65536, "maxTotalBytes": 1048576}  # builder upper bounds (probed)
ADMIT, PAGE, DEOPT = "ADMIT", "PAGE", "DEOPT"
PATH_RE = re.compile(r"(?:tools|vault|modules)/[\w./-]+\.(?:py|json|md)")
LITERAL_RE = re.compile(r"[\w./-]+\.(?:py|json)")


def git(*args: str) -> str:
    return subprocess.run([GIT, "-C", str(ROOT), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def critical(unit: str) -> list[str]:
    pages: set[str] = set()
    for c in UNITS[unit]["commits"]:
        pages |= {p for p in git("show", "--name-only", "--format=", c).split() if p.endswith(".py")}
    return sorted(pages)


def drift(unit: str) -> list[str]:
    """Critical pages whose bytes on disk differ from the unit's last commit: history not reproducible."""
    last = UNITS[unit]["commits"][-1]
    return [p for p in critical(unit)
            if git("rev-parse", f"{last}:{p}").strip() != git("hash-object", p).strip()]


def _module_file(name: str) -> str | None:
    parts = name.split(".")
    for cand in (ROOT.joinpath(*parts).with_suffix(".py"), ROOT.joinpath(*parts, "__init__.py"),
                 ROOT / "tools" / f"{parts[0]}.py"):
        if cand.is_file():
            return cand.relative_to(ROOT).as_posix()
    return None


def deps(rel: str, literals: bool = True) -> set[str]:
    """Direct repo dependencies of one .py page: imports, plus path literals outside docstrings."""
    tree = ast.parse((ROOT / rel).read_text(encoding="utf-8", errors="replace"))
    docs = {id(n.body[0].value) for n in ast.walk(tree)
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    out: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            names = [n.module]
        elif literals and isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
            for s in LITERAL_RE.findall(n.value):
                hit = next((c for c in (ROOT / s, ROOT / "tools" / s) if c.is_file()), None)
                if hit:
                    out.add(hit.relative_to(ROOT).as_posix())
            continue
        else:
            continue
        out |= {f for f in map(_module_file, names) if f}
    out.discard(rel)
    return out


def projection(unit: str) -> list[str]:
    pages = set(critical(unit))
    for s in critical(unit):
        pages |= deps(s, literals=not Path(s).name.startswith("test_"))
    return sorted(pages)


def card_pages(unit: str) -> list[str]:
    card = UNITS[unit]["card"]
    named = dict.fromkeys(PATH_RE.findall((ROOT / card).read_text(encoding="utf-8", errors="replace")))
    return [card] + [p for p in named if p != card and (ROOT / p).is_file()]


def naive_trim(pages: list[str], budget: int) -> list[str]:
    """Pages wholly inside the first `budget` raw bytes of the concatenation, in the given order."""
    kept, used = [], 0
    for p in pages:
        used += (ROOT / p).stat().st_size
        if used > budget:
            break
        kept.append(p)
    return kept


def included(pk: sp.Packet) -> set[str]:
    return {e.get("path") for e in pk.manifest.get("entries") or [] if e.get("status") == "included"}


def judge(pk: sp.Packet, required: list[str], root: Path = ROOT) -> tuple[str, list[tuple[str, str, str]]]:
    if pk.verdict == sp.UNJUDGED:
        return DEOPT, [(p, DEOPT, "builder-unjudged") for p in required]
    by = {e.get("path"): e for e in pk.manifest.get("entries") or []}
    faults = []
    for p in required:
        e = by.get(p) or {}
        if e.get("status") == "included" and not e.get("redactedLines"):
            continue
        fetchable = (Path(root) / p).is_file() and e.get("status") != "blocked"
        why = e.get("status") or ("not-in-packet" if fetchable else "absent-from-disk")
        faults.append((p, PAGE if fetchable else DEOPT, why))
    if not faults:
        return ADMIT, []
    return (DEOPT if any(f[1] == DEOPT for f in faults) else PAGE), faults


def private(unit: str) -> set[str]:
    other = "WU2" if unit == "WU1" else "WU1"
    return set(critical(unit)) - set(projection(other))


def measure(unit: str) -> dict:
    crit = critical(unit)
    dep_pages = projection(unit)
    dep = sp.build(str(ROOT), dep_pages, **WHOLE)
    cur_pages = card_pages(unit)
    cur = sp.build(str(ROOT), cur_pages)
    dep_bytes = len(dep.prompt.encode("utf-8"))
    naive = naive_trim(cur_pages, dep_bytes)
    leak_other = private("WU2" if unit == "WU1" else "WU1")

    def row(name, pages, nbytes, whole):
        return {"projection": name, "pages": len(pages), "bytes": nbytes, "est_tokens": nbytes // 4,
                "critical_whole": f"{len(set(crit) & set(whole))}/{len(crit)}",
                "other_unit_private_pages": sorted(set(whole) & leak_other)}

    return {"unit": unit, "critical": crit, "drift": drift(unit), "dependency_pages": dep_pages,
            "current_pages": cur_pages, "naive_pages": naive,
            "rows": [row("current", cur_pages, len(cur.prompt.encode("utf-8")), included(cur)),
                     row("naive_trim", naive, sum((ROOT / p).stat().st_size for p in naive), naive),
                     row("dependency", dep_pages, dep_bytes, included(dep))],
            "dependency_judge": judge(dep, crit), "dependency_gaps": dep.gaps, "current_gaps": cur.gaps}


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    out = [measure(u) for u in UNITS]
    if argv and "--json" in argv:
        print(json.dumps(out, indent=1))
        return 0
    print("| unit | projection | pages | bytes | est. tokens (bytes/4) | critical whole | other unit's private pages |")
    print("|---|---|---|---|---|---|---|")
    for m in out:
        for r in m["rows"]:
            print(f"| {m['unit']} | {r['projection']} | {r['pages']} | {r['bytes']} | {r['est_tokens']} | "
                  f"{r['critical_whole']} | {', '.join(r['other_unit_private_pages']) or '-'} |")
    for m in out:
        print(f"{m['unit']} critical={m['critical']} drift={m['drift'] or 'none'}")
        print(f"{m['unit']} dependency_pages={m['dependency_pages']}")
        print(f"{m['unit']} current_pages={m['current_pages']}")
        print(f"{m['unit']} naive_pages={m['naive_pages']}")
        print(f"{m['unit']} dependency judge={m['dependency_judge'][0]} faults={m['dependency_judge'][1]}")
        print(f"{m['unit']} dependency gaps={m['dependency_gaps']}")
        print(f"{m['unit']} current gaps={m['current_gaps']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))