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
  R2  consumed owners (--final): this is a delta program; pillars that close by consuming a
      CE / SC pillar (ledger.frozen.consumes) must cite, for each consumed pillar, an
      `owner_ledger` evidence {ref: <owner ledger path>, commit, pillar, terminal}. The
      owner ledger is read AT that commit with git (the commit must be reachable from HEAD,
      so the owner's work has to be on this line of history) and must show that pillar in
      that terminal. A handoff file alone cannot close a consuming pillar.
  R3  measurement scope (--final and --pillar X): a kme_pillars (or, for pillar L, a kme_replay) measurement file carries
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
      FALSIFIED_OR_REJECTED_BY_EVIDENCE) must cite such a primary file. An AUTHORIZATION_BOUND L needs no ranking file.
  R4  owner decisions (--final and --pillar X): an `owner_decision` evidence whose ref is the owner bundle
      (vault/programs/incremental-cognition/owner-bundle.md) is refused for every pillar. The bundle is the
      mission's request, and it names [L] and the other pillar tags, so the CE clause L4 alone would accept it;
      only a file the Owner wrote in their own words counts as the Owner's decision.
  V-ICP-REBIND  the rebinding took: ledger.program must be "incremental-cognition", and a
      ledger read through any other program's path is refused.

Modes and exit codes are CE's: --final / --status / --pillar X / --selftest;
0 pass, 1 fail, 2 could not run.
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
REPO = ce.REPO
BINDING = {"SELF_REL": ce.SELF_REL, "LEDGER_REL": ce.LEDGER_REL, "FROZEN_AT_REL": ce.FROZEN_AT_REL,
           "HANDOFF_DIR": ce.HANDOFF_DIR, "PILLARS": list(ce.PILLARS)}

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
    with contextlib.redirect_stdout(buf):
        _ce_selftest(verbose=True)
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


def check_consumed(led: dict, owners: OwnerLedgers) -> list:
    f = []
    consumes = (led.get("frozen") or {}).get("consumes") or {}
    for pid, wanted in consumes.items():
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
           "HANDOFF_DIR": ce.HANDOFF_DIR, "PILLARS": list(ce.PILLARS)}
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


def terminal_claim_problems(pid: str, fm: dict) -> list:
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
        return bad + frozen_source_problems(den, fm)
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
    return bad + frozen_source_problems(den, fm)


def check_measurement_scope(led: dict, res, only=None) -> list:
    f = []
    for pid in (list(only) if only is not None else list(ce.PILLARS)):
        st = (led.get("state") or {}).get(pid) or {}
        files = []
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
        on_pillar = [(r, fm) for r, fm in files if fm.get("pillar", pid) == pid]
        has_primary = any((fm.get("evidence_role") or "primary") == "primary" and fm.get("terminal_evidence") is True
                          and not terminal_claim_problems(pid, fm) for _r, fm in on_pillar)
        needs_primary = (pid in KME_PILLARS or (pid in REPLAY_PILLARS and st.get("terminal") in MEASUREMENT_TERMINALS))
        if st.get("terminal") and needs_primary and not has_primary and not any(
                fm.get("pillar", pid) != pid or terminal_claim_problems(pid, fm) for _r, fm in files):
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
                for why in terminal_claim_problems(pid, fm):
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


def owner_decision_problem(ref):
    """Why an owner_decision evidence ref cannot be the Owner's answer, or None."""
    if names_the_bundle(ref):
        return BUNDLE_WHY
    if same_bytes_as_bundle(ref):
        return COPY_WHY
    if is_mission_written(ref):
        return MISSION_WRITTEN_WHY
    return None


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
    poles["unrelated-windows-path"] = ("C:\\Users\\User\\Desktop\\my-decision.md", False)
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
    # accepted shape: the Owner's own decision file, in scratch (never in the repo)
    dec = td / "checkout2" / PROGRAM_DIR / "evidence" / "L-owner-decision.md"
    dec.parent.mkdir(parents=True, exist_ok=True)
    dec.write_text("# Decision\n\nIn my own words: decline [L] live sessions.\n", encoding="utf-8")
    poles["accepted-owner-decision-fixture"] = (str(dec), False)
    poles["accepted-owner-decision-relative"] = (PROGRAM_DIR + "evidence/L-owner-decision.md", False)
    return poles


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
    good_kv = dict(instrument=KMEP_INSTRUMENT, pillar="E", denominator="KME-L", rule_denominators=["KME-L"],
                   evidence_role="primary", terminal_evidence=True, population_match="exact", materiality=">= 3 %",
                   second_workload_valid=None, frozen_source=fsrc("frozen_file"))
    prim = fm(**good_kv)
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
    for name, kv in contradictions.items():
        got = r3t("E", {"c": fm(**kv)}, ["c"])
        say(any("claims terminal_evidence true but" in x for x in got),
            f"V-ICP-R3-MUT-{name} killed by R3 (terminal_evidence true contradicts its own fields)")
    d_ref = dict(good_kv, pillar="D", denominator="CPP-D-W7", rule_denominators=["KME-L", "CPP-D-W7"],
                 population_match="referenced", coverage=1.0, frozen_source=fsrc("ce_ledger"))
    say(r3t("D", {"w": fm(**d_ref)}, ["w"], "FALSIFIED_OR_REJECTED_BY_EVIDENCE") == [],
        "V-ICP-R3-TERMINAL-DW7-REFERENCED-ACCEPTED (pillar D, CPP-D-W7 at coverage exactly 1)")
    say(any("claims terminal_evidence true but" in x for x in r3t(
        "D", {"w": fm(**dict(d_ref, coverage=1.5))}, ["w"], "FALSIFIED_OR_REJECTED_BY_EVIDENCE")),
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
                     evidence_role="primary", terminal_evidence=True, population_match="exact", unranked_ids=[],
                     frozen_source=fsrc("frozen_file"))
    l_prim = fm(**good_l_kv)
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
        got = r3t("L", {"c": fm(**kv)}, ["c"])
        say(any(x.startswith("R3 L:") and "claims terminal_evidence true but" in x for x in got),
            f"V-ICP-R3-L-MUT-{name} killed by R3 (terminal_evidence true contradicts its own fields)")
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
    own = PROGRAM_DIR + "evidence/L-owner-decision.md"
    say(check_owner_decisions(r4_led("L", own), only=["L"]) == []
        and check_owner_decisions({"state": {"L": {"evidence": [
            {"kind": "measurement", "ref": OWNER_BUNDLE_REL, "sha256": "0" * 64}]}}}, only=["L"]) == [],
        "V-ICP-R4-OTHER-DECISION-SILENT (the Owner's own decision file, and a non-decision evidence kind, are not refused)")
    with _home(REPO.parent):       # the ~ pole expands against the checkout's parent
        poles = r4_identity_poles()
        off = [name for name, (ref, expect) in poles.items() if r4_refused(ref) != expect]
    say(not off, f"V-ICP-R4-IDENTITY ({len(poles)} spellings / identities of the bundle and of mission-written files "
                 f"refused, the accepted shapes silent; off: {off})")
    for mname, patcher in R4_MUTANTS.items():
        restore = patcher()
        try:
            with _home(REPO.parent):
                off_m = [name for name, (ref, expect) in r4_identity_poles().items() if r4_refused(ref) != expect]
        finally:
            restore()
        say(bool(off_m), f"V-ICP-MUT-{mname} killed by V-ICP-R4-IDENTITY (the poles it leaves open: {off_m[:3]})")
    return ok


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
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
            led = json.loads((REPO / ce.LEDGER_REL).read_text(encoding="utf-8"))
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
            led = json.loads((REPO / ce.LEDGER_REL).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ICP_VERDICT=COULD_NOT_RUN ledger unreadable: {exc}")
            return 2
        r3 = check_measurement_scope(led, ce.Resolver(), only=[pid]) + check_owner_decisions(led, only=[pid])
        for x in r3:
            print("  FAIL", x)
        print(f"ICP_PILLAR_{pid}={'PASS' if rc == 0 and not r3 else 'FAIL'}")
        if rc == 2:
            return 2
        return 0 if rc == 0 and not r3 else 1
    return ce.main(argv)


if __name__ == "__main__":
    sys.exit(main())
