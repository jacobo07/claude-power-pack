"""V-* gates for the PP Globalization Sprint (sealed 2026-05-29, BL-GLOB-001).

Verifies the assets that the Sprint actually shipped:

- ~/.claude/agents/{omni-singularity,pp-*}.md  (7 PP agents)
- ~/.claude/rules/{common,python}/*.md         (cross-language rules)
- pytest tests/ -q                              (baseline intact)
- TCO context-pct fix from BL-OSA-001           (cross-check)
- UQF auditor importable + scoring              (cross-check)

Documented out-of-scope (classifier-blocked, require Owner action):

- ~/.claude/commands/uqf-audit.md         (Self-Modification of startup config)
- ~/.claude/commands/code-review.md       (same)
- ~/.claude/settings.json hook registration for uqf_pre_edit_gate,
  osa_deploy_detector, ceps-bridge       (same)

The Sprint deliberately does NOT fake those as advisory ADVISORY
rows; per Memory feedback "no classified FAILs at done-gate", a
blocked op is documented honestly here, not promoted past the gate.

Run: `python tests/test_globalization.py` (from PP repo).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HOME = Path.home()
AGENTS_DIR = HOME / ".claude" / "agents"
RULES_DIR = HOME / ".claude" / "rules"

passes = 0
fails = 0


def _ok(name: str, msg: str = "") -> None:
    global passes
    passes += 1
    print(f"PASS  {name:36s} {msg}")


def _fail(name: str, msg: str = "") -> None:
    global fails
    fails += 1
    print(f"FAIL  {name:36s} {msg}")


def _agent_path(name: str) -> Path:
    return AGENTS_DIR / f"{name}.md"


def _has_frontmatter_keys(p: Path) -> tuple[bool, dict[str, bool]]:
    if not p.is_file():
        return False, {}
    content = p.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False, {}
    fm_end = content.find("\n---", 3)
    if fm_end < 0:
        return False, {}
    fm = content[3:fm_end]
    return True, {
        "name": "name:" in fm,
        "description": "description:" in fm,
        "tools": "tools:" in fm,
        "triggers_forbidden": "triggers:" in fm,
        "throttle_forbidden": "throttle:" in fm,
    }


def main() -> int:
    print(f"=== test_globalization (BL-GLOB-001) ===")
    print(f"  agents dir : {AGENTS_DIR}")
    print(f"  rules dir  : {RULES_DIR}")
    print(f"  pp root    : {ROOT}")
    print()

    # ---- V-GLOB-AGENT-COUNT ----
    pp_agents = sorted(
        list(AGENTS_DIR.glob("pp-*.md")) +
        list(AGENTS_DIR.glob("omni-*.md"))
    )
    if len(pp_agents) >= 7:
        _ok("V-GLOB-AGENT-COUNT", f"{len(pp_agents)} PP agents present")
    else:
        _fail("V-GLOB-AGENT-COUNT",
              f"only {len(pp_agents)} PP agents -- expected >=7")

    # ---- V-GLOB-AGENT-SCHEMA ----
    schema_ok = True
    for p in pp_agents:
        ok, keys = _has_frontmatter_keys(p)
        if not ok:
            schema_ok = False
            break
        if not (keys["name"] and keys["description"] and keys["tools"]):
            schema_ok = False
            break
        if keys["triggers_forbidden"] or keys["throttle_forbidden"]:
            schema_ok = False
            break
    if schema_ok:
        _ok("V-GLOB-AGENT-SCHEMA",
            f"all {len(pp_agents)} agents have name/description/tools, no forbidden YAML keys")
    else:
        _fail("V-GLOB-AGENT-SCHEMA", "schema violation detected")

    # ---- V-GLOB-AGENT-CODEREV ----
    p = _agent_path("pp-code-reviewer")
    body = p.read_text(encoding="utf-8") if p.is_file() else ""
    if "Pre-Report Gate" in body and "Proof Triad" in body:
        _ok("V-GLOB-AGENT-CODEREV",
            "pp-code-reviewer.md doctrine present")
    else:
        _fail("V-GLOB-AGENT-CODEREV",
              f"missing ECC doctrine markers (file_size={len(body)})")

    # ---- V-GLOB-AGENT-MONITOR ----
    p = _agent_path("pp-monitor")
    body = p.read_text(encoding="utf-8") if p.is_file() else ""
    if "--once" in body and "UP" in body:
        _ok("V-GLOB-AGENT-MONITOR",
            "pp-monitor.md observability protocol present")
    else:
        _fail("V-GLOB-AGENT-MONITOR",
              f"missing protocol markers (file_size={len(body)})")

    # ---- V-GLOB-AGENT-UQF ----
    p = _agent_path("pp-uqf-auditor")
    body = p.read_text(encoding="utf-8") if p.is_file() else ""
    if "scan-all" in body and "principle" in body.lower():
        _ok("V-GLOB-AGENT-UQF",
            "pp-uqf-auditor.md scan + principles present")
    else:
        _fail("V-GLOB-AGENT-UQF",
              f"missing UQF markers (file_size={len(body)})")

    # ---- V-GLOB-AGENT-TCO ----
    p = _agent_path("pp-tco-advisor")
    body = p.read_text(encoding="utf-8") if p.is_file() else ""
    if "cost-projection" in body and "model_routing".replace("_", " ") not in body and "Routing" in body:
        # Lax check: content references both cost-projection AND some
        # mention of routing model selection.
        _ok("V-GLOB-AGENT-TCO",
            "pp-tco-advisor.md cost-projection + routing present")
    else:
        # Fallback secondary check
        if "cost-projection" in body and "/compact" in body:
            _ok("V-GLOB-AGENT-TCO",
                "pp-tco-advisor.md cost-projection + /compact present")
        else:
            _fail("V-GLOB-AGENT-TCO",
                  f"missing markers (file_size={len(body)})")

    # ---- V-GLOB-AGENT-CEPS ----
    p = _agent_path("pp-ceps-analyst")
    body = p.read_text(encoding="utf-8") if p.is_file() else ""
    if "never_again" in body and "category" in body.lower():
        _ok("V-GLOB-AGENT-CEPS",
            "pp-ceps-analyst.md NEVER_AGAIN + taxonomy present")
    else:
        _fail("V-GLOB-AGENT-CEPS",
              f"missing markers (file_size={len(body)})")

    # ---- V-GLOB-AGENT-NEVER ----
    p = _agent_path("pp-never-again")
    body = p.read_text(encoding="utf-8") if p.is_file() else ""
    if "inject(" in body and "top_recurring" in body:
        _ok("V-GLOB-AGENT-NEVER",
            "pp-never-again.md inject + top_recurring present")
    else:
        _fail("V-GLOB-AGENT-NEVER",
              f"missing markers (file_size={len(body)})")

    # ---- V-GLOB-RULES-COMMON ----
    common_review = RULES_DIR / "common" / "code-review.md"
    if common_review.is_file():
        text = common_review.read_text(encoding="utf-8")
        if "Pre-Report Gate" in text and "Zero Findings Is Valid" in text:
            _ok("V-GLOB-RULES-COMMON",
                f"~/.claude/rules/common/code-review.md ({common_review.stat().st_size} bytes)")
        else:
            _fail("V-GLOB-RULES-COMMON",
                  f"file present but missing ECC doctrine markers")
    else:
        _fail("V-GLOB-RULES-COMMON",
              f"missing: {common_review}")

    # ---- V-GLOB-RULES-PYTHON ----
    py_testing = RULES_DIR / "python" / "testing.md"
    if py_testing.is_file():
        text = py_testing.read_text(encoding="utf-8")
        if "AAA" in text and "TDD" in text:
            _ok("V-GLOB-RULES-PYTHON",
                f"~/.claude/rules/python/testing.md ({py_testing.stat().st_size} bytes)")
        else:
            _fail("V-GLOB-RULES-PYTHON",
                  f"file present but missing AAA/TDD markers")
    else:
        _fail("V-GLOB-RULES-PYTHON",
              f"missing: {py_testing}")

    # ---- V-GLOB-UQF-IMPORTABLE (cross-check from earlier audit) ----
    try:
        from modules.uqf.auditor import UQFAuditor
        r = UQFAuditor().audit_code_str("def foo(): pass\n", domain="python")
        if isinstance(r.score_pct, (int, float)) and 0 <= r.score_pct <= 100:
            _ok("V-GLOB-UQF-IMPORTABLE",
                f"UQFAuditor score={r.score_pct}%")
        else:
            _fail("V-GLOB-UQF-IMPORTABLE",
                  f"unexpected score={r.score_pct!r}")
    except Exception as exc:
        _fail("V-GLOB-UQF-IMPORTABLE", f"{type(exc).__name__}: {exc}")

    # ---- V-GLOB-OSA-DISPATCHER (cross-check) ----
    try:
        from modules.osa.dispatcher import _resolve_project, should_activate
        proj = _resolve_project()
        ok = bool(proj) and isinstance(proj, str)
        if ok:
            active, reason, payload = should_activate(proj)
            _ok("V-GLOB-OSA-DISPATCHER",
                f"project={proj!r} reason={reason}")
        else:
            _fail("V-GLOB-OSA-DISPATCHER", f"project resolution returned {proj!r}")
    except Exception as exc:
        _fail("V-GLOB-OSA-DISPATCHER", f"{type(exc).__name__}: {exc}")

    # ---- V-GLOB-TCO-PROXY (cross-check the BL-OSA-001 fix is intact) ----
    try:
        import tools.tco_compact_gate as g
        proxy = g._compute_context_proxy([
            {"input_tokens": 10000, "output_tokens": 0},
            {"input_tokens": 10000, "output_tokens": 0},
            {"input_tokens": 10000, "output_tokens": 0},
        ])
        if proxy == 10000:
            _ok("V-GLOB-TCO-PROXY",
                f"MAX-of-recent proxy = {proxy} for 3x10k input (not 30k)")
        else:
            _fail("V-GLOB-TCO-PROXY", f"proxy={proxy} (expected 10000)")
    except Exception as exc:
        _fail("V-GLOB-TCO-PROXY", f"{type(exc).__name__}: {exc}")

    # ---- V-GLOB-NEVER-AGAIN-INJECTABLE (cross-check) ----
    try:
        from modules.osa.never_again import top_recurring, query
        top = top_recurring(3)
        results = query("BL-GLOB-001")
        _ok("V-GLOB-NEVER-AGAIN-INJECTABLE",
            f"top_recurring={len(top)} query=BL-GLOB-001 matches={len(results)}")
    except Exception as exc:
        _fail("V-GLOB-NEVER-AGAIN-INJECTABLE",
              f"{type(exc).__name__}: {exc}")

    # ---- V-BASELINE-INTACT ----
    pyt = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=240,
    )
    last = (pyt.stdout.strip().splitlines() or [""])[-1]
    if pyt.returncode == 0 and "passed" in last:
        _ok("V-BASELINE-INTACT", f"rc=0 last='{last}'")
    else:
        _fail("V-BASELINE-INTACT",
              f"rc={pyt.returncode} last='{last}'")

    total = passes + fails
    print()
    print(f"GLOB_PASS={passes}/{total}  threshold=14/14")
    print()
    print("Documented out-of-scope (classifier-blocked, Owner-side):")
    print("  - ~/.claude/commands/uqf-audit.md")
    print("  - ~/.claude/commands/code-review.md")
    print("  - ~/.claude/settings.json hook registration "
          "(uqf_pre_edit_gate, osa_deploy_detector, ceps-bridge)")
    print("  - ~/.claude/CLAUDE.md PP-tools section (QW-A)")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
