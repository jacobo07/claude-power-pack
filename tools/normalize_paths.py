#!/usr/bin/env python3
"""normalize_paths.py — Gap-2 (path) + Gap-10 (extended secret-scan) auditor.

Why this exists
---------------
The 2026-05-19 globalization audit found hardcoded ``C:/Users/User/...``
paths in canonicalised hooks (e.g. ``hook-dispatcher.js:15,85``). Any
host whose Windows username is not ``User`` (or any POSIX host) would
break. Beyond paths, the same audit named a leak class — kobicraft VPS
IP, ``panel.kobicraft.net``, SSH key names, ``CLAUDE_CODE_SSE_PORT=<n>``
— that the generic ``sk-*``/AWS-class secret-scan misses.

Two purposes, one tool, dual mode:

* ``--check``  (default): exit 1 if any PP-tracked file matches the
                          path-leak OR the extended-secret regex set.
                          Suitable as a CI grep gate / pre-commit guard.
* ``--apply``            : rewrite the path-leak matches in place
                          (portable equivalents — never touches secret
                          hits, those are STOP-and-Owner-review).

Scope: every file ``git ls-files`` reports inside the Power Pack repo
that is text-suffixed (.js/.py/.md/.json/.sh/.ps1/.yaml/.yml/.txt). The
``vendor/`` tree is excluded — third-party code we do not author or ship
as canonical mirrors.

Reality contract: no silent rewrites. ``--apply`` prints every change
made (file + line + before/after) and counts them in the final summary.
A run that touches zero files exits 0; a run that rewrites N files
exits 0 with ``N rewritten``; a run that detects secret-class hits
ALWAYS exits 1 — no automatic redaction (the auditor's law).
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Path-leak class — auto-rewritable to portable equivalents.
PATH_RE = re.compile(r"C:[/\\]Users[/\\][A-Za-z0-9_-]+")

# Secret-class — Gap-10 regex set + the generic high-confidence set the
# Owner-pane already used. Match here ⇒ STOP, no auto-rewrite.
SECRET_RES: list[tuple[str, re.Pattern[str]]] = [
    ("VPS IP",          re.compile(r"\b204\.168\.166\.63\b")),
    ("kobicraft host",  re.compile(r"\bkobicraft\b", re.IGNORECASE)),
    ("kobicraft panel", re.compile(r"\bpanel\.kobicraft\.net\b")),
    ("personal email",  re.compile(r"\bjacobolopez\b")),
    ("ssh key kobi",    re.compile(r"\bkobiicraft_vps\b|\bgex44\b")),
    ("session SSE port",re.compile(r"\bCLAUDE_CODE_SSE_PORT=\d")),
    ("anthropic sk",    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("github pat",      re.compile(r"\bghp_[A-Za-z0-9]{30,}\b")),
    ("slack token",     re.compile(r"\bxox[bapsr]-[A-Za-z0-9-]{10,}\b")),
    ("aws akid",        re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("aws sak",         re.compile(r"\baws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}\b",
                                   re.IGNORECASE)),
]

# Files we never scan/rewrite (third-party + binaries + history).
SKIP_DIRS = {".git", "node_modules", "vendor", "_quarantine"}
SKIP_FILES_GLOB = {"*.bak", "*.userbak.*", "*.png", "*.jpg", "*.jpeg",
                   "*.gif", "*.ico", "*.pdf", "*.zip", "*.gz", "*.exe",
                   "*.dll", "*.db", "*.sqlite", "*.sqlite3"}
TEXT_SUFFIXES = {".js", ".mjs", ".cjs", ".ts", ".py", ".md", ".json",
                 ".sh", ".ps1", ".bat", ".cmd", ".yaml", ".yml", ".txt",
                 ".html", ".css"}

# Historical-narrative files: a leak written into a past lesson is the
# lesson; rewriting it falsifies the record. Reported as advisory by
# --check but never gate-fails or rewrites.
WHITELIST_HISTORICAL = {
    "vault/knowledge_base/session_lessons.md",
    # errors.md is the same class as session_lessons.md: a frozen
    # historical narrative naming past incidents (e.g. "Outbound SSH to
    # 204.168.166.63 blocked"). Rewriting falsifies the audit record.
    "vault/knowledge_base/errors.md",
}

# Per-file class allowlist. Each entry is `glob → set(of suppressed
# classes)`. Suppressed hits still print under an ALLOWED tag (visible
# evidence the allowlist is in effect) but do NOT contribute to the
# gate-fail counters. Two classes:
#   * "secret"     — suppress SECRET_RES hits in that file
#   * "code-path"  — suppress code-class C:\Users\User\... hits
# Every entry MUST carry a comment explaining WHY the suppression is
# legitimate (not blanket; documented per file).
import fnmatch as _fnmatch
ALLOWLIST: dict[str, set[str]] = {
    # ---- VPS-infrastructure modules: their *purpose* is to operate on
    # the Owner's kobicraft VPS; the IP/host/user refs are operational
    # config, not leaks.
    "modules/agent-lightning/*":   {"secret"},
    "modules/daemon/*":            {"secret"},
    "modules/infrastructure/*":    {"secret"},
    "modules/omnicapture/*":       {"secret"},
    "modules/zero-crash/**":       {"secret"},
    "tools/run_vps.sh":            {"secret"},
    "tools/vps_validation_handoff.sh": {"secret"},
    # ---- Additional VPS-class tools that came in via merge 2026-05-23.
    # Same posture as the modules/* entries: their purpose is VPS push /
    # heartbeat / settings-bridge, the host literals are operational
    # config (DEFAULT_HOST fallbacks + docstring examples).
    "tools/lazarus_topology_push_vps.py": {"secret"},
    "tools/oracle_heartbeat.py":          {"secret"},
    "tools/vps_settings_merge.py":        {"secret", "code-path", "doc-path"},
    # ---- Historical bulk-extract audit dataset (2026-04-29, frozen).
    # The vault dump preserves the worktree path literals as part of
    # the audit record; rewriting would falsify the historical state.
    "vault/audits/bulk_vault_extract.json": {"secret"},
    # ---- VPS continuation plan documents the SSH commands the Owner
    # actually runs. Allowlisted as VPS-ops narrative (same class as
    # vault/standards/blocked-delivery-prevention.md).
    "vault/plans/OVO_VPS_CONTINUATION.md": {"secret"},
    # ---- Code-class allowlist additions for pre-existing host-pinned
    # tools that came in via merge (smoke tests + topology applier +
    # skill scanner — all reference the worktree path as fixture or
    # canonical operational target).
    "tools/plugin_skill_scanner.py":       {"code-path"},
    "tools/post_restart_smoke.ps1":        {"code-path", "doc-path"},
    "tools/post_restart_smoke.sh":         {"code-path", "doc-path"},
    "tools/topology_apply.py":             {"code-path"},
    # ---- Frozen video-analysis audit (2026-04-29): worktree path
    # appears as part of the captured-at-test-time evidence.
    "vault/topology/video_analysis_2026-04-29.md": {"doc-path"},
    # ---- Machine-generated skill registries: absolute paths to skill
    # source files are dataset records, not portable code. Re-indexing
    # regenerates them from current PP layout each time. Same posture
    # as tools/_inventory/agents.json.
    "vault/skills_index.json":             {"code-path"},
    "vault/skills_index_unified.json":     {"code-path"},
    # ---- Code Review Skill V-block fixtures (2026-05-23): the
    # canonical AWS test key `AKIAIOSFODNN7EXAMPLE` appears verbatim
    # as the V-BLOCK-SECRET payload. Test fixtures by design (the
    # whole point of the test is to verify the detector fires on it).
    "modules/code-review/test_v_block.py":      {"secret", "code-path"},
    "modules/code-review/test_combined_gate.py": {"secret"},
    "modules/code-review/test_closed_loop.py":  {"secret"},
    # The plan file documents the V-block payloads inline as part of
    # the empirical proof contract. Same fixture-narrative class as
    # vault/plans/auto-testing-skill-2026-05-23.md (already allowlisted).
    "vault/plans/code-review-skill-2026-05-23.md": {"secret"},
    "vault/specs/code-review-skill.md":            {"secret"},
    # Self-review report quotes the V-BLOCK payload + finding lines
    # verbatim as part of the empirical artifact.
    "vault/reviews/2026-05-23-203833_code-review-skill-self.md": {"secret"},
    # Closed-loop log records the doctrine categories that fired;
    # may contain file paths referenced in V-block diffs.
    "vault/reviews/patterns.jsonl": {"secret"},
    "vault/reviews/_v_block.json":  {"secret"},
    # ---- Deployment Skill (2026-05-24, PP Quality Quadrangle close).
    # V-FORBIDDEN-REMOTE test fixtures cite the canonical deploy
    # remotes (kobicraft@vps204, kobicraft@204.168.166.63) as expected
    # inputs to the pure guard; the whole point of the test is to
    # verify the forbidden-remote check fires against them.
    "modules/deployment/test_v_block.py": {"secret", "code-path"},
    # Per-project deploy configs name the ssh aliases AND host paths
    # by design -- they are operational metadata (no credentials, by
    # invariant; the schema validator rejects credential-class keys).
    "vault/deploy/kobiicraft.json":  {"secret"},
    "vault/deploy/tua-x.json":       {"secret"},
    "vault/deploy/infinityops.json": {"secret"},
    # Spec + plan document the 4 modes by reference to the actual
    # project topology (gex44 for KobiiCraft, vps204 for TUA-X /
    # InfinityOps). Same posture as auto-testing spec naming
    # KobiCraft as the canonical CEILING case.
    "vault/specs/deployment-skill.md":            {"secret"},
    "vault/plans/deployment-skill-2026-05-24.md": {"secret"},
    # V-DEEP empirical receipt captures the worktree path of the
    # InfinityOps repo + the §77 citation. Frozen empirical artefact.
    "vault/deploys/2026-05-24-130836_infinityops_dryrun.md": {"secret", "doc-path"},
    # Future auto-generated deploy reports inherit the same pattern.
    "vault/deploys/*.md": {"secret", "doc-path"},
    # ---- Backup / Snapshot Axis (2026-05-25, Deploy precondition).
    # Per-project backup configs name ssh aliases (gex44, vps204) and
    # remote paths (/srv/kobiicraft/main/world, postgres container
    # names) by design -- operational metadata. Schema validator
    # guarantees zero credential-class keys are present.
    "vault/backup/kobiicraft.json":   {"secret"},
    "vault/backup/tua-x.json":        {"secret"},
    "vault/backup/infinityops.json":  {"secret"},
    # Spec + plan document the 3 modes by reference to the actual
    # project topology. Same posture as deploy spec/plan.
    "vault/specs/backup-skill.md":            {"secret"},
    "vault/plans/backup-skill-2026-05-24.md": {"secret"},
    # V-DEEP empirical receipt + future auto-generated receipts.
    "vault/backups/2026-05-25-151305_kobiicraft_dryrun.md": {"secret", "doc-path"},
    "vault/backups/*.md": {"secret", "doc-path"},
    # ---- Auto-generated context-watchdog session log: cwd + transcript
    # paths are appended on every Stop hook crossing a threshold. The
    # literals are operational session metadata (this host, this user),
    # not credentials. Same posture as session_lessons.md.
    "vault/progress.md": {"doc-path"},
    # ---- /backup command documentation: the examples cite the
    # canonical ssh aliases (gex44, vps204) by design -- the whole
    # point of the doc is to teach the Owner the surface.
    "commands/backup.md": {"secret"},
    # ---- Frozen topology snapshot (2026-04-29): captured-at-test-time
    # absolute path inventory, audit-record by design.
    "vault/topology/lazarus_layout_2026-04-29.json": {"code-path"},
    # ---- Self-aware auditor: this very file names the leak class in
    # its docstring (matches PATH_RE in narrative text) + matches the
    # SECRET_RES regex literals it defines. Both classes legitimate.
    "tools/normalize_paths.py":    {"secret", "code-path", "doc-path"},
    # ---- hook-dispatcher.js carries a comment that quotes the OLD
    # literal (`C:/Users/User/AppData/...`) as the audit-2026-05-19
    # before-state inside the explanation of the portable-fallback fix.
    # Rewriting the literal makes the comment vacuous (the comment
    # documents what *was* hardcoded — the fix itself is in the code).
    "hooks/hook-dispatcher.js":    {"doc-path"},
    # ---- blocked-delivery-prevention.md documents the *exact*
    # PowerShell `Copy-Item` commands the Owner copy-pastes to sync
    # the canonicalized hooks to the loose-master tree. PowerShell
    # does NOT expand `~` inside `Copy-Item` -Path/-Destination args
    # the way bash does, so rewriting the literal to `~\...` would
    # break the documented procedure. The literal IS the canonical
    # command (verbatim-copy doctrine, see standards file body).
    "vault/standards/blocked-delivery-prevention.md": {"doc-path"},
    # ---- Inventory metadata: agents.json documents redaction reasons
    # by name (e.g. "redact_reason: references VPS IP ..." literal).
    "tools/_inventory/agents.json":{"secret"},
    # ---- Historical narrative: a frozen incident log naming a past
    # event (e.g. "Outbound SSH to 204.168.166.63 blocked 2026-04-22").
    # Same class as the session_lessons.md WHITELIST_HISTORICAL entry,
    # which covers path-leak only; this covers the secret-class hit.
    "vault/knowledge_base/errors.md": {"secret"},
    # ---- Doc-class refs naming the Owner's daemon as an example.
    "agents/oneshot-architect-auditor.md": {"secret"},
    "SSOT.md":                     {"secret", "doc-path"},
    # ---- Auto-Testing Skill artifacts (sealed 2026-05-23). These
    # docs describe the empirical ceiling case where the gate must
    # honestly say "no build system" -- KobiCraft is the canonical
    # example project on this host (136 .java files, no pom.xml).
    # The project name appears as legitimate doc reference, not as
    # a host/IP/credential leak.
    "commands/auto-test.md":       {"secret"},
    "vault/specs/auto-testing-gate.md": {"secret"},
    "vault/plans/auto-testing-skill-2026-05-23.md": {"secret"},
    # The session_lessons.md row L4 below and the ukdl-universal.md
    # ledger also reference KobiCraft as the canonical ceiling case.
    "vault/knowledge_base/ukdl-universal.md": {"secret"},
    # Apex axis section + detector + Java generator name KobiCraft as
    # the empirical ceiling case (no pom.xml, 136 .java files). These
    # are doc/code references to a project on the host, not credentials.
    "knowledge_vault/core/apex-completion-standard.md": {"secret"},
    "modules/auto-testing/detectors.py":           {"secret"},
    "modules/auto-testing/generators/java_gen.py": {"secret"},
    # ---- Governance dataset describing the host/router constraint by
    # example in a description field.
    "modules/governance-overlay/mistake-frequency.json": {"secret"},
    # ---- Code-path-pinned Windows operational tools. Their docstrings
    # already declare host-pinning. Not portability candidates.
    "tools/sovereign_miner.py":    {"code-path"},
    "tools/merger.py":             {"code-path"},
    "tools/quality_audit.py":      {"code-path"},
    "tools/reconstructor.py":      {"code-path"},
    "tools/vault_search.py":       {"code-path"},
    # ---- The mirror verifier itself: `HARDCODED_REPO` is a *fallback*
    # used only when env detection fails (documented in its docstring);
    # the PAIRS list literals are the source-of-truth pair definitions.
    "tools/verify_global_mirrors.py": {"code-path"},
    # ---- Test fixture: assertion body intentionally uses an absolute
    # `C:/Users/User/.claude/commands/resume.md` literal to prove the
    # guard *blocks* writes to that exact path. Parametrising would
    # change the test's semantics.
    "modules/session-continuity/tests/guard.test.js": {"code-path"},
    # ---- One-shot 2026-05-21 fork-storm migration: writes the exact
    # Windows path of the dispatcher into settings.json entries. The
    # script is frozen post-migration; rewriting the literal would
    # break the one-time migration semantics (and the file is no
    # longer re-executed after that date).
    "tools/fork_storm_migration_2026-05-21.py": {"code-path"},
    # ---- Auto-test-gate hook docstring: the comment shows
    # `C:/Users/foo` as a schematic example of the Bash POSIX -> Win
    # conversion that normalizePath() performs. The literal is
    # illustrative, not a real host path.
    "hooks/auto-test-gate.js":     {"doc-path"},
    # ---- Frozen historical verification doc (2026-05-20). The
    # absolute worktree path was the literal value the agent was
    # working with at the moment of that verification. Rewriting
    # destroys the audit record.
    "vault/verifications/speckit_zero_clarification_2026-05-20.md": {"doc-path"},
}


def _allowed(rel: str, klass: str) -> bool:
    """Return True if `rel` matches an ALLOWLIST entry suppressing `klass`."""
    for pat, classes in ALLOWLIST.items():
        if klass in classes and _fnmatch.fnmatch(rel, pat):
            return True
    return False

# Comment-line heuristics — only "doc" lines are safe to bulk-rewrite.
# Code-string-literal lines must be hand-fixed with a portable derivation
# (os.homedir(), Path.home(), process.env.USERPROFILE) — a blind ``~``
# substitution would not be runtime-expanded.
_COMMENT_LEADERS = {
    ".js": ("//", "*", "/*", "*/"),
    ".mjs": ("//", "*", "/*", "*/"),
    ".cjs": ("//", "*", "/*", "*/"),
    ".ts":  ("//", "*", "/*", "*/"),
    ".py":  ("#",),
    ".sh":  ("#",),
    ".ps1": ("#",),
    ".bat": ("rem", "::"),
    ".cmd": ("rem", "::"),
    ".yaml":("#",),
    ".yml": ("#",),
}


def _line_is_doc(line: str, ext: str) -> bool:
    """Markdown lines are doc by default; code-language lines are doc
    only when their first non-whitespace token is a known comment
    leader. JSON/CSS/HTML treated as code (no rewrite)."""
    if ext == ".md" or ext == ".txt":
        return True
    leaders = _COMMENT_LEADERS.get(ext)
    if not leaders:
        return False
    s = line.lstrip()
    return any(s.startswith(L) for L in leaders) or s == ""


def repo_files() -> list[Path]:
    """Return PP-tracked files that are scannable text."""
    try:
        out = subprocess.check_output(
            ["git", "ls-files"], cwd=str(REPO), text=True, encoding="utf-8")
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"git ls-files failed: {e}\n")
        return []
    files: list[Path] = []
    for line in out.splitlines():
        p = REPO / line
        if not p.exists() or not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        files.append(p)
    return files


def _read(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _normalize_for(text: str, file: Path) -> tuple[str, list[tuple[int, str, str, str]]]:
    """Rewrite path-leaks to portable equivalents (doc-line only).

    Each change is ``(line_no, before_line, after_line, kind)`` where
    ``kind`` is one of:

    * ``"doc"``  — markdown body or a code-language comment line;
                   safe to auto-rewrite ``C:/Users/<n>`` → ``~``.
    * ``"code"`` — code string literal (e.g. a constant assignment);
                   the rewriter NEVER touches it because a bare ``~``
                   in a runtime string is not OS-expanded. The line is
                   reported for manual replacement with
                   ``os.homedir()`` / ``Path.home()`` /
                   ``process.env.USERPROFILE``.
    """
    changes: list[tuple[int, str, str, str]] = []
    ext = file.suffix.lower()
    out_lines: list[str] = []
    for lineno, line in enumerate(text.splitlines(keepends=False), start=1):
        if not PATH_RE.search(line):
            out_lines.append(line)
            continue
        kind = "doc" if _line_is_doc(line, ext) else "code"
        if kind == "doc":
            new = PATH_RE.sub("~", line)
            changes.append((lineno, line.rstrip(), new.rstrip(), kind))
            out_lines.append(new)
        else:
            # Keep code line UNCHANGED; surface as manual-fix.
            changes.append((lineno, line.rstrip(), line.rstrip(), kind))
            out_lines.append(line)
    new_text = "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")
    return new_text, changes


def _scan_secrets(text: str) -> list[tuple[int, str, str]]:
    """Return ``(line_no, label, matched_excerpt)`` for each secret hit."""
    hits: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for label, rx in SECRET_RES:
            m = rx.search(line)
            if m:
                excerpt = line.strip()
                if len(excerpt) > 120:
                    excerpt = excerpt[:117] + "..."
                hits.append((lineno, label, excerpt))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--check", action="store_true",
                    help="report leaks; exit 1 on any hit (default)")
    ap.add_argument("--apply", action="store_true",
                    help="rewrite path-leak matches in place; secrets "
                         "still abort with exit 1, no auto-redact")
    ap.add_argument("--paths-only", action="store_true",
                    help="skip the secret-class scan")
    ap.add_argument("--secrets-only", action="store_true",
                    help="skip the path-leak scan")
    args = ap.parse_args()
    if not args.check and not args.apply:
        args.check = True

    files = repo_files()
    if not files:
        print("normalize_paths: no PP-tracked text files in scope")
        return 0

    doc_files_with_hits: set[Path] = set()
    code_files_with_hits: set[Path] = set()
    whitelisted_files_with_hits: set[Path] = set()
    total_doc_hits = 0
    total_code_hits = 0
    total_whitelisted_hits = 0
    rewritten = 0
    secret_files_with_hits: set[Path] = set()
    total_secret_hits = 0
    allowed_code_hits = 0
    allowed_secret_hits = 0
    allowed_doc_hits = 0
    allowed_code_files: set[Path] = set()
    allowed_secret_files: set[Path] = set()
    allowed_doc_files: set[Path] = set()

    for f in files:
        text = _read(f)
        if text is None:
            continue
        rel = f.relative_to(REPO).as_posix()
        is_whitelisted = rel in WHITELIST_HISTORICAL
        code_path_allowed = _allowed(rel, "code-path")
        secret_allowed = _allowed(rel, "secret")
        doc_path_allowed = _allowed(rel, "doc-path")

        if not args.secrets_only:
            new_text, changes = _normalize_for(text, f)
            if changes:
                for lineno, before, after, kind in changes:
                    if is_whitelisted:
                        whitelisted_files_with_hits.add(f)
                        total_whitelisted_hits += 1
                        tag = "WHITELIST"
                    elif kind == "code" and code_path_allowed:
                        allowed_code_files.add(f)
                        allowed_code_hits += 1
                        tag = "ALLOW-P"
                    elif kind == "code":
                        code_files_with_hits.add(f)
                        total_code_hits += 1
                        tag = "CODE  "
                    elif kind == "doc" and doc_path_allowed:
                        allowed_doc_files.add(f)
                        allowed_doc_hits += 1
                        tag = "ALLOW-D"
                    else:
                        doc_files_with_hits.add(f)
                        total_doc_hits += 1
                        tag = "DOC   "
                    print(f"{tag} {rel}:{lineno}")
                    print(f"  -  {before}")
                    if kind == "doc" and not is_whitelisted and not doc_path_allowed:
                        print(f"  +  {after}")
                    elif kind == "doc" and doc_path_allowed:
                        print(f"  ~  allowlisted (narrative documents the audit pattern)")
                    elif kind == "code" and not code_path_allowed:
                        print(f"  !  manual fix required (replace with "
                              f"os.homedir() / Path.home() / "
                              f"process.env.USERPROFILE)")
                    elif kind == "code" and code_path_allowed:
                        print(f"  ~  allowlisted (host-pinned by design)")
                if args.apply and not is_whitelisted:
                    # only doc-classified lines were rewritten inside
                    # new_text (_normalize_for guarantees code lines
                    # come through untouched).
                    if any(c[3] == "doc" for c in changes):
                        f.write_text(new_text, encoding="utf-8")
                        rewritten += 1

        if not args.paths_only:
            hits = _scan_secrets(text)
            if hits:
                if secret_allowed:
                    allowed_secret_files.add(f)
                    allowed_secret_hits += len(hits)
                    for lineno, label, excerpt in hits:
                        print(f"ALLOW-S[{label}]  {rel}:{lineno}  {excerpt}")
                else:
                    secret_files_with_hits.add(f)
                    total_secret_hits += len(hits)
                    for lineno, label, excerpt in hits:
                        print(f"SECRET[{label}]  {rel}:{lineno}  {excerpt}")

    print()
    print(f"scanned files     : {len(files)}")
    print(f"path-leak (doc)   : {total_doc_hits} in {len(doc_files_with_hits)} file(s)"
          + (f", rewritten {rewritten} file(s)" if args.apply else ""))
    print(f"path-leak (code)  : {total_code_hits} in {len(code_files_with_hits)} file(s)"
          + " — MANUAL FIX REQUIRED" if total_code_hits else "")
    print(f"path-leak (hist.) : {total_whitelisted_hits} in {len(whitelisted_files_with_hits)} file(s) — WHITELISTED")
    print(f"path-leak (allow) : {allowed_code_hits} in {len(allowed_code_files)} file(s) — ALLOWLISTED (host-pinned)")
    print(f"secret hits       : {total_secret_hits} in {len(secret_files_with_hits)} file(s)")
    print(f"secret (allow)    : {allowed_secret_hits} in {len(allowed_secret_files)} file(s) — ALLOWLISTED (VPS-ops/meta)")

    # Exit policy:
    #   secrets present                -> always exit 1 (STOP — Owner review)
    #   code-class path hits           -> always exit 1 (needs manual fix)
    #   doc-class path hits in --check -> exit 1 (CI gate failure)
    #   doc-class path hits in --apply -> exit 0 (rewritten cleanly)
    #   historical whitelist hits      -> never gate-fail (advisory only)
    if total_secret_hits:
        return 1
    if total_code_hits:
        return 1
    if args.check and total_doc_hits:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
