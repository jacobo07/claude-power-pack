#!/usr/bin/env python
"""test_incremental_cognition_program.py -- done-gate of PLAN-INCREMENTAL-COGNITION-PROGRAM.

    python tools/test_incremental_cognition_program.py --final

A thin wrapper over tools/test_cognitive_economy_program.py (the CE verifier), following
the skill-capability precedent (tools/test_skill_capability_program.py): the CE clauses
read their module globals at call time, so this file rebinds them to this program and
calls the CE main(). The CE file is never edited -- a live mission runs on it.

Inherited unchanged: ledger clauses L1-L9 and the CE selftest, except CE's stale
V-CEP-REAL-HANDOFF line, replaced by the same two poles read from the probe file's
current history (as the SC wrapper does; CE defect handed to its owner, not edited here).

Added here:
  R2  consumed owners (--final and --pillar X): this is a delta program; pillars that close by consuming a
      CE / SC pillar (ledger.frozen.consumes) must cite, for each consumed pillar, an
      `owner_ledger` evidence {ref: <owner ledger path>, commit, pillar, terminal}. The
      owner ledger is read AT that commit with git (the commit must be reachable from HEAD,
      so the owner's work has to be on this line of history) and must show that pillar in
      that terminal. A handoff file alone cannot close a consuming pillar. `--pillar X` checks
      only X's consumed owners; `--final` checks every consuming pillar.
  R3 measurement scope (--final and --pillar X): a kme_pillars (or, for pillar L, a kme_replay) measurement file carries
      `evidence_role` and `terminal_evidence` as line-anchored front-matter fields. Only a reproduced
      primary file (terminal_evidence true) supports a terminal; a second_workload file supports one
      only when it is valid (coverage reached) AND the same pillar also cites such a primary file
      (frozen rule E: "confirmed on a second workload"); a smoke file (KME-G on GEX44) never does; a
      file measuring another pillar never does. A kme_pillars file (its `instrument` line, its
      json block marker or either role field; a leading BOM is ignored) without readable role fields is
      refused, never skipped; only a file with no kme_pillars mark at all is another instrument's and is left
      to the CE clauses. For pillars D..I a TERMINAL must cite at least one kme_pillars primary file whose
      terminal_evidence true agrees with its own fields (instrument mark, role primary, reproduced population,
      measured verdict, denominator inside the frozen rule table kept here, and a `frozen_source` that records the
      committed frozen file / CE ledger with its current sha256); a hand-written file cannot stand in.
      This is the mechanical form of "never substitute
      KME-G for KME-L". Pillar L is covered the same way for the offline replay ranking (wiki/tools/kme_replay.py,
      marked by its `instrument` line or its `<!-- kmer-json -->` block): a file's `terminal_evidence: true` is believed
      only when its own fields agree (instrument, role primary, exact population, denominator KME-L and the rule table
      kept here, `unranked_ids` an empty list, the committed frozen file with its current sha256); a smoke file
      (KME-G) is refused; and an L terminal of a measurement kind (RESEARCH_INSUFFICIENT_EVIDENCE,
      FALSIFIED_OR_REJECTED_BY_EVIDENCE) must cite such a primary file. Exactly these L dispositions need NO ranking
      file from R3 and R3 stays silent for them: AUTHORIZATION_BOUND, IMPLEMENTED_AND_VERIFIED,
      MERGED_INTO_EXISTING_OWNER, DEFERRED_STRONGER_OWNER, EXTERNAL_BLOCKED (the CE clause L4 still demands each one's
      own evidence kinds; V-ICP-R3-L-NEEDS-RANKING-TABLE pins this list against the CE terminals). A terminal file is
      also believed only at the frozen rollover growth, 100000, and only when its ranking is internally consistent.
  R4  owner decisions (--final and --pillar X): an `owner_decision` evidence is refused for every pillar when its ref
      names the owner bundle (vault/programs/incremental-cognition/owner-bundle.md), is a byte copy of it, or is a file
      the mission wrote (anything under the program's evidence/ except L-owner-decision*.md, anything under
      measurements/). Identity is judged, never spelling: the ref is resolved the way the CE evidence reader resolves it
      (`~` expanded, absolute paths accepted) and compared with os.path.samefile, then by its spelled tail under
      vault/programs/incremental-cognition/ (a second checkout, a Windows drive / backslash / mixed-case form), by its
      sha256, and by where a symlink really points. The bundle is the mission's request and names [L] and the other
      pillar tags, so the CE clause L4 alone would accept it; only a file the Owner wrote in their own words counts as
      the Owner's decision. And a name is not authorship (STATE debt (2), Owner decision (c), 2026-10-05): every
      other owner_decision ref is accepted only when its bytes (raw or line-ending-normalised sha256) appear in an
      `attest <sha256> <file>` line of vault/programs/incremental-cognition/OWNER-ATTESTATIONS.md; an absent or
      unreadable attestation file accepts nothing. On a shared host this binds the decision to exact bytes; it does
      not prove who wrote the attestation line.
  V-ICP-REBIND  the rebinding took: ledger.program must be "incremental-cognition", and a
      ledger read through any other program's path is refused.

Modes and exit codes are CE's: --final / --status / --pillar X / --selftest;
0 pass, 1 fail, 2 could not run. `--generation 2 --status|--final|--selftest` judges the IC-gen2 ledger
(vault/programs/incremental-cognition/gen2/ledger.json) through tools/ic_gen2.py, which rebinds the CE globals
only inside a context manager and prints its own ICP_GEN2_VERDICT / ICP_GEN2_SELFTEST lines; `--pillar` is
generation 1 only.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import posixpath
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_cognitive_economy_program as ce  # noqa: E402

PROGRAM = "incremental-cognition"
PROGRAM_DIR = f"vault/programs/{PROGRAM}/"
ce.SELF_REL = "tools/test_incremental_cognition_program.py"
ce.LEDGER_REL = PROGRAM_DIR + "ledger.json"
ce.FROZEN_AT_REL = PROGRAM_DIR + "FROZEN_AT"
ce.HANDOFF_DIR = PROGRAM_DIR + "handoffs/"
ce.PILLARS = [chr(c) for c in range(ord("A"), ord("N") + 1)]
# X2 (traceability rows): left unbound, the CE clause read CE's REQUIREMENTS and judged IC pillars against CE-D..CE-L
# rows (2026-10-05: D told to read MERGED, which is CE D's terminal). Bound here and watched by B1 like the rest.
CE_REQS = (ce.REQS_REL, ce.REQ_ROW)  # CE's own X2 binding, restored only while CE's own selftest runs
ce.REQS_REL =".planning/workstreams/incremental-cognition/REQUIREMENTS.md"
ce.REQ_ROW = re.compile(r"^\|\s*IC-([A-N])\s*\|[^|\n]*\|([^|\n]*)\|\s*$", re.M)
REPO = ce.REPO
BINDING = {"SELF_REL": ce.SELF_REL, "LEDGER_REL": ce.LEDGER_REL, "FROZEN_AT_REL": ce.FROZEN_AT_REL,
           "HANDOFF_DIR": ce.HANDOFF_DIR, "PILLARS": list(ce.PILLARS), "REQS_REL": ce.REQS_REL,
           "REQ_ROW": ce.REQ_ROW.pattern}

# ---------------------------------------------------------------- stale CE control
STALE_CE_CONTROL = "V-CEP-REAL-HANDOFF"
HANDOFF_PROBE = "vault/plans/cognitive-economy-program-2026-10-03.md"
_ce_selftest = ce.selftest


def real_handoff_control(verbose=True) -> bool:
    """Frozen at the probe's newest commit -> nothing landed after; frozen at the parent of
    its first commit -> landed. Poles read from history now, so later edits cannot stale it."""
    shas = ce._git("log", "--format=%H", "HEAD", "--", HANDOFF_PROBE).stdout.split()
    parent = ce._git("rev-parse", f"{shas[-1]}^").stdout.strip() if shas else ""
    if not shas or not parent:
        print(f"  INCONCLUSIVE V-ICP-REAL-HANDOFF: no history for {HANDOFF_PROBE}")
        return False

    def at(sha):
        return type("R", (ce.Resolver,), {"frozen_sha": lambda self: sha})()
    before = at(shas[0]).handoff_landed(HANDOFF_PROBE)
    after = at(parent).handoff_landed(HANDOFF_PROBE)
    good = before is False and after is True
    if verbose or not good:
        print(f"  {'ok  ' if good else 'FAIL'} V-ICP-REAL-HANDOFF (frozen at newest {shas[0][:8]} -> "
              f"{before}, frozen before first {shas[-1][:8]} -> {after}; replaces {STALE_CE_CONTROL})")
    return good


def ce_selftest_with_live_handoff(verbose=True) -> bool:
    buf = io.StringIO()
    mine = (ce.REQS_REL, ce.REQ_ROW)
    ce.REQS_REL, ce.REQ_ROW = CE_REQS  # CE's selftest drives CE-format rows; it judges CE's clause, not IC's binding
    try:
        with contextlib.redirect_stdout(buf):
            _ce_selftest(verbose=True)
    finally:
        ce.REQS_REL, ce.REQ_ROW = mine
    lines = buf.getvalue().splitlines()
    reached = any(STALE_CE_CONTROL in x for x in lines)
    other_fails = [x for x in lines if x.strip().startswith("FAIL") and STALE_CE_CONTROL not in x]
    for x in lines:
        if STALE_CE_CONTROL not in x and (verbose or x in other_fails):
            print(x)
    if not reached:
        print(f"  FAIL CE selftest never reached {STALE_CE_CONTROL}: it did not run to its end")
    return reached and not other_fails and real_handoff_control(verbose)


ce.selftest = ce_selftest_with_live_handoff


# ---------------------------------------------------------------- R2 consumed owners
class OwnerLedgers:
    """Reads an owner ledger at a commit. Faked in the selftest."""

    def reachable(self, sha: str) -> bool:
        return ce.Resolver().commit_reachable(sha)

    def terminal_at(self, sha: str, ref: str, pillar: str):
        r = ce._git("show", f"{sha}:{ref}")
        if r.returncode != 0:
            return None
        try:
            led = json.loads(r.stdout.lstrip("﻿"))
        except json.JSONDecodeError:
            return None
        return ((led.get("state") or {}).get(pillar) or {}).get("terminal")


def load_ledger() -> dict:
    """The program ledger as `--final` and `--pillar` read it (OSError / JSONDecodeError reach the caller)."""
    return json.loads((REPO / ce.LEDGER_REL).read_text(encoding="utf-8"))


def check_consumed(led: dict, owners: OwnerLedgers, only=None) -> list:
    """R2. `only` limits the check to those consuming pillars (--pillar X); None checks every one (--final)."""
    f = []
    consumes = (led.get("frozen") or {}).get("consumes") or {}
    for pid, wanted in consumes.items():
        if only is not None and pid not in only:
            continue
        st = (led.get("state") or {}).get(pid) or {}
        if not st.get("terminal"):
            continue  # an open pillar is L3's failure, not R2's
        cited = [e for e in st.get("evidence") or [] if e.get("kind") == "owner_ledger"]
        for w in wanted:
            ref, pillar = w.get("ledger"), w.get("pillar")
            hit = [e for e in cited if e.get("ref") == ref and e.get("pillar") == pillar]
            if not hit:
                f.append(f"R2 {pid}: consumes {ref}#{pillar} but cites no owner_ledger evidence for it")
                continue
            for e in hit:
                sha, claimed = e.get("commit") or "", e.get("terminal")
                if not owners.reachable(sha):
                    f.append(f"R2 {pid}: owner_ledger commit {sha!r} not reachable from HEAD")
                    continue
                got = owners.terminal_at(sha, ref, pillar)
                if got is None:
                    f.append(f"R2 {pid}: {ref}#{pillar} has no terminal at {sha[:8]}")
                elif got != claimed:
                    f.append(f"R2 {pid}: {ref}#{pillar} is {got} at {sha[:8]}, cited as {claimed}")
    return f


def check_binding(led: dict) -> list:
    f = []
    now = {"SELF_REL": ce.SELF_REL, "LEDGER_REL": ce.LEDGER_REL, "FROZEN_AT_REL": ce.FROZEN_AT_REL,
           "HANDOFF_DIR": ce.HANDOFF_DIR, "PILLARS": list(ce.PILLARS), "REQS_REL": ce.REQS_REL,
           "REQ_ROW": ce.REQ_ROW.pattern}
    for k, v in BINDING.items():
        if now[k] != v:
            f.append(f"B1 CE global {k} rebound away from this program: {now[k]!r}")
    if led.get("program") != PROGRAM:
        f.append(f"B1 ledger program is {led.get('program')!r}, not {PROGRAM!r}")
    return f


# ---------------------------------------------------------------- R3 measurement scope
def front_matter_fields(text: str) -> dict:
    """The line-anchored `key: <json>` lines between the first two `---` lines. A value that is
    not valid JSON is absent. Text that does not open with `---` has no front matter."""
    lines = [x.rstrip("\r") for x in (text or "").lstrip("\ufeff").split("\n")]   # a BOM is not front matter
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}
    out = {}
    for ln in lines[1:end]:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*): (.*)$", ln)
        if not m:
            continue
        try:
            out[m.group(1)] = json.loads(m.group(2))
        except json.JSONDecodeError:
            continue
    return out


KNOWN_ROLES = ("primary", "second_workload", "smoke")
KMEP_INSTRUMENT = "wiki/tools/kme_pillars.py"
KMEP_BODY_MARKER = "<!-- kmep-json -->"
KMEP_BODY_END = "<!-- /kmep-json -->"
# The fields kme_pillars writes into the front matter (mirrors kme_pillars.FRONT_KEYS + FRONT_OPTIONAL; test_kme_pillars
# pins the two equal). Its json block carries the same result object, so each must agree with the block.
KMEP_AGREE_KEYS = ("instrument", "pillar", "denominator", "denominator_kind", "rule_denominators", "evidence_role",
                   "terminal_evidence", "terminal_evidence_reason", "second_workload_valid", "plane", "measured_at",
                   "until", "command", "population_match", "numerator", "share_interval", "share_measured_population",
                   "threshold", "materiality", "materiality_reason", "observability", "second_workload_required",
                   "estimate_model", "since", "until_located", "coverage", "second_workload_confirms", "frozen_source")
KMEP_THRESHOLD = 0.03


def is_kmep_file(text: str, fm: dict) -> bool:
    """A measurement written by kme_pillars: its `instrument` front-matter line, or the json block marker it always
    appends, or either role field. Judged on the whole text, so a damaged or BOM-prefixed front matter does not hide it."""
    t = (text or "").lstrip("\ufeff")
    return (fm.get("instrument") == KMEP_INSTRUMENT or KMEP_BODY_MARKER in t
            or f'"instrument": "{KMEP_INSTRUMENT}"' in t or "evidence_role" in fm or "terminal_evidence" in fm)


def is_kmer_file(text: str, fm: dict) -> bool:
    """A ranking written by kme_replay: its `instrument` front-matter line, its json block marker, or the instrument
    line inside the json block. Judged on the whole text, so a damaged or BOM-prefixed front matter does not hide it."""
    t = (text or "").lstrip("\ufeff")
    return fm.get("instrument") == KMER_INSTRUMENT or KMER_BODY_MARKER in t or f'"instrument": "{KMER_INSTRUMENT}"' in t


KME_PILLARS = ("D", "E", "F", "G", "H", "I")
# Pillar L's instrument (plan 05-03): the offline replay ranker. Mirrors wiki/tools/kme_replay.py; test_kme_replay pins
# the tables equal (V-KMER-R3-TABLE-PINNED).
KMER_INSTRUMENT = "wiki/tools/kme_replay.py"
KMER_BODY_MARKER = "<!-- kmer-json -->"
KMER_BODY_END = "<!-- /kmer-json -->"
KMER_CANDIDATES = ("late_rollover", "identical_rereads", "unchanged_precondition_retries")
KMER_ROLLOVER_GROWTH = 100000     # the frozen late_rollover threshold; any other G is sensitivity / smoke only
REPLAY_PILLARS = ("L",)
REPLAY_RULE_DENOMINATORS = {"L": ["KME-L"]}
MEASUREMENT_TERMINALS = ("RESEARCH_INSUFFICIENT_EVIDENCE", "FALSIFIED_OR_REJECTED_BY_EVIDENCE")
OWNER_BUNDLE_REL = PROGRAM_DIR + "owner-bundle.md"
# The frozen rule's denominators per pillar (ledger frozen.pillars rule text; mirrors kme_pillars.RULE_DENOMINATORS,
# and test_kme_pillars pins the two equal). A file's own `rule_denominators` is checked against THIS table, never
# trusted alone.
FROZEN_RULE_DENOMINATORS = {"D": ["KME-L", "CPP-D-W7"], "E": ["KME-L"], "F": ["KME-L"], "G": ["KME-L"],
                            "H": ["KME-L"], "I": ["KME-L"]}
MEASURED_VERDICTS = (">= 3 %", "< 3 %", "STRADDLES")
# The committed frozen sources a terminal file must have been measured against (mirrors kme_pillars.DENOMS_REL /
# CE_LEDGER_REL; test_kme_pillars pins the two equal). A file records the path and sha256 of the source it read.
FROZEN_SOURCE_DEFAULTS = {
    "frozen_file": "vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json",
    "ce_ledger": "vault/programs/cognitive-economy/ledger.json",
}


def frozen_source_problems(den, fm: dict) -> list:
    """WR-07: the file was measured against the committed frozen source, whose recorded sha256 is still the committed
    file's."""
    bad = []
    src = fm.get("frozen_source")
    need = "ce_ledger" if den == "CPP-D-W7" else "frozen_file"
    ent = src.get(need) if isinstance(src, dict) else None
    if not isinstance(src, dict) or src.get("all_default") is not True or not isinstance(ent, dict):
        bad.append("frozen_source is absent or says a non-default frozen source was read")
    elif ent.get("default") is not True or ent.get("path") != FROZEN_SOURCE_DEFAULTS[need]:
        bad.append(f"frozen_source {need} is {ent.get('path')!r}, not the committed {FROZEN_SOURCE_DEFAULTS[need]!r}")
    else:
        p = REPO / FROZEN_SOURCE_DEFAULTS[need]
        now = ce.lf_sha256(p) if p.is_file() else None
        if ent.get("sha256") != now:
            bad.append(f"frozen_source {need} sha256 {ent.get('sha256')!r} is not the committed file's {now!r}")
    return bad


# The fields a kme_replay file states twice, in its front matter and in its json block: the two must agree.
KMER_AGREE_KEYS = ("instrument", "pillar", "denominator", "evidence_role", "terminal_evidence", "population_match",
                   "weighted_denominator", "rollover_growth", "ranked_ids", "unranked_ids", "frozen_source")


def kmer_ranking_problems(fm: dict, text) -> list:
    """WR-03: why a kme_replay file's ranking contradicts itself. ranked_ids and unranked_ids must be lists that are
    disjoint and together exactly the three candidates; the file carries exactly one parseable json block, and the
    block agrees with the front matter on every field both state."""
    bad = []
    r, u = fm.get("ranked_ids"), fm.get("unranked_ids")
    if not (isinstance(r, list) and isinstance(u, list)):
        bad.append(f"ranked_ids / unranked_ids are {r!r} / {u!r}, not two lists")
    elif (set(r) & set(u) or len(set(r)) != len(r) or len(set(u)) != len(u)
          or set(r) | set(u) != set(KMER_CANDIDATES) or len(r) + len(u) != len(KMER_CANDIDATES)):
        bad.append(f"ranked_ids {r!r} and unranked_ids {u!r} are not disjoint and exactly the three candidates "
                   f"{list(KMER_CANDIDATES)}")
    wd = fm.get("weighted_denominator")
    if isinstance(wd, bool) or not isinstance(wd, (int, float)) or not wd > 0:
        bad.append(f"weighted_denominator is {wd!r}, not a positive number")
    t = (text or "").lstrip("\ufeff")
    if t.count(KMER_BODY_MARKER) != 1 or t.count(KMER_BODY_END) != 1:
        return bad + [f"the file does not carry exactly one {KMER_BODY_MARKER} json block"]
    a = t.index(KMER_BODY_MARKER) + len(KMER_BODY_MARKER)
    b = t.index(KMER_BODY_END)
    try:
        block = json.loads(t[a:b]) if a <= b else None
    except json.JSONDecodeError:
        block = None
    if not isinstance(block, dict):
        return bad + ["the json block is not a parseable object"]
    for k in KMER_AGREE_KEYS:
        if block.get(k) != fm.get(k):
            bad.append(f"json block {k} {block.get(k)!r} disagrees with the front matter {fm.get(k)!r}")
    ranked = block.get("ranked")
    if isinstance(r, list) and (not isinstance(ranked, list) or
                                [e.get("candidate") if isinstance(e, dict) else None for e in ranked] != r):
        bad.append("json block ranked entries are not the front matter's ranked_ids, in order")
    return bad


def kmep_verdict(share_interval, population_match, observability):
    """The verdict kme_pillars.materiality gives these fields (mirrored; V-ICP-R3-KMEP-VERDICT-MIRROR drives both)."""
    if population_match == "drifted" or not (isinstance(share_interval, list) and len(share_interval) == 2):
        return "UNMEASURED"
    lo, hi = share_interval
    if not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in (lo, hi)):
        return "UNMEASURED"
    obs = observability if isinstance(observability, (int, float)) and not isinstance(observability, bool) else 0.0
    if lo >= KMEP_THRESHOLD:
        return ">= 3 %"
    if obs < 1.0:
        return "UNMEASURED"
    return "< 3 %" if hi < KMEP_THRESHOLD else "STRADDLES"


def kmep_block_problems(fm: dict, text) -> list:
    """STATE named debt (1) / 05 WR-03 class: a kme_pillars terminal claim is believed only when the file carries exactly
    one parseable json block that agrees with the front matter on every field the instrument writes, and the stated
    verdict is the one its own share interval gives. Hand-editing the front matter alone is caught by the block; editing
    both consistently is caught by the verdict recomputation."""
    t = (text or "").lstrip("\ufeff")
    if t.count(KMEP_BODY_MARKER) != 1 or t.count(KMEP_BODY_END) != 1:
        return [f"the file does not carry exactly one {KMEP_BODY_MARKER} json block"]
    a = t.index(KMEP_BODY_MARKER) + len(KMEP_BODY_MARKER)
    b = t.index(KMEP_BODY_END)
    try:
        block = json.loads(t[a:b]) if a <= b else None
    except json.JSONDecodeError:
        block = None
    if not isinstance(block, dict):
        return ["the json block is not a parseable object"]
    bad = [f"json block {k} {block.get(k)!r} disagrees with the front matter {fm.get(k)!r}"
           for k in KMEP_AGREE_KEYS if block.get(k) != fm.get(k)]
    want = kmep_verdict(fm.get("share_interval"), fm.get("population_match"), fm.get("observability"))
    if fm.get("materiality") != want:
        bad.append(f"materiality {fm.get('materiality')!r} is not the verdict its share_interval "
                   f"{fm.get('share_interval')!r} gives ({want!r})")
    return bad


def rollover_growth_problems(fm: dict) -> list:
    """WR-04: a terminal ranking is the one at the frozen rollover growth, recorded in the file; the late_rollover figure at
    any other G (a CLI flag) is a statement about that G."""
    g = fm.get("rollover_growth")
    if type(g) is not int or g != KMER_ROLLOVER_GROWTH:
        return [f"rollover_growth is {g!r}, not the frozen {KMER_ROLLOVER_GROWTH} (another G is sensitivity / smoke only)"]
    return []


def terminal_claim_problems(pid: str, fm: dict, text=None) -> list:
    """Why a measurement file that says `terminal_evidence: true` contradicts itself. A claim is believed only when
    the file's own fields agree with it. Pillars D..I (kme_pillars): role primary, the instrument's own mark, a
    population that reproduced the frozen denominator (a referenced CPP-D-W7 only at coverage exactly 1), a measured
    verdict, a denominator inside this pillar's frozen rule, the committed frozen source. Pillar L (kme_replay): the
    same, with an exact population, denominator KME-L, nothing unranked, and no verdict field (it ranks, it does not
    give a verdict)."""
    if fm.get("terminal_evidence") is not True or (pid not in KME_PILLARS and pid not in REPLAY_PILLARS):
        return []
    bad = []
    pm, den = fm.get("population_match"), fm.get("denominator")
    if pid in REPLAY_PILLARS:
        rule = REPLAY_RULE_DENOMINATORS[pid]
        if fm.get("instrument") != KMER_INSTRUMENT:
            bad.append(f"instrument is {fm.get('instrument')!r}, not {KMER_INSTRUMENT!r}")
        if fm.get("evidence_role") != "primary":
            bad.append(f"evidence_role is {fm.get('evidence_role')!r}, not 'primary'")
        if pm != "exact":
            bad.append(f"population_match is {pm!r}, not an exact reproduction of the frozen population")
        if fm.get("rule_denominators") != rule:
            bad.append(f"rule_denominators {fm.get('rule_denominators')!r} is not the frozen rule {rule!r}")
        if den not in rule:
            bad.append(f"denominator {den!r} is not in pillar {pid}'s frozen rule {rule!r}")
        if fm.get("unranked_ids") != []:
            bad.append(f"unranked_ids is {fm.get('unranked_ids')!r}, not [] (every candidate must be measured)")
        return bad + rollover_growth_problems(fm) + kmer_ranking_problems(fm, text) + frozen_source_problems(den, fm)
    if fm.get("instrument") != KMEP_INSTRUMENT:
        bad.append(f"instrument is {fm.get('instrument')!r}, not {KMEP_INSTRUMENT!r}")
    if fm.get("evidence_role") != "primary":
        bad.append(f"evidence_role is {fm.get('evidence_role')!r}, not 'primary'")
    if not (pm == "exact" or (pm == "referenced" and den == "CPP-D-W7" and fm.get("coverage") == 1.0)):
        bad.append(f"population_match is {pm!r} (coverage {fm.get('coverage')!r}), not a reproduced population")
    if fm.get("materiality") not in MEASURED_VERDICTS:
        bad.append(f"materiality is {fm.get('materiality')!r}, not a measured verdict")
    rule = FROZEN_RULE_DENOMINATORS[pid]
    if fm.get("rule_denominators") != rule:
        bad.append(f"rule_denominators {fm.get('rule_denominators')!r} is not the frozen rule {rule!r}")
    if den not in rule:
        bad.append(f"denominator {den!r} is not in pillar {pid}'s frozen rule {rule!r}")
    return bad + frozen_source_problems(den, fm) + kmep_block_problems(fm, text)


def check_measurement_scope(led: dict, res, only=None) -> list:
    f = []
    for pid in (list(only) if only is not None else list(ce.PILLARS)):
        st = (led.get("state") or {}).get(pid) or {}
        files = []
        texts = {}
        for e in st.get("evidence") or []:
            ref = e.get("ref")
            if e.get("kind") != "measurement" or not ref:
                continue
            text = res.file_text(ref)
            fm = front_matter_fields(text)
            if not (is_kmep_file(text, fm) or is_kmer_file(text, fm)):
                continue  # another instrument's measurement: the CE clauses judge it
            if not isinstance(fm.get("evidence_role"), str) or not isinstance(fm.get("terminal_evidence"), bool):
                f.append(f"R3 {pid}: {ref} is a kme_pillars / kme_replay measurement without readable evidence_role / "
                         f"terminal_evidence front matter (absent, unparseable or hand-edited)")
                continue
            files.append((ref, fm))
            texts[ref] = text
        on_pillar = [(r, fm) for r, fm in files if fm.get("pillar", pid) == pid]
        has_primary = any((fm.get("evidence_role") or "primary") == "primary" and fm.get("terminal_evidence") is True
                          and not terminal_claim_problems(pid, fm, texts.get(_r)) for _r, fm in on_pillar)
        needs_primary = (pid in KME_PILLARS or (pid in REPLAY_PILLARS and st.get("terminal") in MEASUREMENT_TERMINALS))
        if st.get("terminal") and needs_primary and not has_primary and not any(
                fm.get("pillar", pid) != pid or terminal_claim_problems(pid, fm, texts.get(_r)) for _r, fm in files):
            if pid in REPLAY_PILLARS:
                f.append(f"R3 {pid}: terminal {st.get('terminal')} cites no kme_replay primary ranking file with "
                         f"terminal_evidence true (a smoke, hand-written or other-instrument file cannot stand in "
                         f"for the KME-L ranking)")
            else:
                f.append(f"R3 {pid}: terminal {st.get('terminal')} cites no kme_pillars primary measurement file "
                         f"with terminal_evidence true (a hand-written or other-instrument file cannot stand in for it)")
        for ref, fm in files:
            if fm.get("pillar", pid) != pid:
                f.append(f"R3 {pid}: {ref} measures pillar {fm.get('pillar')}")
                continue
            role = fm.get("evidence_role") or "primary"
            if role not in KNOWN_ROLES:
                f.append(f"R3 {pid}: {ref} has unknown evidence_role {role!r}")
            elif role == "smoke":
                f.append(f"R3 {pid}: {ref} is a smoke measurement (instrument evidence, never terminal)")
            elif role == "second_workload":
                if fm.get("second_workload_valid") is not True:
                    f.append(f"R3 {pid}: {ref} is a second_workload file with second_workload_valid "
                             f"{fm.get('second_workload_valid')!r} (coverage not reached)")
                elif fm.get("materiality") == "UNMEASURED":
                    f.append(f"R3 {pid}: {ref} is a second_workload file whose own verdict is UNMEASURED "
                             f"(an unmeasured run confirms nothing)")
                elif not has_primary:
                    f.append(f"R3 {pid}: {ref} is a second_workload file cited without a primary file with "
                             f"terminal_evidence true for pillar {pid}")
            elif fm.get("terminal_evidence") is not True:
                f.append(f"R3 {pid}: {ref} is not terminal evidence: "
                         f"{fm.get('terminal_evidence_reason') or 'terminal_evidence is not true'}")
            else:
                for why in terminal_claim_problems(pid, fm, texts.get(ref)):
                    f.append(f"R3 {pid}: {ref} claims terminal_evidence true but {why}")
    return f


BUNDLE_WHY = "is the owner bundle: the mission's request is never the Owner's answer (only the Owner's own words count)"


def _spelled_tail(ref: str):
    """The ref as a posix-normalised, case-folded string with any Windows drive letter dropped (`C:\\Users\\...` and
    `c:/...` are the laptop's spellings; NTFS names are case-insensitive), and the part after the program directory when
    it has one (`vault/programs/incremental-cognition/` anywhere in it, so a second checkout's absolute path counts)."""
    s = re.sub(r"^[A-Za-z]:", "", ref.strip().replace("\\", "/"))
    s = posixpath.normpath(s).casefold()
    probe = "/" + s.lstrip("/")
    i = probe.find("/" + PROGRAM_DIR.casefold())
    return s, (probe[i + 1 + len(PROGRAM_DIR):] if i >= 0 else None)


def _resolved_paths(ref: str) -> list:
    """The existing files the ref reads as, resolved the way the CE evidence reader (L4) resolves it: `~` expanded,
    absolute paths accepted, otherwise relative to this checkout."""
    out = []
    for cand in (ref, ref.replace("\\", "/")):
        try:
            p = ce.Resolver._path(cand)
            if p.exists() and p not in out:
                out.append(p)
        except (OSError, RuntimeError, ValueError):
            continue
    return out


def names_the_bundle(ref) -> bool:
    """Identity, not spelling: True when the ref is the owner bundle however it is written. Resolved through the same
    reader the gate uses (so `~`, absolute paths and symlinks land on the real file, compared with os.path.samefile),
    and by its spelled tail (a second checkout of this repository, whose file is a different file)."""
    if not isinstance(ref, str) or not ref.strip():
        return False
    bundle = REPO / OWNER_BUNDLE_REL
    for p in _resolved_paths(ref):
        try:
            if bundle.exists() and os.path.samefile(p, bundle):
                return True
        except OSError:
            continue
    spelled, tail = _spelled_tail(ref)
    return spelled == OWNER_BUNDLE_REL.casefold() or tail == "owner-bundle.md"


DECISION_FILE = re.compile(r"^l-owner-decision.*\.md$", re.IGNORECASE)   # the name the bundle tells the Owner to use
MISSION_WRITTEN_WHY = ("is a file the mission wrote (under evidence/ or measurements/ of the program directory; only "
                       "evidence/L-owner-decision*.md can be the Owner's decision, in their own words)")
COPY_WHY = "is a byte copy of the owner bundle: the mission's request is never the Owner's answer"
# STATE debt (2), Owner decision (c) 2026-10-05: an owner_decision counts only for bytes the Owner attested, one
# `attest <sha256> <file>` line each. A list so the selftest can point it at scratch; the repo file is never written here.
ATTESTATIONS_FILE = [REPO / PROGRAM_DIR / "OWNER-ATTESTATIONS.md"]


def _mission_written_rel(rel) -> bool:
    """rel = a path below the program directory (case-folded, posix), or None."""
    if rel is None:
        return False
    if rel.startswith("measurements/"):
        return True
    return rel.startswith("evidence/") and not DECISION_FILE.match(posixpath.basename(rel))


def is_mission_written(ref) -> bool:
    """True when the ref is a program-written file: by its spelled tail, or by where it really resolves (a symlink
    named like a decision file that points into evidence/ is still the mission's file)."""
    if _mission_written_rel(_spelled_tail(ref)[1]):
        return True
    try:
        prog = Path(os.path.realpath(REPO / PROGRAM_DIR))
    except OSError:
        return False
    for p in _resolved_paths(ref):
        try:
            rel = Path(os.path.realpath(p)).relative_to(prog).as_posix().casefold()
        except (OSError, ValueError):
            continue
        if _mission_written_rel(rel):
            return True
    return False


def _digests(path: Path) -> set:
    raw = path.read_bytes()
    return {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()}


def same_bytes_as_bundle(ref) -> bool:
    """True when a file the ref reads as has the bundle's content (raw or line-ending-normalised sha256)."""
    bundle = REPO / OWNER_BUNDLE_REL
    if not bundle.is_file():
        return False
    want = _digests(bundle)
    for p in _resolved_paths(ref):
        try:
            if p.is_file() and _digests(p) & want:
                return True
        except OSError:
            continue
    return False


UNATTESTED_WHY = ("has no Owner attestation of these exact bytes (an `attest <sha256> <file>` line in "
                  f"{PROGRAM_DIR}OWNER-ATTESTATIONS.md; STATE debt (2), Owner decision (c), 2026-10-05)")


def attested_digests() -> set:
    """The sha256 values the Owner attested. Unreadable or absent file: none, so nothing is accepted."""
    try:
        text = Path(ATTESTATIONS_FILE[0]).read_text(encoding="utf-8-sig")
    except OSError:
        return set()
    return {m.group(1).lower() for m in re.finditer(r"(?m)^attest\s+([0-9a-fA-F]{64})\b", text)}


def unattested_problem(ref):
    """None only when a file the ref reads as has attested bytes (raw or line-ending-normalised sha256): the name of
    a file says nothing about who wrote it, its bytes bound to an attestation do."""
    want = attested_digests()
    for p in (_resolved_paths(ref) if want else []):
        try:
            if p.is_file() and _digests(p) & want:
                return None
        except OSError:
            continue
    return UNATTESTED_WHY


def owner_decision_problem(ref):
    """Why an owner_decision evidence ref cannot be the Owner's answer, or None."""
    if names_the_bundle(ref):
        return BUNDLE_WHY
    if same_bytes_as_bundle(ref):
        return COPY_WHY
    if is_mission_written(ref):
        return MISSION_WRITTEN_WHY
    return unattested_problem(ref)


def check_owner_decisions(led: dict, only=None) -> list:
    """R4: the owner bundle is the mission's request, never the Owner's answer."""
    f = []
    for pid in (list(only) if only is not None else list((led.get("state") or {}))):
        for e in ((led.get("state") or {}).get(pid) or {}).get("evidence") or []:
            if e.get("kind") == "owner_decision":
                why = owner_decision_problem(e.get("ref"))
                if why:
                    f.append(f"R4 {pid}: owner_decision {e.get('ref')} {why}")
    return f


# ---------------------------------------------------------------- R4 poles (selftest helpers)
@contextlib.contextmanager
def _home(path):
    saved = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
    os.environ["HOME"] = os.environ["USERPROFILE"] = str(path)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


_R4_SCRATCH = []


def r4_identity_poles() -> dict:
    """{name: (ref, expected refused)}: refs that name the bundle (or a mission-written file) in another spelling, and the
    accepted shapes (expected False). Built in a scratch directory; the repo is never written."""
    if not _R4_SCRATCH:
        _R4_SCRATCH.append(tempfile.TemporaryDirectory(prefix="icp-r4-"))
    td = Path(_R4_SCRATCH[0].name)
    bundle = REPO / OWNER_BUNDLE_REL
    raw = bundle.read_bytes()
    poles = {}
    # a second checkout of the same repository: the same repo-relative path under another root, different bytes
    second = td / "checkout2" / OWNER_BUNDLE_REL
    second.parent.mkdir(parents=True, exist_ok=True)
    second.write_bytes(raw + b"\nedited in the second checkout\n")
    poles["second-checkout-abs"] = (str(second), True)
    poles["main-checkout-abs"] = (str(REPO.parent / OWNER_BUNDLE_REL), True)
    poles["absolute-this-checkout"] = (str(bundle), True)
    poles["tilde"] = ("~/" + REPO.relative_to(REPO.parent).as_posix() + "/" + OWNER_BUNDLE_REL, True)
    link = td / "link-to-bundle.md"
    if not link.exists():
        try:
            os.symlink(str(bundle), str(link))
        except (OSError, NotImplementedError):
            pass
    if link.is_symlink():
        poles["symlink"] = (str(link), True)
    # the laptop's spellings: a Windows drive path with backslashes, and NTFS's case-insensitive names
    win = "C:\\Users\\User\\repo\\" + OWNER_BUNDLE_REL.replace("/", "\\")
    poles["windows-drive-backslash"] = (win, True)
    poles["windows-drive-case-variant"] = (win.replace("vault", "VAULT").replace("owner-bundle", "Owner-Bundle")
                                           .replace("programs", "Programs").replace("incremental-cognition",
                                                                                    "Incremental-Cognition"), True)
    poles["relative-case-variant"] = ("Vault/Programs/Incremental-Cognition/OWNER-BUNDLE.md", True)
    poles["windows-forward-slash-drive"] = ("c:/repo/" + OWNER_BUNDLE_REL, True)
    poles["unrelated-windows-path-unattested"] = ("C:\\Users\\User\\Desktop\\my-decision.md", True)
    # WR-02: a verbatim copy of the bundle, and files the mission wrote, are never the Owner's own words
    copy_ = td / "decision-copy.md"
    copy_.write_bytes(raw)
    poles["byte-copy-of-bundle"] = (str(copy_), True)
    crlf = td / "decision-copy-crlf.md"
    crlf.write_bytes(raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    poles["byte-copy-of-bundle-crlf"] = (str(crlf), True)
    poles["mission-evidence-file"] = (PROGRAM_DIR + "evidence/L.md", True)
    poles["mission-evidence-file-absolute"] = (str(REPO / PROGRAM_DIR / "evidence" / "L.md"), True)
    poles["mission-evidence-file-case"] = ("Vault/Programs/Incremental-Cognition/Evidence/l.md", True)
    meas = sorted((REPO / PROGRAM_DIR / "measurements").glob("*.md"))
    if meas:
        poles["mission-measurement-file"] = (meas[0].relative_to(REPO).as_posix(), True)
    poles["mission-evidence-in-second-checkout"] = (str(td / "checkout2" / PROGRAM_DIR / "evidence" / "L.md"), True)
    decoy = td / "checkout2" / PROGRAM_DIR / "evidence" / "L-owner-decision-decoy.md"
    if not decoy.exists():
        try:
            os.symlink(str(REPO / PROGRAM_DIR / "evidence" / "L.md"), str(decoy))
        except (OSError, NotImplementedError):
            pass
    if decoy.is_symlink():
        poles["decision-named-symlink-to-evidence"] = (str(decoy), True)
    # debt (2), Owner decision (c): only attested bytes are the Owner's decision. The attestation file lives in scratch
    # (r4_attestations_path), written here with the LF-normalised sha256 of the accepted fixture only.
    dec = td / "checkout2" / PROGRAM_DIR / "evidence" / "L-owner-decision.md"
    dec.parent.mkdir(parents=True, exist_ok=True)
    dec.write_bytes(b"# Decision\n\nIn my own words: decline [L] live sessions.\n")
    edited = td / "checkout2" / PROGRAM_DIR / "evidence" / "L-owner-decision-edited.md"
    edited.write_bytes(b"# Decision\n\nIn my own words: approve [L] live sessions.\n")
    unattested = td / "checkout2" / PROGRAM_DIR / "evidence" / "L-owner-decision-unattested.md"
    unattested.write_bytes(b"# Decision\n\nWritten by someone, attested by nobody.\n")
    crlf_dec = td / "decision-crlf.md"
    crlf_dec.write_bytes(dec.read_bytes().replace(b"\n", b"\r\n"))
    lf = hashlib.sha256(dec.read_bytes()).hexdigest()
    was = hashlib.sha256(b"# Decision\n\nIn my own words: decline [L] live sessions.\n").hexdigest()
    r4_attestations_path().write_text(f"attest {lf} {dec.name}\n" f"attest {was} {edited.name}\n", encoding="utf-8")
    poles["accepted-owner-decision-attested"] = (str(dec), False)
    poles["accepted-owner-decision-attested-crlf"] = (str(crlf_dec), False)
    poles["decision-edited-after-attestation"] = (str(edited), True)
    poles["decision-named-but-unattested"] = (str(unattested), True)
    poles["decision-relative-not-attested"] = (PROGRAM_DIR + "evidence/L-owner-decision.md", True)
    return poles


def r4_attestations_path() -> Path:
    """The scratch attestation file the R4 poles are judged against (never the repo's OWNER-ATTESTATIONS.md)."""
    if not _R4_SCRATCH:
        _R4_SCRATCH.append(tempfile.TemporaryDirectory(prefix="icp-r4-"))
    return Path(_R4_SCRATCH[0].name) / "OWNER-ATTESTATIONS.md"


@contextlib.contextmanager
def _attestations(path):
    saved = ATTESTATIONS_FILE[0]
    ATTESTATIONS_FILE[0] = Path(path)
    try:
        yield
    finally:
        ATTESTATIONS_FILE[0] = saved


def _old_string_bundle_ref(ref) -> bool:
    """The pre-fix R4 identity: spelling only (backslashes, ./, the absolute path of THIS checkout)."""
    if not isinstance(ref, str) or not ref:
        return False
    r = posixpath.normpath(ref.replace("\\", "/"))
    if r.startswith("/"):
        try:
            r = Path(r).relative_to(REPO).as_posix()
        except ValueError:
            return False
    return r == OWNER_BUNDLE_REL


def _patch_attr(name, fn):
    saved = globals()[name]
    globals()[name] = fn

    def restore():
        globals()[name] = saved
    return restore


def _spelled_tail_case_sensitive(ref: str):
    """The pre-fix tail: no drive-letter strip, no case folding."""
    s = posixpath.normpath(ref.strip().replace("\\", "/"))
    probe = "/" + s.lstrip("/")
    i = probe.find("/" + PROGRAM_DIR)
    return s, (probe[i + 1 + len(PROGRAM_DIR):] if i >= 0 else None)


R4_MUTANTS = {
    "r4-no-byte-compare": lambda: _patch_attr("same_bytes_as_bundle", lambda ref: False),
    "r4-mission-files-accepted": lambda: _patch_attr("is_mission_written", lambda ref: False),
    "r4-case-sensitive-spelling": lambda: _patch_attr("_spelled_tail", _spelled_tail_case_sensitive),
    "r4-string-compare": lambda: _patch_attr("owner_decision_problem",
                                             lambda ref: "the owner bundle" if _old_string_bundle_ref(ref) else None),
    # debt (2) before decision (c): a decision-named file was accepted by its name alone
    "r4-attestation-ignored": lambda: _patch_attr("unattested_problem", lambda ref: None),
}


class FakeOwners(OwnerLedgers):
    def __init__(self, table):
        self.table = table  # {(sha, ref, pillar): terminal}

    def reachable(self, sha):
        return sha in {k[0] for k in self.table}

    def terminal_at(self, sha, ref, pillar):
        return self.table.get((sha, ref, pillar))


def selftest(verbose=True) -> bool:
    ok = True

    def say(good, label):
        nonlocal ok
        if not good:
            ok = False
            print(f"  FAIL {label}")
        elif verbose:
            print(f"  ok   {label}")

    led = json.loads((REPO / ce.LEDGER_REL).read_text(encoding="utf-8"))
    say(not check_binding(led), "V-ICP-REBIND-CLEAN (globals bound here, ledger.program matches)")
    other = copy.deepcopy(led)
    other["program"] = "skill-capability"
    say(any(x.startswith("B1") for x in check_binding(other)), "V-ICP-MUT-foreign-ledger killed by B1")
    saved = ce.LEDGER_REL
    ce.LEDGER_REL = "vault/programs/skill-capability/ledger.json"
    say(any(x.startswith("B1") for x in check_binding(led)), "V-ICP-MUT-rebound-global killed by B1")
    ce.LEDGER_REL = saved
    saved = ce.REQS_REL
    ce.REQS_REL = ".planning/workstreams/cognitive-economy/REQUIREMENTS.md"
    say(any(x.startswith("B1") for x in check_binding(led)), "V-ICP-MUT-rebound-reqs killed by B1")
    ce.REQS_REL = saved

    # X2 reads THIS program's traceability rows: an IC row naming the terminal passes, a wrong terminal and a
    # CE-format row (the 2026-10-05 cross-program read) each fail.
    def x2(text, term="FALSIFIED_OR_REJECTED_BY_EVIDENCE"):
        res = type("R", (ce.Resolver,), {"file_text": lambda self, rel: text if rel == ce.REQS_REL else ""})()
        state = {p: {} for p in ce.PILLARS}
        state["D"] = {"terminal": term}
        return [x for x in ce.check_disposition({"state": state}, res) if x.startswith("X2")]
    say(not x2("| IC-D | Silent-success hooks | Complete -- FALSIFIED_OR_REJECTED_BY_EVIDENCE |\n"),
        "V-ICP-X2-OWN-ROW-CLEAN (IC row names the ledger terminal)")
    say(bool(x2("| IC-D | Silent-success hooks | Complete -- MERGED_INTO_EXISTING_OWNER |\n")),
        "V-ICP-MUT-X2-wrong-terminal killed by X2")
    say(bool(x2("| CE-D | Hooks | Complete -- FALSIFIED_OR_REJECTED_BY_EVIDENCE |\n")),
        "V-ICP-MUT-X2-foreign-row killed by X2 (a CE row is not an IC row)")

    CE = "vault/programs/cognitive-economy/ledger.json"
    base = {"frozen": {"consumes": {"J": [{"ledger": CE, "pillar": "D"}]}},
            "state": {"J": {"terminal": "MERGED_INTO_EXISTING_OWNER", "evidence": [
                {"kind": "owner_ledger", "ref": CE, "commit": "c" * 40, "pillar": "D",
                 "terminal": "MERGED_INTO_EXISTING_OWNER"}]}}}
    good = FakeOwners({("c" * 40, CE, "D"): "MERGED_INTO_EXISTING_OWNER"})
    say(not check_consumed(base, good), "V-ICP-CONSUMED-CLEAN (green)")

    def mut(fn):
        x = copy.deepcopy(base)
        fn(x)
        return x
    mutants = {
        "handoff-only": (mut(lambda x: x["state"]["J"].__setitem__("evidence", [])), good),
        "unreachable-commit": (base, FakeOwners({("d" * 40, CE, "D"): "MERGED_INTO_EXISTING_OWNER"})),
        "owner-still-open": (base, FakeOwners({("c" * 40, CE, "E"): "MERGED_INTO_EXISTING_OWNER"})),
        "terminal-misquoted": (base, FakeOwners({("c" * 40, CE, "D"): "AUTHORIZATION_BOUND"})),
        "wrong-pillar-cited": (mut(lambda x: x["state"]["J"]["evidence"][0].__setitem__("pillar", "E")), good),
    }
    for name, (l_, o_) in mutants.items():
        say(any(x.startswith("R2") for x in check_consumed(l_, o_)), f"V-ICP-MUT-{name} killed by R2")

    # R2 in `--pillar X`: `only` scopes the check, and the per-pillar command executes it (an R2 that ran only under
    # --final let a J terminal with a misquoted owner terminal print ICP_PILLAR_J=PASS).
    bad_ho = mutants["handoff-only"][0]
    scoped_j = check_consumed(bad_ho, good, only=["J"])
    scoped_h = check_consumed(bad_ho, good, only=["H"])
    say(bool(scoped_j) and all(x.startswith("R2 J:") for x in scoped_j) and scoped_h == []
        and check_consumed(bad_ho, good, only=None) == check_consumed(bad_ho, good) == scoped_j,
        "V-ICP-R2-ONLY-SCOPED (only=['J'] -> R2 J lines, only=['H'] -> none, only=None -> as before)")

    owners_j = [("D", "MERGED_INTO_EXISTING_OWNER"), ("E", "MERGED_INTO_EXISTING_OWNER"),
                ("I", "FALSIFIED_OR_REJECTED_BY_EVIDENCE")]
    pm_ok = {"frozen": {"consumes": {"J": [{"ledger": CE, "pillar": p} for p, _ in owners_j]}},
             "state": {"J": {"terminal": "MERGED_INTO_EXISTING_OWNER", "evidence": [
                 {"kind": "owner_ledger", "ref": CE, "commit": "c" * 40, "pillar": p, "terminal": t}
                 for p, t in owners_j]}}}
    pm_bad = copy.deepcopy(pm_ok)
    pm_bad["state"]["J"]["evidence"] = []
    pm_owners = FakeOwners({("c" * 40, CE, p): t for p, t in owners_j})

    def pillar_mode(ledger):
        """main(['--pillar', 'J']) with the ledger, owners and CE verifier replaced; globals restored in finally."""
        saved_ce_main = ce.main
        undo = [_patch_attr("load_ledger", lambda: ledger), _patch_attr("OwnerLedgers", lambda: pm_owners)]
        ce.main = lambda argv: 0
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = main(["--pillar", "J"])
        finally:
            ce.main = saved_ce_main
            for restore in reversed(undo):
                restore()
        return rc, buf.getvalue()

    rc_bad, out_bad = pillar_mode(pm_bad)
    rc_ok, out_ok = pillar_mode(pm_ok)
    say(rc_bad == 1 and "FAIL R2 J:" in out_bad and "ICP_PILLAR_J=FAIL" in out_bad
        and rc_ok == 0 and "ICP_PILLAR_J=PASS" in out_ok and "R2" not in out_ok,
        "V-ICP-R2-PILLAR-MODE (--pillar J reads the owner ledger: missing evidence FAIL, correct rows PASS)")
    undo_r2 = _patch_attr("check_consumed", lambda led, owners, only=None: [])
    try:
        rc_mut, out_mut = pillar_mode(pm_bad)
    finally:
        undo_r2()
    say("ICP_PILLAR_J=PASS" in out_mut and rc_mut == 0 and "ICP_PILLAR_J=FAIL" in pillar_mode(pm_bad)[1],
        "V-ICP-MUT-r2-absent-from-pillar-mode killed by V-ICP-R2-PILLAR-MODE")

    # R2 on REAL git, one green pole: CE ledger at its freeze commit shows pillar A open, at
    # the worker branch head it is closed -- the reader must tell them apart.
    real = OwnerLedgers()
    frozen_ce = ce._git("rev-parse", "--verify", "--quiet", "fa9ae2ed^{commit}").stdout.strip()
    closed_ce = ce._git("rev-parse", "--verify", "--quiet", "21671d6c^{commit}").stdout.strip()
    if frozen_ce and closed_ce:
        open_pole = real.terminal_at(frozen_ce, CE, "A")
        closed_pole = real.terminal_at(closed_ce, CE, "A")
        say(open_pole is None and closed_pole == "IMPLEMENTED_AND_VERIFIED",
            f"V-ICP-REAL-OWNER-READ (CE pillar A at freeze fa9ae2ed -> {open_pole}, "
            f"at phase-1 commit 21671d6c -> {closed_pole})")
    else:
        print("  INCONCLUSIVE V-ICP-REAL-OWNER-READ: fa9ae2ed / 21671d6c not in this clone")

    # R3 measurement scope: each pole on a fake resolver mapping ref -> front-matter text.
    def fm(**kv):
        body = "".join(f"{k}: {json.dumps(v)}\n" for k, v in kv.items())
        return f"---\n{body}---\n\n# measurement\n"

    class FakeText(ce.Resolver):
        def __init__(self, table):
            self.table = table

        def file_text(self, rel):
            return self.table.get(rel, "")

    def r3(pillar, table, refs):
        led_ = {"state": {pillar: {"evidence": [{"kind": "measurement", "ref": r, "sha256": "0" * 64} for r in refs]}}}
        return check_measurement_scope(led_, FakeText(table), only=[pillar])

    def fsrc(key, **over):
        rel = FROZEN_SOURCE_DEFAULTS[key]
        ent = dict({"path": rel, "sha256": ce.lf_sha256(REPO / rel), "default": True}, **over)
        return {key: ent, "all_default": ent["default"]}
    def kmep_file(kv, block=None):
        """A kme_pillars file as the instrument writes it: front matter plus the json block of the same result."""
        b = dict(kv) if block is None else block
        return fm(**kv) + "\n" + KMEP_BODY_MARKER + "\n" + json.dumps(b, indent=1) + "\n" + KMEP_BODY_END + "\n"
    good_kv = dict(instrument=KMEP_INSTRUMENT, pillar="E", denominator="KME-L", rule_denominators=["KME-L"],
                   evidence_role="primary", terminal_evidence=True, population_match="exact", materiality=">= 3 %",
                   share_interval=[0.04, 0.05], observability=1.0,
                   second_workload_valid=None, frozen_source=fsrc("frozen_file"))
    prim = kmep_file(good_kv)
    prim_false = fm(pillar="E", evidence_role="primary", terminal_evidence=False,
                    terminal_evidence_reason="primary file but not terminal: population_match=drifted")
    sec = fm(pillar="E", evidence_role="second_workload", terminal_evidence=False, second_workload_valid=True)
    sec_bad = fm(pillar="E", evidence_role="second_workload", terminal_evidence=False, second_workload_valid=False)
    smoke = fm(pillar="E", evidence_role="smoke", terminal_evidence=False, second_workload_valid=None)
    say(r3("E", {"p": prim}, ["p"]) == [], "V-ICP-R3-CLEAN (primary, terminal_evidence true -> no failure)")
    say(any(x.startswith("R3 E:") and "drifted" in x for x in r3("E", {"p": prim_false}, ["p"])),
        "V-ICP-MUT-terminal-evidence-false killed by R3")
    say(any(x.startswith("R3 E:") and "smoke" in x for x in r3("E", {"s": smoke}, ["s"])),
        "V-ICP-R3-SMOKE-REFUSED")
    say(r3("E", {"p": prim, "w": sec}, ["p", "w"]) == [],
        "V-ICP-R3-E-PAIR-ACCEPTED (primary true + valid second workload, both pillar E)")
    alone = r3("E", {"w": sec}, ["w"])
    say(len(alone) == 1 and alone[0].startswith("R3 E:"), "V-ICP-R3-SECOND-ALONE-REFUSED")
    say(any(x.startswith("R3 E:") and "second_workload_valid" in x for x in r3("E", {"p": prim, "w": sec_bad}, ["p", "w"])),
        "V-ICP-R3-SECOND-INVALID-REFUSED")
    fp = r3("E", {"p": prim_false, "w": sec}, ["p", "w"])
    say(len(fp) == 2 and any("not terminal evidence" in x for x in fp) and any("second_workload" in x for x in fp),
        "V-ICP-R3-SECOND-WITH-FALSE-PRIMARY-REFUSED (both the primary and the orphaned second workload refused)")
    say(any(x.startswith("R3 D:") and "pillar E" in x for x in r3("D", {"p": prim}, ["p"])),
        "V-ICP-R3-WRONG-PILLAR-REFUSED")
    say(r3("E", {"o": fm(pillar="E", denominator="KME-L"), "n": "no front matter here\n"}, ["o", "n"]) == [],
        "V-ICP-R3-NON-KMEP (no evidence_role and no terminal_evidence line -> skipped)")
    quoted = "---\ndenominator: \"KME-L\"\n---\n\nThe words evidence_role: smoke appear in this body sentence.\n"
    say(r3("E", {"q": quoted}, ["q"]) == [] and front_matter_fields(quoted) == {"denominator": "KME-L"},
        "V-ICP-R3-QUOTED-NOT-FIELD (body words are not front matter)")
    # WR-05: a second workload whose own verdict is UNMEASURED is refused even beside a terminal primary.
    sec_unm = fm(pillar="E", evidence_role="second_workload", terminal_evidence=False, second_workload_valid=True,
                 materiality="UNMEASURED")
    sec_below = fm(pillar="E", evidence_role="second_workload", terminal_evidence=False, second_workload_valid=True,
                   materiality="< 3 %")
    say(any("UNMEASURED" in x for x in r3("E", {"p": prim, "w": sec_unm}, ["p", "w"])),
        "V-ICP-R3-SECOND-UNMEASURED-REFUSED")
    say(r3("E", {"p": prim, "w": sec_below}, ["p", "w"]) == [],
        "V-ICP-R3-SECOND-BELOW-3-ACCEPTED (a valid measurement; whether it confirms is second_workload_confirms)")
    # WR-04: a pillar D..I with a terminal needs a cited kme_pillars primary file, and a file's terminal claim must
    # agree with its own fields.
    def r3t(pillar, table, refs, terminal="RESEARCH_INSUFFICIENT_EVIDENCE"):
        led_ = {"state": {pillar: {"terminal": terminal, "evidence": [
            {"kind": "measurement", "ref": r, "sha256": "0" * 64} for r in refs]}}}
        return check_measurement_scope(led_, FakeText(table), only=[pillar])

    say(r3t("E", {"p": prim}, ["p"]) == [], "V-ICP-R3-TERMINAL-CLEAN (terminal + a consistent primary -> no failure)")
    hand = ("---\ndenominator: \"KME-G\"\ncommand: \"python3 x --denominator KME-G\"\n---\n\n"
            "KME-L KME-G CPP-D-W7 measured by hand.\n")
    say(any("cites no kme_pillars primary" in x for x in r3t("E", {"h": hand}, ["h"])),
        "V-ICP-R3-TERMINAL-HAND-WRITTEN-REFUSED (a hand-written KME-G md cannot stand in for KME-L)")
    say(any("cites no kme_pillars primary" in x for x in r3t("E", {}, [])),
        "V-ICP-R3-TERMINAL-NO-EVIDENCE-REFUSED")
    contradictions = {
        "denominator-KME-G": dict(good_kv, denominator="KME-G"),
        "population-drifted": dict(good_kv, population_match="drifted"),
        "verdict-UNMEASURED": dict(good_kv, materiality="UNMEASURED"),
        "no-verdict": {k: v for k, v in good_kv.items() if k != "materiality"},
        "rule-widened": dict(good_kv, rule_denominators=["KME-L", "KME-G"]),
        "foreign-instrument": dict(good_kv, instrument="hand/edited.py"),
        "referenced-on-E": dict(good_kv, population_match="referenced", denominator="CPP-D-W7",
                                rule_denominators=["KME-L", "CPP-D-W7"], coverage=1.0),
        # WR-07: the frozen source the file read
        "no-frozen-source": {k: v for k, v in good_kv.items() if k != "frozen_source"},
        "non-default-source": dict(good_kv, frozen_source=fsrc("frozen_file", default=False)),
        "source-sha-stale": dict(good_kv, frozen_source=fsrc("frozen_file", sha256="0" * 64)),
        "source-path-elsewhere": dict(good_kv, frozen_source=fsrc("frozen_file", path="/tmp/other.json")),
        "wrong-source-kind": dict(good_kv, frozen_source=fsrc("ce_ledger")),
    }
    # STATE debt (1): the json block. Hand-edit one side, or both consistently with a verdict its interval does not give.
    contradictions.update({
        "block-absent": None,
        "block-disagrees-verdict": ("block", dict(good_kv, materiality="< 3 %")),
        "fm-edited-denominator": ("block", dict(good_kv, denominator="KME-G")),
        "verdict-not-interval": ("both", dict(good_kv, materiality=">= 3 %", share_interval=[0.01, 0.02])),
        "straddles-called-above": ("both", dict(good_kv, share_interval=[0.02, 0.04])),
        "partial-observability-below": ("both", dict(good_kv, materiality="< 3 %", share_interval=[0.01, 0.02],
                                                     observability=0.5)),
        "block-unparseable": ("raw", "{not json"),
        "two-blocks": ("twice", good_kv),
    })
    for name, kv in contradictions.items():
        if kv is None:
            text_c = fm(**good_kv)
        elif isinstance(kv, tuple) and kv[0] == "block":
            text_c = kmep_file(good_kv, block=kv[1])
        elif isinstance(kv, tuple) and kv[0] == "both":
            text_c = kmep_file(kv[1])
        elif isinstance(kv, tuple) and kv[0] == "raw":
            text_c = fm(**good_kv) + KMEP_BODY_MARKER + "\n" + kv[1] + "\n" + KMEP_BODY_END + "\n"
        elif isinstance(kv, tuple) and kv[0] == "twice":
            text_c = kmep_file(kv[1]) + KMEP_BODY_MARKER + "\n{}\n" + KMEP_BODY_END + "\n"
        else:
            text_c = kmep_file(kv)
        got = r3t("E", {"c": text_c}, ["c"])
        say(any("claims terminal_evidence true but" in x for x in got),
            f"V-ICP-R3-MUT-{name} killed by R3 (terminal_evidence true contradicts its own fields)")
    d_ref = dict(good_kv, pillar="D", denominator="CPP-D-W7", rule_denominators=["KME-L", "CPP-D-W7"],
                 population_match="referenced", coverage=1.0, frozen_source=fsrc("ce_ledger"))
    say(r3t("D", {"w": kmep_file(d_ref)}, ["w"], "FALSIFIED_OR_REJECTED_BY_EVIDENCE") == [],
        "V-ICP-R3-TERMINAL-DW7-REFERENCED-ACCEPTED (pillar D, CPP-D-W7 at coverage exactly 1)")
    say(any("claims terminal_evidence true but" in x for x in r3t(
        "D", {"w": kmep_file(dict(d_ref, coverage=1.5))}, ["w"], "FALSIFIED_OR_REJECTED_BY_EVIDENCE")),
        "V-ICP-R3-TERMINAL-DW7-COVERAGE-REFUSED (coverage 1.5)")
    # WR-03: a kme_pillars file whose role fields are missing, damaged or hidden behind a BOM is refused, not skipped.
    kmep_fm = fm(instrument=KMEP_INSTRUMENT, pillar="E", denominator="KME-G", command="x")
    bom_smoke = "\ufeff" + fm(instrument=KMEP_INSTRUMENT, pillar="E", evidence_role="smoke", terminal_evidence=False)
    marker_only = "no front matter at all\n\n" + KMEP_BODY_MARKER + "\n{}\n<!-- /kmep-json -->\n"
    broken = fm(instrument=KMEP_INSTRUMENT, pillar="E", evidence_role="primary").replace(
        "---\n\n", "terminal_evidence: tru\n---\n\n", 1)
    say(any("smoke" in x for x in r3("E", {"b": bom_smoke}, ["b"])) and
        front_matter_fields(bom_smoke).get("evidence_role") == "smoke",
        "V-ICP-R3-BOM-READ (a UTF-8 BOM before the front matter no longer hides it: smoke refused)")
    say(any("without readable" in x for x in r3("E", {"k": kmep_fm}, ["k"])),
        "V-ICP-R3-KMEP-NO-ROLE-REFUSED (instrument line present, role fields absent)")
    say(any("without readable" in x for x in r3("E", {"m": marker_only}, ["m"])),
        "V-ICP-R3-KMEP-MARKER-ONLY-REFUSED (only the json block marker survives)")
    say(any("without readable" in x for x in r3("E", {"u": broken}, ["u"])),
        "V-ICP-R3-KMEP-UNPARSABLE-REFUSED (terminal_evidence: tru)")
    smoke_files = sorted((REPO / PROGRAM_DIR / "measurements").glob("D-KME-G-*.md"))
    if smoke_files:
        rel = smoke_files[0].relative_to(REPO).as_posix()
        real_led = {"state": {"D": {"terminal": "FALSIFIED_OR_REJECTED_BY_EVIDENCE", "evidence": [
            {"kind": "measurement", "ref": rel, "sha256": ce.lf_sha256(REPO / rel)}]}}}
        got = check_measurement_scope(real_led, ce.Resolver(), only=["D"])
        say(len(got) >= 1 and all(x.startswith("R3 D:") for x in got) and any("smoke" in x for x in got),
            f"V-ICP-R3-REAL (committed KME-G smoke file {rel} refused: {got[:1]})")
    else:
        ok = False
        print("  INCONCLUSIVE V-ICP-R3-REAL: no KME-G smoke file")
    # Pillar L: a kme_replay ranking file (plan 05-03). The same poles as D..I, read against the L rule table.
    good_l_kv = dict(instrument=KMER_INSTRUMENT, pillar="L", denominator="KME-L", rule_denominators=["KME-L"],
                     evidence_role="primary", terminal_evidence=True, population_match="exact",
                     weighted_denominator=3879.0, rollover_growth=100000, ranked_ids=list(KMER_CANDIDATES),
                     unranked_ids=[], frozen_source=fsrc("frozen_file"))

    def l_block(kv, **over):
        """The json block a real kme_replay file carries: kv's fields plus the ranked entries."""
        ids = kv.get("ranked_ids")
        return dict(kv, ranked=[{"candidate": c} for c in ids] if isinstance(ids, list) else [], **over)

    def l_file(kv, block=None, raw_block=None):
        """A kme_replay-shaped file: the front matter of kv and the json block (kv's own fields unless `block` / `raw_block`
        says otherwise)."""
        body = raw_block if raw_block is not None else KMER_BODY_MARKER + "\n" + json.dumps(
            block if block is not None else l_block(kv)) + "\n" + KMER_BODY_END + "\n"
        return fm(**kv) + "\n" + body
    l_prim = l_file(good_l_kv)
    l_smoke = fm(instrument=KMER_INSTRUMENT, pillar="L", denominator="KME-G", rule_denominators=["KME-L"],
                 evidence_role="smoke", terminal_evidence=False, population_match="exact", unranked_ids=[])
    say(r3t("L", {"p": l_prim}, ["p"]) == [] and r3("L", {"p": l_prim}, ["p"]) == [],
        "V-ICP-R3-L-PRIMARY-ACCEPTED (an exact KME-L primary ranking with the committed frozen source, no unranked)")
    sm = r3("L", {"s": l_smoke}, ["s"])
    say(len(sm) == 1 and sm[0].startswith("R3 L:") and "smoke" in sm[0], "V-ICP-R3-L-SMOKE-REFUSED")
    l_contradictions = {
        "denominator-KME-G": dict(good_l_kv, denominator="KME-G"),
        "population-drifted": dict(good_l_kv, population_match="drifted"),
        "unranked-late-rollover": dict(good_l_kv, unranked_ids=["late_rollover"]),
        "unranked-absent": {k: v for k, v in good_l_kv.items() if k != "unranked_ids"},
        "rule-widened": dict(good_l_kv, rule_denominators=["KME-L", "KME-G"]),
        "foreign-instrument": dict(good_l_kv, instrument=KMEP_INSTRUMENT),
        "no-frozen-source": {k: v for k, v in good_l_kv.items() if k != "frozen_source"},
        "non-default-source": dict(good_l_kv, frozen_source=fsrc("frozen_file", default=False)),
        "source-sha-stale": dict(good_l_kv, frozen_source=fsrc("frozen_file", sha256="0" * 64)),
        "source-path-elsewhere": dict(good_l_kv, frozen_source=fsrc("frozen_file", path="/tmp/other.json")),
    }
    for name, kv in l_contradictions.items():
        got = r3t("L", {"c": l_file(kv)}, ["c"])
        say(any(x.startswith("R3 L:") and "claims terminal_evidence true but" in x for x in got),
            f"V-ICP-R3-L-MUT-{name} killed by R3 (terminal_evidence true contradicts its own fields)")
    # WR-03: the ranking itself is checked, not only the self-asserted front matter
    forged = fm(instrument=KMER_INSTRUMENT, pillar="L", denominator="KME-L", rule_denominators=["KME-L"],
                evidence_role="primary", terminal_evidence=True, population_match="exact", ranked_ids=[],
                unranked_ids=[], rollover_growth=100000, weighted_denominator=1.0, frozen_source=fsrc("frozen_file"),
                command="hand typed") + "\nKME-L [L]\n"
    wr03 = {
        "forged-empty-ranking": forged,
        "ranked-two-of-three": l_file(dict(good_l_kv, ranked_ids=["late_rollover", "identical_rereads"])),
        "ranked-foreign-id": l_file(dict(good_l_kv, ranked_ids=["late_rollover", "identical_rereads", "made_up"])),
        "ranked-duplicate": l_file(dict(good_l_kv, ranked_ids=["late_rollover", "late_rollover", "identical_rereads"])),
        "ranked-not-a-list": l_file(dict(good_l_kv, ranked_ids="late_rollover")),
        "json-block-absent": l_file(good_l_kv, raw_block="no block here\n"),
        "json-block-malformed": l_file(good_l_kv, raw_block=KMER_BODY_MARKER + "\n{not json\n" + KMER_BODY_END + "\n"),
        "json-block-twice": l_file(good_l_kv) + "\n" + KMER_BODY_MARKER + "\n" + json.dumps(l_block(good_l_kv)) + "\n"
                            + KMER_BODY_END + "\n",
        "json-ids-disagree": l_file(good_l_kv, block=l_block(good_l_kv, ranked_ids=["identical_rereads"])),
        "json-unranked-disagree": l_file(good_l_kv, block=l_block(good_l_kv, unranked_ids=["late_rollover"])),
        "json-frozen-sha-disagrees": l_file(good_l_kv, block=l_block(good_l_kv, frozen_source=fsrc(
            "frozen_file", sha256="0" * 64))),
        "json-growth-disagrees": l_file(good_l_kv, block=l_block(good_l_kv, rollover_growth=50000)),
        "json-denominator-disagrees": l_file(good_l_kv, block=l_block(good_l_kv, weighted_denominator=1.0)),
        "json-ranked-entries-disagree": l_file(good_l_kv, block=dict(l_block(good_l_kv), ranked=[])),
        "json-instrument-disagrees": l_file(good_l_kv, block=l_block(good_l_kv, instrument="hand/edited.py")),
    }
    def wr03_off():
        return [n for n, t in wr03.items() if not any(
            x.startswith("R3 L:") and "claims terminal_evidence true but" in x for x in r3t("L", {"c": t}, ["c"]))]
    off03 = wr03_off()
    say(not off03, f"V-ICP-R3-L-RANKING-CHECKED ({len(wr03)} forged / inconsistent ranking files refused; off: {off03})")
    restore = _patch_attr("kmer_ranking_problems", lambda fm_, text_: [])
    try:
        off03_m = wr03_off()
    finally:
        restore()
    say(len(off03_m) == len(wr03), f"V-ICP-MUT-r3l-ranking-unchecked killed by V-ICP-R3-L-RANKING-CHECKED "
                                   f"(it leaves {len(off03_m)} of {len(wr03)} forged files accepted)")
    growth_poles = {
        "growth-1e9": l_file(dict(good_l_kv, rollover_growth=1000000000)),
        "growth-50000": l_file(dict(good_l_kv, rollover_growth=50000)),
        "growth-string": l_file(dict(good_l_kv, rollover_growth="100000")),
        "growth-float": l_file(dict(good_l_kv, rollover_growth=100000.0)),
        "growth-true": l_file(dict(good_l_kv, rollover_growth=True)),
        "growth-absent": l_file({k: v for k, v in good_l_kv.items() if k != "rollover_growth"}),
    }

    def growth_off():
        return [n for n, t in growth_poles.items() if not any(
            x.startswith("R3 L:") and "rollover_growth" in x for x in r3t("L", {"c": t}, ["c"]))]
    goff = growth_off()
    say(not goff, f"V-ICP-R3-L-GROWTH-PINNED ({len(growth_poles)} rollover_growth values other than the frozen "
                  f"{KMER_ROLLOVER_GROWTH} refused; off: {goff})")
    restore = _patch_attr("rollover_growth_problems", lambda fm_: [])
    try:
        goff_m = growth_off()
    finally:
        restore()
    say(len(goff_m) == len(growth_poles), f"V-ICP-MUT-r3l-growth-unpinned killed by V-ICP-R3-L-GROWTH-PINNED "
                                          f"(it leaves {len(goff_m)} of {len(growth_poles)} accepted)")
    say(r3t("L", {"c": l_prim}, ["c"]) == [], "V-ICP-R3-L-RANKING-CONSISTENT-ACCEPTED (the consistent control is silent)")
    got = r3t("L", {"c": fm(**dict(good_l_kv, evidence_role="smoke"))}, ["c"])
    say(any(x.startswith("R3 L:") and "is a smoke measurement" in x for x in got),
        "V-ICP-R3-L-MUT-smoke-role-claims-terminal killed by R3 (a file that calls itself smoke is never terminal)")
    l_hand = ("---\ndenominator: \"KME-G\"\ncommand: \"python3 x --denominator KME-G\"\n---\n\n"
              "late rollover, identical rereads and retries measured by hand.\n")
    no_primary = [r3t("L", {"h": l_hand}, ["h"], t) for t in MEASUREMENT_TERMINALS] + [
        r3t("L", {}, [], t) for t in MEASUREMENT_TERMINALS] + [r3t("L", {"s": l_smoke}, ["s"])]
    say(all(any(x.startswith("R3 L:") and "cites no kme_replay primary" in x for x in got) for got in no_primary),
        "V-ICP-R3-L-NO-PRIMARY-REFUSED (hand-written, absent and smoke-only evidence, both measurement terminals)")
    say(r3t("L", {}, [], "AUTHORIZATION_BOUND") == [] and r3t("L", {"h": l_hand}, ["h"], "AUTHORIZATION_BOUND") == [],
        "V-ICP-R3-L-AUTH-ONLY-SILENT (an owner-decision terminal needs no ranking file; R3 does not speak)")
    say(any("without readable" in x for x in r3("L", {"k": "---\ninstrument: \"" + KMER_INSTRUMENT + "\"\n---\n"}, ["k"])),
        "V-ICP-R3-L-KMER-NO-ROLE-REFUSED (a kme_replay file without role fields is refused, not skipped)")
    # IN-03: the documented list of terminals that need no ranking file is executed, not just stated
    exempt = sorted(ce.TERMINALS - set(MEASUREMENT_TERMINALS))
    silent = [t for t in exempt if r3t("L", {}, [], t) == []]
    loud = [t for t in MEASUREMENT_TERMINALS if any("cites no kme_replay primary" in x for x in r3t("L", {}, [], t))]
    doc = " ".join((__doc__ or "").split())
    undocumented = [t for t in exempt if t not in doc]
    say(silent == exempt and sorted(loud) == sorted(MEASUREMENT_TERMINALS) and not undocumented and len(exempt) == 5,
        f"V-ICP-R3-L-NEEDS-RANKING-TABLE (no ranking file needed for {exempt}; needed for {list(MEASUREMENT_TERMINALS)}; "
        f"silent={silent} loud={loud} not named in the docstring: {undocumented})")
    l_smokes = sorted((REPO / PROGRAM_DIR / "measurements").glob("L-KME-G-*.md"))
    if l_smokes:
        rel = l_smokes[0].relative_to(REPO).as_posix()
        real_l = {"state": {"L": {"terminal": "RESEARCH_INSUFFICIENT_EVIDENCE", "evidence": [
            {"kind": "measurement", "ref": rel, "sha256": ce.lf_sha256(REPO / rel)}]}}}
        got = check_measurement_scope(real_l, ce.Resolver(), only=["L"])
        say(len(got) >= 1 and all(x.startswith("R3 L:") for x in got) and any("is a smoke measurement" in x for x in got),
            f"V-ICP-R3-L-REAL (committed KME-G smoke file {rel} refused for an L terminal: {got[:1]})")
    else:
        ok = False
        print("  INCONCLUSIVE V-ICP-R3-L-REAL: no L-KME-G smoke file")
    # R4: the mission's own bundle is never an owner_decision. Identity, not spelling (CR-01): every pole below names
    # the same file as the bundle, or a file the mission wrote, in a different spelling.
    def r4_led(pillar, ref):
        return {"state": {pillar: {"terminal": "AUTHORIZATION_BOUND", "evidence": [
            {"kind": "owner_decision", "ref": ref, "sha256": "0" * 64}]}}}

    def r4_refused(ref, pillars=("L",)):
        return all(len(g) == 1 and g[0].startswith("R4 ") for g in
                   (check_owner_decisions(r4_led(p_, ref), only=[p_]) for p_ in pillars))
    bundle_forms = [OWNER_BUNDLE_REL, "./" + OWNER_BUNDLE_REL, OWNER_BUNDLE_REL.replace("/", "\\"),
                    "vault/programs/./incremental-cognition/owner-bundle.md", str(REPO / OWNER_BUNDLE_REL)]
    refused = [check_owner_decisions(r4_led(p_, f_), only=[p_]) for p_ in ("L", "B") for f_ in bundle_forms]
    say(all(len(g) == 1 and g[0].startswith("R4 ") and "owner bundle" in g[0] for g in refused),
        "V-ICP-R4-BUNDLE-REFUSED (the bundle as an owner_decision, five spellings, pillars L and B)")
    # the ~ pole expands against the checkout's parent; every R4 judgement below reads the scratch attestation file
    with _home(REPO.parent), _attestations(r4_attestations_path()):
        poles = r4_identity_poles()
        own = poles["accepted-owner-decision-attested"][0]
        say(check_owner_decisions(r4_led("L", own), only=["L"]) == []
            and check_owner_decisions({"state": {"L": {"evidence": [
                {"kind": "measurement", "ref": OWNER_BUNDLE_REL, "sha256": "0" * 64}]}}}, only=["L"]) == [],
            "V-ICP-R4-OTHER-DECISION-SILENT (the Owner's attested decision file, and a non-decision evidence kind, are "
            "not refused)")
        trio = {k: r4_refused(poles[k][0]) for k in ("accepted-owner-decision-attested",
                                                      "decision-edited-after-attestation", "decision-named-but-unattested")}
        say(trio == {"accepted-owner-decision-attested": False, "decision-edited-after-attestation": True,
                     "decision-named-but-unattested": True},
            f"V-ICP-R4-ATTESTED-BYTES-ONLY (debt 2, Owner decision (c): attested bytes accepted; the same name with "
            f"edited bytes, or with no attestation, refused: {trio})")
        off = [name for name, (ref, expect) in poles.items() if r4_refused(ref) != expect]
    say(not off, f"V-ICP-R4-IDENTITY ({len(poles)} spellings / identities of the bundle and of mission-written files "
                 f"refused, the accepted shapes silent; off: {off})")
    # The attestation wall refuses everything unattested, so it would also refuse what a broken identity wall lets
    # through and hide that breakage. Each older wall is therefore judged with the attestation wall held open: a
    # mutant is killed only by poles it opens BEYOND the ones the open attestation wall opens on its own.
    def off_under(patchers):
        restores = [p() for p in patchers]
        try:
            with _home(REPO.parent), _attestations(r4_attestations_path()):
                return {name for name, (ref, expect) in r4_identity_poles().items() if r4_refused(ref) != expect}
        finally:
            for r in reversed(restores):
                r()
    open_attest = R4_MUTANTS["r4-attestation-ignored"]
    held_by_attestation = off_under([open_attest])
    for mname, patcher in R4_MUTANTS.items():
        if patcher is open_attest:
            off_m = sorted(held_by_attestation)
        else:
            off_m = sorted(off_under([open_attest, patcher]) - held_by_attestation)
        say(bool(off_m), f"V-ICP-MUT-{mname} killed by V-ICP-R4-IDENTITY (the poles it leaves open: {off_m[:3]})")
    return ok


def _generation(argv):
    """(generation, argv without the --generation tokens). Absent -> 1; an unparsable value -> (None, argv)."""
    gen, rest, i = 1, [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--generation" and i + 1 < len(argv):
            gen, i = argv[i + 1], i + 2
            continue
        if a.startswith("--generation="):
            gen, i = a.split("=", 1)[1], i + 1
            continue
        rest.append(a)
        i += 1
    try:
        return int(gen), rest
    except (TypeError, ValueError):
        return None, rest


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    gen, g_argv = _generation(argv)
    if gen not in (1, 2):
        print("ICP_GEN2_VERDICT=COULD_NOT_RUN --generation must be 1 or 2")
        return 2
    if gen == 2:
        if any(a == "--pillar" or a.startswith("--pillar=") for a in g_argv):
            print("ICP_GEN2_VERDICT=COULD_NOT_RUN --pillar applies to generation 1 only")
            return 2
        mode = "status" if "--status" in g_argv else "final" if "--final" in g_argv or not g_argv else None
        if "--selftest" in g_argv and mode is None:
            mode = "selftest"
        if mode is None:
            print("ICP_GEN2_VERDICT=COULD_NOT_RUN usage: --generation 2 --status|--final|--selftest")
            return 2
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import ic_gen2  # lazy: generation 1 never loads it
        return ic_gen2.main(mode)
    if "--selftest" in argv:
        own = selftest()
        rc = ce.main(["--selftest"])
        good = own and rc == 0
        print(f"ICP_SELFTEST={'PASS' if good else 'FAIL'}")
        return 0 if good else 1
    if "--final" in argv:
        fails = []
        if not selftest(verbose=False):
            fails.append("S1 wrapper selftest failed")
        rc = ce.main(["--final"])
        if rc == 2:
            print("ICP_VERDICT=COULD_NOT_RUN")
            return 2
        if rc != 0:
            fails.append(f"CE clauses failed (rc {rc})")
        try:
            led = load_ledger()
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ICP_VERDICT=COULD_NOT_RUN ledger unreadable: {exc}")
            return 2
        fails += check_binding(led) + check_consumed(led, OwnerLedgers())
        fails += check_measurement_scope(led, ce.Resolver())
        fails += check_owner_decisions(led)
        for x in fails:
            print("  FAIL", x)
        print(f"ICP_VERDICT={'PASS' if not fails else 'FAIL'} failures={len(fails)}")
        return 0 if not fails else 1
    pid = None
    for i, a in enumerate(argv):
        if a == "--pillar" and i + 1 < len(argv):
            pid = argv[i + 1]
        elif a.startswith("--pillar="):
            pid = a.split("=", 1)[1]
    if pid in ce.PILLARS:
        rc = ce.main(argv)
        try:
            led = load_ledger()
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ICP_VERDICT=COULD_NOT_RUN ledger unreadable: {exc}")
            return 2
        r3 = (check_consumed(led, OwnerLedgers(), only=[pid])
              + check_measurement_scope(led, ce.Resolver(), only=[pid]) + check_owner_decisions(led, only=[pid]))
        for x in r3:
            print("  FAIL", x)
        print(f"ICP_PILLAR_{pid}={'PASS' if rc == 0 and not r3 else 'FAIL'}")
        if rc == 2:
            return 2
        return 0 if rc == 0 and not r3 else 1
    return ce.main(argv)


if __name__ == "__main__":
    sys.exit(main())
