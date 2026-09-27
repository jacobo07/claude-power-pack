"""V-FACTSV2-* -- GSDX-M05: what the fact source could NOT say reaches the gate.

THE DEFECT THIS PROVES CLOSED. `structured_facts.load()` returned a list of
facts in which PRESENCE MEANT HOLDS. `obligation.derive_from_facts` gates every
operator on `_has()`, a set-membership test. So a fact nobody could measure was
simply absent, `_has` returned False, no obligation was derived, and
`closure.project_closure` -- which can only block on obligations that EXIST --
reported ALLOWED. "Measured false" and "could not measure" produced a
byte-identical receipt and an identical gate exit code.

WHAT IS AND IS NOT WORTH BLOCKING FOR. An operator reads a fact in one of two
ways. A GATING read decides whether the obligation exists at all; if it is
unknown, nobody can say what the mission owes, and a closure may not claim
completeness over it. An ENRICHING read only extends an obligation that already
exists, by a sentence of consequence and a citation; an unknown one costs
explanation, never a verdict. Blocking on the second is ceremony tax, and a gate
that charges ceremony tax is a gate somebody switches off -- after which it
protects nothing at all.

THE GREEN POLES ARE THE POINT OF HALF THIS FILE. `cmd_check`'s exit code has
been widened twice before and both attempts broke a mission that should pass
(gsd_x_mission.py, the two paragraphs above its return). This wave widens it
again, so a prose mission, an empty phase directory, a nonexistent root and a
clean v2 document are each pinned here, exiting exactly what they exited before.

HONEST BOUNDARY, ASSERTED RATHER THAN WRITTEN DOWN. V-FACTSV2-PRODUCER-REACH
measures that NO fact today's producer can emit is a gating fact. The mechanism
below is therefore correct and NOT reachable from the real producer: proving it
needs a constructed document. That gate fails the day a producer starts emitting
a gating fact, which is exactly when this note must stop being true.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from modules.gsd_x.mission import closure as cl          # noqa: E402
from modules.gsd_x.mission import obligation as ob       # noqa: E402
from modules.gsd_x.mission import structured_facts as sf  # noqa: E402

CLI = REPO / "tools" / "gsd_x_mission.py"

GATING = "no_completion_signal"        # op_absent_signal_consequence gates on it
ENRICHING = "consumer_assumes_complete"  # same operator, enrichment only
ORPHAN = "unattended_operation"        # read by no operator at all

_passes: list[str] = []
_fails: list[str] = []


def _ok(g: str, e: str) -> None:
    _passes.append(g)
    print(f"  PASS {g}: {e}")


def _fail(g: str, e: str) -> None:
    _fails.append(g)
    print(f"  FAIL {g}: {e}")


def _harness(why: str) -> int:
    print(f"\nHARNESS-FAILED: {why}")
    print("GSDX_FACTSV2_PASS=0/0  threshold=HARNESS")
    return 2


def _dep(path: Path) -> dict:
    return sf.fingerprint(path)


def _v2(facts=(), not_held=(), unknown=()) -> dict:
    return {
        "schema": sf.SCHEMA_V2,
        "provenance": "constructed by tools/test_gsd_x_facts_v2.py",
        "facts": list(facts), "not_held": list(not_held), "unknown": list(unknown),
    }


def _held(name: str, dep: dict, state: str = None) -> dict:
    return {"name": name, "evidence": f"{name} observed for the test",
            "state": state or ob.OBSERVED, "depends_on": [dep]}


def _note(name: str, dep: dict, state: str = None) -> dict:
    return {"name": name, "state": state or ob.UNKNOWN,
            "why": f"{name} could not be established in the test", "depends_on": [dep]}


def _covered(dep: dict, held=(), not_held=(), unknown=()) -> dict:
    """A document that dispositions EVERY gating fact, with named exceptions.

    GSDX-M06 made an undispositioned gating fact block (F7), so a fixture that
    mentions one name now blocks for TWO reasons: the thing it is testing, and
    five gating names nobody asked about. Every case below wants exactly one
    variable, so the baseline is full gating coverage and each case moves only
    the names it is actually about.

    Built from `ob.GATING_FACT_NAMES` rather than a literal list, so a new
    operator changes the fixtures automatically instead of leaving them quietly
    incomplete.
    """
    moved = {n for n in list(not_held) + list(unknown)} | {n for n in held}
    baseline = [_held(n, dep) for n in sorted(ob.GATING_FACT_NAMES - moved)]
    return _v2(facts=baseline + [_held(n, dep) for n in held],
               not_held=[_note(n, dep, ob.OBSERVED) for n in not_held],
               unknown=[_note(n, dep) for n in unknown])


def _refused(doc, label: str, gate: str, expect_in: str = "") -> None:
    with tempfile.TemporaryDirectory(prefix="gsdxv2_") as tmp:
        p = Path(tmp) / sf.FACTS_FILE
        if isinstance(doc, bytes):
            p.write_bytes(doc)
        else:
            p.write_text(json.dumps(doc), encoding="utf-8")
        try:
            got = sf.load_document(p)
        except sf.StructuredFactsError as exc:
            if expect_in and expect_in not in str(exc):
                _fail(gate, f"{label} refused, but for the wrong reason: {exc}")
                return
            _ok(gate, f"{label} refused: {str(exc)[:110]}")
            return
        _fail(gate, f"{label} was ACCEPTED as held={[f.name for f in got.held]}")


def _run_check(root: Path) -> tuple[int, dict]:
    r = subprocess.run([sys.executable, str(CLI), "check", str(root),
                        "--exit-code", "--raw"], capture_output=True, text=True,
                       encoding="utf-8", timeout=180)
    payload = {}
    try:
        payload = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        pass
    return r.returncode, payload


def _mission(tmp: Path, doc=None, intent="", reality="") -> Path:
    root = Path(tmp)
    (root / "INTENT.txt").write_text(intent, encoding="utf-8")
    (root / "README.md").write_text(reality, encoding="utf-8")
    if doc is not None:
        (root / sf.FACTS_FILE).write_text(json.dumps(doc), encoding="utf-8")
    return root


def main() -> int:  # noqa: C901 -- a gate reads better flat than factored
    # ---- the reads table matches the SOURCE ------------------------------
    # Structural, from the AST, never from a second hand-written list. A
    # `_has` inside a guard that returns None is GATING; every other `_has` is
    # ENRICHING. Two hand-maintained truths would drift, and one of them being
    # a comment would drift silently.
    import ast
    src = (REPO / "modules" / "gsd_x" / "mission" / "obligation.py")
    tree = ast.parse(src.read_text(encoding="utf-8"))
    actual: dict[str, tuple[set, set]] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("op_"):
            continue
        gating, enriching = set(), set()
        for sub in ast.walk(node):
            if not isinstance(sub, ast.If):
                continue
            returns_none = any(
                isinstance(s, ast.Return)
                and (s.value is None
                     or (isinstance(s.value, ast.Constant) and s.value.value is None))
                for s in ast.walk(sub))
            for call in ast.walk(sub):
                if not (isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Name)
                        and call.func.id == "_has"):
                    continue
                names = {a.value for a in call.args[1:]
                         if isinstance(a, ast.Constant) and isinstance(a.value, str)}
                (gating if returns_none else enriching).update(names)
        actual[node.name] = (gating, enriching)

    if not actual:
        return _harness("no op_* functions found in obligation.py; the AST walk "
                        "is broken and every comparison below would be vacuous")
    if len(actual) != len(ob._READS):
        _fail("V-FACTSV2-READS-MATCH-SOURCE",
              f"source has {sorted(actual)} but _READS declares {sorted(ob._READS)}")
    else:
        bad = [n for n, (g, e) in actual.items()
               if (set(ob._READS[n][0]), set(ob._READS[n][1])) != (g, e)]
        if bad:
            _fail("V-FACTSV2-READS-MATCH-SOURCE",
                  "; ".join(f"{n}: source gating={sorted(actual[n][0])} "
                            f"enriching={sorted(actual[n][1])} but declared "
                            f"{ob._READS[n]}" for n in bad))
        else:
            _ok("V-FACTSV2-READS-MATCH-SOURCE",
                f"{len(actual)} operators; declared gating/enriching sets equal "
                "the ones walked out of the source")

    if ob.ORPHAN_FACT_NAMES == {ORPHAN}:
        _ok("V-FACTSV2-ORPHAN-NAMED",
            f"exactly one fact in the vocabulary is read by no operator: {ORPHAN!r}")
    else:
        _fail("V-FACTSV2-ORPHAN-NAMED",
              f"expected {{{ORPHAN!r}}}, got {sorted(ob.ORPHAN_FACT_NAMES)}")

    if GATING in ob.GATING_FACT_NAMES and ENRICHING in ob.ENRICHING_FACT_NAMES:
        _ok("V-FACTSV2-FIXTURE-POLES-REAL",
            f"{GATING!r} really is gating and {ENRICHING!r} really is enriching")
    else:
        return _harness(f"the fixture's poles are wrong: {GATING!r} gating="
                        f"{GATING in ob.GATING_FACT_NAMES}, {ENRICHING!r} "
                        f"enriching={ENRICHING in ob.ENRICHING_FACT_NAMES}")

    # ---- loader: both schemas, and every refusal -------------------------
    with tempfile.TemporaryDirectory(prefix="gsdxv2_src_") as tmp:
        srcfile = Path(tmp) / "source.txt"
        srcfile.write_text("original", encoding="utf-8")
        dep = _dep(srcfile)
        # A SECOND source that never moves. The staleness case below rewrites
        # `srcfile`, and every entry sharing one dep would go stale together --
        # so the gate would exit 1 naming all six and the case could no longer
        # show that freshness is per-entry.
        stable = Path(tmp) / "stable.txt"
        stable.write_text("never rewritten", encoding="utf-8")
        dep2 = _dep(stable)

        v1 = {"schema": sf.SCHEMA_V1, "provenance": "legacy",
              "facts": [{"name": GATING, "evidence": "declared the old way"}]}
        with tempfile.TemporaryDirectory(prefix="gsdxv2_") as t2:
            p = Path(t2) / sf.FACTS_FILE
            p.write_text(json.dumps(v1), encoding="utf-8")
            fs = sf.load_document(p)
            if fs.schema == sf.SCHEMA_V1 and len(fs.held) == 1 and not fs.unknown:
                _ok("V-FACTSV2-LEGACY-VALID",
                    "a v1 document still loads, one held fact, no blindness channel")
            else:
                _fail("V-FACTSV2-LEGACY-VALID", f"{fs}")
            if [f.name for f in sf.load(p)] == [GATING]:
                _ok("V-FACTSV2-LOAD-V1-UNCHANGED", "load() still returns held facts")
            else:
                _fail("V-FACTSV2-LOAD-V1-UNCHANGED", f"{sf.load(p)}")

        doc = _v2(facts=[_held(GATING, dep)], unknown=[_note(ENRICHING, dep)])
        with tempfile.TemporaryDirectory(prefix="gsdxv2_") as t2:
            p = Path(t2) / sf.FACTS_FILE
            p.write_text(json.dumps(doc), encoding="utf-8")
            fs = sf.load_document(p)
            if fs.is_v2 and [f.name for f in fs.held] == [GATING] \
                    and fs.unknown_names == [ENRICHING]:
                _ok("V-FACTSV2-VALID",
                    "a v2 document loads held and unknown as separate buckets")
            else:
                _fail("V-FACTSV2-VALID", f"held={fs.held} unknown={fs.unknown_names}")
            # load() must ACCEPT v2 -- refusing it would make every document the
            # producer emits unreadable -- while DROPPING the blindness, which
            # is exactly why the mission path does not use it.
            got = sf.load(p)
            if [f.name for f in got] == [GATING]:
                _ok("V-FACTSV2-LOAD-ACCEPTS-V2-AND-DROPS-BLINDNESS",
                    "load() reads v2 and returns only held facts; the unknown "
                    "bucket is invisible through it, which is why the mission "
                    "path uses load_document()")
            else:
                _fail("V-FACTSV2-LOAD-ACCEPTS-V2-AND-DROPS-BLINDNESS", f"{got}")

        _refused(_v2(facts=[{"name": GATING, "evidence": "x", "depends_on": [dep]}]),
                 "v2 held entry with no state", "V-FACTSV2-REFUSE-NO-STATE", "'state'")
        _refused(_v2(facts=[{"name": GATING, "evidence": "x", "state": ob.OBSERVED}]),
                 "v2 held entry with no depends_on", "V-FACTSV2-REFUSE-NO-DEPENDS-ON",
                 "depends_on")
        _refused({"schema": "gsdx-facts/3", "provenance": "x", "facts": []},
                 "an unsupported future version", "V-FACTSV2-REFUSE-FUTURE-VERSION",
                 "gsdx-facts/3")
        _refused(b"{not json", "malformed JSON", "V-FACTSV2-REFUSE-MALFORMED")
        _refused(_v2(facts=[_held(GATING, dep)], unknown=[_note(GATING, dep)]),
                 "one name in two buckets", "V-FACTSV2-REFUSE-CROSS-BUCKET", "both")
        _refused(_v2(facts=[_held(GATING, dep, state=ob.UNKNOWN)]),
                 "a held entry whose state is UNKNOWN",
                 "V-FACTSV2-REFUSE-HELD-UNKNOWN", "UNKNOWN")
        _refused({"schema": sf.SCHEMA_V1, "provenance": "x", "facts": [],
                  "unknown": [_note(GATING, dep)]},
                 "a v2 bucket inside a v1 document",
                 "V-FACTSV2-REFUSE-V2-BUCKET-IN-V1", sf.SCHEMA_V2)
        _refused(_v2(facts=[{"name": GATING, "evidence": "x", "state": "MADE_UP",
                             "depends_on": [dep]}]),
                 "an unknown state word", "V-FACTSV2-REFUSE-BAD-STATE", "MADE_UP")

        # dump() is v1 by construction, so a round trip RESETS state. Asserted
        # rather than left for a reader to discover.
        rt = sf.dump([ob.Fact(GATING, "e", "prose", state=ob.EXTRACTED)], "x")
        if rt["schema"] == sf.SCHEMA_V1 and "state" not in rt["facts"][0]:
            _ok("V-FACTSV2-DUMP-ROUNDTRIP-IS-V1",
                "dump() emits v1 and carries no state; a round trip returns the "
                "default, which is v1 being v1 and not a silent loss")
        else:
            _fail("V-FACTSV2-DUMP-ROUNDTRIP-IS-V1", f"{rt}")

        # ---- the decision boundary ---------------------------------------
        intent = ("Upload the nightly export to the bucket and then delete the "
                  "local copy.")
        reality = "Versioning: off. No backups. Lifecycle rules: none."

        # (1) a GATING fact unknown -> blocks.
        #     Every OTHER gating fact is held, so the only thing this case can
        #     block on is the unknown. Before GSDX-M06 the bare document also
        #     left five names undispositioned, and the case would have passed
        #     on a compound reason.
        with tempfile.TemporaryDirectory(prefix="gsdxv2_m1_") as t2:
            root = _mission(Path(t2), _covered(dep, unknown=[GATING]),
                            intent, reality)
            code, payload = _run_check(root)
            if code == 1 and payload.get("unmeasured_facts") == [GATING] \
                    and not payload.get("unproduced_facts") \
                    and payload.get("block") is True:
                _ok("V-FACTSV2-UNKNOWN-GATING-BLOCKS",
                    f"exit 1 naming {GATING!r} with open_obligations="
                    f"{payload.get('open_obligations')} and unproduced=[] -- the "
                    "block comes from blindness alone, not from an obligation "
                    "and not from missing coverage")
            else:
                _fail("V-FACTSV2-UNKNOWN-GATING-BLOCKS",
                      f"exit={code} payload={payload}")

        # (2) an ENRICHING fact unknown -> disclosed, never blocks
        with tempfile.TemporaryDirectory(prefix="gsdxv2_m2_") as t2:
            root = _mission(Path(t2), _covered(dep, unknown=[ENRICHING]),
                            intent, reality)
            code, payload = _run_check(root)
            if code == 0 and not payload.get("unmeasured_facts") \
                    and not payload.get("unproduced_facts") \
                    and any(ENRICHING in d for d in payload.get("disclosures", [])):
                _ok("V-FACTSV2-UNKNOWN-ENRICHING-DISCLOSED-NOT-BLOCKING",
                    f"exit 0 and {ENRICHING!r} is disclosed rather than blocked on")
            else:
                _fail("V-FACTSV2-UNKNOWN-ENRICHING-DISCLOSED-NOT-BLOCKING",
                      f"exit={code} payload={payload}")

        # (3) an ORPHAN unknown -> cannot change a verdict, so it does not block
        with tempfile.TemporaryDirectory(prefix="gsdxv2_m3_") as t2:
            root = _mission(Path(t2), _covered(dep, unknown=[ORPHAN]),
                            intent, reality)
            code, payload = _run_check(root)
            if code == 0 and not payload.get("unmeasured_facts") \
                    and not payload.get("unproduced_facts") \
                    and not payload.get("disclosures"):
                _ok("V-FACTSV2-ORPHAN-UNKNOWN-DOES-NOT-BLOCK",
                    f"{ORPHAN!r} is read by no operator, so its absence changes "
                    "no verdict and holds no wave -- and it is never REQUIRED "
                    "either, so coverage does not resurrect it as unproduced")
            else:
                _fail("V-FACTSV2-ORPHAN-UNKNOWN-DOES-NOT-BLOCK",
                      f"exit={code} payload={payload}")

        # (4) a clean v2 document -> GREEN. Without this, a gate that blocked on
        #     every v2 document would pass every assertion above.
        with tempfile.TemporaryDirectory(prefix="gsdxv2_m4_") as t2:
            root = _mission(Path(t2), _covered(dep), intent, reality)
            code, payload = _run_check(root)
            if code == 0 and payload.get("block") is False:
                _ok("V-FACTSV2-GREEN-CLEAN-V2",
                    "a v2 document that dispositions every gating fact and has "
                    "nothing unknown still exits 0 -- the coverage requirement "
                    "is SATISFIABLE, so the F7 block is not a gate that refuses "
                    "every document")
            else:
                _fail("V-FACTSV2-GREEN-CLEAN-V2", f"exit={code} payload={payload}")

        # (4b) an EMPTY but well-formed v2 document -> BLOCKS, and the REASON is
        #      what this pole is for.
        #
        #      INVERTED 2026-09-27 (GSDX-M06). It used to require exit 0, which
        #      was the purest form of F7: a document answering nothing at all
        #      passed. What it was really protecting is unchanged and still
        #      asserted -- `freshness_verdict` answers UNKNOWN for zero rows,
        #      the same word a vanished source gets, so a blindness fed from the
        #      one-word aggregate would block here with `stale_facts` populated.
        #      It must block with stale EMPTY and unproduced FULL: the wave is
        #      held because nobody asked the questions, not because a freshness
        #      aggregate was misread.
        with tempfile.TemporaryDirectory(prefix="gsdxv2_m4b_") as t2:
            root = _mission(Path(t2), _v2(), intent, reality)
            code, payload = _run_check(root)
            if code == 1 and payload.get("block") is True \
                    and set(payload.get("unproduced_facts") or []) \
                    == set(ob.GATING_FACT_NAMES) \
                    and not payload.get("stale_facts") \
                    and not payload.get("unmeasured_facts"):
                _ok("V-FACTSV2-EMPTY-DOCUMENT-IS-NOT-COVERAGE",
                    "a v2 document with no entries exits 1 naming all "
                    f"{len(ob.GATING_FACT_NAMES)} gating facts UNPRODUCED, with "
                    "stale and unmeasured both empty -- it is held for the "
                    "absence of questions, not by the zero-row aggregate")
            else:
                _fail("V-FACTSV2-EMPTY-DOCUMENT-IS-NOT-COVERAGE",
                      f"exit={code} payload={payload}")

        # (5) STALE on a gating fact -> blocks. The source moves after the
        #     document was written, which is the whole freshness contract.
        with tempfile.TemporaryDirectory(prefix="gsdxv2_m5_") as t2:
            # Full gating coverage, but only GATING hangs off the file that
            # moves; the rest depend on `stable`. Sharing one dep would staleize
            # all six together, and the case could no longer show that freshness
            # is decided per entry rather than per document.
            staleable = _v2(
                facts=[_held(GATING, dep)]
                      + [_held(n, dep2)
                         for n in sorted(ob.GATING_FACT_NAMES - {GATING})])
            root = _mission(Path(t2), staleable, intent, reality)
            srcfile.write_text("CHANGED after the document was produced",
                               encoding="utf-8")
            code, payload = _run_check(root)
            srcfile.write_text("original", encoding="utf-8")
            if code == 1 and payload.get("stale_facts") == [GATING] \
                    and not payload.get("unproduced_facts"):
                _ok("V-FACTSV2-STALE-GATING-BLOCKS",
                    f"a source change makes {GATING!r} not current and the gate "
                    "exits 1 naming it")
            else:
                _fail("V-FACTSV2-STALE-GATING-BLOCKS",
                      f"exit={code} payload={payload}")

        # (6) a DEAD operator requires nothing further. `_has()` is `all(...)`,
        #     so an operator with a gating fact measured FALSE can never fire --
        #     demanding its remaining gating facts would be production nobody
        #     can act on, which is the ceremony tax obligation.py:400-420 names
        #     and the reason a gate gets switched off.
        with tempfile.TemporaryDirectory(prefix="gsdxv2_m6_") as t2:
            root = _mission(Path(t2), _covered(dep, not_held=[GATING]),
                            intent, reality)
            code, payload = _run_check(root)
            if code == 0 and not payload.get("unproduced_facts") \
                    and payload.get("block") is False:
                _ok("V-FACTSV2-DEAD-OPERATOR-REQUIRES-NOTHING",
                    f"{GATING!r} measured FALSE kills its operator, so coverage "
                    "stops requiring that operator's other gating reads and the "
                    "wave is not held for a fact that could not change a verdict")
            else:
                _fail("V-FACTSV2-DEAD-OPERATOR-REQUIRES-NOTHING",
                      f"exit={code} payload={payload}")

        # (7) an UNPRODUCED gating fact blocks, and says which one. The narrow
        #     pole for F7 itself; the cutover comparison below is the wide one.
        with tempfile.TemporaryDirectory(prefix="gsdxv2_m7_") as t2:
            missing = sorted(ob.GATING_FACT_NAMES - {GATING})
            root = _mission(Path(t2), _v2(facts=[_held(GATING, dep)]),
                            intent, reality)
            code, payload = _run_check(root)
            if code == 1 and payload.get("block") is True \
                    and payload.get("unproduced_facts") == missing \
                    and not payload.get("unmeasured_facts") \
                    and payload.get("message"):
                _ok("V-FACTSV2-UNPRODUCED-GATING-BLOCKS",
                    f"a document disposing 1 of {len(ob.GATING_FACT_NAMES)} "
                    "gating facts exits 1 naming the other "
                    f"{len(missing)} UNPRODUCED, with a non-empty message -- a "
                    "block the caller can act on rather than retry blindly")
            else:
                _fail("V-FACTSV2-UNPRODUCED-GATING-BLOCKS",
                      f"exit={code} payload={payload}")

    # ---- the green poles the exit code has broken twice before -----------
    with tempfile.TemporaryDirectory(prefix="gsdxv2_g_") as tmp:
        root = Path(tmp) / "prose"
        root.mkdir(parents=True, exist_ok=True)
        _mission(root, None,
                 "Upload the nightly export and then delete the local copy.",
                 "Versioning: off. No backups.")
        code, payload = _run_check(root)
        if code == 0 and payload.get("blindness_source") == "prose":
            _ok("V-FACTSV2-GREEN-PROSE",
                "a prose mission exits 0 and reports source=prose -- the unknown "
                "question cannot be asked there, which is not the same as nothing "
                "being unknown")
        else:
            _fail("V-FACTSV2-GREEN-PROSE", f"exit={code} payload={payload}")

        empty = Path(tmp) / "empty"
        empty.mkdir(parents=True, exist_ok=True)
        code, payload = _run_check(empty)
        if code == 0:
            _ok("V-FACTSV2-GREEN-EMPTY-DIR", "an empty phase dir still exits 0")
        else:
            _fail("V-FACTSV2-GREEN-EMPTY-DIR", f"exit={code} payload={payload}")

        code, payload = _run_check(Path(tmp) / "does-not-exist")
        if code == 2 and "UNREADABLE_INPUT" in json.dumps(payload):
            _ok("V-FACTSV2-GREEN-NONEXISTENT",
                "a nonexistent root is still UNREADABLE_INPUT at exit 2, not a pass")
        else:
            _fail("V-FACTSV2-GREEN-NONEXISTENT", f"exit={code} payload={payload}")

    # ---- measured-empty is not unmeasured --------------------------------
    measured = cl.Blindness(source=sf.SOURCE)
    unmeasured = cl.Blindness()
    if measured.measured and not unmeasured.measured and measured != unmeasured:
        _ok("V-FACTSV2-MEASURED-EMPTY-IS-NOT-UNMEASURED",
            "a document read with nothing unknown and no document at all are "
            "different values, so a receipt cannot conflate them")
    else:
        _fail("V-FACTSV2-MEASURED-EMPTY-IS-NOT-UNMEASURED",
              f"{measured} vs {unmeasured}")

    # ---- INVERTED 2026-09-27 (GSDX-M06): the hole N7 pinned is CLOSED ------
    # THIS GATE USED TO ASSERT THE DEFECT. Until GSDX-M06 it was named
    # V-FACTSV2-CHARACTERIZE-CUTOVER-LOSES-OBLIGATIONS and required, on purpose,
    # that the same INTENT and README produce:
    #
    #   prose      -> DO-1 ACCEPTED, check exit 1
    #   structured -> derived 0,     check exit 0, unmeasured_facts []
    #
    # Merely placing a FACTS.json in a fresh root silently disabled every
    # obligation the prose adapter would have derived, and GSDX-M05's blindness
    # channel could not see it: the three buckets cover facts a producer TRIED
    # to establish, and a fact with NO producer is in none of them -- not even
    # `unknown`. That was the third world the producer's docstring names,
    # "nobody ever asked".
    #
    # It is inverted IN PLACE, and renamed because a gate whose name asserts a
    # defect that no longer exists is a worse lie than no gate. The diff between
    # these two versions is the evidence; a new gate beside a deleted one would
    # not have been.
    #
    # What closed it: modules/gsd_x/mission/coverage.py requires the document to
    # dispose of every GATING fact of every operator that can still fire, and
    # reports the rest as UNPRODUCED -- a category kept distinct from UNKNOWN
    # because a measurement that failed and a question nobody asked need
    # different repairs. The scope is the gating set and nothing wider: the
    # three enriching names and the one orphan are never required, or a ten-name
    # vocabulary would have become a universal prerequisite list.
    with tempfile.TemporaryDirectory(prefix="gsdxv2_cut_") as tmp:
        intent = ("Upload the nightly export to the bucket and then delete the "
                  "local copy.")
        reality = "Versioning: off. No backups. Lifecycle rules: none."
        prose_root = Path(tmp) / "prose"
        prose_root.mkdir(parents=True)
        _mission(prose_root, None, intent, reality)
        prose_code, _ = _run_check(prose_root)
        subprocess.run([sys.executable, str(CLI), "derive", str(prose_root)],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
        prose_code, prose_payload = _run_check(prose_root)

        struct_root = Path(tmp) / "structured"
        struct_root.mkdir(parents=True)
        # Same words, plus a facts document that says nothing about them.
        _mission(struct_root, _v2(facts=[_held(ORPHAN, dep)]), intent, reality)
        subprocess.run([sys.executable, str(CLI), "derive", str(struct_root)],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
        struct_code, struct_payload = _run_check(struct_root)

        # The structured root must block, and it must block FOR THE UNPRODUCED
        # REASON. Asserting only `exit 1` would be satisfied by a gate that
        # refuses every document, which is the failure mode the GREEN poles
        # above exist to exclude -- so the discriminating claim is that the
        # gating names the document never mentioned are named back.
        unprod = set(struct_payload.get("unproduced_facts") or [])
        expected = set(ob.GATING_FACT_NAMES)
        if prose_code == 1 and prose_payload.get("open_obligations") == ["DO-1"] \
                and struct_code == 1 and unprod == expected \
                and struct_payload.get("block") is True \
                and any("UNPRODUCED" in r
                        for r in (struct_payload.get("block_reasons") or [])):
            _ok("V-FACTSV2-CUTOVER-CANNOT-LOSE-OBLIGATIONS",
                "the same intent exits 1 from BOTH adapters: prose derives DO-1, "
                f"and a FACTS.json that says nothing about the {len(expected)} "
                "gating facts exits 1 naming every one of them UNPRODUCED. "
                "Placing a facts document can no longer silently disable an "
                "obligation the prose adapter would have derived")
        else:
            _fail("V-FACTSV2-CUTOVER-CANNOT-LOSE-OBLIGATIONS",
                  f"prose exit={prose_code} open={prose_payload.get('open_obligations')}"
                  f"; structured exit={struct_code} "
                  f"block={struct_payload.get('block')} "
                  f"unproduced={sorted(unprod)} expected={sorted(expected)} "
                  f"reasons={struct_payload.get('block_reasons')}. If the "
                  "structured root exits 0 again, F7 has REGRESSED: a facts "
                  "document is once more able to delete obligations silently")

    # ---- the honest boundary ---------------------------------------------
    # This asserts a LIMITATION. The producer can emit exactly two fact names
    # and neither is gating, so no unknown it produces can reach the block
    # branch above: the mechanism is proved on a constructed document. When a
    # producer starts emitting a gating fact this gate fails, which is the
    # moment this file's opening note must be rewritten.
    sys.path.insert(0, str(REPO / "tools"))
    import gsd_x_fact_producer as FP  # noqa: E402
    producible = set(FP.PRODUCERS)
    reach = producible & ob.GATING_FACT_NAMES
    if not reach:
        _ok("V-FACTSV2-PRODUCER-REACH",
            f"no producible fact is gating (producible={sorted(producible)}); the "
            "blindness block branch is NOT reachable from the real producer "
            "today and is proved on a constructed document")
    else:
        _fail("V-FACTSV2-PRODUCER-REACH",
              f"{sorted(reach)} is now producible AND gating -- the mechanism is "
              "reachable from the producer, so this gate's premise and the "
              "module docstring must both be rewritten")

    total = len(_passes) + len(_fails)
    print(f"\nGSDX_FACTSV2_PASS={len(_passes)}/{total}  threshold={total}/{total}")
    return 0 if not _fails else 1


if __name__ == "__main__":
    sys.exit(main())
