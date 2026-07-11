#!/usr/bin/env python3
"""test_akos_integration.py -- done-gate for the AKOS knowledge integration.

V-gates (grep-able, per PP testing doctrine):
  V-AKOS-DOMAIN-MAP  : repo path component -> correct target domains
  V-AKOS-PARSE       : the real PP brief parses into domain-tagged units
  V-AKOS-SELECT      : selection respects target domains + per_domain/max caps
  V-AKOS-INJECTION   : jit run() on a PP cwd injects an AKOS block with units
  V-AKOS-FAILOPEN    : a missing/unreadable brief -> session starts normally
  V-AKOS-THROTTLE    : a 2nd run() in the same session does NOT re-inject
  V-AKOS-HARVESTER   : question_harvester on a PP cwd yields >=1 AKOS question
  V-AKOS-UNMAPPED    : an unmapped repo -> no injection (conservative policy)

Hermetic: uses a temp HOME-independent cwd for fail-open / unmapped cases and
the real PP brief (read-only) for the positive cases. State writes are routed
to a temp STATE_DIR via monkeypatch so re-runs are idempotent (x3 clean).

Run: python tools/test_akos_integration.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_PP_ROOT), str(_PP_ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


def _pp_cwd() -> str:
    """A cwd whose path component 'claude-power-pack' maps to the brief."""
    return str(_PP_ROOT)


def test_domain_map() -> None:
    from modules.akos_knowledge.akos import load_domain_map, resolve_domains
    cfg = load_domain_map()
    # Nested cwd must still resolve to the repo-root mapping.
    nested = _PP_ROOT / "modules" / "akos_knowledge"
    doms = resolve_domains(nested, cfg)
    if set(doms) == {"ai_automation", "scaling"}:
        _ok("V-AKOS-DOMAIN-MAP", f"nested cwd -> {doms}")
    else:
        _fail("V-AKOS-DOMAIN-MAP", f"expected ai_automation+scaling, got {doms}")
    # InfinityOps variant suffix must match via startswith.
    inf = resolve_domains(Path("C:/x/InfinityOps-bis-capab/sub"), cfg)
    if "saas" in inf and "sales" in inf:
        _ok("V-AKOS-DOMAIN-MAP", f"infinityops-variant -> {inf}")
    else:
        _fail("V-AKOS-DOMAIN-MAP", f"variant suffix not matched: {inf}")


def test_parse_and_select() -> None:
    from modules.akos_knowledge.akos import (
        find_brief, parse_brief, select_units,
    )
    brief = find_brief(_pp_cwd())
    if brief is None:
        _fail("V-AKOS-PARSE", "PP brief not found on disk")
        return
    units = parse_brief(brief.read_text(encoding="utf-8-sig", errors="replace"))
    domains = {u.domain for u in units}
    if len(units) >= 20 and "saas" in domains and "scaling" in domains:
        _ok("V-AKOS-PARSE", f"{len(units)} units, domains include {sorted(domains)[:4]}")
    else:
        _fail("V-AKOS-PARSE", f"weak parse: {len(units)} units, domains={domains}")
    sel = select_units(units, ["ai_automation", "scaling"],
                       max_units=6, per_domain=3)
    ok_caps = len(sel) <= 6 and all(u.domain in ("ai_automation", "scaling")
                                    for u in sel)
    per_dom_ok = sum(1 for u in sel if u.domain == "scaling") <= 3
    if sel and ok_caps and per_dom_ok:
        _ok("V-AKOS-SELECT", f"{len(sel)} units, caps honored, in-domain")
    else:
        _fail("V-AKOS-SELECT", f"cap/domain violation: {[u.domain for u in sel]}")


def _run_jit(cwd: str, session_id: str, tmp_state: Path) -> dict:
    import jit_skill_loader as jit
    jit.STATE_DIR = tmp_state
    # Route CO-12 telemetry to a temp dir too (no global writes).
    from modules.cognitive_os import co_12_telemetry as co12
    orig = co12._default_state_dir
    co12._default_state_dir = lambda: tmp_state / "co12"
    try:
        return jit.run({"prompt": "add a feature to the dashboard",
                        "cwd": cwd, "session_id": session_id})
    finally:
        co12._default_state_dir = orig


def test_injection_and_throttle() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp_state = Path(td) / "state"
        tmp_state.mkdir(parents=True, exist_ok=True)
        r1 = _run_jit(_pp_cwd(), "sess-akos-1", tmp_state)
        ac1 = (r1 or {}).get("additionalContext", "") or ""
        if "AKOS Knowledge (domain-matched" in ac1 and "[ai_automation]" in ac1:
            _ok("V-AKOS-INJECTION", "AKOS block present with domain-tagged unit")
        else:
            _fail("V-AKOS-INJECTION", f"no AKOS block in first run (len={len(ac1)})")
        # Second run, same session -> throttle (no re-inject).
        r2 = _run_jit(_pp_cwd(), "sess-akos-1", tmp_state)
        ac2 = (r2 or {}).get("additionalContext", "") or ""
        if "AKOS Knowledge (domain-matched" not in ac2:
            _ok("V-AKOS-THROTTLE", "2nd run in same session did not re-inject")
        else:
            _fail("V-AKOS-THROTTLE", "AKOS re-injected in same session")
        # CO-12 signal recorded on the first injection (A4).
        sig = tmp_state / "co12" / "signals.jsonl"
        if sig.is_file() and "akos_injection" in sig.read_text(encoding="utf-8"):
            _ok("V-AKOS-INJECTION", "CO-12 akos_injection signal recorded")
        else:
            _fail("V-AKOS-INJECTION", "CO-12 signal not recorded")


def test_failopen_and_unmapped() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp_state = Path(td) / "state"
        tmp_state.mkdir(parents=True, exist_ok=True)
        # Unmapped repo (temp dir name is not in the domain map) + no brief.
        r = _run_jit(td, "sess-akos-unmapped", tmp_state)
        if isinstance(r, dict) and r.get("continue", True) is not False:
            _ok("V-AKOS-FAILOPEN", "unmapped/no-brief cwd -> session continues")
        else:
            _fail("V-AKOS-FAILOPEN", f"unexpected block: {r}")
        ac = (r or {}).get("additionalContext", "") or ""
        if "AKOS Knowledge (domain-matched" not in ac:
            _ok("V-AKOS-UNMAPPED", "no AKOS block for unmapped repo")
        else:
            _fail("V-AKOS-UNMAPPED", "AKOS injected for unmapped repo")


def test_harvester() -> None:
    from modules.frontier_intelligence.question_harvester import _from_akos, harvest
    qs = _from_akos(_pp_cwd())
    akos_q = [q for q in qs if q.source == "akos"]
    if akos_q and akos_q[0].expected_asset == "hard_rule" \
            and akos_q[0].source_ref.startswith("akos:"):
        _ok("V-AKOS-HARVESTER", f"_from_akos -> {len(akos_q)} AKOS questions")
    else:
        _fail("V-AKOS-HARVESTER", f"no valid AKOS question: {qs[:1]}")
    # End-to-end harvest() must include the AKOS source without raising.
    allq = harvest(_pp_cwd())
    if any(q.source == "akos" for q in allq):
        _ok("V-AKOS-HARVESTER", f"harvest() includes AKOS ({len(allq)} total)")
    else:
        _fail("V-AKOS-HARVESTER", "harvest() dropped the AKOS source")


def main() -> int:
    print("== AKOS integration done-gate ==")
    for t in (test_domain_map, test_parse_and_select,
              test_injection_and_throttle, test_failopen_and_unmapped,
              test_harvester):
        try:
            t()
        except Exception as exc:  # a raising test is itself a failure
            _fail(t.__name__, f"raised {type(exc).__name__}: {exc}")
    total = _passes + _fails
    print(f"\nAKOS_PASS={_passes}/{total}  fails={_fails}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
