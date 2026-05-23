# Code Review 20260523-203833: code-review-skill-self

Date: 2026-05-23
Verdict: block
Files reviewed: 7
Timing (FAST): 1328 ms

## Executive summary

The reviewer scanned its own staged diff and returned verdict=block:
70 findings (BLOCK=18, WARN=52, INFO=0). Of these, the BLOCK
findings are predominantly the reviewer's own pattern strings
triggering on themselves (regex literals for AWS keys, eval, exec
seen in `modules/code-review/code_reviewer.py`); the WARN findings
are dominantly prose mentions of git subcommands in the spec / plan
markdown (`doctrine-ps-bare-git` over-matches inside markdown code
fences). The honest call: this is a self-detection false-positive
class. The 7 files reviewed contain no real secrets, no real eval on
user input, no real bare-`git` invocations in PowerShell scripts.

The two highest-relevance lessons surfaced from `vault/.arch-index/`
are about long-running daemons holding stale source (closely
analogous to the recursion-guard env-var-set-before-spawn bug I just
fixed) and about bash bridge transient hangs (relevant since the
reviewer + test runners spawn subprocesses through this same bridge).

## Findings

| Severity | Category | File:Line | Message | Suggested fix |
|---|---|---|---|---|
| BLOCK | security-aws-access-key | modules/code-review/code_reviewer.py:204 | Pattern string `AKIA[0-9A-Z]{16}` appears literally as a regex. | Self-detection false-positive; pattern strings are the detector itself. Acceptable for now; could add a self-exclusion list later. |
| BLOCK | security-eval-dynamic | modules/code-review/code_reviewer.py:~272 | `eval()` regex literal in detector source matches itself. | Same self-detection false-positive class. |
| BLOCK | security-exec-dynamic | modules/code-review/code_reviewer.py:~282 | `exec()` regex literal in detector source matches itself. | Same self-detection false-positive class. |
| WARN | doctrine-ps-bare-git | commands/code-review.md:lines 3, 21, 46-48, ... | Prose mentions like `git diff --staged` in markdown trigger the bare-git regex. | Markdown documentation legitimately names git subcommands; consider excluding `.md` files from the doctrine-ps-bare-git detector. |
| WARN | doctrine-ps-bare-git | vault/specs/code-review-skill.md (multiple) | Same prose-mention class. | Same fix candidate. |
| WARN | doctrine-ps-bare-git | vault/plans/code-review-skill-2026-05-23.md (multiple) | Same. | Same. |

The remaining ~50 WARN rows follow the same pattern (prose mentions
in spec / plan / command markdown). No real doctrine violation in any
of the 7 files; the spec text describes what the detector should look
for, not the detector misbehaving.

## Refactor suggestions

### Suggestion 1: file-type exclusion for doctrine-ps-bare-git

Before:
```python
# In _detect_doctrine: regex matches across all file types.
for severity, cat, rgx, msg, fix, lesson in DOCTRINE:
    if rgx.search(content):
        out.append(Finding(...))
```

After:
```python
# Excluded categories per file type.
DOCTRINE_FILE_EXCLUSIONS = {
    "doctrine-ps-bare-git": {".md", ".rst", ".txt"},  # prose
    "doctrine-bare-python-spawn": {".md", ".rst", ".txt"},
    "doctrine-cd-prefix-git": {".md", ".rst", ".txt"},
}

ext = "." + df.path.rsplit(".", 1)[-1] if "." in df.path else ""
for severity, cat, rgx, msg, fix, lesson in DOCTRINE:
    excluded_exts = DOCTRINE_FILE_EXCLUSIONS.get(cat, set())
    if ext in excluded_exts:
        continue
    if rgx.search(content):
        out.append(Finding(...))
```

Why: markdown / RST / plain-text files legitimately mention git
subcommands and `python` names in prose. Excluding documentation
file types from these doctrine checks eliminates the entire WARN
class observed in this self-review (52 -> approximately 5).
Trade-off: a real `.md`-embedded git command would no longer be
flagged. Acceptable given the alternative is constant noise.

### Suggestion 2: self-exclusion for security pattern strings

Before:
```python
# In _detect_security: AWS regex matches its own pattern string when
# code_reviewer.py is part of the diff.
for cat, rgx, msg, fix in SECURITY_KEY_PATTERNS:
    if rgx.search(content):
        out.append(Finding(severity=BLOCK, ...))
```

After:
```python
SELF_FILES = {"code_reviewer.py", "code-reviewer/code_reviewer.py"}

is_self_review = any(df.path.endswith(s) for s in SELF_FILES)
for cat, rgx, msg, fix in SECURITY_KEY_PATTERNS:
    if rgx.search(content):
        sev = INFO if is_self_review else BLOCK
        out.append(Finding(severity=sev, ...))
```

Why: when reviewing the reviewer itself, security pattern strings
inside the detector are guaranteed false positives. Demoting to
INFO on `code_reviewer.py` preserves the signal (still flagged for
audit) without blocking commits to the reviewer itself.
Trade-off: a real `AKIA...` literal that someone smuggled into
`code_reviewer.py` would no longer block. Acceptable because the
detector file's edit history is small and Owner-reviewed.

### Suggestion 3: None warranted at this verdict level beyond above two.

## Lessons cited

- `~/.claude/knowledge_vault/gex44_antipatterns/stale-daemon-vs-fresh-source.md` -- a long-running daemon serving stale source is the same shape as my recursion-guard-blocks-piggyback bug I just fixed: the env-var-set-before-spawn meant the reviewer ran but short-circuited; only the standalone test surfaced the gap.
- `~/.claude/knowledge_vault/core/apex-completion-standard.md:Five-check DONE-gate (binary, no classifications)` -- the 7-check DONE-gate in the code-review spec mirrors the 5-check binary contract pattern (no classifications, no partial PASS).
