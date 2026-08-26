"""V-UNPAIRED-* -- the 92.5% the mirror comparator cannot speak about.

verify_global_mirrors compares 28 pairs and prints "345 file(s) present on
one side only". A count reads as accounted-for. It is not a disposition,
and this repo has already been bitten once by the difference: an edit to
research-intent-detector never reached production because the dispatcher
that runs resolves './x.js' against its own directory, and nothing in the
estate could say which directory that was.

BROKEN_REGISTRATION -- something wired at a path where no file exists -- is
currently zero in this tree. A branch that never executes proves nothing,
so it is exercised here against a SYNTHETIC case. Every rejection is paired
with an admission: a class that can only say NO is indistinguishable from
a class that is broken.
"""
from __future__ import annotations

import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

from tools.mirror_unpaired_audit import (  # noqa: E402
    BROKEN_REGISTRATION, CANONICAL_DORMANT, LIVE_DORMANT, LIVE_FROM_REPO,
    UNCLASSIFIED, UNVERSIONED_LIVE, audit, classify_hook,
)
from modules.mirror_discovery.discovery import resolve_live_root  # noqa: E402

EXPECTED_GATES = 9
_passes: list[str] = []
_fails: list[str] = []
LIVE = Path("C:/Users/User/.claude")


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  FAIL {gate}: {diagnostic}")


def _check(gate, got, want, note):
    if got == want:
        _ok(gate, f"{want} -- {note}")
    else:
        _fail(gate, f"got {got}, expected {want} ({note})")


def main() -> int:
    # A hook that lives only in the repo, registered by its REPO path: this
    # is the CORRECT arrangement, not a defect. session_start_hub.js is a
    # real instance -- no mirror copy, and live.
    # The INSTALLED repo path, which is not where this suite runs from --
    # it runs from a worktree. Passing it explicitly is the point: the tool
    # used to hardcode this string and was therefore correct only at one
    # address. These fixtures name the installed tree while the process
    # lives somewhere else, so a re-hardcoded version fails here.
    installed = Path("C:/Users/User/.claude/skills/claude-power-pack")
    st_repo = f'"command": "node {installed.as_posix()}/hooks/widget.js"'
    _check("V-UNPAIRED-LIVE-FROM-REPO",
           classify_hook("widget.js", "repo", st_repo, {}, LIVE,
                         installed)[0],
           LIVE_FROM_REPO, "repo-only but registered by repo path")

    # THE FAILING CLASS, which reality does not currently supply: registered
    # at a live path, with no file there. Wired and dead.
    st_live = '"command": "node C:/Users/User/.claude/hooks/widget.js"'
    _check("V-UNPAIRED-BROKEN-REGISTRATION",
           classify_hook("widget.js", "repo", st_live, {}, LIVE,
                         installed)[0],
           BROKEN_REGISTRATION, "registered where no file exists")

    _check("V-UNPAIRED-CANONICAL-DORMANT",
           classify_hook("widget.js", "repo", "", {}, LIVE, installed)[0],
           CANONICAL_DORMANT, "repo-only, nothing registers it")

    _check("V-UNPAIRED-UNVERSIONED-LIVE",
           classify_hook("widget.js", "live", st_live, {}, LIVE,
                         installed)[0],
           UNVERSIONED_LIVE, "running, and not in version control")

    _check("V-UNPAIRED-LIVE-DORMANT",
           classify_hook("widget.js", "live", "", {}, LIVE, installed)[0],
           LIVE_DORMANT, "live-only and unregistered")

    # Registration via the dispatcher, not settings.json. The dispatcher is
    # how most hooks are actually wired, so a classifier blind to it would
    # call 50+ live hooks dormant.
    # PP here is the WORKTREE this suite runs from, deliberately not the
    # installed path used above. Both must classify as registered.
    targets = {"widget.js": PP / "hooks" / "widget.js"}
    _check("V-UNPAIRED-DISPATCHER-COUNTS",
           classify_hook("widget.js", "repo", "", targets, LIVE, PP)[0],
           LIVE_FROM_REPO, "dispatcher registration is registration")

    # --- totality: nothing may be silently dropped -----------------------
    res = audit(PP, resolve_live_root(None))
    if len(res["rows"]) == res["unpaired"]:
        _ok("V-UNPAIRED-TOTAL",
            f"{len(res['rows'])} rows for {res['unpaired']} unpaired files")
    else:
        _fail("V-UNPAIRED-TOTAL",
              f"{len(res['rows'])} rows vs {res['unpaired']} unpaired -- "
              "files are being dropped between discovery and disposition")

    # Unknown must be VISIBLE as unknown. If the non-hook domains ever
    # start reporting a decided status, the evidence for it has to arrive
    # first -- silence in this gate would mean they were assumed fine.
    unclassified = [r for r in res["rows"] if r["status"] == UNCLASSIFIED]
    non_hook = [r for r in res["rows"] if r["domain"] != "hooks"]
    if unclassified and len(unclassified) == len(non_hook):
        _ok("V-UNPAIRED-UNKNOWN-IS-VISIBLE",
            f"{len(unclassified)} non-hook files carry UNCLASSIFIED")
    else:
        _fail("V-UNPAIRED-UNKNOWN-IS-VISIBLE",
              f"{len(unclassified)} unclassified vs {len(non_hook)} "
              "non-hook rows -- a domain gained a verdict without evidence")

    # The dispatcher divergence set IS the wired-canonical-only set. It is
    # allowed to be non-empty (the Owner owns ~/.claude/hooks), but it must
    # be COMPUTED, not remembered.
    div = res.get("divergence") or {}
    if "repo_only" in div and "live_only" in div:
        _ok("V-UNPAIRED-DIVERGENCE-COMPUTED",
            f"repo-only={div['repo_only']} live-only={div['live_only']}")
    else:
        _fail("V-UNPAIRED-DIVERGENCE-COMPUTED",
              "no divergence computed; the SREE class would be invisible")

    ran = len(_passes) + len(_fails)
    print(f"\nUNPAIRED_PASS={len(_passes)}/{ran}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if ran != EXPECTED_GATES:
        print(f"GATE COUNT MISMATCH: {ran} ran, {EXPECTED_GATES} expected")
        return 1
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
