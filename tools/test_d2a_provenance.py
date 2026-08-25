"""V-gates for the D2A family provenance boundary.

Origin: an audit wrote vault/knowledge_base/ucr_cif/, committed it, and the engine then
scored the NEXT session's proposal against KB-UCR-CIF -- the auditor's own output acting
as the authority over its successor. These gates pin the boundary that stops it, including
the part that does NOT work, so a later reader cannot mistake the weaker half for the fix.

Hermetic: every assertion reads committed git history, which does not move between runs.
No wall-clock, no temp files, no writes into the tree a concurrent session may be using.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

from modules.duplicate_to_advantage import provenance as prov  # noqa: E402

KB = "vault/knowledge_base"
UCR = PP / KB / "ucr_cif"
UCR_BIRTH_REV = "a3a66a8"          # the commit that introduced ucr_cif

_p = _f = 0


def _ok(gate, ev):
    global _p
    _p += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, ev):
    global _f
    _f += 1
    print(f"  FAIL {gate}: {ev}")


def _with_cutoff(value, fn):
    """Run fn() with PP_AUDIT_CUTOFF set, restoring the environment afterwards."""
    old = os.environ.get(prov.CUTOFF_ENV)
    if value is None:
        os.environ.pop(prov.CUTOFF_ENV, None)
    else:
        os.environ[prov.CUTOFF_ENV] = value
    prov.reset_cache()
    try:
        return fn()
    finally:
        if old is None:
            os.environ.pop(prov.CUTOFF_ENV, None)
        else:
            os.environ[prov.CUTOFF_ENV] = old
        prov.reset_cache()


def _git_ok():
    """Reuse the module's own git resolver.

    A bare "git" is NOT on this host's non-interactive PowerShell PATH, so probing with
    one made every gate skip and the suite report 0/0 PASS at exit 0 -- a green run that
    asserted nothing, which is the same false-negative class this file exists to catch.
    Ask the code under test how it finds git, or the harness and the subject disagree.
    """
    exe = prov._git()
    if exe is None:
        return False
    try:
        r = subprocess.run([exe, "-C", str(PP), "rev-parse", "--git-dir"],
                           capture_output=True, timeout=20, check=False)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def main():
    if not _git_ok():
        print("SKIP: no git available; the boundary is fail-open by contract.")
        print("D2A_PROVENANCE_PASS=0/0  threshold=0/0")
        return 0

    # V-D2A-PROV-SEALED -- long-standing institutional capital stays a parent.
    r = _with_cutoff(None, lambda: prov.family_provenance(PP / KB / "crawl_os", PP, KB))
    if r["sealed"] and r["tracked"] > 0:
        _ok("V-D2A-PROV-SEALED", f"crawl_os sealed, {r['tracked']} tracked files")
    else:
        _fail("V-D2A-PROV-SEALED", f"crawl_os judged {r}")

    # V-D2A-PROV-UNTRACKED -- a directory git does not track is in-flight output.
    r = _with_cutoff(None, lambda: prov.family_provenance(
        PP / KB / "__no_such_family__", PP, KB))
    if not r["sealed"] and r["tracked"] == 0:
        _ok("V-D2A-PROV-UNTRACKED", r["reason"])
    else:
        _fail("V-D2A-PROV-UNTRACKED", f"expected not-sealed, got {r}")

    # V-D2A-PROV-TRACKED-IS-NOT-ENOUGH -- the half that does NOT close the case.
    # ucr_cif was committed, so tracked-ness alone admits it. Pinned deliberately: the
    # weaker signal must not be mistaken for the fix if someone later drops the cutoff.
    if UCR.is_dir():
        r = _with_cutoff(None, lambda: prov.family_provenance(UCR, PP, KB))
        if r["sealed"]:
            _ok("V-D2A-PROV-TRACKED-IS-NOT-ENOUGH",
                "committed audit output passes tracked-ness -- cutoff is the real boundary")
        else:
            _fail("V-D2A-PROV-TRACKED-IS-NOT-ENOUGH",
                  f"expected sealed under tracked-ness alone, got {r}")

        # V-D2A-PROV-CUTOFF -- a declared frontier excludes it, and only relative to
        # an audit that predates it. Both directions, or the gate proves nothing.
        before = _with_cutoff(f"{UCR_BIRTH_REV}^",
                              lambda: prov.family_provenance(UCR, PP, KB))
        after = _with_cutoff("bc81ca76cd8ef9ea78982c99016a03e979a91570",
                             lambda: prov.family_provenance(UCR, PP, KB))
        if not before["sealed"] and after["sealed"]:
            _ok("V-D2A-PROV-CUTOFF",
                f"excluded pre-birth ({before.get('born','?')}), retained for a later audit")
        else:
            _fail("V-D2A-PROV-CUTOFF",
                  f"pre-birth={before.get('sealed')} later={after.get('sealed')}")

        # V-D2A-PROV-ENGINE-WIRED -- the engine's live discovery path honours it.
        # A module nothing calls is documentation; this asserts the consumer.
        from modules.duplicate_to_advantage import d2a_engine as eng
        n_in = _with_cutoff(None, lambda: len(eng._discover_families()))
        fam_out = _with_cutoff(f"{UCR_BIRTH_REV}^", eng._discover_families)
        if "KB-UCR-CIF" not in fam_out and n_in > len(fam_out):
            _ok("V-D2A-PROV-ENGINE-WIRED",
                f"_discover_families {n_in} -> {len(fam_out)}, KB-UCR-CIF dropped")
        else:
            _fail("V-D2A-PROV-ENGINE-WIRED",
                  f"{n_in} -> {len(fam_out)}, KB-UCR-CIF present={('KB-UCR-CIF' in fam_out)}")
    else:
        _fail("V-D2A-PROV-CUTOFF", "ucr_cif absent; the replay case cannot be exercised")

    # V-D2A-PROV-FAILOPEN -- unknown provenance keeps the pre-existing behaviour.
    r = prov.family_provenance(Path("C:/") / "definitely_outside_repo", PP, KB)
    if r["sealed"]:
        _ok("V-D2A-PROV-FAILOPEN", r["reason"])
    else:
        _fail("V-D2A-PROV-FAILOPEN", f"expected fail-open sealed, got {r}")

    print(f"D2A_PROVENANCE_PASS={_p}/{_p + _f}  threshold={_p + _f}/{_p + _f}")
    return 0 if _f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
