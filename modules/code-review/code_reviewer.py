"""code_reviewer.py -- Code Review Skill verdict engine (FAST + DEEP modes).

PP Quality Triangle Closer:
  Auto-Testing Gate (correction) + Arch-Check (design) + Code Review (this).

Reads a unified diff from STDIN; emits JSON with verdict + findings.

Modes:
  --fast (default): <30 s wall-clock. PP-doctrine + security + complexity
                    + per-language linter dispatch. No LLM.
  --deep:           <60 s. Adds patterns.jsonl history + lesson-citation
                    block. Used by /code-review skill, not the gate.

Spec: vault/specs/code-review-skill.md
Plan: vault/plans/code-review-skill-2026-05-23.md

Reality Contract:
  BLOCK only for secrets / dangerous eval / dynamic shell=True.
  WARN for length / doctrine violations / complexity.
  SKIP-honest when external linters are missing -- never installs.

Recursion guard: CLAUDEPP_CODEREVIEW_RUNNING=1 short-circuits to pass.
Opt-out: CLAUDEPP_CODEREVIEW_DISABLED=1 short-circuits to pass.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUDGET_FAST = 30.0
DEFAULT_BUDGET_DEEP = 60.0
PER_LINTER_BUDGET = 8.0
REVIEWS_DIR = PP_ROOT / "vault" / "reviews"
PATTERNS_LOG = REVIEWS_DIR / "patterns.jsonl"

# Shannon-entropy floor for promoting a password-shaped literal from
# INFO to BLOCK. Dictionary-shaped test fixtures fall below this; real
# random secrets land above.
PASSWORD_ENTROPY_FLOOR = 3.5

# --- Severity ---
BLOCK = "BLOCK"
WARN = "WARN"
INFO = "INFO"

# Verdict values (also map to auto_test.py --gate combined verdict).
VERDICT_PASS = "pass"
VERDICT_WARN = "warn"
VERDICT_BLOCK = "block"
VERDICT_SKIP = "skip"


# --- Finding shape ---
@dataclass
class Finding:
    severity: str
    category: str
    file: str
    line: int
    message: str
    fix: str = ""
    source_class: str = ""   # doctrine / security / complexity / linter-X
    lesson_cited: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# --- Unified-diff parser ---
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass
class DiffFile:
    path: str
    additions: list[tuple[int, str]] = field(default_factory=list)


def parse_unified_diff(diff_text: str) -> list[DiffFile]:
    """Parse `git diff --staged`-shape unified diff.

    Returns list of DiffFile, each with additions list (1-indexed line
    numbers of the NEW file + line content without the leading '+').
    Robust to: binary-file markers, mode-only changes, hunks split
    across files. Skips file headers and removed lines.
    """
    files: list[DiffFile] = []
    cur: DiffFile | None = None
    cur_line = 0
    in_hunk = False

    for raw in diff_text.splitlines():
        if raw.startswith("+++ "):
            rest = raw[4:].strip()
            if rest == "/dev/null":
                cur = None
            else:
                p = rest[2:] if rest.startswith(("a/", "b/")) else rest
                cur = DiffFile(path=p)
                files.append(cur)
            in_hunk = False
            continue
        if cur is None:
            continue
        if raw.startswith("@@"):
            m = HUNK_RE.match(raw)
            if m:
                cur_line = int(m.group(1))
                in_hunk = True
            continue
        if not in_hunk:
            continue
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("+"):
            cur.additions.append((cur_line, raw[1:]))
            cur_line += 1
        elif raw.startswith("-"):
            pass
        elif raw.startswith("\\"):
            pass
        else:
            cur_line += 1

    return [f for f in files if f.additions]


def _shannon_entropy(s: str) -> float:
    """Shannon entropy in bits per character. Empty string returns 0."""
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


# --- PP-doctrine detectors (regex on added lines) ---
DOCTRINE = [
    (
        WARN, "doctrine-bare-python-spawn",
        re.compile(
            r"""(?ix)
            \b(?:execSync|spawn|spawnSync|exec|fork|Popen|check_output|check_call|call)\s*\(\s*
            ['"](?:python|python3)['"]
            """,
            re.VERBOSE,
        ),
        "Bare 'python' in spawn call -- resolves to Microsoft Store stub on Win11.",
        "Use getPythonCommand() (hook-utils.js) or find absolute path via $env:CLAUDEPP_PY_EXE.",
        "2026-05-14 Stop-hook PATH: bare `python` resolves to Store stub on Win11",
    ),
    (
        WARN, "doctrine-bare-node-spawn",
        re.compile(
            r"""(?ix)
            \b(?:execSync|spawn|spawnSync|exec)\s*\(\s*
            ['"]node['"]
            """,
            re.VERBOSE,
        ),
        "Bare 'node' in spawn call -- use process.execPath to neutralize PATH variance.",
        "Replace with process.execPath or getNodeCommand() helper.",
        "2026-05-14 Stop-hook PATH (sister rule for node)",
    ),
    (
        WARN, "doctrine-ps-bare-git",
        re.compile(
            r"""(?ix)
            (?:^|[\s;|`])git(?:\.exe)?\s+(?:status|log|diff|add|commit|push|fetch|pull|rev-parse|rev-list)
            """,
            re.VERBOSE,
        ),
        "Bare 'git' in PowerShell context -- git is NOT on PowerShell -NonInteractive PATH on this host.",
        "Use absolute path: $g = 'C:\\Program Files\\Git\\cmd\\git.exe'; & $g <args>",
        "2026-05-21 PowerShell git PATH gap (feedback_powershell_git_path_gap)",
    ),
    (
        WARN, "doctrine-cd-prefix-git",
        re.compile(
            r"""(?ix)
            \bcd\s+\S+\s*&&\s*git\b
            """,
            re.VERBOSE,
        ),
        "'cd <dir> && git' triggers permission prompts AND sandbox error-loop after 3 invocations.",
        "Use `git -C <path> <args>` to avoid the cd prefix.",
        "feedback_no_cd_prefix_on_git",
    ),
    (
        WARN, "doctrine-utf8-no-bom-strip",
        re.compile(
            r"""(?ix)
            \.read_text\s*\(\s*encoding\s*=\s*['"]utf-8['"]\s*\)
            """,
            re.VERBOSE,
        ),
        "read_text('utf-8') keeps the BOM if writer was PS Out-File; json.loads then fails silently.",
        "Switch to encoding='utf-8-sig' on cross-tool reads.",
        "feedback_python_utf8_bom (BL-0036)",
    ),
    (
        WARN, "doctrine-os-open-no-binary",
        re.compile(
            r"""(?ix)
            \bos\.open\s*\([^)]*os\.O_(?:WRONLY|RDWR|CREAT)
            (?![^)]*os\.O_BINARY)
            """,
            re.VERBOSE,
        ),
        "os.open without O_BINARY translates \\n to \\r\\n on Windows; re-reads compound.",
        "Bitwise-OR `getattr(os, 'O_BINARY', 0)` into the flags.",
        "feedback_windows_text_mode_compounding (BL-0014)",
    ),
    (
        WARN, "doctrine-raw-writeFileSync-state",
        re.compile(
            r"""(?ix)
            \bfs\.writeFileSync\s*\([^)]*(?:registry|slots|state|cache|index)\.(?:json|jsonl)
            """,
            re.VERBOSE,
        ),
        "Raw fs.writeFileSync on shared-state JSON without atomic-write -- crash-cleanup orphans .tmp files.",
        "Use modules/zero-crash/hooks/atomic_write.js (aw.atomicWriteJson) for any registry/state JSON.",
        "2026-05-10 BL-0073: atomic_write bypassed for registry write",
    ),
    (
        WARN, "doctrine-stop-hook-additionalContext",
        re.compile(
            r"""(?ix)
            (?:hookEventName\s*[:=]\s*['"]Stop['"][\s\S]{0,500}?hookSpecificOutput
              |hookSpecificOutput[\s\S]{0,500}?hookEventName\s*[:=]\s*['"]Stop['"])
            """,
            re.VERBOSE,
        ),
        "Stop hook returning hookSpecificOutput -- harness rejects every such payload. Only PreToolUse/UserPromptSubmit/PostToolUse support it.",
        "On Stop, emit top-level keys only: {continue, suppressOutput, stopReason, decision, reason, systemMessage}.",
        "2026-05-14 Stop-hook schema: no hookSpecificOutput",
    ),
    (
        WARN, "doctrine-bash-from-windows",
        re.compile(
            r"""(?ix)
            \brun_in_background\s*[:=]\s*true[\s\S]{0,200}?
            (?:next\s+dev|turbopack|phx\.server|mix\s+phx\.server)
            """,
            re.VERBOSE,
        ),
        "Long-lived dev server via run_in_background -- on Windows, child node processes orphan after TaskStop.",
        "Use the global SessionEnd orphan-reaper hook + Get-Process verification before turn end.",
        "2026-05-22 Background Process Hygiene (post-host-crash)",
    ),
]

# --- Security detectors (high-entropy keys + dangerous eval/shell) ---
# Note: the password-shaped detector lives separately because it needs
# an entropy gate to avoid flagging dictionary-word test fixtures.
SECURITY_KEY_PATTERNS = [
    (
        "security-aws-access-key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "Hardcoded AWS access key.",
        "Move the credential to environment variables or a secret manager. Rotate the leaked key immediately.",
    ),
    (
        "security-aws-secret-key",
        re.compile(
            r"""(?ix)
            aws[_-]?secret(?:[_-]?access)?[_-]?key
            \s*[:=]\s*['"][A-Za-z0-9/+]{40}['"]
            """,
            re.VERBOSE,
        ),
        "Hardcoded AWS secret access key.",
        "Move to env / secret manager. Rotate the leaked key.",
    ),
    (
        "security-openai-key",
        re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
        "Hardcoded OpenAI API key.",
        "Move to env (OPENAI_API_KEY). Rotate the leaked key.",
    ),
    (
        "security-anthropic-key",
        re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b"),
        "Hardcoded Anthropic API key.",
        "Move to env (ANTHROPIC_API_KEY). Rotate the leaked key.",
    ),
    (
        "security-github-token",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b"),
        "Hardcoded GitHub token.",
        "Move to env (GITHUB_TOKEN). Rotate.",
    ),
    (
        "security-private-key-block",
        re.compile(r"-----BEGIN (?:RSA|EC|DSA|OPENSSH|PGP|ENCRYPTED) PRIVATE KEY-----"),
        "Hardcoded private-key PEM block.",
        "Remove from source. Move to secure key store. Rotate the key.",
    ),
]

# Password-shaped assignment. Capture the literal value so we can
# entropy-gate it: dictionary-word fixtures (entropy < 3.5) are INFO;
# random-looking strings are BLOCK.
PASSWORD_SHAPED_RE = re.compile(
    r"""(?ix)
    (?:password|passwd|pwd|secret|api[_-]?key|token)
    \s*[:=]\s*['"]([^'"\s]{8,})['"]
    """,
    re.VERBOSE,
)

INJECTION_PATTERNS = [
    (
        "security-eval-dynamic",
        re.compile(
            r"""(?ix)
            \beval\s*\(\s*(?!['"])[A-Za-z_][A-Za-z_0-9.\[\]'"]*\s*\)
            """,
            re.VERBOSE,
        ),
        "eval() on a non-literal expression -- code-injection risk.",
        "Replace with explicit parsing (ast.literal_eval for Python, JSON.parse for JS, never eval on user data).",
    ),
    (
        "security-exec-dynamic",
        re.compile(
            r"""(?ix)
            \bexec\s*\(\s*(?!['"])[A-Za-z_][A-Za-z_0-9.\[\]'"]*\s*\)
            """,
            re.VERBOSE,
        ),
        "exec() on a non-literal expression -- code-injection risk.",
        "Refactor to avoid dynamic exec; use explicit dispatch tables.",
    ),
    (
        "security-shell-true-dynamic",
        re.compile(
            r"""(?ix)
            subprocess\.(?:run|call|check_call|check_output|Popen)\s*\(
            [^)]*?\bshell\s*=\s*True
            [^)]*?
            (?:request\.|input\(|sys\.argv|os\.environ\[|args\.|f['"])
            """,
            re.VERBOSE,
        ),
        "subprocess(shell=True, ...) with dynamic input -- shell-injection risk.",
        "Use shell=False with a list argv. If shell is required, hard-validate and escape via shlex.quote().",
    ),
]


# --- Complexity heuristics ---
PY_FUNC_RE = re.compile(r"^\s*(?:async\s+)?def\s+\w+\s*\(")
JS_FUNC_RE = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?(?:function\s+\w+|const\s+\w+\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>)"
)


def _detect_complexity(df: DiffFile) -> list[Finding]:
    out: list[Finding] = []
    if not df.additions:
        return out
    is_py = df.path.endswith(".py")
    is_js = df.path.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"))
    if not (is_py or is_js):
        return out

    func_re = PY_FUNC_RE if is_py else JS_FUNC_RE
    added = df.additions
    i = 0
    while i < len(added):
        line_no, content = added[i]
        if func_re.match(content):
            start = line_no
            end = line_no
            base_indent = len(content) - len(content.lstrip())
            j = i + 1
            while j < len(added):
                nl, nc = added[j]
                if nl != end + 1:
                    break
                if not nc.strip():
                    end = nl
                    j += 1
                    continue
                nc_indent = len(nc) - len(nc.lstrip())
                if nc_indent <= base_indent and not nc.startswith((" ", "\t")):
                    break
                end = nl
                j += 1
            length = end - start + 1
            if length > 80:
                out.append(Finding(
                    severity=WARN,
                    category="complexity-long-function",
                    file=df.path,
                    line=start,
                    message=f"Function spans {length} lines (>80 threshold).",
                    fix="Extract sub-functions; aim for <= 40 lines per function.",
                    source_class="complexity",
                    lesson_cited="anti-monolith Ley 28 (function-size)",
                ))
            i = j
            continue
        i += 1

    max_depth_seen = 0
    max_line = 0
    if is_py:
        for ln, c in added:
            stripped = c.rstrip()
            if not stripped or stripped.lstrip().startswith("#"):
                continue
            indent_units = (len(c) - len(c.lstrip())) // 4
            if indent_units > max_depth_seen:
                max_depth_seen = indent_units
                max_line = ln
    else:
        depth = 0
        for ln, c in added:
            for ch in c:
                if ch in "{(":
                    depth += 1
                    if depth > max_depth_seen:
                        max_depth_seen = depth
                        max_line = ln
                elif ch in "})":
                    depth = max(0, depth - 1)

    if max_depth_seen > 5:
        out.append(Finding(
            severity=WARN,
            category="complexity-nesting-depth",
            file=df.path,
            line=max_line,
            message=f"Nesting depth reached {max_depth_seen} (>5 threshold).",
            fix="Extract guard clauses or sub-functions to flatten.",
            source_class="complexity",
            lesson_cited="anti-monolith (cyclomatic)",
        ))

    return out


# Prose / documentation file extensions that legitimately mention code
# constructs (git subcommands, python invocations, eval/exec) as
# illustrative text. Doctrine-class detectors are silenced for these
# extensions to eliminate the markdown-prose false-positive class.
PROSE_EXTENSIONS = {".md", ".rst", ".txt", ".markdown", ".rdoc"}

# The reviewer's own source files. When these appear in a staged diff,
# security pattern matches are demoted from BLOCK to INFO -- the regex
# pattern strings inside the detector itself are guaranteed
# false-positives. A real secret smuggled into the detector still gets
# logged at INFO; the gate stops blocking the detector's own commits.
SELF_REVIEW_PATH_SUFFIXES = (
    "modules/code-review/code_reviewer.py",
    "modules/code-review/test_v_block.py",
    "modules/code-review/test_combined_gate.py",
    "modules/code-review/test_closed_loop.py",
    r"modules\code-review\code_reviewer.py",
)


def _is_prose_file(path: str) -> bool:
    lo = path.lower()
    for ext in PROSE_EXTENSIONS:
        if lo.endswith(ext):
            return True
    return False


def _is_self_review_path(path: str) -> bool:
    p = path.replace("\\", "/").lower()
    for suffix in SELF_REVIEW_PATH_SUFFIXES:
        if p.endswith(suffix.replace("\\", "/").lower()):
            return True
    return False


# --- Detector dispatch ---
def _detect_doctrine(df: DiffFile) -> list[Finding]:
    # Doctrine detectors fire on real code, not prose. A markdown file
    # naming "git status" in instructions is documentation, not a
    # PowerShell script calling bare git.
    if _is_prose_file(df.path):
        return []
    out: list[Finding] = []
    for ln, content in df.additions:
        for severity, cat, rgx, msg, fix, lesson in DOCTRINE:
            if rgx.search(content):
                out.append(Finding(
                    severity=severity, category=cat, file=df.path,
                    line=ln, message=msg, fix=fix,
                    source_class="doctrine", lesson_cited=lesson,
                ))
    return out


def _detect_security(df: DiffFile) -> list[Finding]:
    # Self-review path: demote BLOCK -> INFO for security patterns that
    # are actually the detector's own regex strings (the detector file
    # contains AKIA[...]{16} etc. as pattern literals).
    is_self = _is_self_review_path(df.path)
    # Prose files (markdown / rst / txt) routinely quote pattern strings
    # as documentation ("the detector looks for AKIA[0-9A-Z]{16}"). The
    # security detector treats these as INFO rather than BLOCK; a real
    # secret accidentally pasted in a README still surfaces in the
    # findings list, just without blocking the commit.
    is_prose = _is_prose_file(df.path)
    demote = is_self or is_prose
    demote_note = (
        " [demoted: prose / documentation file]"
        if is_prose and not is_self else
        " [demoted on self-review: detector pattern literal]"
        if is_self else ""
    )
    out: list[Finding] = []
    for ln, content in df.additions:
        # High-entropy key formats. BLOCK on real source; INFO on self-review.
        for cat, rgx, msg, fix in SECURITY_KEY_PATTERNS:
            if rgx.search(content):
                sev = INFO if demote else BLOCK
                self_note = demote_note
                out.append(Finding(
                    severity=sev, category=cat, file=df.path,
                    line=ln, message=msg + self_note, fix=fix,
                    source_class="security",
                    lesson_cited="universal-secret-rule",
                ))
        # Password-shaped assignment: entropy gate decides BLOCK vs INFO.
        # Self-review and prose files always demote to INFO.
        for m in PASSWORD_SHAPED_RE.finditer(content):
            literal_value = m.group(1)
            entropy = _shannon_entropy(literal_value)
            if entropy >= PASSWORD_ENTROPY_FLOOR:
                sev = INFO if demote else BLOCK
                self_note = demote_note
                out.append(Finding(
                    severity=sev,
                    category="security-password-literal-high-entropy",
                    file=df.path, line=ln,
                    message=(f"Password-shaped literal with Shannon entropy "
                             f"{entropy:.2f} >= {PASSWORD_ENTROPY_FLOOR} "
                             f"(looks like a real secret)." + self_note),
                    fix="Move to env / secret manager.",
                    source_class="security",
                    lesson_cited="universal-secret-rule",
                ))
            else:
                out.append(Finding(
                    severity=INFO,
                    category="security-password-literal-low-entropy",
                    file=df.path, line=ln,
                    message=(f"Password-shaped literal but low entropy "
                             f"({entropy:.2f} < {PASSWORD_ENTROPY_FLOOR}) "
                             f"-- likely a test fixture, not BLOCKed."),
                    fix="Confirm this is a test fixture; otherwise move to env.",
                    source_class="security",
                    lesson_cited="universal-secret-rule (entropy-gated)",
                ))
        # Injection patterns. BLOCK on real source; INFO on self-review.
        for cat, rgx, msg, fix in INJECTION_PATTERNS:
            if rgx.search(content):
                sev = INFO if demote else BLOCK
                self_note = demote_note
                out.append(Finding(
                    severity=sev, category=cat, file=df.path,
                    line=ln, message=msg + self_note, fix=fix,
                    source_class="security",
                    lesson_cited="universal-injection-rule",
                ))
    return out


# --- External linter dispatch (SKIP-honest) ---
def _detect_project_type(cwd: Path) -> dict[str, bool]:
    pyproject = cwd / "pyproject.toml"
    return {
        "python_ruff": (
            pyproject.is_file()
            and "[tool.ruff]" in pyproject.read_text(
                encoding="utf-8", errors="replace"
            )
        ),
        "node_eslint": (
            (cwd / "node_modules" / ".bin" / "eslint").exists()
            or (cwd / "node_modules" / ".bin" / "eslint.cmd").exists()
        ),
        "elixir_mix": (cwd / "mix.exs").is_file(),
        "java_maven": (
            any(cwd.glob("**/pom.xml")) if cwd.is_dir() else False
        ),
    }


def _run_ruff(staged_py_files: list[Path], cwd: Path,
              deadline: float) -> list[Finding]:
    ruff = shutil.which("ruff")
    if not ruff:
        return [Finding(
            severity=INFO, category="skip-tool", file="-", line=0,
            message="ruff not installed.",
            fix="pip install ruff",
            source_class="linter-ruff",
        )]
    if not staged_py_files:
        return []
    rel_args = []
    for p in staged_py_files:
        try:
            rel_args.append(str(p.relative_to(cwd)))
        except ValueError:
            rel_args.append(str(p))
    try:
        timeout = max(0.5, deadline - time.monotonic())
        proc = subprocess.run(
            [ruff, "check", "--output-format=json",
             "--select", "E,F,W,B,S", *rel_args],
            cwd=str(cwd), capture_output=True, timeout=timeout,
        )
        if proc.returncode not in (0, 1):
            return [Finding(
                severity=INFO, category="skip-tool", file="-", line=0,
                message=f"ruff failed rc={proc.returncode}",
                fix=proc.stderr.decode("utf-8", "replace")[:200],
                source_class="linter-ruff",
            )]
        items = json.loads(proc.stdout.decode("utf-8", "replace") or "[]")
        out: list[Finding] = []
        # Ruff "S" rules are bandit-derived; many are heuristic
        # (S105 flags any string assigned to a variable named "password",
        # S603 flags every subprocess.run). These are useful WARNs but
        # noisy as BLOCKs. The custom security detector above already
        # catches the real BLOCK material (high-entropy keys + eval +
        # shell=True with dynamic input). Default ruff to WARN; promote
        # specific high-confidence codes if needed.
        for it in items:
            code = it.get("code", "")
            out.append(Finding(
                severity=WARN,
                category=f"ruff-{code or '?'}",
                file=it.get("filename", "-"),
                line=(it.get("location") or {}).get("row", 0),
                message=it.get("message", ""),
                fix=(it.get("fix") or {}).get("message", ""),
                source_class="linter-ruff",
            ))
        return out
    except subprocess.TimeoutExpired:
        return [Finding(
            severity=INFO, category="timeout-tool", file="-", line=0,
            message="ruff timed out within per-linter budget.",
            fix="Reduce staged Python file count or raise PER_LINTER_BUDGET.",
            source_class="linter-ruff",
        )]
    except Exception as exc:
        return [Finding(
            severity=INFO, category="skip-tool", file="-", line=0,
            message=f"ruff crashed: {type(exc).__name__}",
            fix=str(exc)[:200],
            source_class="linter-ruff",
        )]


def _run_mix_format(cwd: Path, deadline: float) -> list[Finding]:
    mix = shutil.which("mix")
    if not mix:
        return [Finding(
            severity=INFO, category="skip-tool", file="-", line=0,
            message="mix not in PATH.",
            fix="Install Elixir (scoop install elixir).",
            source_class="linter-mix",
        )]
    try:
        timeout = max(0.5, deadline - time.monotonic())
        proc = subprocess.run(
            [mix, "format", "--check-formatted"],
            cwd=str(cwd), capture_output=True, timeout=timeout,
        )
        if proc.returncode != 0:
            files_out = proc.stdout.decode("utf-8", "replace").splitlines()
            return [Finding(
                severity=WARN, category="mix-format",
                file=(line.strip() or "-"), line=0,
                message="File not formatted per mix format.",
                fix=f"Run: mix format {line.strip()}",
                source_class="linter-mix",
            ) for line in files_out
              if line.strip() and not line.startswith("**")]
        return []
    except subprocess.TimeoutExpired:
        return [Finding(severity=INFO, category="timeout-tool",
                        file="-", line=0,
                        message="mix format timed out.",
                        fix="", source_class="linter-mix")]
    except Exception as exc:
        return [Finding(severity=INFO, category="skip-tool",
                        file="-", line=0,
                        message=f"mix crashed: {type(exc).__name__}",
                        fix=str(exc)[:200], source_class="linter-mix")]


def _run_java_skip(cwd: Path) -> list[Finding]:
    if not any(cwd.glob("**/pom.xml")):
        return []
    if shutil.which("mvn"):
        return [Finding(
            severity=INFO, category="info-tool", file="-", line=0,
            message="mvn detected but Java static analysis not invoked.",
            fix="Run `mvn checkstyle:check` manually for now.",
            source_class="linter-mvn",
        )]
    return [Finding(
        severity=INFO, category="skip-tool", file="-", line=0,
        message="checkstyle not run: mvn not in PATH.",
        fix="Install Maven (https://maven.apache.org/install.html) to enable Java review.",
        source_class="linter-mvn",
    )]


def _run_external_linters(diff_files: list[DiffFile], cwd: Path,
                          deadline: float) -> list[Finding]:
    out: list[Finding] = []
    py_files = []
    for df in diff_files:
        if df.path.endswith(".py"):
            full = cwd / df.path
            if full.is_file():
                py_files.append(full)
    has_python = bool(py_files)
    has_elixir = (cwd / "mix.exs").is_file()
    has_java_in_diff = any(df.path.endswith(".java") for df in diff_files)
    has_java_project = any(cwd.glob("**/pom.xml"))
    if has_java_in_diff and has_java_project:
        out.extend(_run_java_skip(cwd))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futures = []
        if has_python and py_files:
            sub_deadline = min(deadline, time.monotonic() + PER_LINTER_BUDGET)
            futures.append(ex.submit(_run_ruff, py_files, cwd, sub_deadline))
        if has_elixir:
            sub_deadline = min(deadline, time.monotonic() + PER_LINTER_BUDGET)
            futures.append(ex.submit(_run_mix_format, cwd, sub_deadline))
        for fut in concurrent.futures.as_completed(futures):
            try:
                out.extend(fut.result())
            except Exception as exc:
                out.append(Finding(
                    severity=INFO, category="linter-crash",
                    file="-", line=0,
                    message=f"linter executor crashed: {type(exc).__name__}",
                    fix=str(exc)[:200],
                    source_class="linter-?",
                ))
    return out


def _aggregate_verdict(findings: list[Finding]) -> str:
    if any(f.severity == BLOCK for f in findings):
        return VERDICT_BLOCK
    if any(f.severity == WARN for f in findings):
        return VERDICT_WARN
    return VERDICT_PASS


def _summary(verdict: str, findings: list[Finding]) -> str:
    by_sev = {BLOCK: 0, WARN: 0, INFO: 0}
    cats = set()
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
        cats.add(f.category)
    return (
        f"verdict={verdict} | "
        f"BLOCK={by_sev[BLOCK]} | WARN={by_sev[WARN]} | "
        f"INFO={by_sev[INFO]} | categories={len(cats)}"
    )


def _stdin_text() -> str:
    if sys.stdin.isatty():
        return ""
    try:
        data = sys.stdin.buffer.read()
    except (AttributeError, OSError):
        data = sys.stdin.read().encode("utf-8", errors="replace")
    return data.decode("utf-8", errors="replace")


def _short_circuit_pass(reason: str, start: float) -> dict:
    return {
        "verdict": VERDICT_PASS,
        "findings": [],
        "summary": f"short-circuit: {reason}",
        "source_classes": [],
        "timing_ms": int((time.monotonic() - start) * 1000),
        "timing_partial": False,
    }


def _resolve_diff_input(prompt_arg: str | None, cwd: Path) -> str:
    raw = prompt_arg if prompt_arg is not None else _stdin_text()
    raw = raw.strip()
    if not raw:
        try:
            g = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
            proc = subprocess.run(
                [g, "diff", "--staged"], cwd=str(cwd),
                capture_output=True, timeout=10,
            )
            return proc.stdout.decode("utf-8", errors="replace")
        except Exception:
            return ""
    if raw.startswith("{"):
        try:
            obj = json.loads(raw)
            return obj.get("diff", "")
        except json.JSONDecodeError:
            pass
    return raw


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true", default=True)
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--diff", default=None,
                        help="Inline diff (bypasses STDIN, for testing).")
    parser.add_argument("--budget", type=float, default=None)
    args = parser.parse_args(argv)

    start = time.monotonic()
    budget = args.budget or (DEFAULT_BUDGET_DEEP if args.deep
                              else DEFAULT_BUDGET_FAST)
    deadline = start + budget

    if os.environ.get("CLAUDEPP_CODEREVIEW_RUNNING") == "1":
        print(json.dumps(_short_circuit_pass("recursion-guard", start)))
        return 0
    if os.environ.get("CLAUDEPP_CODEREVIEW_DISABLED") == "1":
        print(json.dumps(_short_circuit_pass("opt-out-env", start)))
        return 0

    cwd = Path(args.cwd).resolve()
    diff_text = _resolve_diff_input(args.diff, cwd)
    if not diff_text.strip():
        print(json.dumps(_short_circuit_pass("empty-diff", start)))
        return 0

    diff_files = parse_unified_diff(diff_text)
    if not diff_files:
        print(json.dumps(_short_circuit_pass("no-additions", start)))
        return 0

    findings: list[Finding] = []
    timing_partial = False

    for df in diff_files:
        findings.extend(_detect_doctrine(df))
        findings.extend(_detect_security(df))
        findings.extend(_detect_complexity(df))

    if time.monotonic() < deadline:
        linter_deadline = min(deadline, start + budget * 0.7)
        try:
            findings.extend(_run_external_linters(
                diff_files, cwd, linter_deadline))
        except Exception as exc:
            findings.append(Finding(
                severity=INFO, category="linter-crash", file="-", line=0,
                message=f"external-linter dispatch crashed: {type(exc).__name__}",
                fix=str(exc)[:200], source_class="linter-?",
            ))

    if time.monotonic() >= deadline:
        timing_partial = True

    verdict = _aggregate_verdict(findings)
    source_classes = sorted(set(
        f.source_class for f in findings if f.source_class))

    payload = {
        "verdict": verdict,
        "findings": [f.to_dict() for f in findings],
        "summary": _summary(verdict, findings),
        "source_classes": source_classes,
        "timing_ms": int((time.monotonic() - start) * 1000),
        "timing_partial": timing_partial,
        "files_reviewed": [df.path for df in diff_files],
    }
    # DEEP mode adds lesson_candidates from the arch-check index +
    # patterns.jsonl history filtered by project type / category.
    if args.deep:
        payload["lesson_candidates"] = _lesson_candidates(
            diff_files, findings)
        payload["patterns_history"] = _patterns_history(
            findings, max_rows=10)
        # Closed loop: append a patterns.jsonl row on non-PASS verdicts.
        if verdict != VERDICT_PASS and findings:
            _append_patterns_row(verdict, findings, diff_files, cwd)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def _append_patterns_row(verdict: str, findings: list[Finding],
                          diff_files: list[DiffFile], cwd: Path) -> None:
    """Write one row to vault/reviews/patterns.jsonl. Fail-OPEN."""
    try:
        REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
        top = next((f for f in findings
                    if f.severity in (BLOCK, WARN)), findings[0])
        project_type = _detect_project_type_label(cwd)
        from datetime import datetime, timezone
        row = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "verdict": verdict,
            "category": top.category,
            "severity": top.severity,
            "file": top.file,
            "line": top.line,
            "lesson_cited": top.lesson_cited,
            "project_type": project_type,
            "files_in_diff": [df.path for df in diff_files][:5],
        }
        with PATTERNS_LOG.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")
    except (OSError, ValueError):
        pass


def _detect_project_type_label(cwd: Path) -> str:
    """Short label for the project shape; used as a filter key."""
    if (cwd / "pyproject.toml").is_file():
        return "python-pyproject"
    if (cwd / "package.json").is_file():
        return "node-package"
    if (cwd / "mix.exs").is_file():
        return "elixir-mix"
    if any(cwd.glob("**/pom.xml")):
        return "java-maven"
    return "unknown"


def _lesson_candidates(diff_files: list[DiffFile],
                       findings: list[Finding]) -> list[dict]:
    """Top lesson hits from vault/.arch-index/index.json.

    Heuristic: build a token set from the diff file paths + finding
    categories, then score each indexed source by intersection with
    the source's shingles. Return the top 5 with non-zero score.
    Returns [] if the arch-index is missing.
    """
    index_path = PP_ROOT / "vault" / ".arch-index" / "index.json"
    if not index_path.is_file():
        return []
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    sources = index.get("sources", [])
    if not sources:
        return []
    tokens: set[str] = set()
    for df in diff_files:
        for piece in re.split(r"[/\\.\-_]", df.path.lower()):
            if len(piece) >= 3:
                tokens.add(piece)
    for f in findings:
        for piece in re.split(r"[-_]", f.category.lower()):
            if len(piece) >= 3:
                tokens.add(piece)
    if not tokens:
        return []
    scored = []
    for src in sources:
        shingles = set(src.get("shingles") or [])
        if not shingles:
            continue
        inter = len(tokens & shingles)
        if inter == 0:
            continue
        scored.append((inter * (src.get("weight") or 0.5), src))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, src in scored[:5]:
        out.append({
            "path": src.get("path"),
            "section": src.get("section"),
            "title": src.get("title"),
            "class": src.get("class"),
            "score": round(score, 3),
        })
    return out


def _patterns_history(findings: list[Finding],
                       max_rows: int = 10) -> list[dict]:
    """Read patterns.jsonl (closed-loop) and return rows matching the
    current findings' categories. Last 30 days only. Returns [] if the
    file is missing or empty."""
    if not PATTERNS_LOG.is_file():
        return []
    categories = set(f.category for f in findings)
    if not categories:
        return []
    cutoff = time.time() - 30 * 24 * 3600
    out = []
    try:
        with PATTERNS_LOG.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("category") not in categories:
                    continue
                # ISO timestamp check.
                try:
                    ts_str = row.get("ts", "")
                    if ts_str.endswith("Z"):
                        ts_str = ts_str[:-1] + "+00:00"
                    from datetime import datetime as _dt
                    row_ts = _dt.fromisoformat(ts_str).timestamp()
                    if row_ts < cutoff:
                        continue
                except (ValueError, AttributeError):
                    pass
                out.append(row)
                if len(out) >= max_rows:
                    break
    except OSError:
        pass
    return out


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
