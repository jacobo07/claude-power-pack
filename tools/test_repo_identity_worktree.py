#!/usr/bin/env python3
"""V-W3-IDENT-* -- repository self-identification must survive a git worktree.

Origin (UCR-CIF W3, 2026-09-19). The W2 handoff reported a standing FIOS/FD-07
warning: "FD flywheel: 0 portable deposits ... this frontier spend left no
reusable asset". It was not a missing asset. `federated_ledger._is_pp_repo`
tested `"claude-power-pack" in <path>`, and UCR-CIF runs from an ISOLATED
worktree at `C:/Users/User/Apps/pp-ucr-cif`, whose path does not carry the
repository's name. So the Power Pack failed to recognise itself and served
itself the advisory written for other repositories.

The subject here is the CLASS, not the string: identity by path substring is
broken by any checkout whose directory is not named after the repository, and a
linked worktree is that case by construction.

Two properties are pinned, and they pull in opposite directions on purpose:

  * `main_repo_root` RESOLVES a worktree to its repository (identity), and
  * `canonical_repo` does NOT (ledger keys stay per-worktree).

Collapsing them would rename every ledger on disk, which `identity.py:41`
refuses by name. A test that only checked the first would let that regression
through.

Run: python tools/test_repo_identity_worktree.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.repo_identity import canonical_repo, main_repo_root  # noqa: E402
from modules.fable_distillation.federated_ledger import (  # noqa: E402
    _is_pp_repo, fdi_advisory,
)

_PASS = 0
_FAIL = 0


def _ok(gate: str, evidence: str) -> None:
    global _PASS
    _PASS += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _FAIL
    _FAIL += 1
    print(f"  FAIL {gate}: {diagnostic}")


def _check(gate: str, cond: bool, evidence: str, diagnostic: str = "") -> None:
    if cond:
        _ok(gate, evidence)
    else:
        _fail(gate, diagnostic or evidence)


# --------------------------------------------------------------------------- #
# Real-subject half. This process is RUNNING inside a real linked worktree, so
# the git layout is observed, never assumed. A synthetic `.git` file could only
# confirm the format I already believe in.
# --------------------------------------------------------------------------- #
def real_worktree_half() -> None:
    print("\n[real worktree -- observed, not synthesised]")
    here = str(_PP_ROOT)
    marker = _PP_ROOT / ".git"

    is_linked = marker.is_file()
    if not is_linked:
        # Not a harness failure and not a pass: the class cannot be observed
        # from a normal checkout. Say so rather than reporting green.
        print(f"  SKIP V-W3-IDENT-REAL: {here} is not a linked worktree "
              f"(.git is not a file); real-subject half unobservable here")
        return

    resolved = main_repo_root(here)
    _check("V-W3-IDENT-REAL-RESOLVE",
           Path(resolved) != Path(here) and (Path(resolved) / ".git").is_dir(),
           f"worktree {here} -> main repo {resolved}",
           f"did not resolve to a main repo: got {resolved!r}")

    # The whole point: the checkout path does NOT contain the repo name, and the
    # resolved identity does. Asserting both makes the test about the class.
    _check("V-W3-IDENT-REAL-PATH-IS-BLIND",
           "claude-power-pack" not in here,
           f"checkout path carries no repo name: {here}",
           f"this worktree is NOT an instance of the class ({here}); "
           f"the regression it guards cannot be observed from here")

    _check("V-W3-IDENT-REAL-SELF",
           _is_pp_repo(here) is True,
           "_is_pp_repo(worktree) is True",
           "_is_pp_repo still blind to its own worktree")

    # Ledger keys must NOT move -- the migration identity.py:41 refuses.
    _check("V-W3-IDENT-LEDGER-KEY-UNMOVED",
           Path(canonical_repo(here)) == Path(here),
           f"canonical_repo unchanged ({canonical_repo(here)})",
           "canonical_repo now resolves the worktree away -- every per-repo "
           "ledger on disk would be renamed")


def behavioural_half() -> None:
    """The effect, not the predicate: does the advisory actually go quiet?"""
    print("\n[behavioural -- fdi_advisory]")
    with tempfile.TemporaryDirectory() as td:
        state = Path(td) / "state"
        state.mkdir()

        # (a) the Power Pack worktree: advisory must be silent.
        adv_pp = fdi_advisory(str(_PP_ROOT), state_dir=state)
        _check("V-W3-IDENT-ADVISORY-SILENT-ON-PP",
               adv_pp is None,
               "fdi_advisory(PP worktree) is None",
               f"still advising the Power Pack: {adv_pp!r}")

        # (b) NEGATIVE CONTROL. A genuine non-PP repository with zero deposits
        # must STILL be advised. Without this, "silence everywhere" passes (a)
        # perfectly -- solving the warning by deleting the feature.
        other = Path(td) / "some-other-project"
        (other / ".git").mkdir(parents=True)
        adv_other = fdi_advisory(str(other), state_dir=state)
        _check("V-W3-IDENT-ADVISORY-STILL-FIRES",
               isinstance(adv_other, str) and "FD flywheel" in adv_other,
               "a non-PP repo with 0 deposits is still advised",
               f"the advisory was disabled for everyone, not fixed: {adv_other!r}")

        # (c) the main checkout keeps its pre-existing answer.
        main = _main_checkout()
        if main is not None:
            adv_main = fdi_advisory(str(main), state_dir=state)
            _check("V-W3-IDENT-ADVISORY-MAIN-UNCHANGED",
                   adv_main is None,
                   f"fdi_advisory(main checkout) is None ({main})",
                   f"main checkout regressed: {adv_main!r}")


def _main_checkout() -> Path | None:
    marker = _PP_ROOT / ".git"
    if not marker.is_file():
        return _PP_ROOT if "claude-power-pack" in str(_PP_ROOT) else None
    resolved = Path(main_repo_root(str(_PP_ROOT)))
    return resolved if resolved.is_dir() else None


# --------------------------------------------------------------------------- #
# Synthetic half. Shapes a real worktree cannot show us here: a RELATIVE gitdir
# (git --relative-paths), a malformed marker, and a plain directory. These are
# about the resolver's failure modes, where fail-open is the contract.
# --------------------------------------------------------------------------- #
def synthetic_half() -> None:
    print("\n[synthetic -- resolver failure modes]")
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)

        # A fake main repo + a linked worktree written with an ABSOLUTE gitdir.
        main = base / "claude-power-pack"
        (main / ".git" / "worktrees" / "wt-abs").mkdir(parents=True)
        wt_abs = base / "pp-somewhere-else"
        wt_abs.mkdir()
        (wt_abs / ".git").write_text(
            f"gitdir: {(main / '.git' / 'worktrees' / 'wt-abs').as_posix()}\n",
            encoding="utf-8")
        _check("V-W3-IDENT-SYN-ABSOLUTE",
               Path(main_repo_root(str(wt_abs))) == main,
               f"absolute gitdir resolved to {main}",
               f"got {main_repo_root(str(wt_abs))!r}, expected {main}")
        _check("V-W3-IDENT-SYN-ABSOLUTE-ISPP",
               _is_pp_repo(str(wt_abs)) is True,
               "_is_pp_repo(synthetic worktree) is True",
               "predicate did not follow the resolver")

        # RELATIVE gitdir.
        (main / ".git" / "worktrees" / "wt-rel").mkdir(parents=True)
        wt_rel = base / "relative-checkout"
        wt_rel.mkdir()
        rel = os.path.relpath(main / ".git" / "worktrees" / "wt-rel", wt_rel)
        (wt_rel / ".git").write_text(f"gitdir: {rel}\n", encoding="utf-8")
        _check("V-W3-IDENT-SYN-RELATIVE",
               Path(main_repo_root(str(wt_rel))).resolve() == main.resolve(),
               f"relative gitdir {rel!r} resolved to {main}",
               f"got {main_repo_root(str(wt_rel))!r}, expected {main}")

        # Malformed marker -- must fall back, never raise.
        bad = base / "broken-checkout"
        bad.mkdir()
        (bad / ".git").write_text("this is not a gitdir pointer\n", encoding="utf-8")
        try:
            got = main_repo_root(str(bad))
            _check("V-W3-IDENT-SYN-MALFORMED",
                   Path(got) == bad,
                   "malformed .git falls back to the checkout itself",
                   f"expected {bad}, got {got!r}")
        except Exception as exc:  # noqa: BLE001
            _fail("V-W3-IDENT-SYN-MALFORMED", f"resolver raised: {exc!r}")

        # A gitdir that is NOT a worktree layout (e.g. a submodule-ish shape).
        sub = base / "submodule-ish"
        sub.mkdir()
        (sub / ".git").write_text(
            f"gitdir: {(main / '.git' / 'modules' / 'x').as_posix()}\n",
            encoding="utf-8")
        _check("V-W3-IDENT-SYN-NOT-WORKTREE",
               Path(main_repo_root(str(sub))) == sub,
               "a non-worktree gitdir shape is left alone",
               f"expected {sub}, got {main_repo_root(str(sub))!r}")

        # A plain directory with no VCS marker at all.
        plain = base / "plain"
        plain.mkdir()
        _check("V-W3-IDENT-SYN-NO-VCS",
               Path(main_repo_root(str(plain))) == Path(canonical_repo(str(plain))),
               "no VCS marker -> agrees with canonical_repo",
               f"diverged: {main_repo_root(str(plain))!r}")


def instrument_controls() -> None:
    """The sweep that found this class must be able to find it again."""
    print("\n[instrument controls]")
    src = (_PP_ROOT / "modules" / "fable_distillation"
           / "federated_ledger.py").read_text(encoding="utf-8", errors="replace")
    _check("V-W3-IDENT-CONTROL-FASTPATH",
           '"claude-power-pack" in text' in src,
           "the cheap substring fast path is still first",
           "fast path removed -- every normal checkout now pays path I/O")
    _check("V-W3-IDENT-CONTROL-RESOLVER-WIRED",
           "main_repo_root" in src,
           "_is_pp_repo consults the canonical resolver",
           "the resolver is no longer wired into the predicate")


def main() -> int:
    print("V-W3-IDENT -- repository identity under git worktrees")
    real_worktree_half()
    behavioural_half()
    synthetic_half()
    instrument_controls()
    total = _PASS + _FAIL
    print(f"\nIDENT_PASS={_PASS}/{total}  failures={_FAIL}")
    if total < 10:
        print("HARNESS-FAILED: fewer gates ran than this file defines")
        return 2
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
