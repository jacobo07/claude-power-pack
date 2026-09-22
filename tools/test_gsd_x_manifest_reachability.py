"""V-GSDXREACH-* -- the capability manifest must be able to FIRE, not merely validate.

Four times this capability was installed, surfaced, validator-clean and unable
to fire, and all four times every existing suite stayed green -- because every
existing suite tests the mission LOGIC and nothing tests the REGISTRATION.

  1. registered on the prose `kind:"gate"` envelope, which always exits 0 (572629f)
  2. deciding on `closure` / `receipt.blocking` instead of the open set (572629f)
  3. registered at execute:wave:post, whose only dispatch reads `hook.check.query`
  4. `activationKey: "enabled"` -- validator-clean and permanently false

This gate closes 3 and 4, and it derives its answer from gsd-core's own
workflow files rather than a list written here, so it keeps being true when
upstream moves. The rule:

  A gate point is USABLE by this manifest only if some gsd-core workflow file
  that mentions the point also carries a `check predicate --predicate` dispatch
  that passes `--phase-dir`.

`--phase-dir` is not incidental. Our predicate interpolates `${PHASE_DIR}`, and
a dispatch that supplies only `--phase-number` leaves it as the empty string
(gate-predicate-evaluator.cjs, `ctx.phaseDir ?? ''`), which reaches our tool as
`check ""` -> fail-closed exit 2 -> every run blocked for a reason unrelated to
obligations. That is how execute:post looks correct and is not.

Positive controls are mandatory here: an empty sweep would satisfy every
assertion below while proving nothing, so the harness fails loudly if it cannot
see gsd-core, and it requires the OLD point to be REJECTED by the same
predicate that accepts the new one.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# GSDX_REACH_MANIFEST lets the mutation drill point this gate at a mutated COPY,
# so the drill never edits the tracked manifest in a tree other writers share.
MANIFEST = Path(os.environ.get(
    "GSDX_REACH_MANIFEST",
    REPO / "capabilities" / "cpp-gsd-x-mission" / "capability.json"))
GSD_WORKFLOWS = Path.home() / ".claude" / "gsd-core" / "workflows"

# The point this capability was registered at until 2026-09-22, kept as a
# standing negative control. It must stay REJECTED by the same predicate that
# accepts whatever point the manifest names today.
RETIRED_POINT = "execute:wave:post"

PREDICATE_DISPATCH = re.compile(r"check\s+predicate\s+--predicate")
PHASE_DIR_FLAG = "--phase-dir"

# A GSD loop extension point, e.g. plan:pre, execute:wave:post, ship:pre.
POINT_TOKEN = re.compile(r"\b((?:plan|execute|verify|ship|discuss)(?::[a-z]+){1,2})\b")
# How far above a dispatch line its owning point may be named. The real
# distances in gsd-core are single-digit (ship.md names ship:pre four lines
# above its dispatch); this is slack, not a guess at the answer.
PROXIMITY = 60

_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  FAIL {gate}: {diagnostic}")


def _harness_failed(why: str) -> "int":
    # A harness failure is not a subject verdict. Exit 2 so a run that could not
    # measure is never read as a run that measured nothing wrong.
    print(f"\nHARNESS-FAILED: {why}")
    print("GSDX_REACH_PASS=0/0  threshold=HARNESS")
    return 2


def _workflow_files() -> list[Path]:
    return sorted(GSD_WORKFLOWS.rglob("*.md"))


def dispatch_sites(files: list[Path]) -> dict[str, list[str]]:
    """Map a hook point -> the predicate dispatches that belong TO IT.

    Co-occurrence in one file is not attribution: plan-phase.md both mentions
    execute:wave:post and carries its own plan:pre predicate dispatch, so a
    file-level rule reports the retired point as usable. (Measured -- the
    negative control below caught exactly that.) A dispatch is attributed to
    the nearest hook point named at or above it, within PROXIMITY lines.
    """
    sites: dict[str, list[str]] = {}
    for path in files:
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        recent: str | None = None
        recent_at = -10**6
        for idx, line in enumerate(text.splitlines()):
            found = POINT_TOKEN.findall(line)
            if found:
                recent, recent_at = found[-1], idx
            if (PREDICATE_DISPATCH.search(line) and PHASE_DIR_FLAG in line
                    and recent is not None and idx - recent_at <= PROXIMITY):
                sites.setdefault(recent, []).append(f"{path.name}:{idx + 1}")
    return sites


def point_is_usable(point: str, sites: dict[str, list[str]]) -> tuple[bool, str]:
    where = sites.get(point)
    if where:
        return True, f"dispatched with {PHASE_DIR_FLAG} at {where}"
    return False, (f"no gsd-core workflow dispatches `check predicate` with "
                   f"{PHASE_DIR_FLAG} for {point!r} (points that do: "
                   f"{sorted(sites)})")


def main() -> int:
    if not GSD_WORKFLOWS.is_dir():
        return _harness_failed(f"gsd-core workflows not readable at {GSD_WORKFLOWS}")
    files = _workflow_files()
    if len(files) < 5:
        return _harness_failed(f"only {len(files)} workflow files found; the sweep "
                               f"may have stopped seeing gsd-core")
    if not MANIFEST.is_file():
        return _harness_failed(f"manifest not readable at {MANIFEST}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    gates = manifest.get("gates") or []

    # --- positive control: the sweep can see predicate dispatches at all -----
    dispatching = [p.name for p in files
                   if PREDICATE_DISPATCH.search(p.read_text(encoding="utf-8-sig",
                                                            errors="replace"))]
    if not dispatching:
        return _harness_failed("no workflow file dispatches `check predicate`; "
                               "the pattern has stopped matching upstream")
    _ok("V-GSDXREACH-SWEEP-ALIVE",
        f"{len(files)} workflow files, {len(dispatching)} dispatch a predicate: {dispatching}")

    sites = dispatch_sites(files)
    if not sites:
        return _harness_failed("no dispatch could be attributed to any hook point; "
                               "the proximity attribution has stopped working")
    _ok("V-GSDXREACH-ATTRIBUTION-ALIVE", f"points with a phase-dir predicate dispatch: {sites}")

    # --- negative control: the retired point must still be rejected ----------
    retired_usable, retired_why = point_is_usable(RETIRED_POINT, sites)
    if retired_usable:
        _fail("V-GSDXREACH-RETIRED-POINT-STILL-REJECTED",
              f"{RETIRED_POINT!r} now looks usable ({retired_why}). Either upstream "
              f"gained a predicate dispatch there -- in which case delete this control "
              f"deliberately -- or the predicate has gone slack and accepts anything.")
    else:
        _ok("V-GSDXREACH-RETIRED-POINT-STILL-REJECTED", retired_why)

    if not gates:
        _fail("V-GSDXREACH-HAS-GATE", "manifest declares no gates")

    for i, gate in enumerate(gates):
        point = gate.get("point", "")
        when = gate.get("when", "")
        check = gate.get("check") or {}

        # --- the point must actually dispatch what we declare ---------------
        usable, why = point_is_usable(point, sites)
        if usable:
            _ok(f"V-GSDXREACH-POINT-DISPATCHES[{i}]", f"{point!r}: {why}")
        else:
            _fail(f"V-GSDXREACH-POINT-DISPATCHES[{i}]", f"{point!r}: {why}")

        # --- predicate, not query: query is not available to a third party --
        if "predicate" in check:
            _ok(f"V-GSDXREACH-USES-PREDICATE[{i}]", "check carries a predicate")
        else:
            _fail(f"V-GSDXREACH-USES-PREDICATE[{i}]",
                  "check carries no predicate. `check.query` is a fixed built-in "
                  "list (check-command-router.cjs) that no third party can extend.")

        # --- the `when` key must be resolvable, i.e. dotted and declared ----
        if "." in when:
            _ok(f"V-GSDXREACH-WHEN-DOTTED[{i}]", f"when={when!r}")
        else:
            _fail(f"V-GSDXREACH-WHEN-DOTTED[{i}]",
                  f"when={when!r} is not dotted. capability-activation.cjs resolves a "
                  f"config key through loaded config / workstream config.json / root "
                  f"config.json / schema default; a bare key is at none of them and "
                  f"resolves false forever. It is also un-namespaced in a host-global "
                  f"config space.")

        # --- activationKey must agree with the gate and be declared ---------
        akey = manifest.get("activationKey")
        if akey == when:
            _ok(f"V-GSDXREACH-ACTIVATION-AGREES[{i}]", f"activationKey == when == {akey!r}")
        else:
            _fail(f"V-GSDXREACH-ACTIVATION-AGREES[{i}]",
                  f"activationKey={akey!r} but gate when={when!r}; the capability and "
                  f"its hook would gate on different keys")

        cfg = manifest.get("config") or {}
        if akey in cfg:
            _ok(f"V-GSDXREACH-ACTIVATION-DECLARED[{i}]",
                f"config declares {akey!r} (default={cfg[akey].get('default')!r})")
        else:
            _fail(f"V-GSDXREACH-ACTIVATION-DECLARED[{i}]",
                  f"config has {sorted(cfg)} which does not include {akey!r}")

        # --- off by default: this gate is blocking and fails closed ---------
        default = (cfg.get(akey) or {}).get("default")
        if default is False:
            _ok(f"V-GSDXREACH-DEFAULT-OFF[{i}]", "default is false")
        else:
            _fail(f"V-GSDXREACH-DEFAULT-OFF[{i}]",
                  f"default={default!r}; a blocking onError:halt gate installed at "
                  f"global scope must not be on by default")

    total = len(_passes) + len(_fails)
    print(f"\nGSDX_REACH_PASS={len(_passes)}/{total}  threshold={total}/{total}")
    return 0 if not _fails else 1


if __name__ == "__main__":
    sys.exit(main())
