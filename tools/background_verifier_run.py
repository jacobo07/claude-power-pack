#!/usr/bin/env python3
"""background_verifier_run.py - the heavy work for Component C (Zero-Command).

Invoked detached by ~/.claude/hooks/background-verifier.js. Performs:
  1. Mirror parity check (global apex vs its PP mirror).
  2. OVO staleness check (last verdict age + uncommitted/ahead).
  3. Spec coherence check (bracketed clarifications vs chain advance).

Writes vault/handoffs/<kind>-<ts>.md only when a check fires AND no
recent (<10 min) handoff of the same kind exists. Never auto-fixes,
never auto-pushes, never auto-runs OVO.

Escalation (2026-07-29). Every finding is routed through
modules.alert_escalation before anything is written. A finding repeated past
the configured threshold without ever being resolved is promoted to URGENT
once, recorded as a standing row in vault/handoffs/ESCALATED.md, and its
routine notices are then suppressed. Origin: this file produced 333 identical
mirror-drift handoffs across 67 days -- detection nobody could act on, because
nothing distinguished the 333rd notice from the first.

Fail-open: any exception inside any check logs to
~/.claude/logs/background-verifier.log and skips that check; never
crashes the process so the Stop hook child doesn't leave zombies. If the
escalation module cannot be imported the checks still run in routine mode,
and the import failure is logged rather than swallowed.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PP_ROOT = HOME / ".claude" / "skills" / "claude-power-pack"
LOG_FILE = HOME / ".claude" / "logs" / "background-verifier.log"

GIT_EXE = "git"
for cand in (
    Path("C:/Program Files/Git/cmd/git.exe"),
    Path("C:/Program Files (x86)/Git/cmd/git.exe"),
):
    if cand.is_file():
        GIT_EXE = str(cand)
        break

DEDUPE_WINDOW_SEC = 600  # 10 min - matches the plan's "no log spam" rule
OVO_STALE_SEC = 24 * 3600

# Corrected 2026-07-29. This list previously paired the global apex standard
# with vault/knowledge_base/apex_baseline_doctrine.md. Those are two different
# documents -- the doctrine file's own header states it mirrors a section of
# ~/.claude/CLAUDE.md, its first heading is "Apex Completeness Doctrine",
# the global file's is "Testing Gate Axis" -- so the equality test could never
# pass and the alert was true by construction. All 333 handoffs on record name
# that wrong pair; the "growing delta" they reported was the size difference
# between two unrelated files tracking the global file's growth. The real
# counterpart is the PP mirror of the same document, which is what
# tools/verify_global_mirrors.py has always compared.
MIRROR_PAIRS = [
    (HOME / ".claude" / "knowledge_vault" / "core" / "apex-completion-standard.md",
     PP_ROOT / "knowledge_vault" / "core" / "apex-completion-standard.md"),
]

# Bracketed clarification markers the chain emits then resolves.
SPEC_MARKER_RX = re.compile(r"\[NEEDS\s+CLARIFICATION:[^\]]+\]", re.I)


def log(msg: str) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} [verifier] {msg}\n")
    except Exception as e:
        sys.stderr.write(f"background_verifier log fail: {e}\n")


if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))
try:
    from modules.alert_escalation import policy as escalation
except Exception as _esc_err:  # visible degradation, never a silent outage
    escalation = None
    log(f"alert_escalation unavailable, routine mode only: {_esc_err}")


def _lf(data: str) -> str:
    """Line-ending-insensitive body. core.autocrlf=true otherwise reports a
    difference that is not a difference."""
    return data.replace("\r\n", "\n").replace("\r", "\n")


def recent_handoff_exists(handoff_dir: Path, kind: str) -> bool:
    try:
        if not handoff_dir.is_dir():
            return False
        cutoff = time.time() - DEDUPE_WINDOW_SEC
        for p in handoff_dir.glob(f"{kind}-*.md"):
            if p.stat().st_mtime > cutoff:
                return True
        return False
    except OSError as e:
        log(f"recent_handoff_exists({kind}) error: {e}")
        return False


def write_handoff(handoff_dir: Path, kind: str, body: str) -> Path:
    handoff_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    path = handoff_dir / f"{kind}-{ts}.md"
    path.write_text(body, encoding="utf-8")
    return path


def _decide(handoff_dir: Path, kind: str, key: str, detail: str,
            legacy_match: str = ""):
    """Route one finding. Returns None when escalation is unavailable, which
    the callers treat as 'write the routine handoff'."""
    if escalation is None:
        return None
    try:
        pol = escalation.load_policy(PP_ROOT)
        return escalation.observe(handoff_dir, pol, kind, key, detail=detail,
                                  legacy_match=legacy_match)
    except Exception as e:
        log(f"escalation decide error ({kind}): {e}")
        return None


def _resolved(handoff_dir: Path, key: str) -> None:
    """The condition no longer holds. Without this call the occurrence count
    could never fall and every finding would eventually escalate."""
    if escalation is None:
        return
    try:
        if escalation.note_resolved(handoff_dir, key):
            log(f"finding resolved, escalation cleared: {key}")
    except Exception as e:
        log(f"escalation resolve error: {e}")


def _severity_block(decision) -> str:
    if decision is None:
        return "- **Severity**: ROUTINE\n"
    if decision.route == escalation.ESCALATE:
        return (f"- **Severity**: URGENT\n"
                f"- **Escalation**: {decision.reason}\n"
                f"- **Occurrences**: {decision.occurrences} "
                f"(threshold {decision.threshold})\n"
                f"- **Standing record**: `vault/handoffs/"
                f"{escalation.STANDING_NAME}`\n")
    return (f"- **Severity**: ROUTINE\n"
            f"- **Occurrences**: {decision.occurrences} "
            f"(threshold {decision.threshold})\n")


def _emit(handoff_dir: Path, kind: str, key: str, detail: str, body_fn,
          legacy_match: str = "") -> None:
    """Decide, then write at most one handoff. SUPPRESS writes nothing: the
    finding is already represented by a standing URGENT row."""
    decision = _decide(handoff_dir, kind, key, detail, legacy_match)
    if decision is not None and decision.route == escalation.SUPPRESS:
        log(f"{kind} suppressed (already escalated, "
            f"{decision.occurrences} occurrences): {key}")
        return
    header = (f"- **Finding key**: `{key}`\n" + _severity_block(decision))
    write_handoff(handoff_dir, kind, body_fn(header))
    if decision is not None and decision.route == escalation.ESCALATE:
        log(f"{kind} ESCALATED to URGENT after {decision.occurrences} "
            f"unresolved occurrences: {key}")
    else:
        log(f"{kind} handoff written: {key}")


def check_mirror_parity(cwd: Path) -> None:
    handoff_dir = cwd / "vault" / "handoffs"
    for global_path, pp_path in MIRROR_PAIRS:
        try:
            if not global_path.is_file() or not pp_path.is_file():
                continue
            key = escalation.finding_key(
                "mirror-drift", global_path.name, pp_path.name
            ) if escalation else f"mirror-drift::{global_path.name}"

            g_body = _lf(global_path.read_text(encoding="utf-8", errors="replace"))
            p_body = _lf(pp_path.read_text(encoding="utf-8", errors="replace"))
            if g_body == p_body:
                _resolved(handoff_dir, key)
                continue
            if recent_handoff_exists(handoff_dir, "mirror-drift"):
                return

            g_lines = g_body.splitlines()
            p_lines = p_body.splitlines()
            detail = (f"`{global_path}` vs `{pp_path}` -- "
                      f"{len(g_lines) - len(p_lines):+d} lines, "
                      f"{len(g_body) - len(p_body):+d} bytes apart. Resolve with "
                      f"`python tools/verify_global_mirrors.py`.")

            def body_fn(header: str, gp=global_path, pp=pp_path,
                        gl=g_lines, pl=p_lines, gb=g_body, pb=p_body) -> str:
                return (
                    f"# Mirror Drift Detected\n\n"
                    f"- **Global path**: `{gp}`\n"
                    f"- **PP path**: `{pp}`\n"
                    f"- **Global lines**: {len(gl)}\n"
                    f"- **PP lines**: {len(pl)}\n"
                    f"- **Line delta**: {len(gl) - len(pl)}\n"
                    f"- **Byte delta**: {len(gb) - len(pb)}\n"
                    + header +
                    f"\n## Action\n"
                    f"Run `python tools/verify_global_mirrors.py` to see the "
                    f"unified diff; resolve by editing the lagging side; commit; "
                    f"re-run mirror verifier.\n"
                    f"\n*Generated by background-verifier (Zero-Command "
                    f"Component C).*\n"
                )

            _emit(handoff_dir, "mirror-drift", key, detail, body_fn)
            return  # one handoff per cycle is enough
        except Exception as e:
            log(f"mirror check error: {e}")


def check_ovo_staleness(cwd: Path) -> None:
    handoff_dir = cwd / "vault" / "handoffs"
    key = "ovo-stale::verdicts"
    try:
        verdicts = cwd / "vault" / "audits" / "verdicts.jsonl"
        if not verdicts.is_file():
            return
        # Read last line; verdicts are append-only.
        last_ts = None
        with open(verdicts, "rb") as f:
            f.seek(0, 2)
            sz = f.tell()
            chunk = min(sz, 4096)
            f.seek(sz - chunk)
            tail = f.read().decode("utf-8", errors="replace")
        for line in reversed(tail.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            ts_raw = row.get("ts") or row.get("timestamp")
            if not ts_raw:
                continue
            try:
                if isinstance(ts_raw, (int, float)):
                    last_ts = float(ts_raw)
                else:
                    last_ts = datetime.fromisoformat(
                        str(ts_raw).replace("Z", "+00:00")
                    ).timestamp()
                break
            except Exception:
                continue
        if last_ts is None:
            return
        age_sec = time.time() - last_ts
        if age_sec < OVO_STALE_SEC:
            _resolved(handoff_dir, key)
            return
        # Check uncommitted/ahead.
        status = subprocess.run(
            [GIT_EXE, "-C", str(cwd), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        ahead = subprocess.run(
            [GIT_EXE, "-C", str(cwd), "rev-list", "--count", "origin/HEAD..HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        dirty = bool(status.stdout.strip())
        ahead_n = 0
        try:
            ahead_n = int(ahead.stdout.strip() or "0")
        except ValueError:
            ahead_n = 0
        if not dirty and ahead_n == 0:
            _resolved(handoff_dir, key)
            return  # nothing to push; stale but no work waiting
        if recent_handoff_exists(handoff_dir, "ovo-stale"):
            return
        hours = int(age_sec / 3600)
        detail = (f"Last OVO verdict is {hours} h old with "
                  f"{'uncommitted changes' if dirty else 'a clean tree'} and "
                  f"{ahead_n} commit(s) ahead of remote.")

        def body_fn(header: str, h=hours, d=dirty, a=ahead_n) -> str:
            return (
                f"# OVO Verdict Stale\n\n"
                f"- **Last verdict age**: {h} h\n"
                f"- **Uncommitted changes**: {'yes' if d else 'no'}\n"
                f"- **Commits ahead of remote**: {a}\n"
                + header +
                f"\n## Action\n"
                f"Run `/ovo-audit` before pushing. The OVO push gate requires "
                f"verdict A or A+ within 600 s TTL.\n"
                f"\n*Generated by background-verifier (Zero-Command Component "
                f"C); no auto-OVO per Owner constraint.*\n"
            )

        _emit(handoff_dir, "ovo-stale", key, detail, body_fn)
    except Exception as e:
        log(f"ovo check error: {e}")


def check_spec_coherence(cwd: Path) -> None:
    handoff_dir = cwd / "vault" / "handoffs"
    try:
        specs_root = cwd / ".specify" / "specs"
        if not specs_root.is_dir():
            return
        for feature_dir in specs_root.iterdir():
            if not feature_dir.is_dir():
                continue
            spec_md = feature_dir / "spec.md"
            if not spec_md.is_file():
                continue
            key = f"spec-incoherent::{feature_dir.name}"
            body = spec_md.read_text(encoding="utf-8", errors="replace")
            markers = SPEC_MARKER_RX.findall(body)
            if not markers:
                _resolved(handoff_dir, key)
                continue
            # Has unresolved markers - check if chain has advanced past spec.
            plan_md = feature_dir / "plan.md"
            tasks_md = feature_dir / "tasks.md"
            if not (plan_md.is_file() or tasks_md.is_file()):
                continue  # spec is still being authored; OK
            if recent_handoff_exists(handoff_dir, "spec-incoherent"):
                return
            detail = (f"`{feature_dir.name}` carries {len(markers)} unresolved "
                      f"clarification marker(s) while plan/tasks already exist.")

            def body_fn(header: str, fd=feature_dir, mk=markers,
                        pm=plan_md, tm=tasks_md) -> str:
                return (
                    f"# Spec Incoherence Detected\n\n"
                    f"- **Feature**: `{fd.name}`\n"
                    f"- **Unresolved clarifications**: {len(mk)}\n"
                    f"- **Plan exists**: {pm.is_file()}\n"
                    f"- **Tasks exist**: {tm.is_file()}\n"
                    + header +
                    f"\n## Sample unresolved markers\n\n"
                    + "\n".join(f"- {m}" for m in mk[:5])
                    + f"\n\n## Action\n"
                    f"Resolve markers in `spec.md` BEFORE iterating plan/tasks - "
                    f"downstream artifacts inherit ambiguity.\n"
                    f"\n*Generated by background-verifier (Zero-Command "
                    f"Component C).*\n"
                )

            _emit(handoff_dir, "spec-incoherent", key, detail, body_fn)
            return  # one per cycle
    except Exception as e:
        log(f"spec check error: {e}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--session", default="unknown")
    args = ap.parse_args()

    cwd = Path(args.cwd)
    if not cwd.is_dir():
        log(f"cwd not a directory: {cwd}")
        return 0

    log(f"start cwd={cwd} session={args.session}")
    check_mirror_parity(cwd)
    check_ovo_staleness(cwd)
    check_spec_coherence(cwd)
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
