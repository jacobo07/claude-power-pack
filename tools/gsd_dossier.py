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
import shutil
import subprocess
import sys
from pathlib import Path

_WIN_GIT = Path(r"C:\Program Files\Git\cmd\git.exe")   # git is absent from a -NonInteractive PowerShell PATH
GIT = shutil.which("git") or (str(_WIN_GIT) if _WIN_GIT.exists() else "git")

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
    cmd = [GIT, "-C", str(root), "grep", "-n", "-I", "-i", "-E", pattern, "--", *globs]
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


# ---------------------------------------------------------------------------------------------
# PROOF OF NON-WORK (A-G1): every obligation gets a disposition before any worker is armed.
# A claim that work is unnecessary is admitted only when a deterministic probe re-checks it now.
# ---------------------------------------------------------------------------------------------
DISPOSITIONS = ("NO_WORK", "ALREADY_SATISFIED", "REUSE_EXISTING", "MERGE", "DETERMINISTIC",
                "CERTIFIED_CAPABILITY", "CHEAP_COGNITION", "STRONG_COGNITION", "FRONTIER_COGNITION",
                "DEFERRED_EXTERNAL", "UNKNOWN")
NEEDS_PROBE = ("NO_WORK", "ALREADY_SATISFIED", "REUSE_EXISTING", "MERGE", "CERTIFIED_CAPABILITY")


def _abs(root: Path, p: str) -> Path:
    q = Path(p)
    return q if q.is_absolute() else root / q


def run_probe(probe: dict, root: Path) -> dict:
    """One deterministic re-check. Never raises: an instrument that cannot run reports ok=False."""
    kind = probe.get("kind")
    try:
        if kind == "file_exists":
            ok = _abs(root, probe["path"]).exists()
            return {"kind": kind, "ok": ok, "detail": probe["path"] + (" exists" if ok else " MISSING")}
        if kind == "commit":
            repo = _abs(root, probe.get("repo", "."))
            p = subprocess.run([GIT, "-C", str(repo), "merge-base", "--is-ancestor", probe["sha"], probe["ref"]],
                               capture_output=True, text=True, errors="replace", timeout=60)
            return {"kind": kind, "ok": p.returncode == 0,
                    "detail": f"{probe['sha']} ancestor-of {probe['ref']} rc={p.returncode} {p.stderr.strip()[:120]}"}
        if kind == "grep":
            target, rx = _abs(root, probe["path"]), re.compile(probe["pattern"], re.M)
            files = sorted(f for f in target.rglob("*") if f.is_file()) if target.is_dir() else [target]
            hits = [f.as_posix() for f in files if f.exists() and rx.search(f.read_text(encoding="utf-8", errors="replace"))]
            return {"kind": kind, "ok": bool(hits), "detail": f"{len(hits)} hit(s) for /{probe['pattern']}/ in {probe['path']}"}
        if kind == "cmd_rc0":
            cmd = probe["cmd"] if isinstance(probe["cmd"], list) else probe["cmd"].split()
            p = subprocess.run(cmd, cwd=_abs(root, probe.get("cwd", ".")), capture_output=True, text=True,
                               errors="replace", timeout=int(probe.get("timeout", 120)))
            marker_ok = probe["marker"] in (p.stdout + p.stderr)
            return {"kind": kind, "ok": p.returncode == 0 and marker_ok,
                    "detail": f"rc={p.returncode} marker {'found' if marker_ok else 'ABSENT'}: {probe['marker']}"}
        return {"kind": kind, "ok": False, "detail": f"unknown probe kind {kind!r}"}
    except (OSError, KeyError, re.error, subprocess.TimeoutExpired) as e:
        return {"kind": kind, "ok": False, "detail": f"PROBE ERROR {type(e).__name__}: {e}"}


def dispose(rows: list, expect: list, root: Path) -> dict:
    """Final disposition per obligation, plus the structural errors --check turns into exit 1."""
    errors, out, seen = [], [], set()
    ids_present = {r.get("id") for r in rows if isinstance(r, dict)}
    for i in expect:
        if i not in ids_present:
            errors.append(f"MISSING {i}: expected obligation has no row")
    for n, r in enumerate(rows):
        oid = r.get("id") if isinstance(r, dict) else None
        if not oid or not r.get("claimed"):
            errors.append(f"MISSING row#{n}: no id or no claimed disposition")
            continue
        if oid in seen:
            errors.append(f"DUPLICATE {oid}")
            continue
        seen.add(oid)
        claimed, final, reason, results = r["claimed"], r["claimed"], "", []
        if claimed not in DISPOSITIONS:
            errors.append(f"VOCAB {oid}: {claimed!r} is outside the closed set")
            final, reason = "UNKNOWN", f"claim {claimed!r} outside vocabulary"
        elif claimed in NEEDS_PROBE:
            results = [run_probe(p, root) for p in r.get("evidence") or []]
            if claimed == "MERGE" and r.get("merge_into") not in ids_present | set(expect):
                errors.append(f"MERGE {oid}: target {r.get('merge_into')!r} is not an obligation id")
                final, reason = "UNKNOWN", "MERGE without a valid target"
            elif not results:
                errors.append(f"PROBE {oid}: {claimed} claimed with no evidence")
                final, reason = "UNKNOWN", "no evidence entry"
            elif not all(x["ok"] for x in results):
                errors.append(f"PROBE {oid}: {claimed} failed its probe")
                final, reason = "UNKNOWN", "; ".join(x["detail"] for x in results if not x["ok"])
        elif claimed == "UNKNOWN":
            reason = r.get("reason", "")
        out.append({"id": oid, "block": r.get("block", ""), "claimed": claimed, "disposition": final,
                    "reason": reason, "merge_into": r.get("merge_into"), "probes": results})
    counts = {d: sum(1 for o in out if o["disposition"] == d) for d in DISPOSITIONS}
    undisposed = sum(1 for e in errors if e.startswith(("MISSING", "DUPLICATE")))
    return {"obligations": out, "counts": {k: v for k, v in counts.items() if v}, "errors": errors,
            "unknown": counts["UNKNOWN"], "undisposed": undisposed}


def dispose_main(argv) -> int:
    ap = argparse.ArgumentParser(prog="gsd_dossier.py dispose")
    ap.add_argument("--obligations", required=True, help="json list, or {expect:[ids], obligations:[...]}")
    ap.add_argument("--out", required=True)
    ap.add_argument("--repo", default=".", help="root that relative probe paths resolve against")
    ap.add_argument("--check", action="store_true", help="exit 1 on any structural error or failed probe")
    a = ap.parse_args(argv)
    data = json.loads(Path(a.obligations).read_text(encoding="utf-8-sig"))
    rows, expect = (data["obligations"], data.get("expect", [])) if isinstance(data, dict) else (data, [])
    res = dispose(rows, expect, Path(a.repo).resolve())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dispositions.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for e in res["errors"]:
        print("ERROR", e)
    print(f"DISPOSE counts={json.dumps(res['counts'], sort_keys=True)} unknown={res['unknown']} "
          f"undisposed={res['undisposed']}")
    return 1 if a.check and res["errors"] else 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "dispose":
        return dispose_main(argv[1:])
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
