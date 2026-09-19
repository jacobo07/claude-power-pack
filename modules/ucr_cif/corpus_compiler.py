# -*- coding: utf-8 -*-
"""UCR-CIF corpus compiler -- 167,842 lines of dialogue into typed requirement units.

WHY THIS EXISTS AT ALL (D2A verdict, 2026-09-19)
------------------------------------------------
Three existing owners were probed before a line of this was written:

  modules/knowledge_acquisition/corpus_parser.py  needs column-zero `N.` prompt
      markers and a declared prompt count. This corpus has 23 markdown headings
      in 167,842 lines, all inside the contamination band. MEASURED MISS.
  modules/karimo-harness/prd_parser.py            deterministic, but whole-document,
      small-input, and emits a PRD baseline -- no incrementality, no restart, no
      lineage. MEASURED MISS.
  tools/distiller/, modules/dataset_first/        target a 22-section distillation
      schema and the DFP->IAS-C1 funding seam respectively. DIFFERENT JOB.

So this is a CREATE with a proven gap -- and it inherits rather than reinvents:
the deterministic state machine and atomic write come from `prd_parser`, and the
fail-closed assertion comes from `corpus_parser`, whose docstring states the
principle this file depends on: *a parse that does not land on its declared
invariant must raise, not ingest a plausible-looking partial corpus.*

THE PHYSICAL CONSTRAINT THAT SHAPES EVERY DECISION HERE
--------------------------------------------------------
The corpus is ~870k tokens. It may never enter model context, and subagents are
not a way around that. So extraction is DETERMINISTIC: no model call, no network,
no judgement. The model later consumes slice summaries, unresolved conflicts and
targeted evidence windows -- never the corpus.

FIVE CONTRACTED PROPERTIES
--------------------------
  incremental       only the requested line range is processed
  restartable       a completed slice is never recomputed; a kill costs the tail
  idempotent        identity is the content hash, so a rerun overwrites with equals
  bounded-memory    lines stream; only one slice plus a small overlap is resident
  crash-survivable  each slice lands atomically, manifest updated after the write

PREFIX REUSE
------------
The 75,350-line predecessor corpus is a literal line-for-line prefix of this one
(measured: first differing line index = None). Its 1,394 inventory records are
institutional capital and are IMPORTED with provenance, never recompiled. This
compiler therefore owns lines 75,351.. by policy -- while remaining *able* to
compile any range, because the boundary-independence proof requires it.

WINDOW-BOUNDARY INDEPENDENCE (the seam property that actually needs proving)
---------------------------------------------------------------------------
A unit split across a slice edge is the real failure mode: it yields two half
records in one run and one whole record in another, and neither run looks wrong.
Identity is the hash of the normalized unit text, so the proof is direct --
compile a range under two different slice offsets and require the resulting unit
id sets to be equal. `--verify-boundary` does exactly that and is the gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field, asdict

SCHEMA_VERSION = 1
DEFAULT_SLICE = 2000
READAHEAD = 400              # lines read PAST a slice edge so a straddling paragraph completes
LOOKBACK = 400               # lines read BEFORE it, so a continuation is not mistaken for a start

# ---------------------------------------------------------------- vocabulary
# Normative markers. Spanish and English, because the corpus is both.
_NORM_ES = (r"debe(?:n|r[ií]a|r[aá]|mos)?|hay que|tiene(?:n)? que|es obligatorio|"
            r"nunca|jam[aá]s|siempre|no puede|no debe|prohibido|proh[ií]be|"
            r"requiere|exige|obliga|basta con|no basta|queda prohibido")
_NORM_EN = (r"must(?: not)?|shall(?: not)?|never|always|required|requires|forbidden|"
            r"may not|cannot|should(?: not)?|is prohibited|has to")
NORM_RX = re.compile(r"\b(?:%s|%s)\b" % (_NORM_ES, _NORM_EN), re.I)

# A normative sentence only counts as INSTITUTIONAL when it also carries a domain
# term or a named entity. Without this the extractor returns every "debe" in a
# 167k-line conversation, which is volume, not requirements.
DOMAIN_RX = re.compile(
    r"\b(sistema|system|capability|capacidad|baseline|gate|evidencia|evidence|"
    r"owner|ownership|contrato|contract|registry|registro|ledger|estado|state|"
    r"promoci[oó]n|promotion|revocaci[oó]n|revocation|applicability|aplicabilidad|"
    r"failure|fallo|intervenci[oó]n|intervention|benchmark|m[eé]trica|metric|"
    r"telemetr[ií]a|telemetry|provenance|procedencia|corpus|dataset|runtime|"
    r"enforcement|hook|loop|pipeline|compiler|compilador|inheritance|herencia|"
    r"maturity|madurez|autonom[ií]a|autonomy|institucional|institutional)\b", re.I)

# Named entities: ALLCAPS acronyms (3-8 chars, optional -SUFFIX) and Title Case runs.
ACRONYM_RX = re.compile(r"\b([A-Z]{3,8}(?:-[A-Z0-9]{1,6})?)\b")
TITLECASE_RX = re.compile(r"\b((?:[A-Z][a-z]{2,}\s+){1,4}[A-Z][a-z]{2,})\b")

DEFN_RX = re.compile(r"\b(?:es|son|significa|se define como|is|are|means|"
                     r"is defined as|se entiende por)\b", re.I)
METRIC_RX = re.compile(r"\b(m[eé]trica|metric|tasa|rate|ratio|porcentaje|percent|"
                       r"cobertura|coverage|latencia|latency|budget|presupuesto|"
                       r"North Star|KPI|denominador|denominator)\b", re.I)
TRAP_RX = re.compile(r"\b(trap|trampa|antipattern|antipatr[oó]n|no confundas|"
                     r"don't|do not confuse|pitfall|falso positivo|false positive|"
                     r"ilusi[oó]n|illusion)\b", re.I)

# Harness contamination, kept as the predecessor measured it: classified, not dropped.
HARNESS_RX = re.compile(
    r"(system[- ]prompt|<function|sandbox|escalation request|approval_policy|"
    r"You are ChatGPT|Codex CLI|tool_call|apply_patch|\.docx|\.pptx|"
    r"assistant channel|developer message)", re.I)

_SENT_SPLIT = re.compile(r"(?<=[.!?;:])\s+|\n")
_WS = re.compile(r"\s+")

#: Positive controls: phrases that MUST be extracted from the new region. A sweep
#: that stopped extracting reports the same clean run as one that works.
POSITIVE_CONTROLS = ("ratchet", "baseline", "capability")


def norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    return _WS.sub(" ", s).strip()


def canon_key(s: str) -> str:
    """Identity key: case/accents/punctuation folded, so a requote is the same unit."""
    s = unicodedata.normalize("NFKD", norm_text(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", "", s)


def shingles(key: str, n: int = 5) -> set:
    w = key.split()
    return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))} or {key}


def sig64(key: str) -> str:
    """Cheap lineage signature: 64-bit min-hash-ish digest over shingles."""
    sh = sorted(hashlib.blake2b(s.encode(), digest_size=8).hexdigest() for s in shingles(key))
    return hashlib.blake2b("".join(sh[:8]).encode(), digest_size=8).hexdigest()


@dataclass
class Unit:
    uid: str
    kind: str
    text: str
    line_start: int
    line_end: int
    entities: list = field(default_factory=list)
    markers: list = field(default_factory=list)
    lang: str = "es"
    contaminated: bool = False
    sig: str = ""
    provenance: str = "compiled"


def classify(sent: str) -> str:
    """Deterministic KIND. Order matters: the most specific claim wins."""
    if TRAP_RX.search(sent):
        return "trap"
    if NORM_RX.search(sent):
        return "law"
    if METRIC_RX.search(sent):
        return "metric"
    if DEFN_RX.search(sent):
        return "definition"
    return "concept"


def detect_lang(sent: str) -> str:
    es = len(re.findall(r"\b(que|para|porque|cuando|debe|esto|cada|pero|donde|"
                        r"sobre|siempre|nunca|puede|mismo|del|las|los)\b", sent, re.I))
    en = len(re.findall(r"\b(the|that|with|from|must|never|always|this|each|"
                        r"which|where|about|into|of|and)\b", sent, re.I))
    return "es" if es >= en else "en"


#: token -> fraction of its occurrences that are ALL-CAPS, derived from the corpus.
#: Module-level because it is a property of the corpus being compiled, constant for
#: the whole run and keyed by corpus_id; threading it through the generator chain
#: would buy nothing. Empty means "no table" and the stop-list fallback applies.
_CASE_TABLE: dict = {}
_WORD_RX = re.compile(r"\b([A-Za-z]{2,8})\b")
_CAPS_STOP = frozenset((
    "PART", "FINAL", "NOTE", "TODO", "AND", "THE", "FOR", "NOT", "YOU", "ALL",
    "ITS", "WHEN", "ONLY", "THAT", "THIS", "WITH", "FROM", "INTO", "EACH", "EVERY",
    "MUST", "SHALL", "SHOULD", "NEVER", "ALWAYS", "CAN", "MAY", "ARE", "WAS", "HAS",
    "QUE", "PARA", "CADA", "DEBE", "NUNCA", "SIEMPRE", "PERO", "COMO", "MAS", "SIN"))


def build_case_table(corpus: str, min_count: int = 3) -> dict:
    """One streaming pass: how often is each token written in ALL CAPS?

    This corpus argues in emphatic capitals -- MUST, EVERY, EVIDENCE, SOFTWARE --
    and a naive ALL-CAPS rule reads those as named systems. Measured on the new
    region, 15 of the top 25 "entities" were emphasis, which would have polluted
    every downstream requirement->owner mapping in W2 with no visible error.

    A genuine acronym (UKDL, UBC, CPP) is essentially always capitalised; an
    emphasised ordinary word has thousands of lowercase occurrences elsewhere in
    the same corpus. So the corpus itself supplies the discriminator, with no
    dictionary, no word list to maintain and no judgement call.
    """
    upper, total = {}, {}
    with open(corpus, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            for w in _WORD_RX.findall(line):
                k = w.upper()
                total[k] = total.get(k, 0) + 1
                if w.isupper():
                    upper[k] = upper.get(k, 0) + 1
    return {k: upper.get(k, 0) / t for k, t in total.items() if t >= min_count}


#: An acronym must be written in caps at least this often to count as a name.
CAPS_RATIO = 0.6

#: Slice artifact filename, e.g. s0075351_0077350.json
_SLICE_FN_RX = re.compile(r"^s\d{7}_\d{7}\.json$")


def entities_in(sent: str) -> list:
    out = []
    for m in ACRONYM_RX.findall(sent):
        if m in _CAPS_STOP:
            continue
        head = m.split("-")[0]
        if _CASE_TABLE:
            ratio = _CASE_TABLE.get(head)
            # Unknown token (too rare to profile) is kept: absence of evidence that
            # it is an ordinary word is not evidence that it is one.
            if ratio is not None and ratio < CAPS_RATIO:
                continue
        out.append(m)
    for m in TITLECASE_RX.findall(sent):
        if len(m) <= 60:
            out.append(m)
    seen, uniq = set(), []
    for e in out:
        if e not in seen:
            seen.add(e)
            uniq.append(e)
    return uniq[:12]


def extract_units(lines, first_lineno: int, emit_from: int, emit_to: int):
    """Yield Units from `lines`, emitting only paragraphs whose START line falls in
    [emit_from, emit_to].

    A slice OWNS a paragraph when the paragraph starts inside it, and it reads PAST
    its own end edge so that paragraph completes. The earlier design did the
    opposite -- it read a look-back window and cut at the end edge -- which silently
    truncated any paragraph straddling the edge: the owning slice emitted units from
    half a paragraph, and the next slice skipped it because its start preceded the
    window. Neither run looked wrong, and the two-offset check passed anyway because
    no paragraph happened to straddle an edge in the sampled range. That is a
    vacuous green, and `--selftest` now forces the case instead of hoping for it.
    """
    buf, buf_start = [], first_lineno
    for off, raw in enumerate(lines):
        lineno = first_lineno + off
        if raw.strip():
            if not buf:
                buf_start = lineno
            buf.append(raw)
            continue
        if buf:
            yield from _units_from_para(buf, buf_start, emit_from, emit_to)
            buf = []
    if buf:
        yield from _units_from_para(buf, buf_start, emit_from, emit_to)


def _units_from_para(para_lines, para_start: int, emit_from: int, emit_to: int):
    para = norm_text(" ".join(para_lines))
    if len(para) < 24:
        return
    contaminated = bool(HARNESS_RX.search(para))
    # Line attribution: a paragraph is small, so a sentence is attributed to the
    # paragraph's span. Precision here is bounded by the source's own formatting.
    span = (para_start, para_start + len(para_lines) - 1)
    if span[0] < emit_from or span[0] > emit_to:
        return
    for sent in _SENT_SPLIT.split(para):
        sent = norm_text(sent)
        if len(sent) < 24 or len(sent) > 1200:
            continue
        is_norm = bool(NORM_RX.search(sent))
        has_domain = bool(DOMAIN_RX.search(sent))
        ents = entities_in(sent)
        # Admission rule, stated so it can be argued with: a unit is material when
        # it is normative AND institutional, or when it defines/measures a named
        # entity. Everything else is dialogue.
        material = (is_norm and has_domain) or \
                   (bool(ents) and (DEFN_RX.search(sent) or METRIC_RX.search(sent))) or \
                   (TRAP_RX.search(sent) and has_domain)
        if not material:
            continue
        key = canon_key(sent)
        if len(key) < 20:
            continue
        yield Unit(
            uid=hashlib.blake2b(key.encode(), digest_size=10).hexdigest(),
            kind=classify(sent), text=sent,
            line_start=span[0], line_end=span[1],
            entities=ents,
            markers=sorted({m.lower() for m in NORM_RX.findall(sent)})[:6],
            lang=detect_lang(sent), contaminated=contaminated, sig=sig64(key),
        )


# ---------------------------------------------------------------- slice I/O
def atomic_write(path: str, data: str) -> None:
    """Inherited from prd_parser: write beside, then replace."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(data)
    os.replace(tmp, path)


def read_range(corpus: str, start: int, end: int):
    """Stream exactly [start, end] 1-based inclusive. Bounded memory by contract."""
    out = []
    with open(corpus, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, start=1):
            if i < start:
                continue
            if i > end:
                break
            out.append(line.rstrip("\n"))
    return out


def corpus_len(corpus: str) -> int:
    n = 0
    with open(corpus, encoding="utf-8", errors="replace") as fh:
        for _ in fh:
            n += 1
    return n


def corpus_id(corpus: str) -> str:
    h = hashlib.blake2b(digest_size=12)
    with open(corpus, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compile_range(corpus: str, start: int, end: int, slice_size: int, outdir: str,
                  cid: str, force: bool = False, quiet: bool = False,
                  readahead: int = READAHEAD):
    """Compile [start,end] into per-slice artifacts. Returns the manifest dict."""
    os.makedirs(outdir, exist_ok=True)
    # Case profile is a property of the corpus, cached beside the slices and keyed
    # by corpus_id so a changed corpus can never be judged by a stale table.
    global _CASE_TABLE
    ct_path = os.path.join(outdir, "casetable.json")
    ct = None
    if os.path.exists(ct_path):
        try:
            blob = json.load(open(ct_path, encoding="utf-8"))
            if blob.get("corpus_id") == cid:
                ct = blob["ratios"]
        except Exception:
            ct = None
    if ct is None:
        ct = build_case_table(corpus)
        atomic_write(ct_path, json.dumps({"corpus_id": cid, "ratios": ct}, indent=0))
    _CASE_TABLE = ct

    man_path = os.path.join(outdir, "manifest.json")
    man = {"schema_version": SCHEMA_VERSION, "corpus_id": cid, "slices": {}}
    if os.path.exists(man_path) and not force:
        try:
            old = json.load(open(man_path, encoding="utf-8"))
            if old.get("corpus_id") == cid:
                man = old
            elif not quiet:
                print("corpus_id changed -- previous slices are for a different corpus, "
                      "recompiling (old=%s new=%s)" % (old.get("corpus_id"), cid))
        except Exception:
            pass

    done = 0
    for s in range(start, end + 1, slice_size):
        e = min(s + slice_size - 1, end)
        sid = "s%07d_%07d" % (s, e)
        spath = os.path.join(outdir, sid + ".json")
        if man["slices"].get(sid, {}).get("state") == "done" and os.path.exists(spath) and not force:
            continue
        # BOTH directions are required, and the self-test proved it by failing when
        # only one was present:
        #   look-back  -- so a paragraph that began BEFORE this slice is recognised as
        #                 a continuation and skipped, instead of being emitted as a
        #                 fragment that starts at `s`.
        #   read-ahead -- so a paragraph that STARTS in this slice completes, instead
        #                 of being truncated at the end edge.
        # Removing look-back alone, or read-ahead alone, changes the unit set; only
        # the pair makes identity independent of where the slice edges fall.
        # `readahead=0` is the mutation the self-test drills.
        lo = max(start, s - LOOKBACK)
        lines = read_range(corpus, lo, e + readahead)
        units = [asdict(u) for u in extract_units(lines, lo, emit_from=s, emit_to=e)]
        atomic_write(spath, json.dumps(
            {"slice": sid, "corpus_id": cid, "line_start": s, "line_end": e,
             "unit_count": len(units), "units": units}, ensure_ascii=False, indent=1))
        man["slices"][sid] = {"state": "done", "line_start": s, "line_end": e,
                              "unit_count": len(units)}
        atomic_write(man_path, json.dumps(man, ensure_ascii=False, indent=1))
        done += 1
        if not quiet and done % 10 == 0:
            print("  ... %d slices written (through line %d)" % (done, e))
    return man


def load_units(outdir: str):
    """uid -> unit, merging duplicate uids and keeping every line occurrence."""
    units = {}
    # Match the slice NAME pattern, never "any .json that is not the manifest" --
    # the outdir also holds the case-profile cache, and a blacklist would have to
    # grow every time a sibling artifact is added beside the slices.
    for fn in sorted(os.listdir(outdir)):
        if not _SLICE_FN_RX.match(fn):
            continue
        d = json.load(open(os.path.join(outdir, fn), encoding="utf-8"))
        for u in d["units"]:
            cur = units.get(u["uid"])
            if cur is None:
                u["occurrences"] = [[u["line_start"], u["line_end"]]]
                units[u["uid"]] = u
            else:
                cur["occurrences"].append([u["line_start"], u["line_end"]])
    return units


def selftest() -> int:
    """Drive the boundary gate's RED branch on a corpus built to break it.

    The real-corpus run passed at two offsets with 65 units each and zero
    disagreement. That was not evidence: a gate only means something once it has
    been seen to fail. This builds a synthetic corpus whose paragraphs are long
    enough to straddle any slice edge, then asserts BOTH poles:

        readahead=400  ->  identical unit sets      (the fix works)
        readahead=0    ->  DIFFERENT unit sets      (the gate can fail)

    If the mutation does not turn it red, the gate is decorative and this exits 1
    -- a green that cannot go red is the thing this whole file is trying not to be.
    """
    import tempfile
    cid = "selftest"
    # 60 paragraphs x 9 lines = 540 lines. Every paragraph carries a normative
    # marker and a domain term, so every one is a material unit; the sentence is
    # split across lines so a truncating slice yields a DIFFERENT normalized text.
    paras = []
    for i in range(60):
        paras.append(
            "El sistema de baseline numero %d debe registrar su evidencia\n"
            "y nunca puede heredar una capability revocada, porque la\n"
            "applicability del contrato exige provenance verificable en\n"
            "cada promotion institucional registrada por el owner canonico\n"
            "para que el gate de enforcement pueda demostrar su failure\n"
            "semantics antes de bloquear cualquier mission futura numero %d\n"
            "y el registry debe conservar la metrica de coverage asociada\n"
            "al denominador descubierto y nunca al curado por memoria %d.\n" % (i, i, i))
    text = "\n".join(paras)

    with tempfile.TemporaryDirectory() as td:
        corpus = os.path.join(td, "synthetic_corpus.txt")
        with open(corpus, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        total = corpus_len(corpus)
        print("selftest corpus_lines=%d" % total)

        def run(readahead):
            sets = []
            for sz in (100, 150):
                with tempfile.TemporaryDirectory() as od:
                    compile_range(corpus, 1, total, sz, od, cid, force=True,
                                  quiet=True, readahead=readahead)
                    sets.append(set(load_units(od).keys()))
            return sets

        a, b = run(READAHEAD)
        fixed_ok = (a == b) and len(a) > 0
        print("POLE_GREEN readahead=%d  slice100=%d slice150=%d identical=%s"
              % (READAHEAD, len(a), len(b), a == b))

        c, d = run(0)
        broke = (c != d)
        print("POLE_RED   readahead=0    slice100=%d slice150=%d identical=%s"
              % (len(c), len(d), c == d))
        if broke:
            print("           mutation changed %d unit ids -- the gate can fail"
                  % len(c.symmetric_difference(d)))

    ok = fixed_ok and broke
    print("SELFTEST=%s" % ("PASS" if ok else "FAIL"))
    if not fixed_ok:
        print("  the fix does not hold: slice offset still changes the unit set")
    if not broke:
        print("  the MUTATION did not go red -- this gate proves nothing and must not "
              "be trusted as a done-gate")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="UCR-CIF corpus compiler")
    ap.add_argument("--corpus", default=None)
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=0, help="0 = end of corpus")
    ap.add_argument("--slice", type=int, default=DEFAULT_SLICE)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--verify-boundary", action="store_true",
                    help="compile a range twice under different slice offsets and "
                         "require identical unit-id sets")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--emit-units", default=None,
                    help="write the deduped unit corpus (W2's input) to this path")
    ap.add_argument("--readahead", type=int, default=READAHEAD,
                    help="0 reintroduces the slice-edge truncation bug; used by --selftest")
    ap.add_argument("--selftest", action="store_true",
                    help="drive the boundary gate's RED branch on a synthetic corpus "
                         "built to straddle a slice edge")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if not os.path.exists(args.corpus):
        print("CORPUS ABSENT: %s" % args.corpus)
        return 2
    cid = corpus_id(args.corpus)
    total = corpus_len(args.corpus)
    end = args.end or total
    print("corpus_lines=%d  corpus_id=%s  range=[%d,%d]  slice=%d"
          % (total, cid, args.start, end, args.slice))

    if args.verify_boundary:
        import tempfile
        lo, hi = args.start, min(args.start + 8000, end)
        sets = []
        for sz in (1000, 1500):                  # co-prime-ish offsets: edges land elsewhere
            with tempfile.TemporaryDirectory() as td:
                compile_range(args.corpus, lo, hi, sz, td, cid, force=True, quiet=True,
                              readahead=args.readahead)
                sets.append(set(load_units(td).keys()))
        a, b = sets
        same = a == b
        print("BOUNDARY_INDEPENDENCE range=[%d,%d] slice_a=1000(%d units) "
              "slice_b=1500(%d units) identical=%s" % (lo, hi, len(a), len(b), same))
        if not same:
            only_a, only_b = sorted(a - b)[:5], sorted(b - a)[:5]
            print("  only_in_a=%s\n  only_in_b=%s" % (only_a, only_b))
            print("VERDICT=FAIL -- a unit is being split by a slice edge")
            return 1
        print("VERDICT=PASS")
        return 0

    man = compile_range(args.corpus, args.start, end, args.slice, args.outdir, cid,
                        force=args.force)
    units = load_units(args.outdir)

    # ---- coverage proof: every line in range belongs to exactly one slice
    covered, gaps, overlaps = set(), [], []
    spans = sorted((v["line_start"], v["line_end"]) for v in man["slices"].values())
    cursor = args.start
    for s, e in spans:
        if s > cursor:
            gaps.append((cursor, s - 1))
        elif s < cursor:
            overlaps.append((s, cursor - 1))
        cursor = max(cursor, e + 1)
        covered.add((s, e))
    if cursor <= end:
        gaps.append((cursor, end))

    print("\n=== RESULT ===")
    print("slices=%d  unique_units=%d" % (len(man["slices"]), len(units)))
    print("coverage: gaps=%s overlaps=%s" % (gaps or "NONE", overlaps or "NONE"))

    kinds, langs, contam = {}, {}, 0
    for u in units.values():
        kinds[u["kind"]] = kinds.get(u["kind"], 0) + 1
        langs[u["lang"]] = langs.get(u["lang"], 0) + 1
        contam += bool(u["contaminated"])
    print("kinds=%s" % dict(sorted(kinds.items(), key=lambda kv: -kv[1])))
    print("lang=%s  contaminated_units=%d" % (langs, contam))
    dupes = sum(len(u["occurrences"]) - 1 for u in units.values())
    print("repeat_occurrences_folded=%d (same statement restated elsewhere)" % dupes)

    ok = True
    if gaps:
        print("CONTROL_FAIL coverage gap -- a compiled corpus with a hole is not compiled")
        ok = False
    lowtext = " ".join(u["text"].lower() for u in list(units.values())[:4000])
    for probe in POSITIVE_CONTROLS:
        if probe not in lowtext:
            print("CONTROL_FAIL positive control '%s' absent from extracted units" % probe)
            ok = False
    if not units:
        print("CONTROL_FAIL zero units extracted")
        ok = False
    print("CONTROLS=%s" % ("PASS" if ok else "FAIL"))

    if args.emit_units:
        # The deduped unit set is the artifact of value and W2's only input. The
        # per-slice files stay on disk for crash-survivability and audit, but they
        # are regenerable in seconds from (corpus_id, range, slice) and are not the
        # durable record.
        payload = {
            "schema_version": SCHEMA_VERSION, "corpus_id": cid,
            "corpus_lines": total, "range": [args.start, end],
            "slice_size": args.slice, "unit_count": len(units),
            "coverage_gaps": gaps, "coverage_overlaps": overlaps,
            "kinds": kinds, "lang": langs,
            "provenance": "compiled",
            "units": sorted(units.values(), key=lambda u: (u["line_start"], u["uid"])),
        }
        atomic_write(args.emit_units, json.dumps(payload, ensure_ascii=False, indent=1))
        print("emitted %d units -> %s" % (len(units), args.emit_units))

    if args.stats:
        ent = {}
        for u in units.values():
            for e_ in u["entities"]:
                ent[e_] = ent.get(e_, 0) + 1
        top = sorted(ent.items(), key=lambda kv: -kv[1])[:25]
        print("\ntop_entities=%s" % top)

    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
