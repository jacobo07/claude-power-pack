"""V-gates for the dependency sovereignty gate (UPAC residue R1).

Synthetic cases run against temporary roots so they are hermetic; the discovery
gate runs against the real repository, because a scanner proven only on fixtures
has not been proven to find anything.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

from modules.dependency_sovereignty import (  # noqa: E402
    DO_NOT_USE, MEASURED, REVIEW, UNKNOWN, UNREACHABLE_RUNGS, USE, WRAP,
    WRAP_THRESHOLD, manifest_coverage, scan,
)

_passes = 0
_fails = 0


def _ok(gate: str, ev: str) -> None:
    global _passes
    _passes += 1
    print(f"[PASS] {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global _fails
    _fails += 1
    print(f"[FAIL] {gate}: {ev}")


def _root(tmp: Path, manifest: str, body: str, lock: str | None = None,
          src: dict | None = None) -> Path:
    (tmp / manifest).write_text(body, encoding="utf-8")
    if lock is not None:
        (tmp / "package-lock.json").write_text(lock, encoding="utf-8")
    for rel, text in (src or {}).items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp


def t_discovers_real_repo() -> None:
    gate = "V-DSSE-DISCOVERS"
    deps = scan(PP)
    cov = manifest_coverage(PP)
    if deps and cov["found"]:
        _ok(gate, f"{len(deps)} declaration(s) across {len(cov['found'])} "
                  f"manifest(s) in the real repo")
    else:
        _fail(gate, f"deps={len(deps)} manifests={len(cov['found'])}")


def t_unpinned_no_lock_is_disqualifying() -> None:
    gate = "V-DSSE-UNPINNED-BLOCKED"
    with tempfile.TemporaryDirectory() as d:
        root = _root(Path(d), "requirements.txt", "somelib\n")
        deps = scan(root)
    got = [x.verdict for x in deps]
    if got == [DO_NOT_USE]:
        _ok(gate, "unpinned + no lockfile -> DO_NOT_USE")
    else:
        _fail(gate, f"verdicts={got}")


def t_use_requires_pin_and_lock() -> None:
    gate = "V-DSSE-USE-REQUIRES-BOTH"
    pkg = json.dumps({"dependencies": {"left-pad": "1.3.0"}})
    lock = json.dumps({"packages": {"": {}, "node_modules/left-pad": {}}})
    with tempfile.TemporaryDirectory() as d:
        both = scan(_root(Path(d), "package.json", pkg, lock=lock))
    with tempfile.TemporaryDirectory() as d:
        pin_only = scan(_root(Path(d), "package.json", pkg))
    v_both = [x.verdict for x in both]
    v_pin = [x.verdict for x in pin_only]
    surf = both[0].transitive_surface if both else None
    if v_both == [USE] and v_pin == [REVIEW] and surf == 1:
        _ok(gate, f"exact+lock -> USE (transitive={surf}); "
                  f"exact without lock -> REVIEW, never USE")
    else:
        _fail(gate, f"both={v_both} pin_only={v_pin} transitive={surf}")


def t_transitive_unknown_is_not_zero() -> None:
    gate = "V-DSSE-TRANSITIVE-UNKNOWN-NOT-ZERO"
    with tempfile.TemporaryDirectory() as d:
        deps = scan(_root(Path(d), "package.json",
                          json.dumps({"dependencies": {"left-pad": "1.3.0"}})))
    if deps and deps[0].transitive_surface is None:
        _ok(gate, "no lockfile -> transitive_surface is None (UNKNOWN), not 0")
    else:
        got = deps[0].transitive_surface if deps else "no-deps"
        _fail(gate, f"transitive_surface={got!r} -- 0 would read as 'no "
                    "transitive deps'")


def t_zero_call_sites_is_unknown_not_low() -> None:
    """The defect this gate exists for: a vps/ requirements file describes a
    REMOTE runtime, so zero local call sites means the usage is out of scan
    scope, not that the dependency is lightly used. It must never earn a
    favourable or actionable verdict."""
    gate = "V-DSSE-ZERO-SITES-IS-UNKNOWN"
    with tempfile.TemporaryDirectory() as d:
        deps = scan(_root(Path(d), "requirements.txt", "Pillow>=10.0\n"))
    if not deps:
        _fail(gate, "no dependency parsed")
        return
    dep = deps[0]
    if (dep.usage_state == UNKNOWN and dep.verdict == REVIEW
            and any("UNKNOWN, not low" in r for r in dep.reasons)):
        _ok(gate, "0 call sites -> usage_state=UNKNOWN, verdict=REVIEW, and the "
                  "report says so rather than implying light usage")
    else:
        _fail(gate, f"usage_state={dep.usage_state} verdict={dep.verdict}")


def t_wrap_requires_observed_usage() -> None:
    gate = "V-DSSE-WRAP-NEEDS-OBSERVED-USAGE"
    src = {f"m{i}.py": "import httpx\n" for i in range(WRAP_THRESHOLD + 1)}
    with tempfile.TemporaryDirectory() as d:
        deps = scan(_root(Path(d), "requirements.txt", "httpx>=0.27\n", src=src))
    if not deps:
        _fail(gate, "no dependency parsed")
        return
    dep = deps[0]
    if (dep.verdict == WRAP and dep.usage_state == MEASURED
            and dep.internal_call_sites >= WRAP_THRESHOLD):
        _ok(gate, f"{dep.internal_call_sites} observed call sites "
                  f"(>= {WRAP_THRESHOLD}) -> WRAP, on MEASURED usage only")
    else:
        _fail(gate, f"verdict={dep.verdict} sites={dep.internal_call_sites} "
                    f"state={dep.usage_state}")


def t_coverage_reports_unparsed() -> None:
    gate = "V-DSSE-COVERAGE-HONEST"
    # A package.json with no `dependencies` key: parsed fine, yielded nothing.
    # 'Parsed to empty' and 'unsupported layout' must not look alike.
    with tempfile.TemporaryDirectory() as d:
        root = _root(Path(d), "package.json", json.dumps({"name": "x"}))
        cov = manifest_coverage(root)
    if cov["found"] and cov["yielded_nothing"] == cov["found"]:
        _ok(gate, "a manifest yielding no dependency is reported, not silently "
                  "counted as dependency-free")
    else:
        _fail(gate, f"found={cov['found']} empty={cov['yielded_nothing']}")


def t_unreachable_rungs_declared() -> None:
    gate = "V-DSSE-UNREACHABLE-DECLARED"
    required = {"CONNECT", "EXTEND", "FORK", "REPLACE", "INTERNALIZE"}
    missing = required - set(UNREACHABLE_RUNGS)
    unreasoned = [k for k, v in UNREACHABLE_RUNGS.items() if not str(v).strip()]
    if not missing and not unreasoned:
        _ok(gate, f"{len(UNREACHABLE_RUNGS)} rungs declared unreachable, each "
                  "with a stated reason (INTERNALIZE included -- it was emitted "
                  "and withdrawn after recommending 'internalize Pillow')")
    else:
        _fail(gate, f"missing={sorted(missing)} unreasoned={unreasoned}")


def t_gate_exit_code() -> None:
    gate = "V-DSSE-GATE-EXITS"
    with tempfile.TemporaryDirectory() as d:
        root = _root(Path(d), "requirements.txt", "somelib\n")
        cp = subprocess.run(
            [sys.executable, "-m", "modules.dependency_sovereignty.sovereignty",
             "--gate", "--root", str(root)],
            cwd=str(PP), capture_output=True, text=True, timeout=120)
    if cp.returncode == 1 and DO_NOT_USE in cp.stdout:
        _ok(gate, "--gate exits 1 when a DO_NOT_USE is present")
    else:
        _fail(gate, f"rc={cp.returncode} stdout_has_verdict="
                    f"{DO_NOT_USE in cp.stdout}")


def t_failopen_on_garbage() -> None:
    gate = "V-DSSE-FAILOPEN"
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "package.json").write_text("{not json at all", encoding="utf-8")
        (root / "pyproject.toml").write_text("\x00\x01 binary junk", encoding="utf-8")
        try:
            deps = scan(root)
            cov = manifest_coverage(root)
        except Exception as e:  # noqa: BLE001
            _fail(gate, f"raised {type(e).__name__}: {e}")
            return
    if deps == [] and len(cov["yielded_nothing"]) == 2:
        _ok(gate, "malformed manifests -> no raise, 0 dependencies, and BOTH "
                  "reported as yielding nothing")
    else:
        _fail(gate, f"deps={len(deps)} empty={cov['yielded_nothing']}")


def main() -> int:
    for t in (t_discovers_real_repo,
              t_unpinned_no_lock_is_disqualifying,
              t_use_requires_pin_and_lock,
              t_transitive_unknown_is_not_zero,
              t_zero_call_sites_is_unknown_not_low,
              t_wrap_requires_observed_usage,
              t_coverage_reports_unparsed,
              t_unreachable_rungs_declared,
              t_gate_exit_code,
              t_failopen_on_garbage):
        t()
    total = _passes + _fails
    verdict = "PASS" if _fails == 0 else "FAIL"
    print(f"DSSE_PASS={_passes}/{total}  threshold={total}/{total}  "
          f"VERDICT={verdict}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
