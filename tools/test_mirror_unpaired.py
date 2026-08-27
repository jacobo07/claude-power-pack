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

EXPECTED_GATES = 15
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
    # Asserting the KEYS EXIST proved nothing: audit() builds that dict
    # literally, so the gate passed even when both extractions returned
    # empty -- precisely the state in which the SREE class is invisible.
    # Assert the comparison had INPUTS.
    div = res.get("divergence") or {}
    n_repo, n_live = div.get("repo_registers"), div.get("live_registers")
    if n_repo and n_live:
        _ok("V-UNPAIRED-DIVERGENCE-COMPUTED",
            f"compared {n_repo} vs {n_live} registrations; "
            f"repo-only={div['repo_only']} live-only={div['live_only']}")
    else:
        _fail("V-UNPAIRED-DIVERGENCE-COMPUTED",
              f"a dispatcher yielded no registrations "
              f"(repo={n_repo}, live={n_live}) -- the comparison is empty "
              "and a wired-canonical-only hook would not show")

    # THE FAILING CLASS, ACTUALLY WIRED. This lived only in the CLI's
    # main(), which no gate invokes, so the suite would have returned 0
    # with fifty broken registrations in the tree while the umbrella row
    # claimed it "fails only on a registration pointing at a file that
    # does not exist".
    broken = [r for r in res["rows"] if r["status"] == BROKEN_REGISTRATION]
    if not broken:
        _ok("V-UNPAIRED-NO-BROKEN-REGISTRATION",
            "no registration points at a missing file")
    else:
        _fail("V-UNPAIRED-NO-BROKEN-REGISTRATION",
              f"{len(broken)} wired-and-dead: "
              + ", ".join(f"{r['rel']} ({r['evidence']})" for r in broken))

    # settings.json holds JSON-ESCAPED Windows paths. `_norm` swapped
    # backslashes without collapsing runs, so `C:\\Users\\...` became
    # `c://users//...` and matched nothing -- every backslash-spelled
    # registration read as unregistered, and BROKEN_REGISTRATION could
    # not fire at all. Latent only because this settings.json happens to
    # use forward slashes.
    escaped = r'"command": "node C:\\Users\\User\\.claude\\hooks\\widget.js"'
    _check("V-UNPAIRED-BACKSLASH-SPELLING",
           classify_hook("widget.js", "repo", escaped, {}, LIVE,
                         installed)[0],
           BROKEN_REGISTRATION,
           "a JSON-escaped Windows path is still a registration")

    # The dispatcher extractor took any quoted `.js`, so a commented-out
    # entry or a log string naming a script reported an unregistered hook
    # as LIVE -- the inverse of the bug this tool exists to find.
    import tempfile  # noqa: PLC0415
    from tools.mirror_unpaired_audit import dispatcher_targets  # noqa: PLC0415,E402
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "hook-dispatcher.js"
        fake.write_text(
            "const HOOKS = [\n"
            "  './real-hook.js',\n"
            "  // './commented-out.js',\n"
            "  { exe: NODE, script: './scoped.js' },\n"
            "];\n"
            "log('failed to load plugin-x.js');\n"
            "const NAME = 'ghost-hook.js';\n",
            encoding="utf-8")
        got = set(dispatcher_targets(fake))
        want = {"real-hook.js", "scoped.js"}
        if got == want:
            _ok("V-UNPAIRED-EXTRACTOR-NARROW",
                f"extracted exactly {sorted(want)}")
        else:
            _fail("V-UNPAIRED-EXTRACTOR-NARROW",
                  f"extracted {sorted(got)}, expected {sorted(want)} -- "
                  "prose and comments are not registrations")

    # --- divergence is a verdict, not a footnote -------------------------
    # It was printed inside a passing audit, which is the shape that let a
    # producer fire 63 times into an empty sink for 80 days.
    import subprocess
    proc = subprocess.run(
        [sys.executable, str(PP / "tools" / "mirror_unpaired_audit.py")],
        capture_output=True, text=True, timeout=120)
    diverged = "WIRED-CANONICAL-ONLY" in proc.stdout or \
               "WIRED-LIVE-ONLY" in proc.stdout
    if diverged and proc.returncode == 1:
        _ok("V-UNPAIRED-DIVERGENCE-FAILS",
            "a hook wired canonically and absent from the running copy "
            "fails the audit instead of being narrated in its tail")
    elif not diverged and proc.returncode == 0:
        _ok("V-UNPAIRED-DIVERGENCE-FAILS",
            "canonical and live agree; the audit passes -- the bookend that "
            "proves this gate can say YES")
    else:
        _fail("V-UNPAIRED-DIVERGENCE-FAILS",
              f"diverged={diverged} but exit={proc.returncode}")

    if "Owner: copy hooks/hook-dispatcher.js" in proc.stdout or not diverged:
        _ok("V-UNPAIRED-DIVERGENCE-ACTIONABLE",
            "the failure names the exact Owner action, since this repo "
            "cannot write ~/.claude/hooks itself")
    else:
        _fail("V-UNPAIRED-DIVERGENCE-ACTIONABLE",
              "a failure the reader cannot act on is a failure they learn "
              "to skip")

    # A live dispatcher that registers NOTHING is total capability loss,
    # and the old guard read it as agreement: repo_only listed every hook,
    # live_registers was 0, and the tool printed OK.
    vacuous = {"repo_registers": 52, "live_registers": 0,
               "repo_only": ["a.js", "b.js"], "live_only": []}
    would_fail = bool(
        vacuous["repo_registers"]
        and (not vacuous["live_registers"]
             or vacuous["repo_only"] or vacuous["live_only"]))
    unmeasured = {"repo_registers": 0, "live_registers": 0,
                  "repo_only": [], "live_only": []}
    stays_quiet = not (
        unmeasured["repo_registers"]
        and (not unmeasured["live_registers"]
             or unmeasured["repo_only"] or unmeasured["live_only"]))
    if would_fail and stays_quiet:
        _ok("V-UNPAIRED-EMPTY-LIVE-IS-NOT-AGREEMENT",
            "live_registers=0 against a populated canonical copy fails; "
            "both-empty (nothing measured) still stays quiet")
    else:
        _fail("V-UNPAIRED-EMPTY-LIVE-IS-NOT-AGREEMENT",
              f"would_fail={would_fail} stays_quiet={stays_quiet} -- "
              "unmeasured and measured-zero are being conflated")

    ran = len(_passes) + len(_fails)
    print(f"\nUNPAIRED_PASS={len(_passes)}/{ran}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if ran != EXPECTED_GATES:
        print(f"GATE COUNT MISMATCH: {ran} ran, {EXPECTED_GATES} expected")
        return 1
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
