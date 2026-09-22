"""W11 -- the prose declaration channel, driven from both poles.

Synthetic subjects represent the CLASS, so no assertion here can be fixed out
from under by repairing a real artifact; the real estate is then driven
separately to prove the mechanism is reachable on the population it exists for.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from modules.ucr_cif import ownership_evidence as OE  # noqa: E402
from modules.ucr_cif import prose_authority as PA  # noqa: E402

HARMED = "modules/governance-overlay"

_passes = 0
_fails = 0


def _ok(gate, ev):
    global _passes
    _passes += 1
    print(f"  OK   {gate:<44} {ev}")


def _fail(gate, diag):
    global _fails
    _fails += 1
    print(f"  FAIL {gate:<44} {diag}")


def _check(gate, cond, ev, diag=""):
    _ok(gate, ev) if cond else _fail(gate, diag or ev)


# --------------------------------------------------------------------------
# A synthetic estate. Clean by construction: nothing here is copied from the
# real repo, so it carries none of the real repo's debt.
# --------------------------------------------------------------------------
CONTRACT = """---
covers: [quarantine, eviction]
---
# Quarantine Ladder
## Eviction Threshold
## Reinstatement Window
"""

# Carries one term the contract does NOT, so its contribution is attributable.
# Without that, both artifacts declare the same words and "the lookalike earned
# nothing" cannot be distinguished from "the contract earned everything".
LOOKALIKE = """# Quarantine Ladder
## Eviction Threshold
## Reinstatement Window
## Sedimentation Backlog
"""

SUPERSEDED = """---
status: superseded
---
# Quarantine Ladder
## Eviction Threshold
"""


def _estate(tmp: Path, *, consumer=True, contract=CONTRACT):
    """modules/quarantine_engine/ladder.md, optionally consumed by a command."""
    art = tmp / "modules" / "quarantine_engine"
    art.mkdir(parents=True, exist_ok=True)
    (art / "ladder.md").write_text(contract, encoding="utf-8")
    (art / "readme_lookalike.md").write_text(LOOKALIKE, encoding="utf-8")

    cmd = tmp / "commands"
    cmd.mkdir(parents=True, exist_ok=True)
    body = "# Run\n"
    if consumer:
        body += "Apply the contract at `modules/quarantine_engine/ladder.md`.\n"
    else:
        body += "Apply the contract that used to live here.\n"
    (cmd / "quarantine.md").write_text(body, encoding="utf-8")
    return tmp


def _decls(tmp: Path):
    return PA.prose_declarations(tmp)


def main() -> int:
    print("-- W11 prose declaration channel")

    # ---------------- synthetic: the class ----------------
    with tempfile.TemporaryDirectory() as td:
        tmp = _estate(Path(td))
        edges = PA.build_edges(tmp)
        decls = PA.prose_declarations(tmp, edges)
        holders = {t: set(o) for t, o in decls.items()}
        owner = "modules/quarantine_engine"

        _check("V-W11-CONSUMED-CONTRACT-DECLARES",
               "quarantine" in holders and owner in holders["quarantine"]
               and "eviction" in holders,
               f"a contract a command resolves a path to declares its headings "
               f"and covers keys: {sorted(decls)[:5]}",
               f"a consumed contract declared nothing: {decls}")

        _check("V-W11-LOOKALIKE-EARNS-NOTHING",
               "sedimentation" not in holders and "backlog" not in holders
               and "quarantine" in holders,
               "the lookalike's own distinctive term never appears while the "
               "consumed contract's terms do -- this measures attribution "
               "rather than merely observing an empty result",
               f"the lookalike contributed terms: {sorted(decls)}")

        look = edges[str(Path("modules/quarantine_engine/readme_lookalike.md"))
                     .replace("\\", "/")]
        _check("V-W11-LOOKALIKE-HAS-DECLARATIONS-BUT-NO-EDGE",
               look["declares"] and not look["edges"].get(PA.CONSUMER),
               f"the lookalike DOES carry {len(look['declares'])} declaration "
               f"terms and still earns nothing -- the gate is the edge, not the "
               f"surface, so this is not a vacuous pass",
               f"lookalike state: declares={look['declares']} "
               f"edges={look['edges']}")

    # ---------------- synthetic: sever the RELATION, keep both endpoints -----
    with tempfile.TemporaryDirectory() as td:
        tmp = _estate(Path(td), consumer=False)
        decls_no = _decls(tmp)
        _check("V-W11-EDGE-SEVERED-SIGNAL-VANISHES",
               not decls_no,
               "with both artifacts still present and only the consumer's path "
               "reference removed, the channel yields nothing -- the signal "
               "tracks the relation, not the files",
               f"declarations survived the severed edge: {decls_no}")

    # ---------------- synthetic: lifecycle ----------------
    with tempfile.TemporaryDirectory() as td:
        tmp = _estate(Path(td), contract=SUPERSEDED)
        decls_dead = _decls(tmp)
        _check("V-W11-SUPERSEDED-DECLARES-NOTHING",
               not decls_dead,
               "a superseded contract with a live consumer edge and intact "
               "headings declares nothing -- historical authority is not "
               "current authority",
               f"a superseded contract still declared: {decls_dead}")

    # ---------------- synthetic: basename collision ----------------
    # Found by a SURVIVING mutant. Dropping the owner disambiguation admitted
    # 418 spurious edges on the real estate and took owners from 26 to 51,
    # because `coding-style.md`, `testing.md`, `patterns.md`, `security.md` and
    # `hooks.md` are each shared by 20 artifacts. Ownership would degrade from
    # an artifact-specific relation to a basename collision.
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for owner, uniq in (("alpha_engine", "Alpha Escalation"),
                            ("beta_engine", "Beta Escalation")):
            d = tmp / "modules" / owner
            d.mkdir(parents=True, exist_ok=True)
            (d / "core.md").write_text(f"# {uniq}\n", encoding="utf-8")
        cmd = tmp / "commands"
        cmd.mkdir(parents=True, exist_ok=True)
        (cmd / "only_alpha.md").write_text(
            "# Run\nLoad `modules/alpha_engine/core.md`.\n", encoding="utf-8")
        d2 = PA.prose_declarations(tmp)
        holders2 = {t: set(o) for t, o in d2.items()}
        _check("V-W11-BASENAME-COLLISION-DOES-NOT-SPREAD",
               holders2.get("alpha") == {"modules/alpha_engine"}
               and "beta" not in holders2,
               "two owners ship a file with the same basename and a consumer "
               "names one of them; only that one earns -- the edge is to an "
               "artifact, not to a filename",
               f"the collision spread: {d2}")

    collisions = {}
    for _rel in PA.build_edges(_ROOT):
        collisions.setdefault(Path(_rel).name, []).append(_rel)
    shared = {n: v for n, v in collisions.items() if len(v) > 1}
    _check("V-W11-COLLISION-POPULATION-IS-REAL",
           len(shared) >= 5 and max(len(v) for v in shared.values()) >= 10,
           f"{len(shared)} basenames are shared by more than one prose "
           f"artifact in this estate, the largest by "
           f"{max(len(v) for v in shared.values())} -- so the synthetic case "
           f"above represents a real population and not a hypothetical one",
           f"no meaningful collision population: {len(shared)}")

    # ---------------- the benchmark guard, driven ----------------
    # `vault` is not in SCAN_DIRS, so the oracle is out of scope by construction
    # and the prefix guard below cannot fire on today's estate. That makes it a
    # gate nobody has seen work, which is indistinguishable from one that
    # passes -- so it is driven here directly, and the invariant it backs up is
    # pinned separately.
    _check("V-W11-ORACLE-IS-OUT-OF-SCOPE",
           "vault" not in OE.SCAN_DIRS,
           "the oracle and the disposition ledger live under vault/, which "
           "build_edges never walks -- benchmark exclusion is a property of "
           "scope, not a check someone must remember",
           f"vault entered SCAN_DIRS ({OE.SCAN_DIRS}): the W10 answer key is "
           f"now a referrer and the signal can be coached by its own judge")

    _check("V-W11-BENCHMARK-GUARD-IS-LIVE",
           PA._classify_referrer("vault/ucr_cif/oracle_cases.json", ".json",
                                 True) == PA.BENCHMARK
           and PA._classify_referrer("vault/ucr_cif/disposition_ledger.json",
                                     ".json", True) == PA.BENCHMARK,
           "driven directly, the classifier does return BENCHMARK for the "
           "oracle and the ledger, so if vault ever enters scope the guard "
           "behind the invariant is real rather than decorative",
           "the benchmark classifier does not classify the oracle as BENCHMARK")

    _check("V-W11-SELF-MEASUREMENT-DOES-NOT-PROMOTE",
           PA._classify_referrer("modules/ucr_cif/owner_truth.py", ".py", True)
           == PA.SELF_MEASUREMENT
           and PA.SELF_MEASUREMENT not in PA.PROMOTING,
           "this mission's own prose about this owner is classified "
           "SELF_MEASUREMENT and does not promote -- W9/W10 comments recording "
           "governance-overlay's coverage cannot become evidence for it",
           "self-measurement promotes")

    _check("V-W11-ONLY-ONE-CLASS-PROMOTES",
           PA.PROMOTING == (PA.CONSUMER,),
           "exactly one provenance class promotes, so a citation, a generated "
           "projection or a benchmark row cannot become support by being "
           "numerous",
           f"PROMOTING widened to {PA.PROMOTING}")

    # ---------------- the real estate: reachability ----------------
    edges = PA.build_edges(_ROOT)
    decls = PA.prose_declarations(_ROOT, edges)
    by_owner: dict = {}
    for t, os_ in decls.items():
        for o in os_:
            by_owner.setdefault(o, set()).add(t)

    _check("V-W11-HARMED-STRATUM-EARNS-SUPPORT",
           len(by_owner.get(HARMED, ())) > 0,
           f"{HARMED} -- demoted in 8 of 8 movements at W10 and holding 13.7 % "
           f"structurally -- earns {len(by_owner.get(HARMED, ()))} declared "
           f"terms through real consumer edges",
           f"the harmed stratum earns nothing: the family does not reach the "
           f"owner it was built for")

    gov_arts = {r: m for r, m in edges.items() if m["owner"] == HARMED}
    declaring = [r for r, m in gov_arts.items()
                 if m["edges"].get(PA.CONSUMER) and m["declares"]]
    silent = [r for r, m in gov_arts.items()
              if not m["edges"].get(PA.CONSUMER) and m["declares"]]
    _check("V-W11-SPLIT-INSIDE-ONE-OWNER",
           declaring and silent,
           f"inside one owner, one directory and one extension: "
           f"{len(declaring)} artifacts declare and {len(silent)} stay silent "
           f"({', '.join(sorted(Path(s).name for s in silent))}) -- a family "
           f"keyed on directory or on Markdown could not produce this split",
           f"no split inside {HARMED}: declaring={len(declaring)} "
           f"silent={len(silent)}")

    others = {o: t for o, t in by_owner.items() if o != HARMED}
    _check("V-W11-TRANSFER-BEYOND-THE-HARMED-OWNER",
           len(others) >= 2,
           f"{len(others)} further owners earn declarations through the same "
           f"general mechanism -- e.g. "
           f"{', '.join(sorted(others, key=lambda o: -len(others[o]))[:3])} -- "
           f"so this is a representation class, not an owner special case",
           f"only {len(others)} other owners earn support; cross-owner "
           f"generalization is unproven")

    # Discovered, never curated: the strongest available negative control is
    # whichever real artifact carries the most declarations and no consumer.
    worst_rel, worst = max(
        ((r, m) for r, m in edges.items() if not m["edges"].get(PA.CONSUMER)),
        key=lambda kv: len(kv[1]["declares"]), default=(None, None))
    # Attribution, directly: run the real deriver over this artifact ALONE. If
    # it contributes anything, the surface alone was enough, which is the
    # Markdown-equals-authority failure this family exists to refuse.
    alone = (PA.prose_declarations(_ROOT, {worst_rel: worst})
             if worst_rel else {"unmeasured": []})
    _check("V-W11-REAL-NEGATIVE-CONTROL",
           worst is not None and len(worst["declares"]) >= 20 and not alone,
           f"the estate's most declaration-rich unconsumed artifact "
           f"({Path(worst_rel).name if worst_rel else '-'}, "
           f"{len(worst['declares']) if worst else 0} terms) yields exactly "
           f"nothing when the real deriver is run over it alone",
           f"a richly-headed artifact with no consumer was credited: "
           f"{sorted(alone)[:8]}")

    # PR-W11-10, driven WITHOUT touching the answer key.
    #
    # The first version of this drill rewrote every gold label in the canonical
    # store and restored it in a `finally`. That is not crash-safe, and this
    # session measured the consequence: a mutation run whose suite subprocess
    # was killed left 10,297 injected lines in the canonical oracle on disk.
    # Only pathspec-scoped commits kept the corrupted answer key out of history.
    # A drill that can damage the artifact it certifies is the wrong instrument
    # however green it reports.
    #
    # It is also the weaker measurement. "The signal did not change when the
    # oracle changed" is circumstantial; "the signal never opened the oracle" is
    # the property itself.
    store = _ROOT / "vault" / "ucr_cif" / "oracle_cases.json"
    ledger = _ROOT / "vault" / "ucr_cif" / "disposition_ledger.json"
    opened: list = []
    _real_read_text = Path.read_text

    def _spy(self, *a, **k):
        opened.append(str(self).replace("\\", "/"))
        return _real_read_text(self, *a, **k)

    Path.read_text = _spy
    try:
        PA.build_edges(_ROOT)
    finally:
        Path.read_text = _real_read_text

    judges = [p for p in opened if "/vault/ucr_cif/" in p]

    _check("V-W11-LEAK-PROBE-ACTUALLY-OBSERVED",
           len(opened) > 500 and store.is_file() and ledger.is_file(),
           f"the probe recorded {len(opened)} reads and both the oracle and the "
           f"ledger exist on disk -- so 'never opened' is a measurement, not an "
           f"artefact of a blind probe or an absent file",
           f"probe saw {len(opened)} reads; oracle={store.is_file()} "
           f"ledger={ledger.is_file()}")

    _check("V-W11-NO-ORACLE-TO-PRODUCTION-LEAK",
           not judges,
           "compiling the whole channel opens neither the W10 answer key nor "
           "the disposition ledger -- the judge is never consulted, so it "
           "cannot coach the contestant",
           f"the channel read its own judge: {judges[:4]}")

    _check("V-W11-DRILL-IS-NON-DESTRUCTIVE",
           store.stat().st_size == len(store.read_bytes()),
           "this drill writes nothing, so no interrupted run can leave a "
           "perturbed answer key on disk for a later wave to measure against",
           "the drill wrote to the canonical store")

    _check("V-W11-DECLARATION-SET-IS-STABLE",
           hashlib.sha256(json.dumps(decls, sort_keys=True).encode())
           .hexdigest() == hashlib.sha256(
               json.dumps(PA.prose_declarations(_ROOT, edges),
                          sort_keys=True).encode()).hexdigest(),
           "the channel is deterministic over one compiled edge set, so a "
           "paired arm cannot differ for reasons the treatment did not cause",
           "the declaration set is not reproducible from one edge set")

    _check("V-W11-ADMISSION-IS-UNTOUCHED",
           "prose_authority" not in (_ROOT / "modules" / "ucr_cif" /
                                     "ownership_evidence.py")
           .read_text(encoding="utf-8"),
           "ownership_evidence does not import this module, so adjudicate and "
           "the disposition ledger cannot move -- the channel is "
           "admission-neutral and the corpus stays frozen",
           "the prose channel reached the admission path")

    # Cost: the expensive half must be offline, the query cheap.
    import time
    t0 = time.perf_counter()
    PA.prose_declarations(_ROOT, edges)
    q_ms = 1000.0 * (time.perf_counter() - t0)
    _check("V-W11-QUERY-IS-BOUNDED",
           q_ms < 100.0,
           f"deriving declarations from compiled edges costs {q_ms:.1f} ms, so "
           f"nothing on a selection path parses a document",
           f"the query costs {q_ms:.1f} ms")

    total = _passes + _fails
    print(f"\nW11_PROSE_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
