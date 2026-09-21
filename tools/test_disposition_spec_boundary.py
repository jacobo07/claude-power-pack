#!/usr/bin/env python3
"""UCR-CIF W6 -- the SECOND authoritative-disposition consumption boundary.

W5 proved the corpus can reach one decision: `check_novelty_gate`, which fires
only on mega-system vocabulary (fabric / kernel / operating system / compendium
or an enumerated dataset catalog). Ordinary L/XL engineering work never says
those words, so the ownership evidence never reached the decisions where
duplication actually originates.

This suite pins the second edge, at the SDD-OS L/XL spec boundary.

WHAT THE HANDOFF GOT WRONG, AND HOW IT WAS MEASURED
---------------------------------------------------
The handoff asserted `check_spec_gate` was already live because the hook log
showed `spec-injected ... 8979 B`. That log line is emitted when the JIT loader
injects the BODY of an existing spec file; `check_spec_gate` appears nowhere in
`tools/jit_skill_loader.py`. Two further premises fell on measurement:

  * the JIT's One-Shot injector calls `compile_contract(prompt[:300], "L")`
    with NO cwd, and `compile_contract` consults the gate only when a cwd is
    supplied -- so that path never reaches the gate at all;
  * `pp_agents/signals/sdd_tier.py` DOES reach it, with the full prompt and a
    real cwd, but read `gate_passed` and `action` and threw `message` away.

So enriching `SpecGateResult.message` alone would have been a reader, not a
consumer. The material effect therefore lands where it is actually rendered:
the ProactiveSignal that `sdd_tier` emits into additionalContext. The gate
stays the one place routing is COMPUTED (`routing`, machine-readable); the
signal reads that object, never another consumer's prose.

V-W6-* gates. Run from the repo root.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from modules.spec_gate import gate as G                       # noqa: E402
from modules.pp_agents.signals import sdd_tier                # noqa: E402
from modules.ucr_cif import disposition_consumer as DC        # noqa: E402

PASSES = 0
FAILS = 0


def check(name: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS
    if cond:
        PASSES += 1
        print(f"  OK   {name}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {name}  {evidence}")


# --- fixtures -----------------------------------------------------------
# ORDINARY: real feature work. Tier 2 via 'module'. Carries distinctive
# evidence terms of two real owners. Says nothing about fabrics or kernels --
# that is the whole point: this prompt cannot reach the first door.
ORDINARY = ("Add a scraper module that handles knowledge acquisition from "
            "vendor documentation during a long session, with governance over "
            "which sources count as institutional, and persist the "
            "acquisition results so later work can reuse them.")

# FOREIGN: same SHAPE, same tier trigger, genuine lexical overlap (session,
# sources, during, documentation, vendor, database) about a domain the corpus
# has never heard of. The negative is non-vacuous because units DO survive the
# applicability filter here; no owner reaches the per-owner floor.
FOREIGN = ("Add a booking module for the bicycle repair shop: during opening "
           "hours a customer picks a session slot, the shop records which "
           "sources sent them, persists the results to a database, and emails "
           "documentation of the appointment to the vendor who serviced it.")

# GENERIC: built ENTIRELY from this boundary's own trigger vocabulary. A term
# that is ubiquitous inside a boundary cannot discriminate inside it
# (T-THE-TRIGGER-VOCABULARY-CANNOT-DISCRIMINATE-001).
GENERIC = ("Implement a new feature for the project: a module with a clean "
           "architecture, an api endpoint, a database schema and a migration, "
           "plus monitoring and automation for the whole system, documented "
           "in a spec so the software implementation is maintainable.")

# The W5 fixture, used ONLY to prove the first door still works.
P_OWNED = ("I propose a new Universal Knowledge Acquisition Fabric: an "
           "institutional operating system for continuous acquisition of "
           "knowledge from every session, with harvesting, distillation, "
           "curation, retrieval and a knowledge graph, plus 12 new dataset "
           "families for governance overlays.")


def _owners(res) -> list[str]:
    r = getattr(res, "routing", None)
    return [o.owner for o in getattr(r, "owners", ()) or ()]


def _stat(res, attr, default=0):
    """Read a Selection field without crashing when there is no Selection.

    Under a severed-edge mutation `routing` is None, and a suite that raises
    an AttributeError there reports a VERIFIER failure where a subject failure
    belongs: the probe still sees a non-zero exit and calls the mutation
    caught, but the run stops at the first casualty and nobody can see how
    many gates the mutation actually moved. Measured: severing W18 crashed
    this file after two FAILs, so its own summary line never printed.
    """
    return getattr(getattr(res, "routing", None), attr, default)


def main() -> int:
    print("=== UCR-CIF W6 -- second consumption boundary (L/XL spec gate) ===")

    # --- 1. the boundary is where we say it is -------------------------
    jit = (REPO / "tools/jit_skill_loader.py").read_text(encoding="utf-8")
    sdd_src = (REPO / "modules/pp_agents/signals/sdd_tier.py").read_text(
        encoding="utf-8")
    disp_src = (REPO / "modules/pp_agents/proactive_dispatcher.py").read_text(
        encoding="utf-8")

    check("V-W6-LIVE-CHAIN",
          "proactive_dispatcher" in jit
          and "sdd_tier" in disp_src
          and "check_spec_gate" in sdd_src
          and "cwd=root" in sdd_src,
          "jit_skill_loader -> proactive_dispatcher -> sdd_tier -> "
          "check_spec_gate(prompt, cwd=root): the live UserPromptSubmit chain")

    # A tripwire, not a finding: the handoff believed the One-Shot injector was
    # the boundary. It is not, because it passes no cwd. If that ever changes
    # this goes red and the boundary must be re-measured rather than assumed.
    oneshot_line = [ln for ln in jit.splitlines()
                    if "compile_contract(" in ln and "import" not in ln]
    check("V-W6-ONESHOT-IS-NOT-THE-BOUNDARY",
          len(oneshot_line) == 1 and "cwd" not in oneshot_line[0],
          f"the JIT's only compile_contract call passes no cwd, so it never "
          f"reaches the gate: {oneshot_line[0].strip() if oneshot_line else '?'}")

    # --- 2. ordinary work cannot reach the FIRST door ------------------
    t_ord = G.classify_tier(ORDINARY)
    n_ord = G.check_novelty_gate(ORDINARY)
    check("V-W6-ORDINARY-IS-LXL-AND-NOT-NOVELTY",
          t_ord.tier >= 2 and t_ord.size in ("L", "XL") and not n_ord.applies,
          f"tier={t_ord.tier}/{t_ord.size} ({t_ord.reason}); novelty gate does "
          f"NOT fire -- this prompt could never reach the W5 consumer")

    # --- 3. POSITIVE POLE ----------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        pos = G.check_spec_gate(ORDINARY, cwd=Path(td), task_size=t_ord.size)
        pos_owners = _owners(pos)
        check("V-W6-POSITIVE-GATE",
              pos.action == "create_spec"
              and len(pos_owners) >= 1
              and all(o in pos.message for o in pos_owners)
              and pos.routing is not None and pos.routing.routed,
              f"action={pos.action}; {len(pos_owners)} owner(s) named in the "
              f"message and carried on .routing: {pos_owners}")

        # the LIVE surface, not the prose: does the signal change?
        sig = sdd_tier.evaluate(ORDINARY, cwd=td)
        check("V-W6-MATERIAL-EFFECT-ON-LIVE-SIGNAL",
              sig is not None
              and all(o in sig.advisory for o in pos_owners)
              and all(o in sig.actionable for o in pos_owners)
              and "INSPECT" in sig.actionable,
              "the ProactiveSignal that reaches additionalContext NAMES the "
              "owners and tells the agent to inspect them before the spec")

        # paired control: same prompt, same repo, routing switched off.
        os.environ["CLAUDEPP_UCR_ROUTING_DISABLE"] = "1"
        try:
            off_gate = G.check_spec_gate(ORDINARY, cwd=Path(td),
                                         task_size=t_ord.size)
            off_sig = sdd_tier.evaluate(ORDINARY, cwd=td)
        finally:
            os.environ.pop("CLAUDEPP_UCR_ROUTING_DISABLE", None)
        back = sdd_tier.evaluate(ORDINARY, cwd=td)
        check("V-W6-PAIRED-CONTROL",
              not _owners(off_gate)
              and off_sig is not None
              and not any(o in off_sig.advisory for o in pos_owners)
              and off_gate.action == "create_spec"
              and back is not None
              and all(o in back.advisory for o in pos_owners),
              "kill switch off -> no owner reaches the signal and the gate "
              "still answers; re-enabled -> the owners come back")

        # --- 4. NEGATIVE POLE, non-vacuous ------------------------------
        neg = G.check_spec_gate(FOREIGN, cwd=Path(td), task_size="L")
        neg_sig = sdd_tier.evaluate(FOREIGN, cwd=td)
        overlap = (_stat(neg, "applicable_units")
                   + _stat(neg, "rejected_generic"))
        check("V-W6-NEGATIVE-OVERLAP-NO-FALSE-ROUTING",
              overlap > 0 and not _owners(neg)
              and neg_sig is not None
              and "ALREADY OWNED" not in neg.message
              and "already owned" not in neg_sig.advisory,
              f"foreign domain, real overlap ({_stat(neg, 'applicable_units')} "
              f"applicable + {_stat(neg, 'rejected_generic')} generic-only) "
              f"and 0 owners routed; the signal keeps its baseline text")

        # --- 5. the boundary's own vocabulary cannot discriminate -------
        gen = G.check_spec_gate(GENERIC, cwd=Path(td), task_size="L")
        check("V-W6-GENERIC-VOCABULARY-ROUTES-NOTHING",
              _stat(gen, "rejected_generic") > 0 and not _owners(gen),
              f"a prompt built only from tier vocabulary (feature/module/api/"
              f"schema/system...) shares terms with "
              f"{_stat(gen, 'rejected_generic')} unit(s), none distinctive -> "
              f"0 owners")

        # --- 6. the non-applicable paths stay free ----------------------
        sm = G.check_spec_gate(ORDINARY, cwd=Path(td), task_size="M")
        check("V-W6-SM-PATH-UNTOUCHED",
              sm.action == "proceed" and sm.routing is None
              and "UCR-CIF" not in sm.message,
              "an S/M task returns before the corpus is consulted at all")

        blank = G.check_spec_gate("", cwd=Path(td), task_size="L")
        check("V-W6-BLANK-DESCRIPTION-NO-ROUTING",
              blank.routing is None,
              "modules/dataset_first/classifier probes this gate with '' to "
              "read .has_spec; a blank description is not a proposal and pays "
              "for no ledger read")

        # --- 7. an empty answer is not one state ------------------------
        real = DC.select_for
        seen = {}
        for kind, refusal in (
                ("UNREADABLE", "ledger unreadable: /nowhere/ledger.json"),
                ("SCHEMA", "ledger schema_version=100, this consumer speaks 1"),
                ("POPULATION", "authoritative population 3 below floor 200")):
            DC.select_for = (lambda _t, _r=None, _x=refusal:
                             DC.Selection(refusal=_x))
            try:
                r = G.check_spec_gate(ORDINARY, cwd=Path(td), task_size="L")
            finally:
                DC.select_for = real
            seen[kind] = r.message
        check("V-W6-FOUR-REFUSALS-STAY-DISTINCT",
              len(set(seen.values())) == 3
              and all("could not be consulted" in m for m in seen.values())
              and all("NOT evidence that nothing" in m for m in seen.values())
              and "could not be consulted" not in neg.message,
              "UNREADABLE / SCHEMA / POPULATION each produce a DIFFERENT "
              "message, each says it is a statement about the corpus, and "
              "none of them reads like the silent 'nothing applies' case")

        # --- 8. a routing failure never becomes a gate failure ----------
        def _boom(*_a, **_k):
            raise RuntimeError("corpus exploded")

        DC.select_for = _boom
        try:
            broken = G.check_spec_gate(ORDINARY, cwd=Path(td), task_size="L")
        finally:
            DC.select_for = real
        check("V-W6-FAILS-OPEN-SAFELY",
              broken.action == "create_spec" and broken.routing is None
              and "UCR-CIF" not in broken.message,
              "the selector raising leaves the spec verdict intact, with no "
              "invented owner and no claim that nothing is owned")

        # --- 9. context stays bounded -----------------------------------
        rows = DC.load_ledger()[1] or []       # (meta, rows), not (rows, ...)
        every = " ".join(sorted({str(t) for r in rows
                                 for t in (r.get("evidence_terms") or ())})
                         )[:4000]
        flood = G.check_spec_gate("Add a module for " + every,
                                  cwd=Path(td), task_size="L")
        check("V-W6-BOUNDED-MATERIALIZATION",
              len(_owners(flood)) <= DC.MAX_OWNERS
              and len(flood.message.encode("utf-8")) < 4000,
              f"a prompt containing every corpus term yields "
              f"{len(_owners(flood))} owners (cap {DC.MAX_OWNERS}) and a "
              f"{len(flood.message.encode('utf-8'))}-byte message")

        # --- 10. one selection, two consumer-correct renderings ---------
        nov = G.check_novelty_gate(P_OWNED)
        check("V-W6-LEAD-IS-CONSUMER-CORRECT",
              "novelty proof" not in pos.message
              and "Question 4" not in pos.message
              and "ALREADY OWNED" in pos.message
              and "Question 4" in nov.message,
              "the spec boundary does not cite 'question 4 of the novelty "
              "proof' (there is no such question here) while the novelty "
              "gate still does -- one renderer, two leads")

        check("V-W6-FIRST-DOOR-INDEPENDENT",
              nov.applies and getattr(nov.routing, "routed", False)
              and len(_stat(nov, "owners", ())) >= 1,
              f"the W5 novelty consumer still routes "
              f"{len(_stat(nov, 'owners', ()))} owner(s) with the second edge "
              f"live")

        # --- 11. provenance + determinism -------------------------------
        again = G.check_spec_gate(ORDINARY, cwd=Path(td), task_size="L")
        check("V-W6-REPEATABLE",
              again.message == pos.message,
              "same prompt + same corpus -> byte-identical obligation")

        check("V-W6-PROVENANCE",
              "vault/ucr_cif/disposition_ledger.json" in pos.message
              and "AUTHORITATIVE dispositions" in pos.message
              and (_stat(pos, "corpus_id", "") or "")[:12] in pos.message,
              f"the spec obligation names its ledger and corpus "
              f"{(_stat(pos, 'corpus_id', '') or '?')[:12]} and states the "
              f"population is authoritative")

        check("V-W6-NO-CORPUS-BODIES",
              not any(len(str(r.get("text") or "")) > 80
                      and str(r.get("text"))[:80] in pos.message
                      for r in rows[:400]),
              "no corpus unit body reaches the spec gate; owners, counts, "
              "terms and uids only")

        # --- 11a. the KNOWN GAP, pinned rather than described ----------
        # sdd_tier fires only when action == "create_spec". SPEC_GLOBS covers
        # vault/specs/*.md and vault/plans/*.md, so in a mature repo a spec is
        # almost always found, the action is read_spec, and the signal stays
        # silent -- while the gate has ALREADY routed the owners and carries
        # them on .routing. The second door is therefore widest in a fresh
        # project and narrowest at home, which is the opposite of where it was
        # built. That is the same reader-not-consumer shape this wave closed,
        # one condition further out, and it is the next wave's target.
        #
        # Asserted, not written in prose, for two reasons: a limitation nobody
        # executes is indistinguishable from one that was fixed, and the day
        # someone widens sdd_tier's trigger this gate must be changed on
        # purpose rather than silently outlived.
        here = G.check_spec_gate(ORDINARY, cwd=REPO, task_size="L")
        here_sig = sdd_tier.evaluate(ORDINARY, cwd=str(REPO))
        check("V-W6-KNOWN-GAP-SPEC-PRESENT-SIGNAL-SILENT",
              here.action == "read_spec"
              and len(_owners(here)) >= 1
              and all(o in here.message for o in _owners(here))
              and here_sig is None,
              f"in THIS repo a spec exists ({Path(here.spec_path or '?').name}) "
              f"so the gate routes {len(_owners(here))} owner(s) into its "
              f"message and .routing, and sdd_tier still returns None -- the "
              f"owners are computed and reach nobody. KNOWN, next wave")

        # --- 11b. the whole-hook topology ------------------------------
        # This claim spans BOTH boundaries, so it lives here, in the suite of
        # the newer one. It was briefly in the W5 suite and that was wrong:
        # severing the W6 edge then turned the W5 suite red, which is the
        # false shared fate that makes two call sites look like one
        # unverifiable aggregate. The W5 suite now asserts only its own leg.
        real_sel = DC.select_for
        seen = {"n": 0}

        def _counting(text, repo=None):
            seen["n"] += 1
            return real_sel(text, repo)

        DC.load_ledger()                    # the parse is once per process
        DC.select_for = _counting
        try:
            seen["n"] = 0
            G.check_novelty_gate(ORDINARY)
            n_novelty = seen["n"]
            sdd_tier.evaluate(ORDINARY, cwd=td)
            n_total = seen["n"]
        finally:
            DC.select_for = real_sel

        check("V-W6-HOOK-TOPOLOGY",
              n_novelty == 0 and n_total == 1,
              f"an ORDINARY prompt consults the corpus exactly once, through "
              f"the second door only (novelty={n_novelty}, spec="
              f"{n_total - n_novelty}) -- the first door does not fire here, "
              f"which is the whole reason this boundary exists")

        # --- 12. cost, paired and in-process ----------------------------
        def _median(fn, n=5):
            xs = []
            for _ in range(n):
                t0 = time.perf_counter()
                fn()
                xs.append((time.perf_counter() - t0) * 1000.0)
            return sorted(xs)[len(xs) // 2]

        warm_app = _median(lambda: G.check_spec_gate(
            ORDINARY, cwd=Path(td), task_size="L"))
        warm_non = _median(lambda: G.check_spec_gate(
            ORDINARY, cwd=Path(td), task_size="M"))
        warm_miss = _median(lambda: G.check_spec_gate(
            FOREIGN, cwd=Path(td), task_size="L"))
        print(f"\n  [cost] warm applicable L   {warm_app:8.2f} ms")
        print(f"  [cost] warm no-match L     {warm_miss:8.2f} ms")
        print(f"  [cost] non-applicable S/M  {warm_non:8.2f} ms")
        sig_on = _median(lambda: sdd_tier.evaluate(ORDINARY, cwd=td))
        os.environ["CLAUDEPP_UCR_ROUTING_DISABLE"] = "1"
        try:
            sig_off = _median(lambda: sdd_tier.evaluate(ORDINARY, cwd=td))
        finally:
            os.environ.pop("CLAUDEPP_UCR_ROUTING_DISABLE", None)
        check("V-W6-MARGINAL-COST-BOUNDED",
              (sig_on - sig_off) < 250,
              f"the second door adds {sig_on - sig_off:+.1f} ms to the live "
              f"consumer ({sig_on:.1f} on vs {sig_off:.1f} off, paired, same "
              f"process, warm cache) -- a hook-subprocess clock on this host "
              f"swings by seconds and cannot resolve this")
        check("V-W6-SM-IS-ORDERS-CHEAPER",
              warm_non < warm_app,
              f"the path most prompts take is cheaper than the routed one "
              f"({warm_non:.2f} ms vs {warm_app:.2f} ms, paired, same "
              f"process, same host state)")

    total = PASSES + FAILS
    print(f"\nW6_SPEC_BOUNDARY_PASS={PASSES}/{total}  threshold={total}/{total}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
