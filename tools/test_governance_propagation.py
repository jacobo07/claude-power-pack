"""V-gates for PP Governance Propagation (BL-GOV-PROP-001 / SCS C43).

Proves the PP governance systems (SDD-OS tiers + spec requirement, Setup-OS
scan) fire in ANY repo via the proactive dispatcher's cross-repo rail -- not
only inside the PP repo.

Hermetic by construction: every gate uses a fresh tempfile.mkdtemp() repo (no
spec, unique path) so classify_tier / check_spec_gate / the Setup-OS registry
are deterministic and host-independent. The one registry round-trip
(V-SETUP-SCAN-SILENT) saves to the REAL registry under a unique-hash filename
and unlinks it in a finally, so back-to-back runs stay clean (the
V-CPC-RESTART flaky-gate lesson).

Run: python tools/test_governance_propagation.py  ->  GOV_PROP_PASS=7/7
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parent.parent
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.signals import sdd_tier, setup_scan  # noqa: E402
from modules.setup_os import registry  # noqa: E402
from modules.setup_os.scanner import scan  # noqa: E402
from modules.pp_agents import proactive_dispatcher as dispatcher  # noqa: E402

passes = 0
fails = 0


def _ok(gate: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"OK   {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def main() -> int:
    # An external repo: a unique tmp dir, NOT the PP repo, NO spec, NO profile.
    ext = tempfile.mkdtemp(prefix="gov-prop-ext-")

    # V-SDD-FIRES-CROSS-REPO -- Tier 2 prompt in an external cwd -> advisory.
    sig = sdd_tier.evaluate("build user auth", ext, "ext")
    if (sig is not None and sig.agent_name == "pp-sdd-tier"
            and "Tier 2" in sig.advisory):
        _ok("V-SDD-FIRES-CROSS-REPO",
            f"build user auth @ {Path(ext).name} -> Tier 2 advisory")
    else:
        _fail("V-SDD-FIRES-CROSS-REPO", f"no Tier-2 advisory: {sig!r}")

    # V-SDD-SILENT-TIER0 -- trivial prompt -> silence (Tier 0).
    if sdd_tier.evaluate("fix typo", ext, "ext") is None:
        _ok("V-SDD-SILENT-TIER0", "fix typo -> silence")
    else:
        _fail("V-SDD-SILENT-TIER0", "fix typo wrongly fired")

    # V-SETUP-SCAN-ADVISORY -- an un-profiled repo -> /scan-repo advisory.
    s = setup_scan.evaluate(ext, "ext")
    if s is not None and s.agent_name == "pp-setup-scan":
        _ok("V-SETUP-SCAN-ADVISORY", "unscanned repo -> scan advisory")
    else:
        _fail("V-SETUP-SCAN-ADVISORY", f"no advisory: {s!r}")

    # V-SETUP-SCAN-SILENT -- once profiled (real registry round-trip) -> silent.
    saved = None
    try:
        saved = registry.save_profile(ext, {"project_name": "ext", "stub": True})
        s2 = setup_scan.evaluate(ext, "ext")
        if s2 is None:
            _ok("V-SETUP-SCAN-SILENT", "profiled repo -> silence")
        else:
            _fail("V-SETUP-SCAN-SILENT", f"fired despite profile: {s2!r}")
    finally:
        try:
            if saved is not None:
                Path(saved).unlink()
        except OSError:
            pass

    # V-SCANREPO-CROSS-REPO -- scan reflects the EXTERNAL repo, not the PP repo.
    (Path(ext) / "package.json").write_text(
        '{"dependencies": {"react": "^18.0.0"}}', encoding="utf-8")
    prof = scan(ext)
    repo_path = prof.repo_path.value
    fw = prof.framework_primary.value
    if (Path(repo_path).resolve() == Path(ext).resolve()
            and str(PP_ROOT) not in str(repo_path) and fw == "React"):
        _ok("V-SCANREPO-CROSS-REPO",
            f"scan -> repo_path={Path(repo_path).name}, framework={fw}")
    else:
        _fail("V-SCANREPO-CROSS-REPO",
              f"scan leaked/wrong: repo_path={repo_path} fw={fw}")

    # V-THROTTLE-RESPECTED -- the no-spam cooldowns are wired as specified.
    cfg = dispatcher.AGENT_CONFIGS
    sdd_cd = getattr(cfg.get("pp-sdd-tier"), "cooldown_minutes", None)
    setup_cd = getattr(cfg.get("pp-setup-scan"), "cooldown_minutes", None)
    if sdd_cd == 5 and setup_cd == 1440:
        _ok("V-THROTTLE-RESPECTED", "sdd_tier=5m, setup_scan=1440m")
    else:
        _fail("V-THROTTLE-RESPECTED",
              f"sdd_tier={sdd_cd} setup_scan={setup_cd}")

    # V-BASELINE-INTACT -- dispatcher + retained spec_compliance still import.
    try:
        from modules.pp_agents.signals import spec_compliance  # noqa: F401
        assert callable(dispatcher.dispatch)
        assert callable(dispatcher.dispatch_to_additional_context)
        _ok("V-BASELINE-INTACT", "dispatcher + spec_compliance import clean")
    except Exception as exc:  # noqa: BLE001
        _fail("V-BASELINE-INTACT", f"import regression: {exc}")

    total = passes + fails
    print(f"\nGOV_PROP_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
