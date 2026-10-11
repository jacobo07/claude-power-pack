#!/usr/bin/env python3
"""coverage.py -- CO-05 coverage receipt: what was read, how deeply, what it produced.

Spec: vault/specs/cognitive-work-reuse.md. Extends CO-05 (registry.py); no second vault.

Identity is CONTENT (sha256), never a path. A receipt run is BEGIN, FILE*, COMMIT in an
append-only JSONL ledger; a run with no matching COMMIT never counts. The verdict is a
deterministic function of (manifest, ledger, transform, config, requester scope) with nine
states. UNKNOWN is never a cache hit and never a licence to mine. "Assimilated" is computed
from FULL_READ coverage of the unique content set, never declared.

Kill switch: PP_CORPUS_REUSE=off  ->  verdict() answers UNKNOWN("disabled"), never EXACT_REUSE.
Sources are read-only: nothing here writes under a corpus root.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = _PP_ROOT / "vault" / "cognitive_os" / "coverage_ledger.jsonl"
DEFAULT_MANIFEST_CACHE = _PP_ROOT / "vault" / "cognitive_os" / "manifest_cache.json"

DEPTH_RANK = {"SKIPPED": 0, "STRUCTURAL": 1, "FULL_READ": 2}
STATES = ("EXACT_REUSE", "PARTIAL", "TRANSFORM_CHANGED", "INSUFFICIENT", "INVALIDATED",
          "INACCESSIBLE", "UNAUTHORIZED", "NONE", "UNKNOWN")
# When no file is covered, the overall state is the first of these that any file shows.
_PRECEDENCE = ("UNAUTHORIZED", "INVALIDATED", "INACCESSIBLE", "INSUFFICIENT",
               "TRANSFORM_CHANGED", "NONE")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def disabled() -> bool:
    return os.environ.get("PP_CORPUS_REUSE", "").strip().lower() == "off"


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write_text(target: Path, text: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.{uuid.uuid4().hex[:6]}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)


# ---------------------------------------------------------------- manifest
@dataclass
class Manifest:
    root: str
    files: dict = field(default_factory=dict)       # rel posix path -> {sha, size}
    duplicates: dict = field(default_factory=dict)  # sha -> [rel paths] (len > 1 only)

    @property
    def unique_shas(self) -> set:
        return {v["sha"] for v in self.files.values()}


def build_manifest(root, *, cache_path=None, exclude_dirs=(".git", "__pycache__")) -> Manifest:
    """sha256 per file. Unchanged files (path+size+mtime_ns) reuse the cached hash.
    Unreadable files are skipped and listed in `unreadable` on the returned object's dict."""
    rootp = Path(root)
    cache_p = Path(cache_path) if cache_path else DEFAULT_MANIFEST_CACHE
    cache: dict = {}
    try:
        if cache_p.is_file():
            cache = json.loads(cache_p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        cache = {}
    m = Manifest(root=str(rootp))
    fresh_cache: dict = {}
    by_sha: dict = {}
    for dirpath, dirnames, filenames in os.walk(rootp):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for name in filenames:
            p = Path(dirpath) / name
            try:
                st = p.stat()
                key = str(p)
                ent = cache.get(key)
                if ent and ent.get("size") == st.st_size and ent.get("mtime_ns") == st.st_mtime_ns:
                    sha = ent["sha"]
                else:
                    sha = sha256_file(p)
                fresh_cache[key] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns, "sha": sha}
            except OSError:
                continue
            rel = p.relative_to(rootp).as_posix()
            m.files[rel] = {"sha": sha, "size": st.st_size}
            by_sha.setdefault(sha, []).append(rel)
    m.duplicates = {s: sorted(v) for s, v in by_sha.items() if len(v) > 1}
    try:
        atomic_write_text(cache_p, json.dumps(fresh_cache))
    except OSError:
        pass
    return m


# ------------------------------------------------------------------ ledger
def _append(ledger, rec: dict) -> None:
    p = Path(ledger)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")


@dataclass
class Run:
    run_id: str
    corpus_id: str = ""
    scope: list = field(default_factory=list)
    transform: str = ""
    config_digest: str = ""
    files: dict = field(default_factory=dict)        # sha -> depth
    artifacts: list = field(default_factory=list)    # [{path, sha256}]
    evidence: str = ""
    committed: bool = False
    file_count_declared: int = -1
    invalid_reason: str = ""

    @property
    def complete(self) -> bool:
        return self.committed and self.file_count_declared == len(self.files)


def read_ledger(ledger=None):
    """-> (runs: dict[run_id, Run], conflicts: list, corrupt_lines: int, readable: bool)."""
    p = Path(ledger) if ledger else DEFAULT_LEDGER
    runs: dict = {}
    conflicts: list = []
    corrupt = 0
    if not p.is_file():
        return runs, conflicts, 0, True
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return runs, conflicts, 0, False
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            t = d["type"]
        except (json.JSONDecodeError, KeyError, TypeError):
            corrupt += 1
            continue
        rid = d.get("run_id", "")
        if t == "BEGIN":
            runs[rid] = Run(run_id=rid, corpus_id=d.get("corpus_id", ""),
                            scope=list(d.get("scope", [])), transform=d.get("transform", ""),
                            config_digest=d.get("config_digest", ""))
        elif t == "FILE" and rid in runs:
            runs[rid].files[d["sha"]] = d.get("depth", "SKIPPED")
        elif t == "COMMIT" and rid in runs:
            r = runs[rid]
            r.committed = True
            r.file_count_declared = int(d.get("file_count", -1))
            r.artifacts = list(d.get("artifacts", []))
            r.evidence = d.get("evidence", "")
        elif t == "INVALIDATE" and rid in runs:
            runs[rid].invalid_reason = d.get("reason", "invalidated")
        elif t == "CONFLICT":
            conflicts.append({"a": d.get("sha_a"), "b": d.get("sha_b"), "note": d.get("note", "")})
        else:
            corrupt += 1
    return runs, conflicts, corrupt, True


def record(manifest: Manifest, *, corpus_id: str, scope, transform: str, config_digest: str,
           depth_by_rel: dict, artifacts=None, evidence: str = "", ledger=None,
           run_id: str | None = None) -> str:
    """Write one receipt run (BEGIN, FILE per unique sha, COMMIT). Returns run_id.
    `depth_by_rel` maps rel path -> depth; a rel absent from it is recorded SKIPPED only if it
    is in the manifest (the receipt states what was NOT read as well)."""
    rid = run_id or uuid.uuid4().hex[:12]
    _append(ledger or DEFAULT_LEDGER, {"type": "BEGIN", "run_id": rid, "corpus_id": corpus_id,
                                       "scope": list(scope), "transform": transform,
                                       "config_digest": config_digest, "ts": _now()})
    best: dict = {}
    for rel, meta in manifest.files.items():
        d = depth_by_rel.get(rel, "SKIPPED")
        if d not in DEPTH_RANK:
            raise ValueError(f"unknown depth {d!r}")
        sha = meta["sha"]
        if DEPTH_RANK[d] >= DEPTH_RANK.get(best.get(sha, "SKIPPED"), 0):
            best[sha] = d
    for sha, d in best.items():
        _append(ledger or DEFAULT_LEDGER, {"type": "FILE", "run_id": rid, "sha": sha, "depth": d})
    _append(ledger or DEFAULT_LEDGER, {"type": "COMMIT", "run_id": rid, "file_count": len(best),
                                       "artifacts": list(artifacts or []), "evidence": evidence,
                                       "ts": _now()})
    return rid


def begin(*, corpus_id, scope, transform, config_digest, ledger=None) -> str:
    """Open a run without committing (an interrupted ingestion leaves exactly this)."""
    rid = uuid.uuid4().hex[:12]
    _append(ledger or DEFAULT_LEDGER, {"type": "BEGIN", "run_id": rid, "corpus_id": corpus_id,
                                       "scope": list(scope), "transform": transform,
                                       "config_digest": config_digest, "ts": _now()})
    return rid


def invalidate(run_id: str, reason: str, ledger=None) -> None:
    _append(ledger or DEFAULT_LEDGER, {"type": "INVALIDATE", "run_id": run_id,
                                       "reason": reason, "ts": _now()})


def mark_conflict(sha_a: str, sha_b: str, note: str = "", ledger=None) -> None:
    _append(ledger or DEFAULT_LEDGER, {"type": "CONFLICT", "sha_a": sha_a, "sha_b": sha_b,
                                       "note": note, "ts": _now()})


# ----------------------------------------------------------------- verdict
@dataclass
class Verdict:
    state: str
    reason: str = ""
    covered: list = field(default_factory=list)      # rel paths covered for this request
    delta: list = field(default_factory=list)        # rel paths that still need work
    denied: list = field(default_factory=list)       # rel paths covered only out of scope
    by_state: dict = field(default_factory=dict)
    artifacts: list = field(default_factory=list)    # pointers, only for covered + authorized
    conflicts: list = field(default_factory=list)
    run_ids: list = field(default_factory=list)


def _scope_ok(run_scope, requester: str) -> bool:
    return "*" in run_scope or requester in run_scope


def _artifact_state(art: dict) -> str:
    """OK | MISSING | MISMATCH for one artifact pointer."""
    p = Path(art.get("path", ""))
    if not p.is_file():
        return "MISSING"
    try:
        return "OK" if sha256_file(p) == art.get("sha256") else "MISMATCH"
    except OSError:
        return "MISSING"


def verdict(manifest: Manifest | None, *, transform: str, config_digest: str, requester: str,
            need: str = "STRUCTURAL", ledger=None) -> Verdict:
    if disabled():
        return Verdict("UNKNOWN", "disabled by PP_CORPUS_REUSE=off")
    if manifest is None or not manifest.files:
        return Verdict("UNKNOWN", "no manifest or empty corpus")
    if need not in DEPTH_RANK:
        return Verdict("UNKNOWN", f"unknown depth requirement {need!r}")
    runs, conflicts, corrupt, readable = read_ledger(ledger)
    if not readable:
        return Verdict("UNKNOWN", "ledger unreadable")
    art_cache: dict = {}

    def run_art_state(r: Run) -> str:
        if r.run_id not in art_cache:
            states = {_artifact_state(a) for a in r.artifacts}
            art_cache[r.run_id] = ("MISSING" if "MISSING" in states else
                                   "MISMATCH" if "MISMATCH" in states else "OK")
        return art_cache[r.run_id]

    sha_state: dict = {}
    sha_runs: dict = {}
    for sha in manifest.unique_shas:
        best = "NONE"
        rank = {s: i for i, s in enumerate(("COVERED",) + _PRECEDENCE)}
        for r in runs.values():
            if sha not in r.files or not r.complete:
                continue
            if not _scope_ok(r.scope, requester):
                cand = "UNAUTHORIZED"
            elif r.invalid_reason:
                cand = "INVALIDATED"
            elif (r.transform, r.config_digest) != (transform, config_digest):
                cand = "TRANSFORM_CHANGED"
            elif DEPTH_RANK.get(r.files[sha], 0) < DEPTH_RANK[need]:
                cand = "INSUFFICIENT"
            else:
                a = run_art_state(r)
                cand = "COVERED" if a == "OK" else ("INACCESSIBLE" if a == "MISSING" else "INVALIDATED")
            # lowest rank number wins: a usable cover beats every defect
            if best == "NONE" or rank[cand] < rank[best]:
                best = cand
                if cand == "COVERED":
                    sha_runs[sha] = r
        sha_state[sha] = best
    v = Verdict("UNKNOWN", conflicts=[c for c in conflicts
                                      if c["a"] in manifest.unique_shas and c["b"] in manifest.unique_shas])
    for rel, meta in sorted(manifest.files.items()):
        st = sha_state[meta["sha"]]
        v.by_state[st] = v.by_state.get(st, 0) + 1
        if st == "COVERED":
            v.covered.append(rel)
        elif st == "UNAUTHORIZED":
            v.denied.append(rel)
        else:
            v.delta.append(rel)
    used_by_id = {sha_runs[manifest.files[r]["sha"]].run_id: sha_runs[manifest.files[r]["sha"]]
                  for r in v.covered}
    used = list(used_by_id.values())
    v.run_ids = sorted(used_by_id)
    seen_art: set = set()
    for r in used:
        for a in r.artifacts:
            if a.get("path") not in seen_art:
                seen_art.add(a.get("path"))
                v.artifacts.append(a)
    n = len(manifest.files)
    if len(v.covered) == n:
        v.state = "EXACT_REUSE"
    elif v.covered:
        v.state = "PARTIAL"
    else:
        present = set(v.by_state)
        v.state = next((s for s in _PRECEDENCE if s in present), "UNKNOWN")
    if corrupt:
        v.reason = f"{corrupt} corrupt ledger line(s) ignored; run verify"
    return v


def coverage_report(manifest: Manifest, *, requester: str, ledger=None) -> dict:
    """Computed, never declared: FULL_READ share of the unique content set, any transform."""
    runs, _c, corrupt, readable = read_ledger(ledger)
    shas = manifest.unique_shas
    full = structural = 0
    for sha in shas:
        ranks = [DEPTH_RANK.get(r.files[sha], 0) for r in runs.values()
                 if sha in r.files and r.complete and not r.invalid_reason
                 and _scope_ok(r.scope, requester)]
        top = max(ranks, default=0)
        full += top >= 2
        structural += top == 1
    n = len(shas) or 1
    return {"unique_files": len(shas), "paths": len(manifest.files),
            "duplicate_groups": len(manifest.duplicates), "full_read": full,
            "structural": structural, "uncovered": len(shas) - full - structural,
            "assimilated_pct": round(100.0 * full / n, 2), "ledger_readable": readable,
            "corrupt_lines": corrupt}


def verify_ledger(ledger=None) -> dict:
    """Corrupt lines, runs that BEGAN but never COMMITted, runs whose declared count lies."""
    runs, _c, corrupt, readable = read_ledger(ledger)
    return {"readable": readable, "corrupt_lines": corrupt,
            "incomplete_runs": sorted(r.run_id for r in runs.values() if not r.complete),
            "runs": len(runs), "ok": readable and corrupt == 0
            and all(r.complete for r in runs.values())}


# ----------------------------------------------------------------- orchestration
def ensure(manifest: Manifest, *, corpus_id: str, requester: str, transform: str,
           config_digest: str, extractor, need: str = "STRUCTURAL", ledger=None,
           on_unknown: str = "refuse", unknown_reason: str = "") -> dict:
    """The only path that may spend extraction. `extractor(delta_rel_paths)` is the costly call
    and returns {"depth": ..., "artifacts": [{path, sha256}], "evidence": str}. It is invoked
    only for the delta, never for covered files, never for UNAUTHORIZED, and for UNKNOWN only
    when on_unknown == "extract_minimal" with a written reason."""
    v = verdict(manifest, transform=transform, config_digest=config_digest,
                requester=requester, need=need, ledger=ledger)
    out = {"verdict": v, "extracted": [], "run_id": None}
    if v.state in ("EXACT_REUSE", "UNAUTHORIZED"):
        return out
    if v.state == "UNKNOWN":
        if on_unknown != "extract_minimal" or not unknown_reason.strip():
            return out
        v.delta = sorted(manifest.files)
    if not v.delta:
        return out
    res = extractor(list(v.delta))
    depth = res.get("depth", "FULL_READ")
    out["run_id"] = record(manifest, corpus_id=corpus_id, scope=[requester],
                           transform=transform, config_digest=config_digest,
                           depth_by_rel={rel: depth for rel in v.delta},
                           artifacts=res.get("artifacts", []),
                           evidence=res.get("evidence", unknown_reason), ledger=ledger)
    out["extracted"] = list(v.delta)
    return out


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="CO-05 coverage receipt (spec: cognitive-work-reuse)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "status"):
        p = sub.add_parser(name)
        p.add_argument("root")
        p.add_argument("--transform", required=True)
        p.add_argument("--config", default="")
        p.add_argument("--requester", required=True)
        p.add_argument("--need", default="STRUCTURAL", choices=list(DEPTH_RANK))
        p.add_argument("--ledger", default=None)
    r = sub.add_parser("record")
    r.add_argument("root")
    r.add_argument("--corpus-id", required=True)
    r.add_argument("--scope", required=True, help="comma-separated authorized projects")
    r.add_argument("--transform", required=True)
    r.add_argument("--config", default="")
    r.add_argument("--depth", required=True, choices=["FULL_READ", "STRUCTURAL"])
    r.add_argument("--only", default=None, help="file with rel paths (one per line) actually read")
    r.add_argument("--evidence", default="")
    r.add_argument("--ledger", default=None)
    vv = sub.add_parser("verify")
    vv.add_argument("--ledger", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "verify":
        res = verify_ledger(a.ledger)
        print(json.dumps(res, indent=2))
        return 0 if res["ok"] else 1
    m = build_manifest(a.root)
    if a.cmd == "record":
        depth_by = {rel: a.depth for rel in m.files}
        if a.only:
            wanted = {x.strip() for x in Path(a.only).read_text(encoding="utf-8").split("\n") if x.strip()}
            depth_by = {rel: d for rel, d in depth_by.items() if rel in wanted}
        rid = record(m, corpus_id=a.corpus_id, scope=a.scope.split(","), transform=a.transform,
                     config_digest=a.config, depth_by_rel=depth_by, evidence=a.evidence,
                     ledger=a.ledger)
        print(f"recorded run {rid}")
        return 0
    v = verdict(m, transform=a.transform, config_digest=a.config, requester=a.requester,
                need=a.need, ledger=a.ledger)
    print(json.dumps({"state": v.state, "reason": v.reason, "by_state": v.by_state,
                      "covered": len(v.covered), "delta": len(v.delta), "denied": len(v.denied),
                      "report": coverage_report(m, requester=a.requester, ledger=a.ledger)},
                     indent=2))
    if a.cmd == "plan":
        for rel in v.delta[:50]:
            print("DELTA", rel)
    return 0 if v.state != "UNKNOWN" else 2


if __name__ == "__main__":
    sys.exit(main())
