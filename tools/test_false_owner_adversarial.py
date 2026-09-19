#!/usr/bin/env python3
"""V-W3-OWNER-* -- the false-owner adversarial gate (UCR-CIF W3, PR-W3-9).

The claim under attack: `disposition_ledger.propose` is a candidate generator
whose evidence is LEXICAL, so an owner with broader vocabulary wins whether or
not it owns anything. Measured on the real ledger with an instrument that is not
the scorer:

    spearman(proposals, distinct vocabulary) = +0.756
    spearman(proposals, bytes)               = +0.735
    agents/oneshot-architect-auditor.md -- 214 proposals from ONE 36 KB file

This gate is INDEPENDENT of that scorer by construction (§XIX: no generator
grading itself). It never calls `propose`; it builds a synthetic estate on disk,
runs the structural adjudicator over it, and requires the SMALL REAL OWNER to
win against a LARGE IRRELEVANT ONE.

The six adversarial cases the mission names, each a directory in a throwaway
repository:

  1 large irrelevant vocabulary candidate   a big document saying everything
  2 small but actual runtime owner          a tiny module that DEFINES the thing
  3 documentation-only vs real consumer     prose about it vs an import of it
  4 alias names                             snake_case / camelCase / kebab-case
  5 multiple legitimate owners              two real owners -> no false pick
  6 no-owner case                           a term nobody owns -> ABSTAIN

Run: python tools/test_false_owner_adversarial.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.ucr_cif.ownership_evidence import (  # noqa: E402
    VOLUME_OUTLIER_PROPOSALS, adjudicate, build_structural_index, distinctive,
    evidence_for, structural_holders,
)

_PASS = 0
_FAIL = 0


def _ok(g, e):
    global _PASS
    _PASS += 1
    print(f"  PASS {g}: {e}")


def _fail(g, d):
    global _FAIL
    _FAIL += 1
    print(f"  FAIL {g}: {d}")


def _check(g, cond, ev, diag=""):
    _ok(g, ev) if cond else _fail(g, diag or ev)


# --------------------------------------------------------------------------- #
# A synthetic estate. Built rather than mocked: the adjudicator walks a real
# directory tree, so this exercises its real parsing, not a stubbed index.
# --------------------------------------------------------------------------- #
FILLER = " ".join(f"word{i}" for i in range(1, 900))


def build_estate(root: Path) -> None:
    mod = root / "modules"

    # 1. The volume candidate. Enormous, mentions everything, defines nothing.
    big = mod / "governance-overlay"
    big.mkdir(parents=True)
    (big / "doctrine.md").write_text(
        "# Doctrine\n"
        + ("Every mission must consider quarantine, quarantine policy, and the "
           "quarantine of failing capabilities. " * 60)
        + FILLER + "\n" + FILLER + "\n",
        encoding="utf-8")
    (big / "more.md").write_text(FILLER + "\nquarantine " * 40, encoding="utf-8")

    # 2. The real owner. One small file that DEFINES the capability.
    real = mod / "quarantine_engine"
    real.mkdir(parents=True)
    (real / "quarantine.py").write_text(
        "class QuarantineEngine:\n"
        "    def quarantine_unit(self, uid):\n"
        "        return uid\n",
        encoding="utf-8")

    # 3. A consumer, so the real owner has an inbound edge.
    consumer = mod / "pipeline"
    consumer.mkdir(parents=True)
    (consumer / "run.py").write_text(
        "from modules.quarantine_engine.quarantine import QuarantineEngine\n"
        "def go():\n"
        "    return QuarantineEngine()\n",
        encoding="utf-8")

    # 5. A second legitimate owner of a DIFFERENT capability.
    other = mod / "ledger_writer"
    other.mkdir(parents=True)
    (other / "ledger_writer.py").write_text(
        "def write_ledger_row(row):\n    return row\n", encoding="utf-8")
    (other / "registry.json").write_text(
        json.dumps({"ledger_row": {"schema": 1}}), encoding="utf-8")

    # 4. Alias spellings of one capability, across three naming conventions.
    alias = mod / "retry_budget"
    alias.mkdir(parents=True)
    (alias / "retryBudget.js").write_text(
        "class RetryBudget { }\nfunction retry_budget_of(x) { return x }\n",
        encoding="utf-8")

    # 7. THE DILUTION ATTACK. Enough mention-only decoys that, if mentions were
    # counted as structural holders, `quarantine` would exceed the ceiling and
    # stop being distinctive -- so a false owner could disarm a real one just by
    # talking about its capability. One decoy cannot express this; the mutation
    # that counts mentions survived a fixture that had only one.
    for i in range(6):
        d = mod / f"chatter_{i}"
        d.mkdir(parents=True)
        (d / "notes.md").write_text(
            "quarantine quarantine quarantine, we discuss quarantine at "
            "length and define nothing.\n" + FILLER, encoding="utf-8")

    # 8. A term MANY owners structurally hold. Held is not the same as
    # discriminating: a symbol six modules all define cannot select between
    # them, and promotion on it would be promotion on estate vocabulary.
    for i in range(6):
        d = mod / f"shared_helper_{i}"
        d.mkdir(parents=True)
        (d / "helper.py").write_text(
            "def commonhelper(x):\n    return x\n", encoding="utf-8")


def main() -> int:
    print("V-W3-OWNER -- false-owner adversarial gate")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        build_estate(root)
        idx = build_structural_index(root)

        # Instrument controls FIRST. An index that saw nothing would make every
        # assertion below pass by reporting ABSTAIN everywhere.
        print("\n[instrument controls]")
        _check("V-W3-OWNER-CONTROL-POPULATION",
               idx["files_seen"] >= 7 and len(idx["owners"]) >= 5,
               f"index saw {idx['files_seen']} files across "
               f"{len(idx['owners'])} owners",
               f"index is empty or tiny: {idx['files_seen']} files, "
               f"{len(idx['owners'])} owners -- every verdict below would be "
               "vacuous")
        _check("V-W3-OWNER-CONTROL-VOLUME-IS-BIGGEST",
               len(idx["owner_terms"]["modules/governance-overlay"])
               > len(idx["owner_terms"]["modules/quarantine_engine"]) * 10,
               f"the decoy really is the vocabulary winner: "
               f"{len(idx['owner_terms']['modules/governance-overlay'])} terms "
               f"vs {len(idx['owner_terms']['modules/quarantine_engine'])}",
               "the decoy is not actually larger; the trap is not represented")

        # --- case 1+2: volume candidate vs small real owner -----------------
        print("\n[case 1+2 -- large irrelevant vocabulary vs small real owner]")
        terms = ["quarantine"]
        counts = {"modules/governance-overlay": 452,
                  "modules/quarantine_engine": 3}

        a_big = adjudicate("u1", "modules/governance-overlay", terms, idx, counts)
        _check("V-W3-OWNER-VOLUME-REJECTED",
               a_big.verdict == "REJECT",
               f"volume candidate -> {a_big.verdict}: {a_big.reason}",
               f"a 118 KB document that defines nothing was not rejected: "
               f"{a_big.verdict} / {a_big.reason}")

        a_real = adjudicate("u1", "modules/quarantine_engine", terms, idx, counts)
        _check("V-W3-OWNER-REAL-VERIFIED",
               a_real.verdict == "VERIFY" and "SYMBOL" in a_real.evidence["structural"],
               f"real owner -> VERIFY on {a_real.evidence['structural']}",
               f"the actual owner was not verified: {a_real.verdict} / "
               f"{a_real.reason}")

        # The load-bearing comparison: the two verdicts must DIFFER. Asserting
        # only the rejection would pass against an adjudicator that rejects
        # everything.
        _check("V-W3-OWNER-DISCRIMINATES",
               a_big.verdict != a_real.verdict,
               f"same term, opposite verdicts: big={a_big.verdict} "
               f"real={a_real.verdict}",
               "the adjudicator returns the same verdict for both -- it is not "
               "discriminating, it is just refusing")

        # --- case 3: documentation-only vs real consumer --------------------
        print("\n[case 3 -- documentation-only vs a real consumer]")
        ev_big = evidence_for("modules/governance-overlay", terms, idx)
        ev_real = evidence_for("modules/quarantine_engine", terms, idx)
        _check("V-W3-OWNER-DOC-HAS-NO-STRUCTURE",
               not ev_big.structural,
               "the document carries no structural signal at all",
               f"the document claimed {ev_big.structural}")
        _check("V-W3-OWNER-CONSUMER-EDGE",
               ev_real.inbound_imports >= 1,
               f"the real owner has {ev_real.inbound_imports} inbound import(s)",
               "the real owner shows no consumer edge; the import was not seen")

        # --- case 4: alias names --------------------------------------------
        print("\n[case 4 -- alias spellings of one capability]")
        owners_for_alias = idx["defined"].get("retry", set()) | \
            idx["defined"].get("budget", set())
        _check("V-W3-OWNER-ALIAS-RESOLVED",
               "modules/retry_budget" in owners_for_alias,
               "camelCase `RetryBudget`, snake_case `retry_budget_of` and the "
               "kebab path all resolve to one owner",
               f"alias spellings did not resolve: {sorted(owners_for_alias)}")

        # --- case 5: multiple legitimate owners -----------------------------
        print("\n[case 5 -- two real owners, no false pick]")
        a_ledger = adjudicate("u2", "modules/ledger_writer", ["ledger"], idx,
                              counts)
        a_cross = adjudicate("u2", "modules/quarantine_engine", ["ledger"], idx,
                             counts)
        _check("V-W3-OWNER-SECOND-OWNER-VERIFIED",
               a_ledger.verdict == "VERIFY",
               f"the ledger owner verifies on its own term: "
               f"{a_ledger.evidence['structural']}",
               f"a legitimate second owner was not verified: {a_ledger.reason}")
        _check("V-W3-OWNER-NO-CROSS-CLAIM",
               a_cross.verdict != "VERIFY",
               f"the quarantine owner does NOT verify for 'ledger' "
               f"({a_cross.verdict})",
               "an owner verified for a capability it does not own")

        # --- case 6: no owner ------------------------------------------------
        print("\n[case 6 -- a term nobody owns]")
        a_none = adjudicate("u3", "modules/pipeline", ["zzzznonexistent"], idx,
                            counts)
        _check("V-W3-OWNER-NO-OWNER-ABSTAINS",
               a_none.verdict == "ABSTAIN",
               f"unowned term -> ABSTAIN: {a_none.reason}",
               f"an unowned term produced {a_none.verdict}")
        a_empty = adjudicate("u4", "", ["quarantine"], idx, counts)
        _check("V-W3-OWNER-NO-CANDIDATE-ABSTAINS",
               a_empty.verdict == "ABSTAIN",
               "no candidate at all -> ABSTAIN, never a guess",
               f"an empty candidate produced {a_empty.verdict}")

        # --- distinctiveness is the antidote to volume ----------------------
        print("\n[distinctiveness -- why breadth cannot win]")
        # Exact, not a `>=` comparison. The first version asserted
        # `len(owned) >= len(shared)`, which is true in BOTH worlds and let a
        # mutation disabling distinctiveness entirely pass 14/14.
        shared = distinctive(["word5"], idx)
        owned = distinctive(["quarantine"], idx)
        _check("V-W3-OWNER-DISTINCTIVENESS",
               shared == [] and owned == ["quarantine"],
               f"filler held by nobody is NOT distinctive ({shared}); the "
               f"structurally-owned term is ({owned})",
               f"distinctiveness did not separate them: filler={shared} "
               f"owned={owned}")

        # The dilution attack: six decoys mention `quarantine` and define
        # nothing. If mentions counted as holders, the term would exceed the
        # ceiling and the REAL owner would lose its distinctive evidence.
        holders = structural_holders("quarantine", idx)
        _check("V-W3-OWNER-DILUTION-RESISTED",
               holders == {"modules/quarantine_engine"},
               f"six mention-only decoys did not become holders: "
               f"{sorted(holders)}",
               f"mentions became structural holders: {sorted(holders)} -- a "
               "false owner can disarm a real one by talking about it")
        a_diluted = adjudicate("u6", "modules/quarantine_engine", terms, idx,
                               counts)
        _check("V-W3-OWNER-DILUTION-VERDICT-HOLDS",
               a_diluted.verdict == "VERIFY",
               "the real owner still VERIFIES with six decoys present",
               f"dilution changed the verdict to {a_diluted.verdict}")

        # Held by many is not discriminating: promotion must not follow.
        many = structural_holders("commonhelper", idx)
        _check("V-W3-OWNER-SHARED-SYMBOL-NOT-DISTINCTIVE",
               len(many) >= 5 and distinctive(["commonhelper"], idx) == [],
               f"a symbol {len(many)} owners define is not distinctive",
               f"a widely-defined symbol stayed distinctive: holders={len(many)}")
        a_shared = adjudicate("u7", "modules/shared_helper_0", ["commonhelper"],
                              idx, counts)
        _check("V-W3-OWNER-SHARED-SYMBOL-ABSTAINS",
               a_shared.verdict == "ABSTAIN",
               f"a real symbol on estate-wide vocabulary -> ABSTAIN: "
               f"{a_shared.reason}",
               f"promoted on a term six owners define: {a_shared.verdict}")

        # --- the rule that must NOT be reachable by lexical means ------------
        print("\n[promotion requires structure, always]")
        lexical_only = adjudicate("u5", "modules/governance-overlay",
                                  ["quarantine"] * 50, idx, counts)
        _check("V-W3-OWNER-REPETITION-CANNOT-PROMOTE",
               lexical_only.verdict != "VERIFY",
               f"the same term fifty times still cannot promote "
               f"({lexical_only.verdict})",
               "repetition promoted a candidate -- the gate is lexical after "
               "all")

    total = _PASS + _FAIL
    print(f"\nOWNER_PASS={_PASS}/{total}  failures={_FAIL}")
    if total < 13:
        print(f"HARNESS-FAILED: only {total} gates ran")
        return 2
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
