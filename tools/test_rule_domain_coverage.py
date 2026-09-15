"""Rule-domain coverage and ownership gates.

`~/.claude/rules/` is a GLOBAL USER surface that Power Pack SHARES rather than
owns: 2 of its 11 files are PP mirrors, 9 were written by sessions in other
repositories. Until 2026-09-15 the census could not see the directory at all,
because `DOMAINS` is a hand-typed tuple and an aperture cannot report what it
never enumerates.

This file holds the three claims that extension has to earn:

  * the foreign nine are LISTED, never ACCUSED       (negative control)
  * a PP-produced rule with no source IS detected    (positive control)
  * a new live directory cannot become invisible     (aperture ratchet)

The positive control uses a SYNTHETIC subject on purpose. `/cpp-compound`'s
global pass has never run -- `last_run_global: null` -- so PP's own live-only
rule population is empty, and a drill pinned to a real offender would have
nothing to assert. An empty offender list satisfies a completeness claim
whether or not the check still works; that is exactly the state this file
exists to make impossible.

Evidence: vault/audits/live-rule-ownership-2026-09-15.md
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP_ROOT))

from modules.mirror_discovery import discovery as MD  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [OK] {gate} -- {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate} -- {diagnostic}")


# The two repo rules that have ever mirrored. Anchored by NAME, not by a
# count: a count is satisfied by deleting one and adding another.
PP_MIRRORED_RULES = ("common/code-review.md", "python/testing.md")

# A floor on the live directory population, so a sweep that silently matched
# nothing cannot report a clean bill. The real tree held 53 on 2026-09-15.
LIVE_DIR_FLOOR = 30


def _live_dirs(live_root: Path) -> set[str]:
    return {p.name for p in live_root.iterdir() if p.is_dir()}


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


# --------------------------------------------------------------------------
# 1. The domain exists at all.
# --------------------------------------------------------------------------
def gate_domain_present() -> None:
    names = [d for d, _ in MD.DOMAINS]
    if "rules" in names:
        _ok("V-RULES-DOMAIN-PRESENT", f"DOMAINS = {names}")
    else:
        _fail("V-RULES-DOMAIN-PRESENT",
              f"rules absent from DOMAINS; live doctrine is invisible ({names})")


# --------------------------------------------------------------------------
# 2. The PP-owned rules pair. Floor by name.
# --------------------------------------------------------------------------
def gate_paired_floor() -> None:
    d = MD.discover(PP_ROOT)
    paired = {p.repo.as_posix().split("/rules/", 1)[-1]
              for p in d.pairs if p.domain == "rules"}
    missing = [r for r in PP_MIRRORED_RULES if r not in paired]
    if missing:
        _fail("V-RULES-PAIRED-FLOOR",
              f"PP-owned rule(s) no longer pair: {missing}; paired={sorted(paired)}")
    else:
        _ok("V-RULES-PAIRED-FLOOR",
            f"{len(PP_MIRRORED_RULES)} PP rules paired by name: "
            f"{list(PP_MIRRORED_RULES)}")


# --------------------------------------------------------------------------
# 3. The census aperture must NOT become the deployment aperture.
#
# Adding a domain ARMS install_global_core._repo_population for it. This gate
# pins the separation and also PROVES the hazard is real rather than
# theoretical, by measuring what would ship if the separation were lost.
# --------------------------------------------------------------------------
def gate_not_shippable() -> None:
    src = (PP_ROOT / "tools" / "install_global_core.py").read_text(
        encoding="utf-8")
    line = next((ln.strip() for ln in src.splitlines()
                 if ln.strip().startswith("SHIPPABLE_KINDS")), None)
    if line is None:
        _fail("V-RULES-NOT-SHIPPABLE",
              "SHIPPABLE_KINDS not found in install_global_core.py; the "
              "separation this gate pins may have been renamed away")
        return
    if "rules" in line:
        _fail("V-RULES-NOT-SHIPPABLE",
              f"rules is SHIPPABLE: {line} -- a clean install would write this "
              f"repo's rule tree into the operator's global home")
        return

    import tools.install_global_core as IGC
    would_ship = IGC._repo_population(PP_ROOT, "rules")
    n = len(would_ship or {})
    if n < 50:
        _fail("V-RULES-NOT-SHIPPABLE",
              f"population for rules resolved to {n}; expected the repo's full "
              f"rule tree. The hazard this gate guards may be unmeasurable, "
              f"which makes the green meaningless")
        return
    _ok("V-RULES-NOT-SHIPPABLE",
        f"{line}; population resolves {n} rule sources that stay unshipped "
        f"(hazard real, separation held)")


# --------------------------------------------------------------------------
# 4 + 5. Both poles, on one synthetic tree.
#
# Foreign rule (no frontmatter, like the real nine) -> listed, not owned.
# PP-produced rule (origin: unattended-compound) with no repo source -> owned
# and detected. Neither pole can pass while the other is broken.
# --------------------------------------------------------------------------
def gate_ownership_poles() -> None:
    with tempfile.TemporaryDirectory(prefix="pp-rules-poles-") as tmp:
        live = Path(tmp) / "live"
        _write(live / "rules" / "foreign-doctrine.md",
               "# Foreign Doctrine\n\nWritten by another repo's session.\n\n"
               "## Source\n\n**2026-09-10** (Some Other Project).\n")
        _write(live / "rules" / "pp-produced.md",
               "---\norigin: unattended-compound\n"
               "run_at: 2026-09-15T12:00:00Z\n"
               "source_project: C:/somewhere\nsignal_count: 5\n---\n\n"
               "# PP Produced\n\nMaterialised by /cpp-compound.\n")

        d = MD.discover(PP_ROOT, live)
        live_only = {rel for dom, rel in d.live_only if dom == "rules"}
        owned = MD.pp_owned_live_only(PP_ROOT, live)
        owned_names = {rel for rel, _ in owned}

        # Negative pole: the foreign rule is inventory, not a PP defect.
        if "foreign-doctrine.md" not in live_only:
            _fail("V-RULES-FOREIGN-NOT-DEFECT",
                  "foreign rule was not even listed as live-only inventory")
        elif "foreign-doctrine.md" in owned_names:
            _fail("V-RULES-FOREIGN-NOT-DEFECT",
                  "foreign rule was claimed as PP-owned -- coverage expansion "
                  "has become ownership pollution")
        else:
            _ok("V-RULES-FOREIGN-NOT-DEFECT",
                "unstamped foreign rule listed as inventory, claimed by nobody")

        # Positive pole: a PP-produced rule with no source is detected.
        if "pp-produced.md" in owned_names:
            origin = dict(owned)["pp-produced.md"]
            _ok("V-RULES-PP-OWNED-DETECTED",
                f"PP-produced rule with no repo source detected "
                f"(origin={origin})")
        else:
            _fail("V-RULES-PP-OWNED-DETECTED",
                  f"a rule stamped origin:unattended-compound with no repo "
                  f"source went UNDETECTED; owned={sorted(owned_names)}. This "
                  f"is the exact artifact /cpp-compound will create on its "
                  f"first global run")

        # The discriminator must be the stamp, not the directory.
        if len(owned_names) == 1:
            _ok("V-RULES-OWNERSHIP-DISCRIMINATES",
                "2 unsourced live rules, exactly 1 claimed -- the marker "
                "separates them, not their location")
        else:
            _fail("V-RULES-OWNERSHIP-DISCRIMINATES",
                  f"expected exactly 1 of 2 unsourced rules claimed, got "
                  f"{sorted(owned_names)}")


# --------------------------------------------------------------------------
# 6. Real-tree control: PP owns no unsourced live rule TODAY.
# --------------------------------------------------------------------------
def gate_real_estate_clean() -> None:
    owned = MD.pp_owned_live_only(PP_ROOT)
    if owned:
        _fail("V-RULES-PP-OWNED-ZERO",
              f"PP-produced live rules with no repo source: {owned}. PP wrote "
              f"these and cannot restore them")
    else:
        d = MD.discover(PP_ROOT)
        n = sum(1 for dom, _ in d.live_only if dom == "rules")
        _ok("V-RULES-PP-OWNED-ZERO",
            f"0 PP-produced unsourced rules; the {n} live-only rules present "
            f"carry no PP origin stamp and are not PP's to restore")


# --------------------------------------------------------------------------
# 7 + 8 + 9. The aperture ratchet -- the fifth-recurrence prevention.
# --------------------------------------------------------------------------
def gate_aperture_declared() -> None:
    live_root = MD.resolve_live_root()
    if not live_root.is_dir():
        _fail("V-RULES-APERTURE-DECLARED",
              f"live root {live_root} is not a directory; aperture unmeasurable")
        return
    dirs = _live_dirs(live_root)

    if len(dirs) < LIVE_DIR_FLOOR:
        _fail("V-RULES-APERTURE-FLOOR",
              f"only {len(dirs)} live directories found (floor "
              f"{LIVE_DIR_FLOOR}); the sweep probably matched nothing, and an "
              f"empty sweep reports the same green as a clean one")
    else:
        _ok("V-RULES-APERTURE-FLOOR",
            f"{len(dirs)} live directories enumerated")

    declared = {d for d, _ in MD.DOMAINS} | set(MD.NON_DOMAINS)
    undeclared = sorted(dirs - declared)
    if undeclared:
        _fail("V-RULES-APERTURE-DECLARED",
              f"live directories neither a domain nor a declared non-domain: "
              f"{undeclared}. Decide which each is -- an artifact class that "
              f"nobody classified is how rules/ stayed invisible")
    else:
        _ok("V-RULES-APERTURE-DECLARED",
            f"all {len(dirs)} live directories classified "
            f"({len(MD.DOMAINS)} domains, {len(MD.NON_DOMAINS)} non-domains)")

    stale = sorted(set(MD.NON_DOMAINS) - dirs)
    if stale:
        _fail("V-RULES-APERTURE-STALE",
              f"declared non-domains that no longer exist: {stale}. A list "
              f"describing deleted directories reads exactly like one "
              f"describing covered ones")
    else:
        _ok("V-RULES-APERTURE-STALE",
            f"no stale entries; all {len(MD.NON_DOMAINS)} declared "
            f"non-domains exist")


def gate_aperture_red_branch() -> None:
    """Drive the red branch on a synthetic tree, not on a real defect."""
    with tempfile.TemporaryDirectory(prefix="pp-aperture-red-") as tmp:
        live = Path(tmp) / "live"
        for name in ("hooks", "commands", "agents", "knowledge_vault", "rules"):
            (live / name).mkdir(parents=True, exist_ok=True)
        for name in list(MD.NON_DOMAINS)[:5]:
            (live / name).mkdir(parents=True, exist_ok=True)

        declared = {d for d, _ in MD.DOMAINS} | set(MD.NON_DOMAINS)

        clean = sorted(_live_dirs(live) - declared)
        if clean:
            _fail("V-RULES-APERTURE-RED",
                  f"control tree was already dirty: {clean}")
            return

        (live / "brand-new-artifact-class").mkdir()
        caught = sorted(_live_dirs(live) - declared)
        if caught == ["brand-new-artifact-class"]:
            _ok("V-RULES-APERTURE-RED",
                "undeclared live directory detected; clean control stayed "
                "clean, so the detector discriminates rather than always firing")
        else:
            _fail("V-RULES-APERTURE-RED",
                  f"a new undeclared directory was NOT caught: {caught}")


def main() -> int:
    print("Rule-domain coverage and ownership")
    print("-" * 68)
    gate_domain_present()
    gate_paired_floor()
    gate_not_shippable()
    gate_ownership_poles()
    gate_real_estate_clean()
    gate_aperture_declared()
    gate_aperture_red_branch()
    total = _passes + _fails
    print("-" * 68)
    print(f"RULE_DOMAIN_PASS={_passes}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
