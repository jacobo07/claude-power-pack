#!/usr/bin/env python3
"""M19 -- PP Globalization Sprint standards-sealer.

Appends:
  (a) SCS clause C16 (Global-Intervention-by-default) to BOTH
      skill-completion-standard.md mirrors.
  (b) Apex axis v8 (PP Globalization Sprint) to BOTH
      apex-completion-standard.md mirrors.

Idempotent by marker. Atomic write. Mirror parity preserved
(BL-GLOB-001 inherits the BL-OSA-001 cherry-pick / drift-resolver
discipline).
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

PP_SCS = Path("knowledge_vault/core/skill-completion-standard.md")
LOOSE_SCS = Path(os.path.expanduser(
    "~/.claude/knowledge_vault/core/skill-completion-standard.md"))
PP_APEX = Path("knowledge_vault/core/apex-completion-standard.md")
LOOSE_APEX = Path(os.path.expanduser(
    "~/.claude/knowledge_vault/core/apex-completion-standard.md"))

C16_MARKER = "### C16 -- Global-Intervention-by-default (sealed v8, 2026-05-29)"
C16_BODY = """

### C16 -- Global-Intervention-by-default (sealed v8, 2026-05-29)

Every NEW PP feature that improves code / runtime quality must
make itself discoverable in any repo, not just from PP cwd. Four
binary obligations:

1. **One global surface area** -- the feature MUST have either a
   hook in `~/.claude/settings.json` OR a global agent file at
   `~/.claude/agents/<name>.md`. At least one of the two. Hooks
   require Owner-side registration (classifier-blocked in
   auto-mode); agents do not. Prefer agents when uncertain.
2. **External-runnable** -- the feature MUST be verifiable from
   `/tmp` (or any non-PP cwd) via absolute path OR via
   `sys.path.insert` + import. The verification script lives in
   `tests/test_globalization.py` or `tools/verify_globalization.py`.
3. **Advisory-only for proactive intervention** -- any feature
   that injects context or veto during ANOTHER agent's tool call
   MUST use `continue: true` semantics (additionalContext or
   advisory output). Blocking the Owner's agent without explicit
   Owner authorization is forbidden.
4. **Documented gap when classifier-blocked** -- if a sub-feature
   requires editing `~/.claude/settings.json` or
   `~/.claude/commands/` (both classifier-blocked in auto-mode),
   ship the PP-internal half (hook script, command body) and
   document the Owner-side registration step in the agent's body.

Without (1) + (2) + (3) + (4): the feature is not SCS-complete on
the global-intervention axis.

Sealed alongside Apex axis v8 (BL-GLOB-001).
"""

APEX_MARKER = "## PP Globalization Sprint Axis v8 (sealed 2026-05-29)"
APEX_BODY = """

## PP Globalization Sprint Axis v8 (sealed 2026-05-29) -- proactive-availability DONE

The tenth Apex DONE axis. A PP install is Apex-complete on this
axis iff PP's quality tooling is **discoverable, invokable, and
schema-valid in any repo** the Owner works from. This is the
discovery / reach axis that complements the OSA axis v7 (proactive
audit) and the ECC-UQF axis v6 (quality framework).

### Six required components (all six must be present)

1. **At least 7 PP agents globally installed** at
   `~/.claude/agents/{omni-singularity,pp-code-reviewer,pp-monitor,
   pp-uqf-auditor,pp-tco-advisor,pp-ceps-analyst,pp-never-again}.md`.
   Each agent file MUST have valid YAML frontmatter (`name`,
   `description`, `tools` -- no `triggers:`/`throttle:` keys, which
   the Claude Code agent loader silently ignores; activation logic
   lives in Python).
2. **Cross-language rules taxonomy at `~/.claude/rules/`** with
   at least `common/code-review.md` (ECC Pre-Report Gate + Zero
   Findings Is Valid + Proof Triad doctrine) and one language
   subdirectory (e.g. `python/testing.md` with AAA + TDD).
3. **External verifiability** -- `tests/test_globalization.py`
   passes from PP cwd with empirical V-gates on agent
   schema + rules presence + cross-checks against BL-OSA-001
   (UQF importable, TCO MAX-of-recent proxy intact, OSA
   dispatcher returns valid tuple).
4. **Verify probe** -- `tools/verify_globalization.py` returns
   `GLOB_PROBE = 5/5` via a new `globalization` row in
   `tools/verify_spp.py`.
5. **OSA daemon setup documented** -- `vault/osa/daemon_setup.md`
   has Linux crontab + Windows Task Scheduler instructions for the
   `python -m modules.osa.osa_command --audit` periodic runner.
6. **Honest blocker documentation** -- assets that require
   Owner-side registration in `~/.claude/settings.json` or
   `~/.claude/commands/` (classifier-blocked) are documented as
   such in the globalization status report, NOT advisory-tagged.

### Six-check DONE-gate (binary)

1. `python tests/test_globalization.py` exit 0 with `GLOB_PASS = 15/15`.
2. `python tools/verify_globalization.py` exit 0 with `GLOB_PROBE = 5/5`.
3. `ls ~/.claude/agents/{pp-*,omni-*}.md | wc -l` >= 7.
4. `~/.claude/rules/common/code-review.md` and
   `~/.claude/rules/python/testing.md` both exist + carry doctrine
   markers.
5. `tools/verify_spp.py` row `globalization` returns rc=0 with
   `GLOB_PROBE=5/5`.
6. `vault/audits/globalization_status_<ts>.md` exists with a
   36-asset matrix + Plan section ranked by ROI.

### Empirical baseline (2026-05-29)

- 7 PP agents installed and schema-valid: `omni-singularity`,
  `pp-code-reviewer`, `pp-monitor`, `pp-uqf-auditor`,
  `pp-tco-advisor`, `pp-ceps-analyst`, `pp-never-again`.
- `~/.claude/rules/{common/code-review.md, python/testing.md}`
  installed -- cross-language baseline.
- `test_globalization.py` GLOB_PASS=15/15.
- `verify_globalization.py` GLOB_PROBE=5/5.
- `verify_spp.py` extended to 14 rows; the new `globalization`
  row passes.
- Daemon setup at `vault/osa/daemon_setup.md` (Linux crontab +
  Windows Task Scheduler).
- Globalization status report at
  `vault/audits/globalization_status_20260529T111424Z.md` with 36
  assets + 8-entry Plan ranked by ROI.

### Honest classifier blockers (Owner-side actions)

The following sub-features ship the PP-internal half but require
the Owner to authorize the global-side registration:

- `~/.claude/commands/uqf-audit.md` (new) -- classifier denies
  agent self-modification of startup commands directory.
- `~/.claude/commands/code-review.md` (new) -- same.
- `~/.claude/settings.json` hook registration for
  `uqf_pre_edit_gate` / `osa_deploy_detector` / `ceps-bridge` --
  classifier denies hook self-registration.
- `~/.claude/CLAUDE.md` PP-tools section append (QW-A) -- classifier
  denies global startup-config edit.

Per Memory feedback "no classified FAILs at done-gate", these are
documented honestly, NOT promoted to ADVISORY rows. The Owner's
explicit authorization is the remediation path.

### Asymmetric complement to prior axes

- **ECC v6** absorbed the quality FRAMEWORK.
- **OSA v7** absorbed the proactive AUDIT.
- **Globalization v8** makes both REACH every repo, not just PP.

Sealed 2026-05-29 (BL-GLOB-001).
"""


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                               dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_section(target: Path, marker: str, body: str) -> bool:
    if not target.is_file():
        print(f"missing (skip): {target}", file=sys.stderr)
        return False
    raw = target.read_text(encoding="utf-8")
    if marker in raw:
        print(f"already present (idempotent skip): {target}")
        return True
    if not raw.endswith("\n"):
        raw += "\n"
    _atomic_write(target, raw + body)
    print(f"appended: {target} (bytes={target.stat().st_size})")
    return True


def main() -> int:
    ok = True
    ok &= append_section(PP_SCS, C16_MARKER, C16_BODY)
    ok &= append_section(LOOSE_SCS, C16_MARKER, C16_BODY)
    ok &= append_section(PP_APEX, APEX_MARKER, APEX_BODY)
    ok &= append_section(LOOSE_APEX, APEX_MARKER, APEX_BODY)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
