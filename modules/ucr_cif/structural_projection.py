#!/usr/bin/env python3
"""structural_projection.py -- compiled structural ownership evidence (W9).

`ownership_evidence.build_structural_index` produces genuinely relational
facts: a symbol DEFINED, a file NAMED, a registry key REGISTERED, an inbound
import edge. It is also far too expensive to consult on a hook path -- measured
on this estate, **45,525 ms cold and 10,080 ms warm over 1,364 files**. Running
it per prompt is the common-path repository archaeology the architecture
forbids.

So it is compiled, once, into a bounded projection:

    term -> [ledger owners that STRUCTURALLY hold that term]

restricted to the corpus's own evidence-term universe and to the 40 owners the
authoritative ledger actually names. Measured: **674 terms, 50,036 bytes,
0.73 ms to parse.**

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
This file is a PROJECTION. It is a cache of facts whose authority lives in the
repository itself and whose term universe belongs to the disposition ledger.
It is never a second source of truth, and three properties enforce that:

  * it records the identity of BOTH its inputs (the repo fingerprint and the
    ledger binding), so it can say when it no longer describes them;
  * a projection that cannot vouch for itself degrades to UNKNOWN, never to a
    negative verdict -- absence of structural evidence and inability to look
    are different facts, and only one of them is about an owner;
  * it corroborates nothing on its own. A term it reports is a term the
    structural index already held; counting both would be the
    source-plus-projection double count this wave exists to avoid.

THE TWO FRESHNESS TIERS, AND WHY THEY DIFFER
--------------------------------------------
BINDING (checked on every load, ~0 ms). The ledger's `compiled_corpus_id` plus
its size/mtime identity. A regenerated ledger means a term universe this
projection was not built for, so it degrades.

SOURCE (checked explicitly, never on the hook path). A digest over the scanned
files' (path, size, mtime_ns). Verified by `--verify` and by a gate.

The asymmetry is deliberate and it is only safe while structural evidence is
used for RANKING. A stale projection can reorder owners; it cannot refuse one.
If an admission clause ever ships, the source check becomes load-bearing on the
read path and this docstring is wrong -- amend it in the same commit.

Stdlib-only. Fail-open per stage: an unreadable projection costs the structural
signal, never the selection.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from modules.ucr_cif import ownership_evidence as _oe
from modules.ucr_cif import prose_authority as _pa

#: Bumped when the on-disk shape changes. A reader that speaks a different
#: version degrades rather than guessing at the layout.
#:
#: 2 (W11) adds `prose_terms`. The bump is deliberate rather than an optional
#: field: a reader that can consult prose evidence, handed a projection built
#: before prose existed, would find an empty map and report "no owner declares
#: this" -- which is the collapse of "we could not look" into "nobody holds it"
#: that this module exists to refuse. A version mismatch degrades loudly.
SCHEMA_VERSION = 2

PROJECTION_REL = "vault/ucr_cif/structural_projection.json"
LEDGER_REL = "vault/ucr_cif/disposition_ledger.json"

#: Status values. Kept disjoint because they demand different responses and
#: because collapsing any two of them tells a caller something false.
#:
#:   LOADED        the projection describes the current inputs
#:   ABSENT        never built -- not an assertion about any owner
#:   UNREADABLE    present and unparseable -- an instrument failure
#:   SCHEMA        built by a different version of this module
#:   STALE_LEDGER  the ledger moved under it; the term universe is not ours
#:
#: Only LOADED may contribute evidence. Every other value means UNKNOWN, and
#: UNKNOWN is never resolved toward the convenient answer.
LOADED = "LOADED"
ABSENT = "ABSENT"
#: Withheld deliberately by the operator, via UCR_CIF_STRUCTURAL_DISABLE=1.
#:
#: Its own value, never folded into ABSENT. "Nobody built this projection" and
#: "somebody switched it off for this run" are different facts about the
#: world, and a measurement that cannot tell them apart cannot say whether its
#: control arm was actually a control. This is also the operational rollback:
#: it degrades the selector to W8's ordering, which it can do safely for
#: exactly the reason M2 is ranking-only -- withholding structural evidence
#: reorders owners and can never refuse one.
DISABLED = "DISABLED"
DISABLE_ENV = "UCR_CIF_STRUCTURAL_DISABLE"
UNREADABLE = "UNREADABLE"
SCHEMA = "SCHEMA"
STALE_LEDGER = "STALE_LEDGER"

_CACHE: dict = {}


#: W11. Whether PROSE declarations join the ranking evidence. Off by default and
#: separate from W9's switch on purpose: W9's arm is `STRUCTURAL only` and must
#: stay byte-reproducible as the known-harmful reference, so the prose arm is a
#: DISTINCT treatment identity rather than the same treatment with more data.
PROSE_RANK_ENV = "UCR_CIF_PROSE_RANK"


def _prose_ranking() -> bool:
    return os.environ.get(PROSE_RANK_ENV, "") == "1"


@dataclass(frozen=True)
class Projection:
    """Compiled structural facts, plus an honest account of their standing."""
    status: str
    terms: dict                      # term -> frozenset(owner)
    corpus_id: str | None = None
    built_at: str | None = None
    repo_fingerprint: str | None = None
    detail: str | None = None
    #: W11. term -> owners that DECLARE it in a normatively-consumed prose
    #: contract. Compiled and reported always; consulted for ranking only under
    #: the W11 arm. Kept in its own map rather than merged into `terms` so that
    #: `holders()` -- and therefore every W9 measurement -- stays exactly what it
    #: was, and so a reader can always tell the two evidence kinds apart.
    prose_terms: dict = field(default_factory=dict)

    @property
    def usable(self) -> bool:
        """LOADED is the only state that may contribute evidence."""
        return self.status == LOADED

    def holders(self, term: str) -> frozenset:
        """Ledger owners that structurally hold `term`.

        An unusable projection answers with the empty set AND reports a status
        that is not LOADED -- the caller must read both. Reading the set alone
        turns 'we could not look' into 'nobody holds it', which is exactly the
        collapse this module refuses to make.
        """
        if not self.usable:
            return frozenset()
        return self.terms.get(str(term).lower(), frozenset())

    def prose_holders(self, term: str) -> frozenset:
        """Ledger owners that DECLARE `term` in a consumed prose contract.

        Same refusal as `holders`: an unusable projection answers empty AND
        carries a status that is not LOADED.
        """
        if not self.usable:
            return frozenset()
        return self.prose_terms.get(str(term).lower(), frozenset())

    def holds(self, owner: str, term: str) -> bool:
        """Structural support, with the prose channel gated by the W11 arm.

        `holders()` is deliberately NOT widened. W9's arm has to keep producing
        the numbers W10 judged, or the harmful reference stops being a
        reference; so the union happens here, on the W11 path only.
        """
        if not owner:
            return False
        if owner in self.holders(term):
            return True
        return _prose_ranking() and owner in self.prose_holders(term)


def repo_root(start=None) -> Path:
    return Path(__file__).resolve().parents[2] if start is None else Path(start)


def _ledger_binding(root: Path) -> dict:
    """Identity of the ledger this projection's term universe came from.

    BUILD-TIME ONLY. It parses the 1.9 MB ledger, which is free here and was
    not free on the read path: calling it from `load` cost a measured
    **70.8 ms** per process against a projection that parses in 0.73 ms, i.e.
    99 % of the cost of consulting the cache was re-reading the very file the
    cache exists to avoid touching. `load` compares the recorded binding
    against a `stat` plus the corpus id its caller has already parsed.

    `mtime_ns` is RECORDED and deliberately NOT COMPARED. It is diagnostic.
    No clone, export or checkout preserves it, so comparing it would report
    every fresh working tree as stale and silently disable structural
    evidence exactly where nobody would think to look for it. `corpus_id` is
    content-derived and `size` is byte-derived; both survive a clone, and
    together they are what "the same ledger generation" actually means.
    """
    path = root / LEDGER_REL
    try:
        st = path.stat()
    except OSError:
        return {}
    out = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
    try:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
        out["corpus_id"] = str(doc.get("compiled_corpus_id") or "") or None
        out["schema_version"] = doc.get("schema_version")
    except (OSError, ValueError):
        # A binding without a corpus id still detects movement by size.
        out["corpus_id"] = None
    return out


def repo_fingerprint(root: Path) -> str:
    """Digest over the scanned files' (path, size, mtime_ns).

    Deliberately NOT a content hash: this runs over ~1,400 files and its job is
    to notice that the structural source moved, not to prove what it now says.
    Reading every byte would make the check cost what the build costs, which
    would defeat having a projection at all.
    """
    h = hashlib.sha256()
    for d in sorted(_oe.SCAN_DIRS):
        base = root / d
        if not base.is_dir():
            continue
        rows = []
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames
                           if x not in (".git", "__pycache__", "node_modules")]
            for fn in filenames:
                if not fn.endswith(_oe.ALL_EXT):
                    continue
                p = Path(dirpath) / fn
                try:
                    st = p.stat()
                except OSError:
                    continue
                rel = str(p.relative_to(root)).replace("\\", "/")
                rows.append("%s|%d|%d" % (rel, st.st_size, st.st_mtime_ns))
        for row in sorted(rows):
            h.update(row.encode("utf-8", "replace"))
            h.update(b"\n")
    return h.hexdigest()


def _ledger_universe(root: Path):
    """(evidence-term universe, owner set) of the AUTHORITATIVE rows.

    Authoritative only, and for the same reason the consumer selects on them:
    a candidate is not an authority, so a term that only ever appeared on an
    unreviewed row is not part of the population being selected from.
    """
    path = root / LEDGER_REL
    doc = json.loads(path.read_text(encoding="utf-8-sig"))
    terms: set = set()
    owners: set = set()
    for r in doc.get("rows") or []:
        if not (r.get("disposition") and r.get("reviewed_by")):
            continue
        owner = str(r.get("proposed_owner") or "")
        if owner:
            owners.add(owner)
        for t in (r.get("evidence_terms") or []):
            terms.add(str(t).lower())
    return terms, owners


def build(repo=None) -> dict:
    """Compile the projection document. Offline: this is the expensive half."""
    root = repo_root(repo)
    t0 = time.perf_counter()
    universe, owners = _ledger_universe(root)
    index = _oe.build_structural_index(root)
    terms: dict = {}
    for t in sorted(universe):
        held = sorted(_oe.structural_holders(t, index) & owners)
        if held:
            terms[t] = held
    # W11. Restricted to the SAME ledger universe and owner set as the symbol
    # channel, so the two maps are comparable and a prose owner cannot enter
    # through a term the corpus never adjudicated.
    prose_raw = _pa.prose_declarations(root)
    prose_terms: dict = {}
    for t in sorted(universe):
        held = sorted(set(prose_raw.get(t, ())) & owners)
        if held:
            prose_terms[t] = held
    build_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "schema_version": SCHEMA_VERSION,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "build_ms": round(build_ms, 1),
        # Provenance: which producer, over which inputs. A projection that
        # cannot name its source is indistinguishable from an authority.
        "source": {
            "producer": "modules.ucr_cif.ownership_evidence.build_structural_index",
            "signals": ["SYMBOL", "FILENAME", "REGISTRY", "DECLARATION"],
            "declaration_producer":
                "modules.ucr_cif.prose_authority.prose_declarations",
            "scan_dirs": list(_oe.SCAN_DIRS),
            "files_seen": index["files_seen"],
            "distinctive_max_holders": _oe.DISTINCTIVE_MAX_HOLDERS,
        },
        "prose_held_terms": len(prose_terms),
        "prose_terms": prose_terms,
        "ledger_binding": _ledger_binding(root),
        "repo_fingerprint": repo_fingerprint(root),
        "universe_terms": len(universe),
        "ledger_owners": len(owners),
        "held_terms": len(terms),
        "terms": terms,
    }


def save(doc: dict, repo=None) -> Path:
    root = repo_root(repo)
    path = root / PROJECTION_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")
    return path


def load(repo=None, corpus_id=None) -> Projection:
    """Read the projection and judge its standing. Never raises.

    Cached on (path, mtime_ns, size, corpus_id) exactly as the ledger is, so a
    mission pays the 0.73 ms parse once per process and a rebuilt projection
    is never served from a stale cache.

    `corpus_id` is the ledger's `compiled_corpus_id`, supplied by a caller
    that has already parsed it. Supplying it is what makes the binding check
    free; omitting it is honest but weaker -- the check falls back to the
    ledger's byte size alone, which catches a regenerated ledger of a
    different length and cannot catch a same-length one. The consumer always
    supplies it.
    """
    if os.environ.get(DISABLE_ENV, "") == "1":
        # Checked before the file is even stat'd, so a control arm is a
        # control whatever happens to be on disk.
        return Projection(DISABLED, {},
                          detail="withheld by %s=1" % DISABLE_ENV)
    root = repo_root(repo)
    path = root / PROJECTION_REL
    try:
        st = path.stat()
    except OSError:
        return Projection(ABSENT, {}, detail="no projection at " + str(path))
    key = (str(path), st.st_mtime_ns, st.st_size, corpus_id)
    hit = _CACHE.get("k")
    if hit == key:
        return _CACHE["proj"]

    try:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
        raw = doc["terms"]
        if not isinstance(raw, dict):
            raise ValueError("terms is not an object")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        proj = Projection(UNREADABLE, {}, detail="%s: %s"
                          % (type(exc).__name__, exc))
        _CACHE.update({"k": key, "proj": proj})
        return proj

    if doc.get("schema_version") != SCHEMA_VERSION:
        proj = Projection(SCHEMA, {}, detail="projection schema_version=%r, "
                          "this reader speaks %r"
                          % (doc.get("schema_version"), SCHEMA_VERSION))
        _CACHE.update({"k": key, "proj": proj})
        return proj

    # BINDING. The term universe belongs to a specific ledger generation.
    #
    # Compared with a `stat` and the corpus id the caller already holds --
    # never by re-reading the ledger, which is the file this projection
    # exists so the hook path does not have to touch. `mtime_ns` is not
    # compared: see `_ledger_binding`.
    was = doc.get("ledger_binding") or {}
    moved = []
    try:
        if (root / LEDGER_REL).stat().st_size != was.get("size"):
            moved.append("size")
    except OSError:
        moved.append("ledger unreadable")
    if corpus_id is not None and was.get("corpus_id") != corpus_id:
        moved.append("corpus_id")
    if moved:
        proj = Projection(
            STALE_LEDGER, {}, corpus_id=was.get("corpus_id"),
            built_at=doc.get("built_at"),
            repo_fingerprint=doc.get("repo_fingerprint"),
            detail="ledger moved since build (%s differ)" % ", ".join(moved))
        _CACHE.update({"k": key, "proj": proj})
        return proj

    terms = {str(t).lower(): frozenset(o) for t, o in raw.items()
             if isinstance(o, list)}
    prose = {str(t).lower(): frozenset(o)
             for t, o in (doc.get("prose_terms") or {}).items()
             if isinstance(o, list)}
    proj = Projection(LOADED, terms, corpus_id=was.get("corpus_id"),
                      built_at=doc.get("built_at"),
                      repo_fingerprint=doc.get("repo_fingerprint"),
                      prose_terms=prose)
    _CACHE.update({"k": key, "proj": proj})
    return proj


def verify(repo=None) -> dict:
    """Explicit source check. Recomputes the repo fingerprint.

    Kept off the read path on purpose: it walks and stats every scanned file.
    A gate drives it; the hook does not.
    """
    root = repo_root(repo)
    proj = load(root)
    out = {"status": proj.status, "built_at": proj.built_at,
           "held_terms": len(proj.terms)}
    if proj.status in (ABSENT, UNREADABLE, SCHEMA):
        out["source_fresh"] = None
        out["detail"] = proj.detail
        return out
    current = repo_fingerprint(root)
    out["source_fresh"] = (current == proj.repo_fingerprint)
    out["repo_fingerprint_now"] = current
    out["repo_fingerprint_at_build"] = proj.repo_fingerprint
    if proj.status == STALE_LEDGER:
        out["detail"] = proj.detail
    return out


def _main(argv) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true",
                    help="compile and write the projection")
    ap.add_argument("--verify", action="store_true",
                    help="report standing, including the source fingerprint")
    ap.add_argument("--repo", default=None)
    args = ap.parse_args(argv)

    if args.build:
        doc = build(args.repo)
        path = save(doc, args.repo)
        print("BUILT %s" % path)
        print("  terms=%d of universe=%d  owners=%d  files_seen=%d"
              % (doc["held_terms"], doc["universe_terms"],
                 doc["ledger_owners"], doc["source"]["files_seen"]))
        print("  build_ms=%.0f  bytes=%d"
              % (doc["build_ms"], path.stat().st_size))
        print("  corpus_id=%s" % (doc["ledger_binding"].get("corpus_id"),))
        return 0

    info = verify(args.repo)
    for k in ("status", "built_at", "held_terms", "source_fresh", "detail"):
        if info.get(k) is not None:
            print("%-16s %s" % (k, info[k]))
    if info["status"] != LOADED:
        return 1
    return 0 if info.get("source_fresh") else 2


__all__ = [
    "ABSENT", "DISABLED", "DISABLE_ENV",
    "LOADED", "PROJECTION_REL", "Projection", "SCHEMA",
    "SCHEMA_VERSION", "STALE_LEDGER", "UNREADABLE", "build", "load",
    "repo_fingerprint", "save", "verify",
]

if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
