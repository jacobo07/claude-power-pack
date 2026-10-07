#!/usr/bin/env python3
"""Compile a bounded reality-scan dossier with zero model calls.

WHY THIS EXISTS
---------------
Measured on EDD Phase 1 (m-ee81e1595007, 2026-10-06): a GSD phase researcher spent
26.8M processed tokens on 102 calls, one grep or sed per call, each call re-sending a
context that grew from 77k to 407k. The questions it answered -- which module owns a
concept, who imports it, where a keyword lives -- are answerable by deterministic
search. This tool runs that search once, below the model boundary, and writes:

  dossier.md   bounded (default 160 KB, about 40k tokens) -- what a worker reads
  refs.jsonl   every hit with path:line -- what a worker PAGES when the dossier is short

A worker that needs more than the dossier pages refs.jsonl or the file range it names;
it never guesses. Truncation is reported in the dossier, never silent.

CONCEPT DENOMINATOR
-------------------
Concepts are DISCOVERED from a contract file, never hand-listed: every section title in a
`=====`-fenced mission prompt (the form CPP mission prompts use), or every markdown
heading otherwise. A hand-curated list measures memory, not reality.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

STOP = frozenset("""a an and are as at be by for from has have in into is it its of on or that the
this to was were will with not no only must should may can every each all any per vs versus our
your their than then when where which who whom whose what why how do does done""".split())
FENCE = re.compile(r"^={8,}\s*$")
SKIP_DIRS = ("/.git/", "/node_modules/", "/__pycache__/", "/_audit_cache/", "/.claude/worktrees/")


def concepts_from_contract(text: str) -> list[dict]:
    """Section titles of a fenced contract, or markdown headings as a fallback."""
    lines = text.splitlines()
    titles = []
    for i in range(1, len(lines) - 1):
        if FENCE.match(lines[i - 1]) and FENCE.match(lines[i + 1]) and lines[i].strip():
            titles.append(lines[i].strip())
    if not titles:
        titles = [m.group(2).strip() for m in (re.match(r"^(#{1,3})\s+(.*)", ln) for ln in lines) if m]
    out, seen = [], set()
    for t in titles:
        key = re.sub(r"\W+", " ", t.lower()).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        words = [w for w in re.findall(r"[a-z][a-z\-]{3,}", t.lower()) if w not in STOP]
        out.append({"id": f"C-{len(out) + 1:02d}", "title": t, "keywords": words[:4]})
    return out


def rg(pattern: str, root: Path, globs: list[str]) -> list[tuple[str, int, str]]:
    """path, line, text for a case-insensitive regex; git grep keeps it to tracked files."""
    cmd = ["git", "-C", str(root), "grep", "-n", "-I", "-i", "-E", pattern, "--", *globs]
    p = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if p.returncode not in (0, 1):
        raise RuntimeError(f"git grep failed rc={p.returncode}: {p.stderr[:300]}")
    hits = []
    for ln in p.stdout.splitlines():
        parts = ln.split(":", 2)
        if len(parts) == 3 and parts[1].isdigit() and not any(s in "/" + parts[0] for s in SKIP_DIRS):
            hits.append((parts[0], int(parts[1]), parts[2].strip()[:160]))
    return hits


def module_map(root: Path, module_root: str) -> list[dict]:
    """Public defs of every .py under module_root and the files that import that module."""
    rows = []
    for f in sorted((root / module_root).rglob("*.py")):
        rel = f.relative_to(root).as_posix()
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as e:
            rows.append({"path": rel, "error": f"SyntaxError {e.lineno}"})
            continue
        doc = (ast.get_docstring(tree) or "").strip().splitlines()
        defs = [f"{n.name}:{n.lineno}" for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))
                and not n.name.startswith("_")]
        dotted = rel[:-3].replace("/", ".").removesuffix(".__init__")
        leaf = dotted.rsplit(".", 1)[-1]
        importers = sorted({h[0] for h in rg(rf"(import|from)\s+[\w.]*{re.escape(leaf)}\b", root, ["*.py"])
                            if h[0] != rel})
        rows.append({"path": rel, "doc": doc[0][:140] if doc else "", "defs": defs, "importers": importers})
    return rows


def concept_hits(root: Path, concept: dict, globs: list[str], per: int) -> list[dict]:
    """Files ranked by how many of the concept's keywords they contain (all must be >= 1 hit)."""
    files: dict[str, dict] = {}
    for kw in concept["keywords"]:
        for path, line, text in rg(re.escape(kw), root, globs):
            f = files.setdefault(path, {"path": path, "kws": set(), "first": (line, text), "n": 0})
            f["kws"].add(kw)
            f["n"] += 1
    need = min(2, len(concept["keywords"]))
    ranked = sorted((f for f in files.values() if len(f["kws"]) >= need),
                    key=lambda f: (-len(f["kws"]), -f["n"], f["path"]))
    return [{"path": f["path"], "line": f["first"][0], "text": f["first"][1],
             "kws": sorted(f["kws"]), "n": f["n"]} for f in ranked[:per]]


def run_cmd(cmd: list[str], root: Path, timeout: int) -> dict:
    try:
        p = subprocess.run(cmd, cwd=root, capture_output=True, text=True, errors="replace", timeout=timeout)
        return {"cmd": " ".join(cmd), "rc": p.returncode, "tail": (p.stdout + p.stderr)[-3000:]}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"cmd": " ".join(cmd), "rc": None, "tail": f"NOT RUN: {type(e).__name__}: {e}"}


def build(args) -> dict:
    root = Path(args.repo).resolve()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    concepts = concepts_from_contract(Path(args.contract).read_text(encoding="utf-8", errors="replace"))
    if not concepts:
        raise SystemExit("no concepts discovered in contract: refusing to emit an empty dossier")
    mods = [r for m in args.module_root for r in module_map(root, m)]
    hits = {c["id"]: concept_hits(root, c, args.glob, args.per_concept) for c in concepts}
    cmds = [run_cmd(c.split(), root, args.cmd_timeout) for c in args.cmd]
    with (out / "refs.jsonl").open("w", encoding="utf-8") as fh:
        for c in concepts:
            for h in hits[c["id"]]:
                fh.write(json.dumps({"concept": c["id"], **h}) + "\n")
        for r in mods:
            fh.write(json.dumps({"module": r}) + "\n")
    parts = [f"# Dossier: {root.name}\n",
             f"Contract: {args.contract} -> {len(concepts)} concepts. Zero model calls. "
             f"Raw hits: refs.jsonl (page it; never guess).\n"]
    parts.append("\n## Modules\n")
    for r in mods:
        parts.append(f"- `{r['path']}` {r.get('doc', '')} | defs: {', '.join(r.get('defs', [])[:12]) or '-'}"
                     f" | imported by: {', '.join(r.get('importers', [])[:8]) or 'NONE'}"
                     f"{' (+' + str(len(r['importers']) - 8) + ')' if len(r.get('importers', [])) > 8 else ''}\n")
    parts.append("\n## Concepts (top candidate owners by keyword co-occurrence; a candidate is not an owner)\n")
    for c in concepts:
        parts.append(f"\n### {c['id']} {c['title']}  [kw: {', '.join(c['keywords'])}]\n")
        for h in hits[c["id"]] or []:
            parts.append(f"- `{h['path']}:{h['line']}` ({len(h['kws'])}kw, {h['n']} hits) {h['text']}\n")
        if not hits[c["id"]]:
            parts.append("- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)\n")
    for r in cmds:
        parts.append(f"\n## Command: `{r['cmd']}` rc={r['rc']}\n```\n{r['tail']}\n```\n")
    for s in args.salvage:
        p = Path(s)
        if p.exists():
            heads = [ln for ln in p.read_text(encoding="utf-8", errors="replace").splitlines()
                     if ln.startswith("#")]
            parts.append(f"\n## Salvaged prior work: `{s}` ({p.stat().st_size} B; headings only, page for body)\n")
            parts.extend(h + "\n" for h in heads[:80])
    body, used, dropped = "", 0, 0
    for piece in parts:
        if used + len(piece.encode()) > args.max_bytes:
            dropped += 1
            continue
        body += piece
        used += len(piece.encode())
    if dropped:
        body += f"\n**TRUNCATED: {dropped} sections dropped at {args.max_bytes} B; page refs.jsonl.**\n"
    (out / "dossier.md").write_text(body, encoding="utf-8")
    summary = {"concepts": len(concepts), "modules": len(mods), "bytes": used, "dropped_sections": dropped,
               "concepts_without_candidate": [c["id"] for c in concepts if not hits[c["id"]]],
               "commands": [{k: r[k] for k in ("cmd", "rc")} for r in cmds]}
    (out / "dossier.summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--contract", required=True, help="mission prompt / spec whose sections are the concepts")
    ap.add_argument("--out", required=True)
    ap.add_argument("--module-root", action="append", default=[])
    ap.add_argument("--glob", action="append", default=None, help="git pathspecs to search (default: all)")
    ap.add_argument("--cmd", action="append", default=[], help="deterministic command whose tail is included")
    ap.add_argument("--salvage", action="append", default=[])
    ap.add_argument("--per-concept", type=int, default=6)
    ap.add_argument("--max-bytes", type=int, default=160_000)
    ap.add_argument("--cmd-timeout", type=int, default=300)
    a = ap.parse_args(argv)
    a.glob = a.glob or ["."]
    print(json.dumps(build(a), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
