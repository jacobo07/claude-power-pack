#!/usr/bin/env python3
"""V-INSTALL-* -- what the installer is allowed to put on a clean machine.

The installer read `inv[kind]["items"]` for four months against inventory
files that have never had an `items` key. The loop body never executed, so
every counter -- including the reject branch that would have made it
visible -- read zero, and the install returned 0 with a clean report while
shipping nothing. Its own E1 gate saw the empty tree and blamed the host.

Three properties have to hold at once, and each has a red branch driven
here rather than assumed:

  the population is DISCOVERED, so a new legitimate root cannot be
  forgotten by a list nobody remembered to edit;

  sovereignty is DECLARED, so widening discovery cannot absorb a foreign
  or operator-owned estate -- this branch has never fired in production
  because no excluded name currently has a repo source, which is exactly
  why it needs a synthetic subject;

  a name the inventory claims as canonical with no source anywhere is
  REPORTED, not silently dropped.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

_spec = importlib.util.spec_from_file_location(
    "igc_under_test", PP / "tools" / "install_global_core.py")
igc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(igc)

from modules.mirror_discovery import discovery as md  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


@contextmanager
def _fixture_repo(roots: dict[str, list[str]], inventory: dict | None = None):
    """A throwaway repo holding agent files in the named roots.

    Synthetic by design. A drill pinned to whichever real agent is
    misplaced today has an interest in that misplacement surviving, and
    stops asserting anything the day it is fixed.
    """
    tmp = Path(tempfile.mkdtemp(prefix="pp-install-pop-"))
    try:
        for root, names in roots.items():
            d = tmp / root
            d.mkdir(parents=True, exist_ok=True)
            for n in names:
                (d / n).write_text(f"---\nname: {n[:-3]}\n---\nbody\n",
                                   encoding="utf-8")
        inv_dir = tmp / "tools" / "_inventory"
        inv_dir.mkdir(parents=True, exist_ok=True)
        for kind in ("agents", "commands", "hooks"):
            payload = (inventory or {}).get(kind, {
                "schema_version": 1, "kind": kind,
                "pp_original": [], "plugins": {}, "user_personal": [],
            })
            (inv_dir / f"{kind}.json").write_text(
                json.dumps(payload), encoding="utf-8")
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@contextmanager
def _extra_roots(mapping: dict[str, tuple[str, ...]]):
    prior = md.EXTRA_REPO_ROOTS
    md.EXTRA_REPO_ROOTS = mapping
    try:
        yield
    finally:
        md.EXTRA_REPO_ROOTS = prior


def gate_population_spans_declared_roots() -> None:
    """Green AND red in one run: the extra roots are load-bearing.

    Same fixture, same call. With the roots declared the population spans
    three directories; with the declaration removed it collapses to one.
    That makes the 22 attributable to the declaration rather than to a
    scan that happened to wander.
    """
    gate = "V-INSTALL-POP-DISCOVERED"
    roots = {
        "agents": ["primary.md"],
        "vault/agents": ["staged.md"],
        "vendor/rtk/agents": ["vendored.md"],
    }
    with _fixture_repo(roots) as repo:
        with _extra_roots({"agents": ("vault/agents", "vendor/rtk/agents")}):
            wide = igc._repo_population(repo, "agents")
        with _extra_roots({}):
            narrow = igc._repo_population(repo, "agents")

    if wide is None or narrow is None:
        _fail(gate, "population came back None; discovery unreachable")
        return
    want_wide = {"primary.md", "staged.md", "vendored.md"}
    if set(wide) != want_wide:
        _fail(gate, f"declared roots -> {sorted(wide)}, want {sorted(want_wide)}")
        return
    if set(narrow) != {"primary.md"}:
        _fail(gate, f"RED BRANCH DID NOT FIRE: undeclaring the extra roots "
                    f"still yielded {sorted(narrow)}; the pairing is not "
                    f"attributable to the declaration")
        return
    _ok(gate, f"declared={sorted(wide)} undeclared={sorted(narrow)} "
              f"(red branch drove)")


def gate_population_is_not_the_items_key() -> None:
    """The exact regression: the shipping loop's old reader returns zero.

    Pinned against the REAL inventory, because the defect was a
    disagreement between this repo's files and this repo's reader. A
    fixture would have agreed with whichever schema the fixture chose.
    """
    gate = "V-INSTALL-POP-NOT-ITEMS"
    inv = igc._load_inventory(PP)
    legacy = sum(len(inv.get(k, {}).get("items", []))
                 for k in ("agents", "commands"))
    discovered = igc._repo_population(PP, "agents")
    if discovered is None:
        _fail(gate, "discovery unreachable against the real repo")
        return
    if legacy != 0:
        _fail(gate, f"inventory now HAS an items key ({legacy} rows). This "
                    f"gate assumed the schema that caused the outage; "
                    f"re-read install_global_core before trusting it")
        return
    if not discovered:
        _fail(gate, "discovered population is empty -- the outage is back")
        return
    _ok(gate, f"legacy items reader={legacy}, discovered agents="
              f"{len(discovered)}")


def gate_sovereignty_excludes_foreign() -> None:
    """The branch production has never reached.

    Every currently-excluded name (the operator's own specialist, the gsd
    plugin family) is live-only, so discovery never offers it and the
    exclusion never fires. A guard with no reachable subject reports the
    same clean green as one that works.
    """
    gate = "V-INSTALL-SOVEREIGNTY"
    inventory = {"agents": {
        "schema_version": 1, "kind": "agents",
        "pp_original": [],
        "plugins": {"gsd": ["gsd-planner.md"]},
        "user_personal": [{"name": "operator-owned.md",
                           "redact_reason": "holds a private host"}],
    }}
    roots = {"agents": ["ours.md", "operator-owned.md", "gsd-planner.md"]}
    with _fixture_repo(roots, inventory) as repo:
        with _extra_roots({}):
            population = igc._repo_population(repo, "agents")
        inv = igc._load_inventory(repo)
        excluded = igc._sovereignty_exclusions(inv, "agents")

    if population is None:
        _fail(gate, "population came back None")
        return
    shippable = sorted(n for n in population if n not in excluded)
    if "operator-owned.md" in shippable:
        _fail(gate, "operator-owned file would be installed by PP")
        return
    if "gsd-planner.md" in shippable:
        _fail(gate, "plugin-owned file would be installed by PP")
        return
    if shippable != ["ours.md"]:
        _fail(gate, f"expected only ours.md to ship, got {shippable}")
        return
    if len(excluded) != 2:
        _fail(gate, f"expected 2 declared exclusions, got {excluded}")
        return
    _ok(gate, f"ships {shippable}; refuses {sorted(excluded)} "
              f"(both reasons recorded)")


def gate_sovereignty_does_not_over_refuse() -> None:
    """Positive control for the gate above.

    A predicate that excluded everything would pass the red branch and
    look like a working boundary.
    """
    gate = "V-INSTALL-SOVEREIGNTY-NO-OVER-REFUSAL"
    inventory = {"agents": {
        "schema_version": 1, "kind": "agents", "pp_original": [],
        "plugins": {}, "user_personal": [],
    }}
    with _fixture_repo({"agents": ["a.md", "b.md"]}, inventory) as repo:
        inv = igc._load_inventory(repo)
        excluded = igc._sovereignty_exclusions(inv, "agents")
    if excluded:
        _fail(gate, f"nothing was declared foreign, yet {sorted(excluded)} "
                    f"was refused")
        return
    _ok(gate, "no declarations -> no refusals")


def gate_alias_keys_by_live_name() -> None:
    """A pair whose two names differ must key by the name the install writes.

    Keyed by the repo name, the install writes a SECOND file under the
    repo's spelling and never touches the live one it meant to update.
    """
    gate = "V-INSTALL-ALIAS-LIVE-NAME"
    live_rel, repo_rel = None, None
    for k, v in md.ALIASES.items():
        if k.startswith("commands/") and v.startswith("commands/"):
            live_rel, repo_rel = k.split("/", 1)[1], v.split("/", 1)[1]
            break
    if live_rel is None:
        _fail(gate, "no commands alias declared; this gate has no subject "
                    "and must be re-pointed, not deleted")
        return
    population = igc._repo_population(PP, "commands")
    if population is None:
        _fail(gate, "discovery unreachable")
        return
    if repo_rel in population:
        _fail(gate, f"population keyed by the repo name {repo_rel}; the "
                    f"install would create a duplicate instead of updating "
                    f"{live_rel}")
        return
    if live_rel not in population:
        _fail(gate, f"{live_rel} absent from the population entirely")
        return
    _ok(gate, f"{repo_rel} is offered as {live_rel}")


def gate_unreachable_discovery_is_not_empty() -> None:
    """'I could not ask' must not be spelled the same as 'nothing exists'.

    An empty population installs nothing and exits clean, which is the
    original outage. None makes the caller refuse instead.
    """
    gate = "V-INSTALL-POP-UNREACHABLE"
    saved = sys.modules.get("modules.mirror_discovery")
    sys.modules["modules.mirror_discovery"] = None  # forces ImportError
    try:
        result = igc._repo_population(PP, "agents")
    finally:
        if saved is None:
            sys.modules.pop("modules.mirror_discovery", None)
        else:
            sys.modules["modules.mirror_discovery"] = saved
    if result == {}:
        _fail(gate, "unreachable discovery returned {} -- indistinguishable "
                    "from an estate with no agents, which installs nothing "
                    "and reports success")
        return
    if result is not None:
        _fail(gate, f"expected None on unreachable discovery, got {result}")
        return
    _ok(gate, "unreachable discovery -> None (caller refuses)")


def gate_real_repo_floor() -> None:
    """Positive control anchored on NAMES from each root, not on a count.

    A count is satisfied by any twenty files. Naming one agent per root
    means a root that is renamed or emptied goes red instead of quietly
    finding fewer.
    """
    gate = "V-INSTALL-POP-REAL-FLOOR"
    population = igc._repo_population(PP, "agents")
    if population is None:
        _fail(gate, "discovery unreachable against the real repo")
        return
    anchors = {
        "oneshot-architect-auditor.md": "agents",
        "cdio-reviewer.md": "vault/agents",
        "rust-rtk.md": "vendor/rtk/agents",
    }
    missing = [n for n in anchors if n not in population]
    if missing:
        _fail(gate, f"anchor(s) absent: {missing}; a declared root is "
                    f"renamed, emptied, or no longer scanned")
        return
    wrong = []
    for name, want_root in anchors.items():
        got = population[name].relative_to(PP).parent.as_posix()
        if got != want_root:
            wrong.append(f"{name}: {got} != {want_root}")
    if wrong:
        _fail(gate, "; ".join(wrong))
        return
    if len(population) < 20:
        _fail(gate, f"only {len(population)} agents discovered; the floor "
                    f"is 20 and was 22 when measured 2026-09-14")
        return
    _ok(gate, f"{len(population)} agents; anchors resolve to their own roots")


def gate_inventory_digests_match_source() -> None:
    """The inventory's sha256 field had no reader anywhere in the estate.

    Written once on 2026-05-19 and consumed by nothing: install_global_core
    computes its own hashes from files, and no other tool reads the field. So
    two entries drifted for four months in silence -- restart.md, rebuilt by
    estate commits in May and June, and oneshot-architect-auditor.md, rewritten
    in 7ed31ae. Both were found by hand this session, which is not a mechanism.

    Before Step 3 most of these names had no repo source at all, so the digest
    could not have been checked against anything. Now that they do, the field
    gets a consumer instead of a refresh -- refreshing a number nothing reads
    buys one honest day.

    Normalisation is the estate's own: LF-normalised, so a CRLF checkout cannot
    manufacture drift. Verified on a real pair -- worktree and committed blob
    hash identically.
    """
    gate = "V-INSTALL-DIGEST-TRUTH"
    inv = igc._load_inventory(PP)
    checked, drifted, unsourced = 0, [], 0
    for kind in ("agents", "commands"):
        population = igc._repo_population(PP, kind)
        if population is None:
            _fail(gate, "discovery unreachable")
            return
        for entry in (inv.get(kind, {}) or {}).get("pp_original", []) or []:
            if not isinstance(entry, dict):
                continue
            name, want = entry.get("name"), entry.get("sha256")
            if not name or not want:
                continue
            src = population.get(name)
            if src is None:
                unsourced += 1
                continue
            checked += 1
            have = igc._sha256(src)
            if have != want:
                drifted.append(f"{kind}/{name}: source={have[:12]} "
                               f"inventory={want[:12]}")
    if drifted:
        _fail(gate, "inventory digest disagrees with the captured source -- "
                    "fix the SOURCE or refresh deliberately, never pick the "
                    "value that makes this green: " + "; ".join(drifted))
        return
    if checked < 10:
        _fail(gate, f"only {checked} digest(s) were comparable; this gate "
                    f"reports the same green when it checks nothing, and "
                    f"{unsourced} claimed name(s) still have no source")
        return
    _ok(gate, f"{checked} inventory digest(s) match their captured source; "
              f"{unsourced} claimed name(s) not yet sourced")


def gate_digest_drift_is_detected() -> None:
    """Red branch, synthetic: a changed source must break the claim.

    Pinned to a fabricated entry rather than to whichever real digest is
    stale today -- the two real ones are being corrected in this same commit,
    so a drill naming them would assert about subjects that no longer offend.
    """
    gate = "V-INSTALL-DIGEST-DRIFT-CAUGHT"
    inventory = {"agents": {
        "schema_version": 1, "kind": "agents",
        "pp_original": [{"name": "drifter.md", "sha256": "0" * 64}],
        "plugins": {}, "user_personal": [],
    }}
    with _fixture_repo({"agents": ["drifter.md"]}, inventory) as repo:
        with _extra_roots({}):
            population = igc._repo_population(repo, "agents")
        inv = igc._load_inventory(repo)
        entry = inv["agents"]["pp_original"][0]
        src = population.get(entry["name"])
        if src is None:
            _fail(gate, "fixture source missing; the drill proves nothing")
            return
        real = igc._sha256(src)
        if real == entry["sha256"]:
            _fail(gate, "fabricated digest collided with the real one")
            return
        # ... and the matching half, so the comparison is not simply != always
        entry_ok = dict(entry, sha256=real)
        if igc._sha256(src) != entry_ok["sha256"]:
            _fail(gate, "a correct digest did not compare equal; the "
                        "comparison itself is broken")
            return
    _ok(gate, "a drifted digest compares unequal and a correct one compares "
              "equal (both halves driven)")


def main() -> int:
    print("V-INSTALL-* -- installer population, sovereignty and aperture")
    print("=" * 68)
    gate_population_spans_declared_roots()
    gate_population_is_not_the_items_key()
    gate_sovereignty_excludes_foreign()
    gate_sovereignty_does_not_over_refuse()
    gate_alias_keys_by_live_name()
    gate_unreachable_discovery_is_not_empty()
    gate_real_repo_floor()
    gate_inventory_digests_match_source()
    gate_digest_drift_is_detected()
    total = _passes + _fails
    print("=" * 68)
    print(f"INSTALL_POPULATION_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
