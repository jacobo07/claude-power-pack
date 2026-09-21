"""V-W7-* -- gates for the activation reach calibration instrument.

W7's product is a MEASUREMENT, so the thing that has to be proven correct
is the instrument. Every gate here drives both poles: a green that nobody
has seen fail could have every clause removed and read the same.

Run:  python tools/test_ucr_cif_reach.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.ucr_cif import reach_calibration as rc  # noqa: E402
from modules.ucr_cif import reach_ground_truth as gt  # noqa: E402
from modules.ucr_cif.prompt_population import (  # noqa: E402
    DerivedCase, _user_text, semantic_class)
from modules.ucr_cif.reach_funnel import replay  # noqa: E402

_PASS = 0
_FAIL = 0


def _ok(gate: str, evidence: str) -> None:
    global _PASS
    _PASS += 1
    print(f"  OK   {gate}  {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _FAIL
    _FAIL += 1
    print(f"  FAIL {gate}  {diag}")


def _check(gate: str, cond: bool, evidence: str, diag: str = "") -> None:
    _ok(gate, evidence) if cond else _fail(gate, diag or evidence)


def _mkrepo(root: Path, name: str, marker: str = "dir",
            gitdir: str = "", spec: str = "") -> Path:
    """Build a synthetic repository. Never touches a real checkout."""
    p = root / name
    p.mkdir(parents=True, exist_ok=True)
    if marker == "dir":
        (p / ".git").mkdir(exist_ok=True)
    elif marker == "file":
        (p / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
    elif marker == "broken":
        (p / ".git").write_text("not a gitdir line\n", encoding="utf-8")
    if spec:
        target = p / spec
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# synthetic spec\n", encoding="utf-8")
    return p


# --------------------------------------------------------------- discovery
def t_discovery(tmp: Path) -> None:
    main = _mkrepo(tmp, "mainrepo")
    _mkrepo(tmp, "wt-a", marker="file",
            gitdir=str(main / ".git" / "worktrees" / "wt-a"))
    _mkrepo(tmp, "wt-b", marker="file",
            gitdir=str(main / ".git" / "worktrees" / "wt-b"))
    _mkrepo(tmp, "broken", marker="broken")
    (tmp / "plain").mkdir()

    disc = rc.discover_repos((str(tmp),), max_depth=3)
    names = {p.name for p in disc.repos}

    # RED POLE this catches: the first host sweep of this wave matched
    # `.git` as a DIRECTORY only, which is blind to every worktree --
    # including the one this mission runs in.
    _check("V-W7-WORKTREE-MARKER-IS-A-FILE-TOO",
           {"wt-a", "wt-b"} <= names,
           f"discovered {sorted(names)}",
           f"worktrees invisible: {sorted(names)}")
    _check("V-W7-NON-REPO-NOT-COUNTED", "plain" not in names,
           "a directory with no .git marker is not a repository")

    groups = {p.name: rc.repo_group(p)[0] for p in disc.repos}
    _check("V-W7-WORKTREES-COLLAPSE-TO-ONE-REPOSITORY",
           groups["wt-a"] == groups["wt-b"] == groups["mainrepo"],
           "two worktrees and their main checkout share one group id",
           f"groups={groups}")
    _check("V-W7-BROKEN-MARKER-FAILS-APART",
           len({groups["broken"]} & {groups["mainrepo"]}) == 0,
           "an unreadable .git marker becomes its OWN group -- wrongly "
           "splitting costs one duplicate, wrongly merging deletes a "
           "repository from the population")

    empty = tmp / "nothing"
    empty.mkdir()
    d2 = rc.discover_repos((str(empty),), max_depth=2)
    _check("V-W7-EMPTY-ROOT-IS-EMPTY-NOT-ERROR",
           d2.repos == [] and d2.missing_roots == [],
           "an existing root with no repositories reports zero, and is "
           "distinguishable from an absent root")
    d3 = rc.discover_repos((str(tmp / "does-not-exist"),), max_depth=2)
    _check("V-W7-ABSENT-ROOT-IS-NAMED",
           d3.missing_roots and not d3.repos,
           f"absent root reported by name: {d3.missing_roots}",
           "an absent root read as an empty one")


# ------------------------------------------------------------------- door
def t_door(tmp: Path) -> None:
    open_repo = _mkrepo(tmp, "door-open")
    shut_repo = _mkrepo(tmp, "door-shut", spec="vault/plans/x.md")

    s_open = rc.measure_repo(open_repo)
    s_shut = rc.measure_repo(shut_repo)
    _check("V-W7-DOOR-OPEN-WITHOUT-SPEC",
           s_open.door_reachable and not s_open.spec_present,
           "no spec -> create_spec reachable")
    _check("V-W7-DOOR-SHUT-WITH-SPEC",
           (not s_shut.door_reachable) and s_shut.spec_present
           and s_shut.matched_globs == ["vault/plans/*.md"],
           f"spec present via {s_shut.matched_globs} -> door shut",
           f"{s_shut}")

    # The ceiling must be computed from the GATE'S OWN glob list. A local
    # copy would keep answering after the product's list changed, and
    # would measure a world the product does not live in.
    from modules.spec_gate import gate as gmod
    original = gmod.SPEC_GLOBS
    try:
        gmod.SPEC_GLOBS = ("no-such-file-anywhere.md",)
        rewired = rc.measure_repo(shut_repo)
    finally:
        gmod.SPEC_GLOBS = original
    restored = rc.measure_repo(shut_repo)
    _check("V-W7-CEILING-READS-THE-GATES-OWN-GLOBS",
           rewired.door_reachable and not restored.door_reachable,
           "narrowing the gate's SPEC_GLOBS flips the ceiling, and "
           "restoring it flips back -- no private copy of the list",
           f"rewired={rewired.door_reachable} restored="
           f"{restored.door_reachable}")
    _check("V-W7-NO-PRIVATE-GLOB-COPY",
           not hasattr(rc, "SPEC_GLOBS"),
           "reach_calibration defines no glob list of its own")


# ------------------------------------------------------------- population
def t_population() -> None:
    real = {"type": "user", "message": {"content": "add a validator"}}
    meta = {"type": "user", "isMeta": True,
            "message": {"content": "add a validator"}}
    reminder = {"type": "user",
                "message": {"content": "<system-reminder>x</system-reminder>"}}
    toolres = {"type": "user", "message": {"content": [
        {"type": "tool_result", "content": "ok"}]}}
    blocks = {"type": "user", "message": {"content": [
        {"type": "text", "text": "build the thing"}]}}
    assistant = {"type": "assistant", "message": {"content": "hi"}}

    _check("V-W7-HUMAN-TEXT-ACCEPTED",
           _user_text(real) == "add a validator"
           and _user_text(blocks) == "build the thing",
           "plain and block-shaped user text both read")
    _check("V-W7-MACHINE-TEXT-EXCLUDED",
           all(_user_text(o) is None
               for o in (meta, reminder, toolres, assistant)),
           "isMeta, system-reminder, tool_result and assistant records "
           "are not prompts -- counting them would inflate the "
           "denominator with text no human typed")

    # The bug this pins: first-match-wins put 100 of 127 Tier>=2 prompts
    # into `investigation` because that row happened to be first.
    text = "fix the broken error, the bug fails on a crash"
    _check("V-W7-SEMANTIC-CLASS-NOT-DECIDED-BY-TABLE-ORDER",
           semantic_class("explain " + text) == "repair",
           "one 'explain' needle loses to five repair needles",
           f"got {semantic_class('explain ' + text)!r}")
    _check("V-W7-SEMANTIC-CLASS-HAS-A-NULL",
           semantic_class("zzz qqq") == "unclassified",
           "no needle -> unclassified, never a forced class")


# ------------------------------------------------------------ privacy
def t_privacy(tmp: Path) -> None:
    repo = _mkrepo(tmp, "privacy-repo")
    secret = ("build a new integration module for the payments api "
              "SECRET-CANARY-7f3a")
    case = replay(secret, str(repo), "sess-1", "2026-09-21T10:00:00Z")
    blob = repr(case.__dict__)
    _check("V-W7-NO-PROMPT-TEXT-IN-THE-DERIVED-CASE",
           "SECRET-CANARY-7f3a" not in blob and secret not in blob,
           "the persisted record carries a digest, a length and verdicts "
           "-- never the prompt")
    _check("V-W7-NO-ABSOLUTE-PATH-IN-THE-DERIVED-CASE",
           str(tmp) not in blob,
           "the record carries a group id and a directory name, never a "
           "host path",
           blob[:200])
    _check("V-W7-DIGEST-IS-STABLE-AND-DISCRIMINATING",
           replay(secret, str(repo), "s", "").prompt_sha == case.prompt_sha
           and replay(secret + "!", str(repo), "s", "").prompt_sha
           != case.prompt_sha,
           "same text -> same digest; changed text -> different digest")


# --------------------------------------------------------------- funnel
def t_funnel(tmp: Path) -> None:
    open_repo = _mkrepo(tmp, "funnel-open")
    shut_repo = _mkrepo(tmp, "funnel-shut", spec="vault/plans/p.md")
    small = replay("fix a typo in the label", str(open_repo), "s", "")
    _check("V-W7-TIER-BELOW-2-IS-CORRECT-SILENCE",
           small.miss_layer == "tier_below_2" and not small.signal_emitted,
           f"tier {small.tier} -> {small.miss_layer}")

    proposal = ("build a universal knowledge acquisition module with "
                "deep research and a governance overlay for every repo")
    opened = replay(proposal, str(open_repo), "s", "")
    shut = replay(proposal, str(shut_repo), "s", "")
    _check("V-W7-DOOR-OPEN-RENDERS-OWNERS",
           opened.miss_layer == "none" and opened.signal_emitted
           and opened.signal_named_owners and opened.owners_routed,
           f"owners rendered: {opened.owners_routed}",
           f"{opened}")
    _check("V-W7-KNOWN-GAP-REPRODUCED-ON-A-SYNTHETIC-REPO",
           shut.miss_layer == "owners_routed_signal_silent"
           and shut.owners_routed == opened.owners_routed
           and not shut.signal_emitted,
           "the SAME proposal in a repo holding any spec computes the "
           f"same {len(shut.owners_routed)} owner(s) and renders none",
           f"{shut}")
    _check("V-W7-CWD-UNREADABLE-IS-NOT-A-NEGATIVE",
           replay(proposal, str(tmp / "gone"), "s", "").miss_layer
           == "cwd_unreadable",
           "a vanished cwd is unjudgeable, never a shut door")


# ---------------------------------------------------------- ground truth
def t_ground_truth() -> None:
    owners = ["modules/knowledge_acquisition"]
    hit = {"modules/knowledge_acquisition/loader.py"}
    miss = {"modules/unrelated/other.py"}
    shared = {"vault/knowledge_base/notes.md"}

    _check("V-W7-ORACLE-RELEVANT",
           gt.label_case(owners, hit, True, True)[0] == "RELEVANT",
           "work landed inside a routed owner path")
    _check("V-W7-ORACLE-NOT-RELEVANT",
           gt.label_case(owners, miss, True, True)[0] == "NOT_RELEVANT",
           "substantive work landed entirely elsewhere")
    _check("V-W7-ORACLE-AMBIGUOUS",
           gt.label_case(owners, shared, True, True)[0] == "AMBIGUOUS",
           "commits touching only shared paths decide nothing")
    _check("V-W7-UNLABELLED-IS-NOT-NEGATIVE",
           gt.label_case(owners, set(), True, True)[0]
           == "UNLABELLED_NO_COMMITS"
           and gt.label_case(owners, hit, True, False)[0]
           == "UNLABELLED_BY_DOMAIN"
           and gt.label_case(owners, hit, False, True)[0]
           == "UNLABELLED_NO_HISTORY",
           "no commits / out of domain / no history each keep their own "
           "state -- none of them becomes NOT_RELEVANT")

    src = (PP_ROOT / "modules" / "ucr_cif"
           / "reach_ground_truth.py").read_text(encoding="utf-8")
    code = "\n".join(l for l in src.splitlines()
                     if not l.lstrip().startswith("#"))
    body = code.split('"""', 2)[-1]
    forbidden = [t for t in ("sdd_tier", "check_spec_gate",
                             "disposition_consumer", "ProactiveSignal")
                 if t in body]
    _check("V-W7-ORACLE-IS-INDEPENDENT-OF-THE-TRIGGER",
           not forbidden,
           "the oracle's code references no part of the activation chain "
           "it grades",
           f"references {forbidden}")


def main() -> int:
    print("== V-W7 ACTIVATION REACH INSTRUMENT ==")
    with tempfile.TemporaryDirectory(prefix="w7-reach-") as raw:
        tmp = Path(raw)
        t_discovery(tmp / "disc")
        t_door(tmp / "door")
        t_population()
        t_privacy(tmp / "priv")
        t_funnel(tmp / "funnel")
    t_ground_truth()
    total = _PASS + _FAIL
    print(f"\nW7_REACH_PASS={_PASS}/{total}  threshold={total}/{total}")
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(main())
