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
      file measuring another pillar never does. A measurement file with neither field is another
      instrument's and is left to the CE clauses. This is the mechanical form of "never substitute
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
    lines = [x.rstrip("\r") for x in (text or "").split("\n")]
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


def check_measurement_scope(led: dict, res, only=None) -> list:
    f = []
    for pid in (list(only) if only is not None else list(ce.PILLARS)):
        st = (led.get("state") or {}).get(pid) or {}
        files = []
        for e in st.get("evidence") or []:
            ref = e.get("ref")
            if e.get("kind") != "measurement" or not ref:
                continue
            fm = front_matter_fields(res.file_text(ref))
            if "evidence_role" not in fm and "terminal_evidence" not in fm:
                continue  # another instrument's measurement: the CE clauses judge it
            files.append((ref, fm))
        on_pillar = [(r, fm) for r, fm in files if fm.get("pillar", pid) == pid]
        has_primary = any((fm.get("evidence_role") or "primary") == "primary" and fm.get("terminal_evidence") is True
                          for _r, fm in on_pillar)
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
                elif not has_primary:
                    f.append(f"R3 {pid}: {ref} is a second_workload file cited without a primary file with "
                             f"terminal_evidence true for pillar {pid}")
            elif fm.get("terminal_evidence") is not True:
                f.append(f"R3 {pid}: {ref} is not terminal evidence: "
                         f"{fm.get('terminal_evidence_reason') or 'terminal_evidence is not true'}")
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

    prim = fm(pillar="E", evidence_role="primary", terminal_evidence=True, second_workload_valid=None)
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
    smoke_files = sorted((REPO / PROGRAM_DIR / "measurements").glob("D-KME-G-*.md"))
    if smoke_files:
        rel = smoke_files[0].relative_to(REPO).as_posix()
        real_led = {"state": {"D": {"terminal": "FALSIFIED_OR_REJECTED_BY_EVIDENCE", "evidence": [
            {"kind": "measurement", "ref": rel, "sha256": ce.lf_sha256(REPO / rel)}]}}}
        got = check_measurement_scope(real_led, ce.Resolver(), only=["D"])
        say(len(got) == 1 and got[0].startswith("R3 D:"),
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
