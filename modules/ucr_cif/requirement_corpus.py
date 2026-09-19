# -*- coding: utf-8 -*-
"""Unified requirement corpus -- inherited prefix + compiled new region.

WHAT THIS REFUSES TO DO
-----------------------
Recompile the prefix. Lines 1..PREFIX_END are a literal line-for-line prefix of
the current corpus, and a predecessor session already inventoried them into 1,394
records. Those are institutional capital. They are IMPORTED with provenance and
never re-derived -- that is the whole economic argument for measuring the prefix
property before starting.

WHAT IT REFUSES TO PRETEND
--------------------------
That the two halves are the same kind of thing. They are not, and merging them
into one undifferentiated pile would be the more convenient lie:

    inherited  a NAMED CONCEPT   (NAME + DEFINITION + KIND + PARENT + IO)
               produced by model agents reading the prefix
    compiled   a NORMATIVE STATEMENT (one sentence, deterministic extraction)
               produced by corpus_compiler.py over the new region

Both are dispositional subjects -- each must end with an explicit owner in W2 --
so both belong in this corpus, carrying `unit_class` so nothing downstream has to
guess which it is holding, and carrying `claim_class` so nobody mistakes an
agent's judgement for a measurement.

THE PARTITION IS VERIFIED, NOT ASSUMED
--------------------------------------
The no-gap / no-duplicate claim rests on the two sets occupying disjoint line
ranges that together cover the corpus. An inherited record whose LINES fall
outside the prefix would break it silently, and the LINES field is agent-produced,
so it is checked rather than trusted. Violations are REPORTED, never clamped --
clamping would manufacture the very partition the report exists to prove.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter

SCHEMA_VERSION = 1

#: Last line of the inherited region. Not a tuning knob: it is the measured length
#: of the predecessor corpus, which is a literal prefix of the current one.
PREFIX_END = 75350

#: Floors. A sweep that silently stopped importing reports the same clean run as
#: one that works, so the population is asserted rather than observed.
MIN_INHERITED = 1300
MIN_COMPILED = 500

#: Named systems the predecessor measured in the prefix. A floor cannot see a
#: sweep that imports the wrong things; a named control can.
POSITIVE_CONTROLS = ("UBC", "HIC-OAR", "IFC")

LINES_RX = re.compile(r"^\s*(\d+)\s*[-_]\s*(\d+)\s*$")


def canon_key(s: str) -> str:
    s = unicodedata.normalize("NFKD", re.sub(r"\s+", " ", (s or "")).strip().lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", "", s)


def uid_for(prefix: str, key: str) -> str:
    return prefix + hashlib.blake2b(key.encode(), digest_size=9).hexdigest()


def parse_span(rec: dict):
    """(start, end) from LINES, or None.

    `ranges` is deliberately not trusted: the same corpus carries '52500_75350'
    and 'r2_slice4' in that field, because it was written by different agents.
    """
    m = LINES_RX.match(str(rec.get("LINES", "")))
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    return (a, b) if a <= b else (b, a)


def load_inherited(path: str, source_label: str):
    recs = json.load(open(path, encoding="utf-8-sig"))
    units, unattributed, out_of_prefix = [], [], []
    for r in recs:
        name = (r.get("NAME") or "").strip()
        if not name:
            continue
        key = r.get("canonical_key") or canon_key(name)
        span = parse_span(r)
        if span is None:
            unattributed.append(name)
            span = (0, 0)
        elif span[1] > PREFIX_END or span[0] < 1:
            out_of_prefix.append((name, span))
        defn = (r.get("DEFINITION") or "").strip()
        aliases = [a.strip() for a in str(r.get("ALIASES") or "").split(",")
                   if a.strip() and a.strip().upper() != "NONE"]
        units.append({
            "uid": uid_for("i", key),
            "unit_class": "concept",
            "claim_class": "INFERRED",      # model-agent judgement over the prefix
            "kind": (r.get("KIND") or "concept").strip().lower(),
            "name": name,
            "text": defn if defn and defn != "NONE" else name,
            "line_start": span[0],
            "line_end": span[1],
            "entities": [name] + aliases,
            "parent": (r.get("PARENT") or "").strip() or None,
            "substance": (r.get("SUBSTANCE") or "").strip() or None,
            "provenance": "inherited:" + source_label,
            "canonical_key": key,
        })
    return units, unattributed, out_of_prefix


def load_compiled(path: str):
    blob = json.load(open(path, encoding="utf-8"))
    units = []
    for u in blob["units"]:
        units.append({
            "uid": "c" + u["uid"],
            "unit_class": "statement",
            "claim_class": "OBSERVED",      # deterministic extraction from source text
            "kind": u["kind"],
            "name": None,
            "text": u["text"],
            "line_start": u["line_start"],
            "line_end": u["line_end"],
            "entities": u.get("entities", []),
            "parent": None,
            "substance": None,
            "provenance": "compiled:" + str(blob.get("corpus_id", "?")),
            "canonical_key": canon_key(u["text"]),
            "lang": u.get("lang"),
            "contaminated": u.get("contaminated", False),
            "occurrences": u.get("occurrences", []),
        })
    return units, blob


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the unified UCR-CIF requirement corpus")
    ap.add_argument("--inherited", required=True)
    ap.add_argument("--inherited-label", default="predecessor")
    ap.add_argument("--compiled", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    inh, unattributed, out_of_prefix = load_inherited(args.inherited, args.inherited_label)
    comp, blob = load_compiled(args.compiled)

    print("=== SOURCES ===")
    print("inherited=%d  (concepts, claim_class=INFERRED, provenance=%s)"
          % (len(inh), args.inherited_label))
    print("compiled =%d  (statements, claim_class=OBSERVED, corpus_id=%s, range=%s)"
          % (len(comp), blob.get("corpus_id"), blob.get("range")))

    print("\n=== PARTITION (verified, not assumed) ===")
    comp_lo = min((u["line_start"] for u in comp), default=0)
    comp_hi = max((u["line_end"] for u in comp), default=0)
    inh_hi = max((u["line_end"] for u in inh), default=0)
    print("inherited line span: 1..%d   (prefix ends %d)" % (inh_hi, PREFIX_END))
    print("compiled  line span: %d..%d" % (comp_lo, comp_hi))
    print("unattributed_inherited=%d  out_of_prefix_inherited=%d"
          % (len(unattributed), len(out_of_prefix)))
    for nm, sp in out_of_prefix[:8]:
        print("   OUT OF PREFIX: %s %s" % (nm, sp))
    disjoint = comp_lo > PREFIX_END and not out_of_prefix
    print("DISJOINT=%s  (compiled starts after the prefix AND no inherited record "
          "claims a line beyond it)" % disjoint)

    ikeys = {u["canonical_key"] for u in inh}
    cross = [u for u in comp if u["canonical_key"] in ikeys]
    print("\n=== CROSS-HALF DUPLICATES (by canonical key) ===")
    print("compiled units whose key already exists as an inherited concept: %d" % len(cross))
    for u in cross[:5]:
        print("   %s" % u["text"][:100])

    by_uid, collisions = {}, 0
    for u in inh + comp:
        if u["uid"] in by_uid:
            collisions += 1
            continue
        by_uid[u["uid"]] = u

    print("\n=== RESULT ===")
    print("total_units=%d  uid_collisions=%d" % (len(by_uid), collisions))
    print("unit_class=%s" % dict(Counter(u["unit_class"] for u in by_uid.values())))
    print("claim_class=%s" % dict(Counter(u["claim_class"] for u in by_uid.values())))
    print("kinds=%s" % dict(Counter(u["kind"] for u in by_uid.values()).most_common(16)))

    ok = True
    if len(inh) < MIN_INHERITED:
        print("CONTROL_FAIL inherited floor %d < %d" % (len(inh), MIN_INHERITED))
        ok = False
    if len(comp) < MIN_COMPILED:
        print("CONTROL_FAIL compiled floor %d < %d" % (len(comp), MIN_COMPILED))
        ok = False
    ents = {str(e).upper() for u in by_uid.values() for e in (u.get("entities") or [])}
    names = {str(u.get("name") or "").upper() for u in by_uid.values()}
    for probe in POSITIVE_CONTROLS:
        if probe not in ents and not any(probe in n for n in names):
            print("CONTROL_FAIL positive control '%s' absent -- the importer may have "
                  "stopped importing" % probe)
            ok = False
    if not disjoint:
        print("CONTROL_FAIL the two halves are NOT disjoint -- the no-duplicate claim "
              "cannot be made, and clamping the spans would manufacture it")
        ok = False
    print("CONTROLS=%s" % ("PASS" if ok else "FAIL"))

    payload = {
        "schema_version": SCHEMA_VERSION,
        "prefix_end": PREFIX_END,
        "inherited_source": args.inherited_label,
        "compiled_corpus_id": blob.get("corpus_id"),
        "counts": {"inherited": len(inh), "compiled": len(comp), "total": len(by_uid),
                   "uid_collisions": collisions, "cross_half_key_matches": len(cross)},
        "partition": {"prefix_end": PREFIX_END, "compiled_line_span": [comp_lo, comp_hi],
                      "inherited_max_line": inh_hi, "disjoint": disjoint,
                      "unattributed_inherited": len(unattributed),
                      "out_of_prefix_inherited": [{"name": n, "span": list(s)}
                                                  for n, s in out_of_prefix]},
        "controls_pass": ok,
        "units": sorted(by_uid.values(), key=lambda u: (u["unit_class"], u["line_start"])),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, args.out)
    print("\nwrote %s (%d units)" % (args.out, len(by_uid)))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
