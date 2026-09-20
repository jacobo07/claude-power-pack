#!/usr/bin/env python3
"""V-gates for CONSUMPTION of the authoritative disposition corpus.

Selection is proven next door (test_disposition_selection.py). Reading is not
consuming, so these gates ask the only question that closes W5:

    does a downstream DECISION change because an authoritative disposition
    exists, and does it change back when the disposition does not?

The consumer is modules/spec_gate/gate.py::check_novelty_gate, reached live
from tools/jit_skill_loader.py on UserPromptSubmit. Its output IS an
obligation: thirteen questions the agent must answer before a new
institutional system may be admitted. Question 4 -- "Why is extending an
existing owner insufficient?" -- is exactly what 996 adjudicated dispositions
already answer, and for six consecutive audits it was answered by hand.

TWO ALTITUDES, AND THE SECOND IS THE ONE THAT COUNTS
----------------------------------------------------
V-W5-CON-*  in-process, against the real corpus.
V-W5-PR-*   PRODUCTION REALITY: the real hook script, in a subprocess, fed the
            payload the harness feeds it, read back through its stdout.

The production half runs under an ISOLATED HOME whose
.claude/skills/claude-power-pack is a junction to this worktree, because the
hook resolves `modules` from the INSTALLED tree by construction
(PP_ROOT = ~/.claude/skills/claude-power-pack). Without that junction this
file would measure the deployed copy and report a green about code that is
not the code under test -- the same SOURCE != LOADED != EFFECTIVE gap that is
still open for FIOS. If the junction cannot be made, these gates report
HARNESS-FAILED and exit 2. A drill that could not run is not a drill that
passed.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from modules.spec_gate import gate as G                      # noqa: E402

PASSES = 0
FAILS = 0
PR_PASSES = 0
PR_TOTAL = 0

P_OWNED = ("I propose a new Universal Knowledge Acquisition Fabric: an "
           "institutional operating system for continuous acquisition of "
           "knowledge from every session, with harvesting, distillation, "
           "curation, retrieval and a knowledge graph, plus 12 new dataset "
           "families for governance overlays.")
P_FOREIGN = ("I propose a new institutional operating system for espresso: a "
             "kernel that tracks bean freshness, grind size and portafilter "
             "temperature in the kitchen.")
P_NOSIGNAL = "Fix the typo in the README heading."

#: The one string that exists only where this wave's routing exists.
MARKER = "UCR-CIF holds ADJUDICATED evidence"


def check(gate: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS, PR_PASSES, PR_TOTAL
    if gate.startswith("V-W5-PR-"):
        PR_TOTAL += 1
        if cond:
            PR_PASSES += 1
    if cond:
        PASSES += 1
        print(f"  OK   {gate}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {gate}  {evidence}")


# ---------------------------------------------------------- consumer half --
def consumer_gates() -> None:
    base = G.NOVELTY_PROOF_QUESTIONS
    owned = G.check_novelty_gate(P_OWNED)
    foreign = G.check_novelty_gate(P_FOREIGN)
    quiet = G.check_novelty_gate(P_NOSIGNAL)

    named = tuple(q for q in owned.questions if q not in base)

    # POSITIVE POLE -- the obligation itself changed, not a log line. The
    # COUNT is unchanged on purpose: it is part of this gate's published
    # contract ("answer all 13 questions"), and a first version that appended
    # the owners made the verdict contradict its own instruction while a
    # pre-existing gate pinned 13. Substitution in place is the stronger
    # change anyway: the one question the corpus can answer stops being
    # generic.
    check("V-W5-CON-OBLIGATION-CHANGES",
          owned.applies and len(named) == 1
          and len(owned.questions) == len(base)
          and owned.questions.index(named[0]) == base.index(
              G._OWNERSHIP_QUESTION)
          and named[0].count("modules/") >= 2,
          f"question {base.index(G._OWNERSHIP_QUESTION) + 1} of {len(base)} "
          f"replaced in place, naming {named[0].count('modules/')} owners")

    # The substitution is a REPLACEMENT, so the generic question cannot sit
    # beside its own answer.
    check("V-W5-CON-GENERIC-QUESTION-REPLACED",
          G._OWNERSHIP_QUESTION in base
          and G._OWNERSHIP_QUESTION not in owned.questions
          and G._OWNERSHIP_QUESTION in foreign.questions,
          "generic ownership question: absent when owners are named, "
          "present when they are not")

    # NEGATIVE POLE -- same trigger, nothing applicable, no routing.
    check("V-W5-CON-NOT-APPLICABLE",
          foreign.applies and tuple(foreign.questions) == base
          and foreign.routing is not None and not foreign.routing.owners,
          "foreign proposal: corpus consulted, 0 owners, obligation unchanged")

    # CONSULTED-AND-EMPTY is not NOT-CONSULTED. Collapsing these would make a
    # silently broken join indistinguishable from an honest no.
    check("V-W5-CON-NOT-CONSULTED-IS-DISTINCT",
          quiet.applies is False and quiet.routing is None
          and foreign.routing is not None,
          "no novelty signal -> routing=None (store never opened); "
          "signal with no match -> routing present with 0 owners")

    # TYPE PRESERVATION -- an advisory gate stays advisory. Turning every
    # disposition into a hard block is the failure mode on the other side.
    check("V-W5-CON-STILL-ADVISORY",
          "answer all 13 questions" in owned.message
          and not hasattr(owned, "blocked") and owned.applies is True,
          "routed verdict still carries the advisory proof request; no "
          "blocking field was introduced")

    # The verdict's own prose counts its own obligations. This gate is why the
    # substitution is in place rather than appended: the message hardcodes the
    # number, so any change to the tuple's length silently makes the gate lie
    # about what it is asking for.
    stated = re.search(r"answer all (\d+) questions", owned.message)
    check("V-W5-CON-COUNT-MATCHES-ITS-OWN-CLAIM",
          stated is not None
          and int(stated.group(1)) == len(owned.questions) == len(base),
          f"message says {stated.group(1) if stated else '?'} questions and "
          f"the verdict carries {len(owned.questions)}")

    # PROVENANCE -- a downstream obligation traces back to corpus units.
    sel = owned.routing
    uid0 = sel.owners[0].uids[0]
    check("V-W5-CON-PROVENANCE",
          "vault/ucr_cif/disposition_ledger.json" in owned.message
          and (sel.corpus_id or "")[:12] in owned.message
          and uid0 in owned.message
          and json.loads(json.dumps(sel.to_dict()))["population"] == 996,
          f"ledger + corpus {sel.corpus_id[:12]} + uid {uid0} in the "
          "obligation; selection round-trips as JSON")

    # A kill switch must be legible as a kill switch, never as "nothing owned".
    os.environ["CLAUDEPP_UCR_ROUTING_DISABLE"] = "1"
    try:
        off = G.check_novelty_gate(P_OWNED)
    finally:
        os.environ.pop("CLAUDEPP_UCR_ROUTING_DISABLE", None)
    back = G.check_novelty_gate(P_OWNED)
    check("V-W5-CON-KILLSWITCH",
          off.routing is None and tuple(off.questions) == base
          and tuple(back.questions) == tuple(owned.questions),
          "disabled -> no routing and the generic obligation; re-enabled -> "
          "the named obligation returns")

    # FAIL-OPEN, in the safe direction: a broken corpus falls back to asking
    # for the sweep. It never invents an owner and never reports its own
    # failure as evidence that nothing is owned.
    real = G._ucr_routing

    def _boom(_):
        raise RuntimeError("corpus exploded")
    G._ucr_routing = _boom
    try:
        broken = G.check_novelty_gate(P_OWNED)
    finally:
        G._ucr_routing = real
    check("V-W5-CON-FAILS-OPEN-SAFELY",
          broken.applies and tuple(broken.questions) == base
          and "answer all 13 questions" in broken.message,
          "consumer raises -> baseline obligation, no crash, no invented owner")

    # UNKNOWN SAFETY (PR-W5-9). The consumer may never turn institutional
    # state into certainty it does not have. It asks a question; it never
    # asserts that anything is satisfied, verified or complete.
    ratchet = json.loads(
        (REPO / "vault/capability_runtime/lifecycle_ratchet.json").read_text(
            encoding="utf-8-sig"))
    # Word boundaries, not substrings: the first version matched "proven"
    # inside "Provenance" -- in a line this file added -- and reported the
    # obligation as asserting a certainty it does not claim. A detector whose
    # vocabulary matches its own output is measuring itself.
    forbidden = ("already satisfied", "verified", "is complete", "no longer",
                 "proven", "retired")
    blob = owned.message.lower()
    hit = [f for f in forbidden
           if re.search(r"\b" + re.escape(f) + r"\b", blob)]
    check("V-W5-CON-UNKNOWN-SAFETY",
          "spec_depth_selection" in ratchet.get("unknown", [])
          and not hit
          and all(q.strip().endswith("?") for q in owned.questions),
          "spec_depth_selection still UNKNOWN in the ratchet; every "
          "obligation is a question and asserts no satisfaction")

    # REPEATABILITY (PR-W5-10).
    twice = G.check_novelty_gate(P_OWNED)
    check("V-W5-CON-REPEATABLE",
          twice.message == owned.message
          and tuple(twice.questions) == tuple(owned.questions),
          "same proposal + same corpus -> identical obligation")


# ------------------------------------------------- production reality half --
def _isolated_home(tmp: Path):
    """A HOME whose .claude/skills/claude-power-pack IS this worktree.

    The hook computes PP_ROOT from HOME, so this is the only way to drive the
    REAL script against the code under test instead of the installed copy.
    """
    home = tmp / "home"
    (home / ".claude" / "skills").mkdir(parents=True, exist_ok=True)
    link = home / ".claude" / "skills" / "claude-power-pack"
    if os.name == "nt":
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(REPO)],
                           capture_output=True, text=True)
        ok = r.returncode == 0
    else:
        try:
            link.symlink_to(REPO, target_is_directory=True)
            ok = True
        except OSError:
            ok = False
    return (home, link) if ok and link.exists() else (None, None)


def _run_hook(home: Path, prompt: str, sid: str, disable=False, cwd=None):
    env = dict(os.environ)
    env["USERPROFILE"] = str(home)
    env["HOME"] = str(home)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("CLAUDEPP_UCR_ROUTING_DISABLE", None)
    if disable:
        env["CLAUDEPP_UCR_ROUTING_DISABLE"] = "1"
    payload = json.dumps({"hook_event_name": "UserPromptSubmit",
                          "session_id": sid, "cwd": str(cwd or REPO),
                          "prompt": prompt})
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, "-B",
                        str(REPO / "tools" / "jit_skill_loader.py")],
                       input=payload, capture_output=True, text=True,
                       env=env, timeout=180)
    dt = (time.perf_counter() - t0) * 1000
    try:
        out = json.loads(r.stdout or "{}")
    except ValueError:
        out = {"_unparsed": r.stdout[:400]}
    return out, dt, r


def production_reality(home: Path) -> None:
    tag = f"w5pr{int(time.time())}"

    owned, dt_owned, r1 = _run_hook(home, P_OWNED, tag + "a")
    ac = owned.get("additionalContext") or ""
    check("V-W5-PR-HOOK-ANSWERS",
          isinstance(owned, dict) and owned.get("continue") is not False
          and "_unparsed" not in owned,
          f"real hook returned parseable JSON in {dt_owned:.0f} ms "
          f"(rc={r1.returncode}, {len(ac)} bytes of context)")

    # PR-W5-1 / PR-W5-12: the obligation reached the surface the next
    # execution phase actually reads. Asserted on the strings the LIVE path
    # emits: the hook injects the verdict's message, not its questions tuple,
    # so a gate asserting on the tuple's wording measured something the
    # surface never carries. (It did, at first, and went red while the
    # obligation was sitting in the output.)
    routed_lines = [ln for ln in ac.splitlines()
                    if ln.strip().startswith("- modules/")
                    and "Why is extending it insufficient?" in ln]
    check("V-W5-PR-LIVE-OBLIGATION",
          "[novelty-gate]" in ac
          and MARKER in ac and len(routed_lines) >= 2,
          f"{len(routed_lines)} named owner obligation(s) in the live "
          "additionalContext, under the novelty card")

    # An INDEPENDENT control that the junction worked. The first version
    # asserted a string this file's own obligation contains, so it could only
    # confirm what the gate above already said. This one is two-sided: the
    # marker must be present in the output AND provably absent from the
    # installed tree, so its presence is attributable to this worktree.
    installed = Path(os.path.expanduser("~")) / ".claude/skills/claude-power-pack"
    inst_src = installed / "modules/ucr_cif/disposition_consumer.py"
    inst_has = inst_src.exists() and MARKER in inst_src.read_text(
        encoding="utf-8-sig", errors="replace")
    check("V-W5-PR-TREE-UNDER-TEST",
          MARKER in ac and not inst_has,
          f"marker present in the hook's output and absent from the "
          f"installed tree ({'file exists' if inst_src.exists() else 'no such file'})")

    # PR-W5-3 / the negative pole, through the same live path.
    foreign, dt_foreign, _ = _run_hook(home, P_FOREIGN, tag + "b")
    acf = foreign.get("additionalContext") or ""
    check("V-W5-PR-LIVE-NEGATIVE",
          "[novelty-gate]" in acf and MARKER not in acf,
          f"foreign proposal: novelty card fires, 0 owner routing "
          f"({dt_foreign:.0f} ms)")

    # PR-W5-11: the injection is once per session. A resumed or repeated
    # prompt must not bill the mission twice for one obligation.
    again, _, _ = _run_hook(home, P_OWNED, tag + "a")
    aca = again.get("additionalContext") or ""
    check("V-W5-PR-NO-DUPLICATE-OBLIGATION",
          aca.count(MARKER) == 0 and ac.count(MARKER) == 1,
          "second prompt in the same session re-injects nothing")

    # Hook latency: this wave adds synchronous work to UserPromptSubmit, so
    # the cost is a done-gate for this path. Measured as a PAIRED delta
    # against the same hook with the routing disabled -- a host at 6% free
    # memory cannot give an absolute number worth reporting, but both arms
    # pay the same contention.
    on, off = [], []
    for i in range(3):
        _, a, _ = _run_hook(home, P_OWNED, f"{tag}on{i}")
        _, b, _ = _run_hook(home, P_OWNED, f"{tag}off{i}", disable=True)
        on.append(a)
        off.append(b)
    delta = statistics.median(on) - statistics.median(off)
    check("V-W5-PR-LATENCY-BOUNDED",
          delta < 400,
          f"median {statistics.median(on):.0f} ms with routing vs "
          f"{statistics.median(off):.0f} ms without: delta {delta:+.0f} ms "
          "(paired, same host state)")


def main() -> int:
    print("--- consumer ---")
    consumer_gates()
    print("--- production reality ---")
    tmp = Path(tempfile.mkdtemp(prefix="w5pr-"))
    try:
        home, link = _isolated_home(tmp)
        if home is None:
            print("  HARNESS-FAILED  could not create the junction that points "
                  "an isolated HOME at this worktree; the production-reality "
                  "gates measure nothing and are NOT reported as passing.")
            return 2
        production_reality(home)
    finally:
        # The junction points AT this worktree, so the cleanup is a recursive
        # delete aimed at the repository. Observed safe across every run --
        # rmtree unlinks a reparse point rather than descending through it --
        # but "it did not delete the repo the last four times" is not a
        # guarantee anyone should rely on. Drop the link first, then REFUSE to
        # recurse while it is still there.
        try:
            if link is not None and link.exists():
                os.rmdir(link)
        except OSError:
            pass
        if link is not None and link.exists():
            print(f"  NOTE  left {tmp} in place: the junction at {link} could "
                  "not be removed, and a recursive delete through it could "
                  "reach the repository.")
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    total = PASSES + FAILS
    print(f"\nDISPOSITION_CONSUMPTION_PASS={PASSES}/{total}  "
          f"threshold={total}/{total}")
    print(f"PRODUCTION_REALITY_PASS={PR_PASSES}/{PR_TOTAL}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
