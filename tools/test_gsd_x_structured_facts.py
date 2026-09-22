"""V-GSDXFACTS-* -- GSDX-M04: facts from structured input, not from a fitted vocabulary.

The derivation operators are general over FACTS. The prose adapter that mines
facts out of README text is a closed vocabulary -- three domains cost three
pattern corrections (gsd-x-n4.RESUMPTION.md, GSDX-M04). This suite proves a
second fact source that does not have that ceiling, and it proves it without
fitting anything to the sealed answer.

g2 PARITY is derived MECHANICALLY from the sealed fixture. The structured facts
are not written by hand: the prose adapter runs over the three sealed blobs,
its facts are serialized to the structured schema, and that document is fed
back through the structured loader. The obligations must be identical. A
hand-authored structured fixture, written with the operators in view, is
exactly the fitting the seal (HOLDOUT-SEALED.md:3-5) exists to exclude -- and
the blob-id seal cannot detect an ADDED file, only an edited one. The seal's
blob ids are re-checked here before anything is derived.

g1 UNSEEN VOCABULARY. A domain phrased with none of the adapter's verbs
("mirror ... then wipe"): the prose adapter misses the irreversibility fact --
that is the measured ceiling, asserted as a control rather than assumed -- and
the same domain declared as structured facts derives the obligation. What this
does NOT prove, and says so: the structured facts were DECLARED. The vocabulary
burden has moved from a regex to whoever writes the facts file; it has not
disappeared. Deriving facts from real infrastructure artifacts is the next
wave, not this one.

Refusals are part of the contract. A fact name the operators do not know is an
instrument error, never a silently dropped fact: a typo'd name would otherwise
remove an obligation and report a clean pass.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

FIXTURE = REPO / "vault" / "benchmarks" / "mission_spine" / "fixture"
SEALED = {  # HOLDOUT-SEALED.md:13-15 -- the seal of record
    "INTENT.txt": "65b00c0",
    "README.md": "b85af34",
    "probe_env.py": "35e1a7d",
}
GIT = r"C:\Program Files\Git\cmd\git.exe"

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
    print("GSDX_FACTS_PASS=0/0  threshold=HARNESS")
    return 2


def _shape(obs) -> list[tuple]:
    """The part of an obligation that must not depend on where facts came from."""
    return sorted((o.identifier, o.operator, tuple(sorted(o.parents)), o.done_gate)
                  for o in obs)


def main() -> int:
    try:
        from modules.gsd_x.mission import obligation as ob
        from modules.gsd_x.mission import structured_facts as sf
    except ImportError as exc:
        # RED by design until the structured adapter exists. This is a subject
        # failure (the capability is absent), not a harness failure.
        _fail("V-GSDXFACTS-MODULE-EXISTS", f"structured adapter not importable: {exc}")
        print(f"\nGSDX_FACTS_PASS={len(_passes)}/{len(_passes) + len(_fails)}  threshold=RED")
        return 1
    _ok("V-GSDXFACTS-MODULE-EXISTS", "modules.gsd_x.mission.structured_facts imports")

    # ---- the seal holds before anything is derived from it ----------------
    for name, want in SEALED.items():
        p = FIXTURE / name
        if not p.is_file():
            return _harness(f"sealed fixture file missing: {p}")
        got = subprocess.run([GIT, "hash-object", str(p)], capture_output=True,
                             text=True).stdout.strip()
        if not got.startswith(want):
            _fail("V-GSDXFACTS-SEAL-INTACT", f"{name} blob {got[:7]} != sealed {want}")
            break
    else:
        _ok("V-GSDXFACTS-SEAL-INTACT", f"3/3 blob ids match HOLDOUT-SEALED.md: {SEALED}")

    intent = (FIXTURE / "INTENT.txt").read_text(encoding="utf-8-sig")
    reality = (FIXTURE / "README.md").read_text(encoding="utf-8-sig")

    # ---- g2: parity, mechanically derived from the seal -------------------
    prose_obs, prose_facts = ob.derive(intent, reality)
    if not prose_obs:
        return _harness("the prose path derived nothing from the sealed fixture; "
                        "parity against an empty set proves nothing")
    doc = sf.dump(prose_facts, provenance="mechanical: prose adapter over sealed fixture")
    with tempfile.TemporaryDirectory(prefix="gsdx_facts_") as tmp:
        path = Path(tmp) / sf.FACTS_FILE
        path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        loaded = sf.load(path)
    struct_obs, _ = ob.derive_from_facts(loaded, intent, reality)
    if _shape(struct_obs) == _shape(prose_obs):
        _ok("V-GSDXFACTS-G2-PARITY",
            f"structured path reproduces the prose path exactly: "
            f"{[o.identifier for o in struct_obs]} from {len(loaded)} facts")
    else:
        _fail("V-GSDXFACTS-G2-PARITY",
              f"prose={_shape(prose_obs)} structured={_shape(struct_obs)}")

    if all(f.source == "structured" for f in loaded):
        _ok("V-GSDXFACTS-PROVENANCE", "every loaded fact is marked source=structured")
    else:
        _fail("V-GSDXFACTS-PROVENANCE",
              f"sources={sorted({f.source for f in loaded})}; a structured fact must say so")

    # ---- g1: a domain the vocabulary has never seen -----------------------
    unseen_intent = ("Mirror the ledger database to cold storage each night, then "
                     "wipe the primary tablespace to reclaim space.")
    unseen_reality = ("The cold storage tier keeps a single generation; there is no "
                      "snapshot schedule on the primary.")
    u_prose_obs, u_prose_facts = ob.derive(unseen_intent, unseen_reality)
    if not any(o.identifier == "DO-1" for o in u_prose_obs):
        _ok("V-GSDXFACTS-G1-CEILING-MEASURED",
            f"prose adapter misses the irreversibility fact on unseen wording "
            f"(facts={[f.name for f in u_prose_facts]})")
    else:
        # If this ever passes, the vocabulary grew to cover "mirror/wipe" and the
        # control needs a new unseen wording -- it is not evidence against g1.
        _fail("V-GSDXFACTS-G1-CEILING-MEASURED",
              "prose adapter now derives DO-1 on this wording; choose a new unseen "
              "domain before trusting g1")

    unseen_doc = {"schema": sf.SCHEMA, "provenance": "declared: test domain",
                  "facts": [
                      {"name": "destructive_act_commanded",
                       "evidence": "INTENT: mirror to cold storage, then wipe the primary"},
                      {"name": "no_recovery_mechanism",
                       "evidence": "cold tier keeps one generation; no snapshots"},
                  ]}
    with tempfile.TemporaryDirectory(prefix="gsdx_facts_") as tmp:
        p = Path(tmp) / sf.FACTS_FILE
        p.write_text(json.dumps(unseen_doc), encoding="utf-8")
        u_struct_obs, _ = ob.derive_from_facts(sf.load(p), unseen_intent, unseen_reality)
    if [o.identifier for o in u_struct_obs] == ["DO-1"]:
        _ok("V-GSDXFACTS-G1-UNSEEN-DERIVES",
            "the same domain, declared structurally, derives exactly DO-1")
    else:
        _fail("V-GSDXFACTS-G1-UNSEEN-DERIVES",
              f"expected [DO-1], got {[o.identifier for o in u_struct_obs]}")

    # negative control: structured input does not over-derive
    one_fact = {"schema": sf.SCHEMA, "provenance": "declared: negative control",
                "facts": [{"name": "destructive_act_commanded",
                           "evidence": "intent destroys after transfer"}]}
    with tempfile.TemporaryDirectory(prefix="gsdx_facts_") as tmp:
        p = Path(tmp) / sf.FACTS_FILE
        p.write_text(json.dumps(one_fact), encoding="utf-8")
        neg_obs, _ = ob.derive_from_facts(sf.load(p), "", "")
    if not neg_obs:
        _ok("V-GSDXFACTS-NO-OVERDERIVE",
            "destructive act WITHOUT absent recovery derives nothing, as the operator requires")
    else:
        _fail("V-GSDXFACTS-NO-OVERDERIVE", f"derived {[o.identifier for o in neg_obs]}")

    # ---- refusals: an instrument error is never a silent drop -------------
    def refused(doc_or_bytes, label: str, gate: str) -> None:
        with tempfile.TemporaryDirectory(prefix="gsdx_facts_") as tmp:
            p = Path(tmp) / sf.FACTS_FILE
            if isinstance(doc_or_bytes, bytes):
                p.write_bytes(doc_or_bytes)
            else:
                p.write_text(json.dumps(doc_or_bytes), encoding="utf-8")
            try:
                got = sf.load(p)
            except sf.StructuredFactsError as exc:
                _ok(gate, f"{label} refused: {exc}")
                return
            _fail(gate, f"{label} was ACCEPTED as {[f.name for f in got]}")

    refused({"schema": sf.SCHEMA, "provenance": "x",
             "facts": [{"name": "no_recovery_mechansim", "evidence": "typo"}]},
            "unknown fact name", "V-GSDXFACTS-REFUSE-UNKNOWN-NAME")
    refused({"provenance": "x", "facts": []}, "missing schema", "V-GSDXFACTS-REFUSE-NO-SCHEMA")
    refused({"schema": sf.SCHEMA, "provenance": "x",
             "facts": [{"name": "unattended_operation", "evidence": ""}]},
            "fact without evidence", "V-GSDXFACTS-REFUSE-NO-EVIDENCE")
    refused({"schema": sf.SCHEMA, "provenance": "x",
             "facts": [{"name": "unattended_operation", "evidence": "a"},
                       {"name": "unattended_operation", "evidence": "b"}]},
            "duplicate fact", "V-GSDXFACTS-REFUSE-DUPLICATE")
    refused(b"{not json", "malformed JSON", "V-GSDXFACTS-REFUSE-MALFORMED")
    refused({"schema": sf.SCHEMA, "facts": []}, "missing provenance",
            "V-GSDXFACTS-REFUSE-NO-PROVENANCE")

    # BOM tolerance: PowerShell 5.1 and spreadsheet exports emit one, and a
    # parser that dies on it turns a real facts file into an instrument error.
    with tempfile.TemporaryDirectory(prefix="gsdx_facts_") as tmp:
        p = Path(tmp) / sf.FACTS_FILE
        p.write_bytes(b"\xef\xbb\xbf" + json.dumps(unseen_doc).encode("utf-8"))
        try:
            n = len(sf.load(p))
            _ok("V-GSDXFACTS-BOM-TOLERATED", f"UTF-8 BOM accepted, {n} facts")
        except Exception as exc:  # noqa: BLE001
            _fail("V-GSDXFACTS-BOM-TOLERATED", f"{exc.__class__.__name__}: {exc}")

    # ---- the CLI chooses the structured source when it is present ---------
    py = sys.executable
    cli = REPO / "tools" / "gsd_x_mission.py"
    with tempfile.TemporaryDirectory(prefix="gsdx_facts_cli_") as tmp:
        root = Path(tmp)
        (root / "INTENT.txt").write_text(unseen_intent, encoding="utf-8")
        (root / "README.md").write_text(unseen_reality, encoding="utf-8")
        (root / sf.FACTS_FILE).write_text(json.dumps(unseen_doc), encoding="utf-8")
        d = subprocess.run([py, str(cli), "derive", str(root)], capture_output=True,
                           text=True, encoding="utf-8")
        c = subprocess.run([py, str(cli), "check", str(root), "--exit-code", "--raw"],
                           capture_output=True, text=True, encoding="utf-8")
        payload = {}
        try:
            payload = json.loads(c.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            pass
        if "source   : structured" in d.stdout and c.returncode == 1 \
                and payload.get("open_obligations") == ["DO-1"]:
            _ok("V-GSDXFACTS-CLI-END-TO-END",
                "derive reports the structured source; check exits 1 naming DO-1")
        else:
            _fail("V-GSDXFACTS-CLI-END-TO-END",
                  f"derive_exit={d.returncode} check_exit={c.returncode} "
                  f"open={payload.get('open_obligations')} derive_out={d.stdout[-200:]!r} "
                  f"err={d.stderr[-200:]!r}")

    total = len(_passes) + len(_fails)
    print(f"\nGSDX_FACTS_PASS={len(_passes)}/{total}  threshold={total}/{total}")
    return 0 if not _fails else 1


if __name__ == "__main__":
    sys.exit(main())
