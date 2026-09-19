# -*- coding: utf-8 -*-
"""Institutional closure audit -- does anything READ what we write?

The Reality Contract bans two states estate-wide: a producer with no consumer,
and a consumer with no producer. Nothing measured them, so this does.

Why an AST and not a grep: a grep over a file that both appends to and reads a
store cannot tell the two apart, so it reports whichever it looked for. A first
pass at this question (2026-09-19, UCR-CIF W0) bucketed any file containing an
append pattern as a writer and therefore reported `readers=0` for two live
stores. That number was an artifact of the instrument. It is recorded here
rather than quietly replaced.

Two instrument failures are recorded in the same spirit, because both produced a
confident-looking answer:

  1. Tokens taken from the filename STEM were simultaneously too coarse and too
     narrow -- `index` matched the English word everywhere, while
     `baseline_ledger` matched nothing. Tokens are now the filename WITH its
     extension, plus the repo-relative path.
  2. Matching against the unparsed call expression could not see a path held in
     a module constant, which is how most of this estate writes. Module-level
     string constants are now resolved (literals, f-strings, os.path.join and
     pathlib `/` chains) and substituted before matching.

Access is resolved at TWO levels, because most consumers never touch the path:

  L1 direct    -- open()/read_text/write_text/json.load/dump whose path
                  expression mentions the store, classified by mode.
  L2 indirect  -- a function performing an L1 access becomes an ACCESSOR; a
                  module importing it and calling it inherits that access class.

Three outcomes per store, never two:
  CLOSED        -- has a producer and a consumer
  OPEN_PRODUCER -- written, never read      (the Reality Contract violation)
  OPEN_CONSUMER -- read, never written      (reads fail or silently default)
  INERT         -- neither; on disk, untouched by code

Controls, because an empty finding list is also what a broken sweep produces:
  * population floor    -- a sweep that stopped seeing code cannot report clean
  * parse floor         -- syntax errors are counted, never silently skipped
  * positive control    -- known accessors must be found, by name
  * unresolved-path count -- open() sites whose path could not be resolved are
    REPORTED, so coverage is a measured number and not an assumption
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from collections import defaultdict

MIN_FILES_PARSED = 300
MIN_STORES = 5
SCAN_DIRS = ("tools", "modules", "hooks", "commands", "agents")
STORE_SUFFIX = (".jsonl", ".json")
STORE_NAME_HINT = re.compile(
    r"(ledger|registry|events|record|baseline|state|index|audit|history|queue)", re.I)
# Positive controls: real accessors this sweep must be able to find.
POSITIVE_CONTROLS = ("baseline_ledger.jsonl", "events.jsonl")

WRITE_FUNCS = {"dump", "dumps", "write_text", "write_bytes", "writelines", "write"}
READ_FUNCS = {"load", "loads", "read_text", "read_bytes", "readlines", "read"}
WRITE_MODES = re.compile(r"[waxo+]")


# ---------------------------------------------------------------- constants
class ConstResolver(ast.NodeVisitor):
    """Resolve module-level names that hold path-ish strings."""

    def __init__(self):
        self.table: dict[str, str] = {}

    def visit_Module(self, node):
        for stmt in node.body:
            if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                val = getattr(stmt, "value", None)
                if val is None:
                    continue
                s = self.lit(val)
                if s:
                    for t in targets:
                        if isinstance(t, ast.Name):
                            self.table[t.id] = s
        # do not descend; module scope only

    def lit(self, node, depth=0):
        """Best-effort string value of an expression, or '' when unknowable."""
        if depth > 6 or node is None:
            return ""
        if isinstance(node, ast.Constant):
            return str(node.value) if isinstance(node.value, str) else ""
        if isinstance(node, ast.Name):
            return self.table.get(node.id, "")
        if isinstance(node, ast.Attribute):
            return self.table.get(node.attr, "")
        if isinstance(node, ast.JoinedStr):
            return "/".join(filter(None, (self.lit(v, depth + 1) for v in node.values)))
        if isinstance(node, ast.BinOp):
            # Path(...) / "x" / "y"  and  "a" + "b"  and  "%s" % x
            return "/".join(filter(None, (self.lit(node.left, depth + 1),
                                          self.lit(node.right, depth + 1))))
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
            if name in ("join", "Path", "PurePath", "resolve", "expanduser", "absolute",
                        "parent", "with_name", "format", "joinpath", "str"):
                parts = [self.lit(a, depth + 1) for a in node.args]
                base = self.lit(fn.value, depth + 1) if isinstance(fn, ast.Attribute) else ""
                return "/".join(filter(None, [base] + parts))
        return ""


# ---------------------------------------------------------------- accessors
class Accessor(ast.NodeVisitor):
    def __init__(self, tokens, consts):
        self.tokens = tokens
        self.consts = consts
        self.stack: list[str] = []
        self.hits = defaultdict(set)
        self.module_hits = set()
        self.unresolved = 0          # path-taking calls that matched no store

    def _expand(self, node):
        try:
            blob = ast.unparse(node)
        except Exception:
            return ""
        extra = [v for n, v in self.consts.items() if re.search(r"\b" + re.escape(n) + r"\b", blob)]
        return (blob + " " + " ".join(extra)).replace("\\", "/").lower()

    def _match(self, node):
        low = self._expand(node)
        return {t for t in self.tokens if t in low}

    def _record(self, toks, cls):
        where = self.stack[-1] if self.stack else None
        for t in toks:
            (self.hits[where].add if where else self.module_hits.add)((t, cls))

    def visit_FunctionDef(self, node):
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node):
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
        path_taking = name == "open" or name in WRITE_FUNCS or name in READ_FUNCS
        toks = self._match(node) if path_taking else set()

        if path_taking and not toks and name == "open":
            self.unresolved += 1

        if toks:
            if name == "open":
                mode = ""
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    mode = str(node.args[1].value)
                for kw in node.keywords or []:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                self._record(toks, "W" if WRITE_MODES.search(mode) else "R")
            elif name in WRITE_FUNCS:
                self._record(toks, "W")
            else:
                self._record(toks, "R")
        self.generic_visit(node)


# ---------------------------------------------------------------- discovery
def discover_stores(repo: str):
    stores = {}
    for root, _d, files in os.walk(os.path.join(repo, "vault")):
        for f in files:
            if f.endswith(STORE_SUFFIX) and STORE_NAME_HINT.search(f):
                rel = os.path.relpath(os.path.join(root, f), repo).replace("\\", "/")
                stores[rel] = {"token": f.lower(), "path": rel.lower()}
    return stores


def analyse(repo: str, stores: dict):
    tok_to_stores = defaultdict(list)
    for rel, meta in stores.items():
        tok_to_stores[meta["token"]].append(rel)
    tokens = set(tok_to_stores)

    files = []
    for sub in SCAN_DIRS:
        for root, _d, fs in os.walk(os.path.join(repo, sub)):
            for f in fs:
                if f.endswith(".py"):
                    files.append(os.path.join(root, f))

    parsed, unresolved = 0, 0
    syntax_errors, accessors, src_cache = [], {}, {}
    direct = defaultdict(lambda: {"R": set(), "W": set()})

    for path in files:
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        rel = os.path.relpath(path, repo).replace("\\", "/")
        src_cache[rel] = src
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            syntax_errors.append((rel, str(e).split("(")[0].strip()))
            continue
        parsed += 1
        cr = ConstResolver()
        cr.visit(tree)
        v = Accessor(tokens, cr.table)
        v.visit(tree)
        unresolved += v.unresolved
        if not v.hits and not v.module_hits:
            continue
        accessors[rel] = v.hits
        for tok, cls in v.module_hits:
            direct[tok][cls].add(rel)
        for _fn, pairs in v.hits.items():
            for tok, cls in pairs:
                direct[tok][cls].add(rel)

    indirect = defaultdict(lambda: {"R": set(), "W": set()})
    for owner_rel, funcs in accessors.items():
        owner_mod = os.path.splitext(os.path.basename(owner_rel))[0]
        for fname, pairs in funcs.items():
            if not fname or fname.startswith("_"):
                continue
            call_pat = re.compile(r"\b" + re.escape(fname) + r"\s*\(")
            for rel, src in src_cache.items():
                if rel == owner_rel or owner_mod not in src:
                    continue
                if call_pat.search(src):
                    for tok, cls in pairs:
                        indirect[tok][cls].add(rel)

    return {"files_found": len(files), "parsed": parsed, "syntax_errors": syntax_errors,
            "direct": direct, "indirect": indirect, "tok_to_stores": tok_to_stores,
            "unresolved_open_sites": unresolved}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--fail-on-open-producer", action="store_true",
                    help="exit 1 when an OPEN_PRODUCER exists (ratchet mode)")
    args = ap.parse_args()
    repo = args.repo

    stores = discover_stores(repo)
    res = analyse(repo, stores)

    print("=== CONTROLS ===")
    print("python_files_found=%d  parsed=%d  syntax_errors=%d"
          % (res["files_found"], res["parsed"], len(res["syntax_errors"])))
    print("stores_discovered=%d" % len(stores))
    print("unresolved_open_sites=%d  (path not statically resolvable -- coverage caveat)"
          % res["unresolved_open_sites"])
    ok = True
    if res["parsed"] < MIN_FILES_PARSED:
        print("CONTROL_FAIL population floor: parsed %d < %d" % (res["parsed"], MIN_FILES_PARSED))
        ok = False
    if len(stores) < MIN_STORES:
        print("CONTROL_FAIL store floor: %d < %d" % (len(stores), MIN_STORES))
        ok = False
    touched = {t for t, d in res["direct"].items() if d["R"] or d["W"]}
    for probe in POSITIVE_CONTROLS:
        if probe not in touched:
            print("CONTROL_FAIL positive control '%s' not reached -- a detector that stopped "
                  "detecting reports the same clean sweep as one that works" % probe)
            ok = False
    print("CONTROLS=%s" % ("PASS" if ok else "FAIL"))
    for rel, msg in res["syntax_errors"][:5]:
        print("  unparsed: %s (%s)" % (rel, msg))

    print("\n=== PER-STORE CLOSURE ===")
    print("%-40s %5s %5s %5s %5s  %s" % ("STORE", "dW", "dR", "iW", "iR", "VERDICT"))
    rows = []
    for tok in sorted(tok for tok in res["tok_to_stores"]):
        d, i = res["direct"][tok], res["indirect"][tok]
        w, r = len(d["W"]) + len(i["W"]), len(d["R"]) + len(i["R"])
        verdict = ("CLOSED" if w and r else "OPEN_PRODUCER" if w
                   else "OPEN_CONSUMER" if r else "INERT")
        rows.append({"token": tok, "stores": res["tok_to_stores"][tok], "verdict": verdict,
                     "direct_writers": sorted(d["W"]), "direct_readers": sorted(d["R"]),
                     "indirect_writers": sorted(i["W"]), "indirect_readers": sorted(i["R"])})
        print("%-40s %5d %5d %5d %5d  %s" % (tok[:40], len(d["W"]), len(d["R"]),
                                             len(i["W"]), len(i["R"]), verdict))

    counts = defaultdict(int)
    for r in rows:
        counts[r["verdict"]] += 1
    print("\nCLOSED=%d  OPEN_PRODUCER=%d  OPEN_CONSUMER=%d  INERT=%d"
          % (counts["CLOSED"], counts["OPEN_PRODUCER"], counts["OPEN_CONSUMER"], counts["INERT"]))

    for label, v in (("OPEN PRODUCERS (written, never read)", "OPEN_PRODUCER"),
                     ("OPEN CONSUMERS (read, never written)", "OPEN_CONSUMER")):
        grp = [r for r in rows if r["verdict"] == v]
        if not grp:
            continue
        print("\n--- %s ---" % label)
        for r in grp:
            print("  %s  -> %s" % (r["token"], ", ".join(r["stores"][:2])))
            for p in (r["direct_writers"] + r["indirect_writers"])[:4]:
                print("      W: %s" % p)
            for p in (r["direct_readers"] + r["indirect_readers"])[:4]:
                print("      R: %s" % p)

    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump({"controls_pass": ok, "files_parsed": res["parsed"],
                       "stores_discovered": len(stores),
                       "unresolved_open_sites": res["unresolved_open_sites"],
                       "rows": rows}, fh, indent=2)
        print("\nwrote %s" % args.json_out)

    if not ok:
        return 2                                    # instrument failure OUTRANKS subject findings
    if args.fail_on_open_producer and counts["OPEN_PRODUCER"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
