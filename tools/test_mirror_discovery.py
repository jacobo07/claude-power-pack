#!/usr/bin/env python3
"""test_mirror_discovery.py -- gates for the discovered mirror-pair producer.

The load-bearing gate is coverage: every pair the deleted literal list
declared must still be found, or the producer traded one blind spot for
another. The end-to-end gates build a throwaway git repo and a throwaway live
tree, so drift, inventory and strict mode are exercised against real `git
cat-file` output rather than a mock.

Run: python tools/test_mirror_discovery.py
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.mirror_discovery import discovery as md  # noqa: E402

HOME = Path.home()
LIVE = HOME / ".claude"
BUDGET_SEC = 15  # tools/verify_spp.py mirror-parity row budget

# The nine tuples tools/verify_global_mirrors.py carried until 2026-07-29.
# Kept here as historical evidence: the producer must not lose any of them.
LEGACY_PAIRS = [
    ("commands/ultra.md", "commands/ultra.md"),
    ("agents/oneshot-architect-auditor.md", "agents/oneshot-architect-auditor.md"),
    ("commands/cpp-resume-sovereign.md", "commands/resume-sovereign.md"),
    ("knowledge_vault/core/apex-completion-standard.md",
     "knowledge_vault/core/apex-completion-standard.md"),
    ("hooks/learning-sentinel.js", "hooks/learning-sentinel.js"),
    ("hooks/hook-dispatcher.js", "hooks/hook-dispatcher.js"),
    ("hooks/lazarus-livesnap.js", "hooks/lazarus-livesnap.js"),
    ("hooks/zero-issue-gate.js", "hooks/zero-issue-gate.js"),
    ("hooks/jobs-woz-gatekeeper.js", "hooks/jobs-woz-gatekeeper.js"),
]

_passes: list = []
_fails: list = []
_skips: list = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  [OK] {gate} -- {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  [X ] {gate} -- {diagnostic}")


def _skip(gate: str, why: str) -> None:
    _skips.append(gate)
    print(f"  [..] {gate} -- SKIP: {why}")


def _load_verifier():
    spec = importlib.util.spec_from_file_location(
        "vgm_under_test", PP_ROOT / "tools" / "verify_global_mirrors.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------- V-MIRROR-COVERS-LEGACY

def gate_covers_legacy() -> None:
    d = md.discover(PP_ROOT)
    missing = []
    skipped = []
    for live_rel, repo_rel in LEGACY_PAIRS:
        lp, rp = LIVE / live_rel, PP_ROOT / repo_rel
        if not lp.is_file() or not rp.is_file():
            skipped.append(live_rel)
            continue
        if not d.covers(lp, rp):
            missing.append(f"{live_rel} -> {repo_rel}")
    if missing:
        _fail("V-MIRROR-COVERS-LEGACY",
              f"producer lost {len(missing)} declared pair(s): {missing}")
        return
    checked = len(LEGACY_PAIRS) - len(skipped)
    note = f" ({len(skipped)} absent on this host)" if skipped else ""
    _ok("V-MIRROR-COVERS-LEGACY",
        f"{checked}/{checked} historically-declared pairs rediscovered{note}")


def gate_coverage_grows() -> None:
    d = md.discover(PP_ROOT)
    if len(d.pairs) <= len(LEGACY_PAIRS):
        _fail("V-MIRROR-COVERAGE-GROWS",
              f"discovered {len(d.pairs)} <= declared {len(LEGACY_PAIRS)}; "
              f"a producer that finds no more than the list buys nothing")
        return
    counts = d.domain_counts()
    per = ", ".join(f"{k}={v[md.PAIRED]}" for k, v in counts.items())
    _ok("V-MIRROR-COVERAGE-GROWS",
        f"{len(LEGACY_PAIRS)} declared -> {len(d.pairs)} discovered ({per}); "
        f"{d.unpaired_total} one-sided files now visible")


def gate_alias() -> None:
    d = md.discover(PP_ROOT)
    alias = [p for p in d.pairs if p.origin == "alias"]
    live_rel, repo_rel = next(iter(md.ALIASES.items()))
    if not (LIVE / live_rel).is_file() or not (PP_ROOT / repo_rel).is_file():
        _skip("V-MIRROR-ALIAS", f"{live_rel} absent on this host")
        return
    if not alias:
        _fail("V-MIRROR-ALIAS",
              "a pair whose sides carry different names was not produced; "
              "name-identity alone would silently drop it")
        return
    unpaired = {rel for _dom, rel in d.live_only} | {rel for _dom, rel in d.repo_only}
    leaked = [r for r in (Path(live_rel).name, Path(repo_rel).name)
              if r in unpaired]
    if leaked:
        _fail("V-MIRROR-ALIAS", f"alias halves also reported unpaired: {leaked}")
        return
    _ok("V-MIRROR-ALIAS",
        f"{len(alias)} alias pair(s) produced ({alias[0].label}); "
        f"neither half leaks into the unpaired inventory")


def gate_foreign_excluded() -> None:
    d = md.discover(PP_ROOT)
    unpaired = [rel for _dom, rel in d.live_only + d.repo_only]
    paired = [p.live.name for p in d.pairs]
    bad = [r for r in unpaired + paired
           if Path(r).name.startswith(md.FOREIGN_PREFIXES)]
    if bad:
        _fail("V-MIRROR-FOREIGN-EXCLUDED",
              f"{len(bad)} foreign file(s) entered the result: {bad[:4]}")
        return
    if not d.excluded:
        _skip("V-MIRROR-FOREIGN-EXCLUDED", "no foreign files on this host")
        return
    _ok("V-MIRROR-FOREIGN-EXCLUDED",
        f"{len(d.excluded)} file(s) from other tools excluded from pairs and "
        f"from the inventory")


# ------------------------------------------------------ V-MIRROR-SYNTHETIC

def gate_synthetic_classification() -> None:
    live = Path(tempfile.mkdtemp(prefix="mdlive-"))
    repo = Path(tempfile.mkdtemp(prefix="mdrepo-"))
    try:
        for root in (live, repo):
            (root / "hooks").mkdir(parents=True)
            (root / "commands").mkdir(parents=True)
        (live / "hooks" / "shared.js").write_text("x", encoding="utf-8")
        (repo / "hooks" / "shared.js").write_text("x", encoding="utf-8")
        (live / "hooks" / "only-live.js").write_text("x", encoding="utf-8")
        (repo / "hooks" / "only-repo.js").write_text("x", encoding="utf-8")
        (live / "hooks" / "gsd-foreign.js").write_text("x", encoding="utf-8")
        (live / "commands" / "shared.md").write_text("x", encoding="utf-8")
        (repo / "commands" / "shared.md").write_text("x", encoding="utf-8")

        d = md.discover(repo, live)
        paired = sorted(p.repo.name for p in d.pairs)
        lo = sorted(rel for _dom, rel in d.live_only)
        ro = sorted(rel for _dom, rel in d.repo_only)
        want = (["shared.js", "shared.md"], ["only-live.js"], ["only-repo.js"])
        if (paired, lo, ro) == want:
            _ok("V-MIRROR-SYNTHETIC",
                f"paired={paired} live_only={lo} repo_only={ro}; "
                f"foreign file classified into none of the three")
        else:
            _fail("V-MIRROR-SYNTHETIC",
                  f"got paired={paired} live_only={lo} repo_only={ro}, want {want}")
    finally:
        shutil.rmtree(live, ignore_errors=True)
        shutil.rmtree(repo, ignore_errors=True)


# ------------------------------------------------------ end-to-end with git

def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    mod = _load_verifier()
    return subprocess.run([mod._git_exe(), "-C", str(repo), *args],
                          capture_output=True, text=True, timeout=30)


def _make_repo(repo: Path) -> bool:
    init = _git(repo, "init", "-b", "main")
    if init.returncode != 0:
        return False
    _git(repo, "config", "user.email", "gate@example.invalid")
    _git(repo, "config", "user.name", "gate")
    _git(repo, "add", "-A")
    return _git(repo, "commit", "-m", "fixture").returncode == 0


def _e2e(drifted: bool, strict: bool = False):
    """Returns (rc, output) from check_pairs over throwaway trees."""
    live = Path(tempfile.mkdtemp(prefix="e2elive-"))
    repo = Path(tempfile.mkdtemp(prefix="e2erepo-"))
    prior = os.environ.get(md.ENV_LIVE_ROOT)
    try:
        (live / "hooks").mkdir(parents=True)
        (repo / "hooks").mkdir(parents=True)
        (live / "hooks" / "same.js").write_text("identical\n", encoding="utf-8")
        (repo / "hooks" / "same.js").write_text("identical\n", encoding="utf-8")
        (live / "hooks" / "pair.js").write_text("live side\n", encoding="utf-8")
        (repo / "hooks" / "pair.js").write_text(
            "repo side\n" if drifted else "live side\n", encoding="utf-8")
        (live / "hooks" / "only-live.js").write_text("l\n", encoding="utf-8")
        (repo / "hooks" / "only-repo.js").write_text("r\n", encoding="utf-8")
        if not _make_repo(repo):
            return None, "git unavailable"
        os.environ[md.ENV_LIVE_ROOT] = str(live)
        mod = _load_verifier()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = mod.check_pairs(str(repo), None, strict=strict)
        return rc, buf.getvalue()
    finally:
        if prior is None:
            os.environ.pop(md.ENV_LIVE_ROOT, None)
        else:
            os.environ[md.ENV_LIVE_ROOT] = prior
        shutil.rmtree(live, ignore_errors=True)
        shutil.rmtree(repo, ignore_errors=True)


def gate_e2e_drift() -> None:
    rc, out = _e2e(drifted=True)
    if rc is None:
        _skip("V-MIRROR-E2E-DRIFT", out)
        return
    if rc == 5 and "[DRIFT] pair.js" in out and "[OK] same.js" in out:
        _ok("V-MIRROR-E2E-DRIFT",
            "real git blobs: drifted pair reported, identical pair clean, exit 5")
    else:
        _fail("V-MIRROR-E2E-DRIFT", f"rc={rc} out={out[-260:]!r}")


def gate_e2e_clean_and_inventory() -> None:
    rc, out = _e2e(drifted=False)
    if rc is None:
        _skip("V-MIRROR-E2E-CLEAN", out)
        return
    onesided = "only-live.js" in out or "only-repo.js" in out
    if rc == 0 and not onesided:
        _ok("V-MIRROR-E2E-CLEAN",
            "two matching pairs plus one file on each side alone -> exit 0; "
            "one-sided files are inventory, never drift")
    else:
        _fail("V-MIRROR-E2E-CLEAN",
              f"rc={rc} onesided_in_failure_path={onesided} out={out[-260:]!r}")


def gate_e2e_strict() -> None:
    rc, out = _e2e(drifted=False, strict=True)
    if rc is None:
        _skip("V-MIRROR-E2E-STRICT", out)
        return
    if rc == 5 and "live-only:hooks/only-live.js" in out \
            and "repo-only:hooks/only-repo.js" in out:
        _ok("V-MIRROR-E2E-STRICT",
            "--strict promotes both one-sided files to failures, opt-in only")
    else:
        _fail("V-MIRROR-E2E-STRICT", f"rc={rc} out={out[-260:]!r}")


# ------------------------------------------------------------- source guards

def gate_no_literal_pairs() -> None:
    src = (PP_ROOT / "tools" / "verify_global_mirrors.py").read_text(
        encoding="utf-8")
    if "PAIRS = [" in src or "PAIRS=[" in src:
        _fail("V-MIRROR-NO-LITERAL-PAIRS",
              "a literal pair list is back in the verifier")
        return
    if "discover(" not in src:
        _fail("V-MIRROR-NO-LITERAL-PAIRS", "verifier does not call the producer")
        return
    _ok("V-MIRROR-NO-LITERAL-PAIRS",
        "verifier declares no pair tuples; only aliases and foreign prefixes "
        "remain declared, and both are decisions rather than observations")


def gate_budget() -> None:
    mod = _load_verifier()
    buf = io.StringIO()
    start = time.time()
    with contextlib.redirect_stdout(buf):
        mod.check_pairs(str(PP_ROOT), None)
    elapsed = time.time() - start
    pairs = md.discover(PP_ROOT).pairs
    if elapsed <= BUDGET_SEC:
        _ok("V-MIRROR-BUDGET",
            f"{len(pairs)} pairs verified in {elapsed:.2f}s "
            f"(budget {BUDGET_SEC}s; one cat-file batch per ref, not per pair)")
    else:
        _fail("V-MIRROR-BUDGET",
              f"{elapsed:.2f}s over the {BUDGET_SEC}s verify_spp budget")


def gate_batch_blobs() -> None:
    mod = _load_verifier()
    rels = ["tools/verify_global_mirrors.py", "does/not/exist.md"]
    got = mod.batch_blobs(str(PP_ROOT), "main", rels)
    real, reason_real = got.get(rels[0], (None, "absent"))
    fake, reason_fake = got.get(rels[1], (None, "absent"))
    if real and b"BL-0064" in real and fake is None and "missing" in str(reason_fake):
        _ok("V-MIRROR-BATCH-BLOBS",
            f"one subprocess returned {len(real)} B for a tracked path and a "
            f"clean '{reason_fake}' for an absent one")
    else:
        _fail("V-MIRROR-BATCH-BLOBS",
              f"real={bool(real)} reason_real={reason_real} "
              f"fake={bool(fake)} reason_fake={reason_fake}")


def main() -> int:
    print("Mirror Discovery Gates (Option B -- producer replaces literal list)")
    print("")
    gate_covers_legacy()
    gate_coverage_grows()
    gate_alias()
    gate_foreign_excluded()
    gate_synthetic_classification()
    gate_e2e_drift()
    gate_e2e_clean_and_inventory()
    gate_e2e_strict()
    gate_no_literal_pairs()
    gate_batch_blobs()
    gate_budget()
    total = len(_passes) + len(_fails)
    print("")
    print(f"MIRROR_DISCOVERY_PASS={len(_passes)}/{total}  skipped={len(_skips)}")
    return 0 if not _fails else 1


if __name__ == "__main__":
    sys.exit(main())
