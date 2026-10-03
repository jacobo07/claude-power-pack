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
  R3  measurement scope (--final and --pillar X): a kme_pillars measurement file carries
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
      KME-G for KME-L".
  V-ICP-REBIND  the rebinding took: ledger.program must be "incremental-cognition", and a
      ledger read through any other program's path is refused.

Modes and exit codes are CE's: --final / --status / --pillar X / --selftest;
0 pass, 1 fail, 2 could not run.
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
import re
import sys
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


KME_PILLARS = ("D", "E", "F", "G", "H", "I")
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


def terminal_claim_problems(pid: str, fm: dict) -> list:
    """Why a kme_pillars file that says `terminal_evidence: true` contradicts itself (pillars D..I only). A claim
    is believed only when the file's own fields agree with it: role primary, the instrument's own mark, a population
    that reproduced the frozen denominator (a referenced CPP-D-W7 only at coverage exactly 1), a measured verdict,
    and a denominator inside this pillar's frozen rule."""
    if pid not in KME_PILLARS or fm.get("terminal_evidence") is not True:
        return []
    bad = []
    if fm.get("instrument") != KMEP_INSTRUMENT:
        bad.append(f"instrument is {fm.get('instrument')!r}, not {KMEP_INSTRUMENT!r}")
    if fm.get("evidence_role") != "primary":
        bad.append(f"evidence_role is {fm.get('evidence_role')!r}, not 'primary'")
    pm, den = fm.get("population_match"), fm.get("denominator")
    if not (pm == "exact" or (pm == "referenced" and den == "CPP-D-W7" and fm.get("coverage") == 1.0)):
        bad.append(f"population_match is {pm!r} (coverage {fm.get('coverage')!r}), not a reproduced population")
    if fm.get("materiality") not in MEASURED_VERDICTS:
        bad.append(f"materiality is {fm.get('materiality')!r}, not a measured verdict")
    rule = FROZEN_RULE_DENOMINATORS[pid]
    if fm.get("rule_denominators") != rule:
        bad.append(f"rule_denominators {fm.get('rule_denominators')!r} is not the frozen rule {rule!r}")
    if den not in rule:
        bad.append(f"denominator {den!r} is not in pillar {pid}'s frozen rule {rule!r}")
    # WR-07: measured against the committed frozen source, whose recorded sha256 is still the committed file's
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
            if not is_kmep_file(text, fm):
                continue  # another instrument's measurement: the CE clauses judge it
            if not isinstance(fm.get("evidence_role"), str) or not isinstance(fm.get("terminal_evidence"), bool):
                f.append(f"R3 {pid}: {ref} is a kme_pillars measurement without readable evidence_role / "
                         f"terminal_evidence front matter (absent, unparseable or hand-edited)")
                continue
            files.append((ref, fm))
        on_pillar = [(r, fm) for r, fm in files if fm.get("pillar", pid) == pid]
        has_primary = any((fm.get("evidence_role") or "primary") == "primary" and fm.get("terminal_evidence") is True
                          and not terminal_claim_problems(pid, fm) for _r, fm in on_pillar)
        if st.get("terminal") and pid in KME_PILLARS and not has_primary and not any(
                fm.get("pillar", pid) != pid or terminal_claim_problems(pid, fm) for _r, fm in files):
            f.append(f"R3 {pid}: terminal {st.get('terminal')} cites no kme_pillars primary measurement file with "
                     f"terminal_evidence true (a hand-written or other-instrument file cannot stand in for it)")
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
        r3 = check_measurement_scope(led, ce.Resolver(), only=[pid])
        for x in r3:
            print("  FAIL", x)
        print(f"ICP_PILLAR_{pid}={'PASS' if rc == 0 and not r3 else 'FAIL'}")
        if rc == 2:
            return 2
        return 0 if rc == 0 and not r3 else 1
    return ce.main(argv)


if __name__ == "__main__":
    sys.exit(main())
