# BLOCKED_DELIVERY.md Prevention Standard

**Sealed**: 2026-05-20
**Cycle**: /ultra "Fix BLOCKED_DELIVERY.md recurrente / KERNEL vMAX-NULL-ERROR"
**Related**: `vault/plans/blocked-delivery-fix-2026-05-20.md`,
[CLAUDE.md → Reality Contract → Analytical-Log Exemption (sealed 2026-05-16)]

## What this standard is

A binding rule for any new code shipped to the Power Pack codebase whose
purpose is to **detect** scaffold-illusion patterns (Mistake #16) in
OTHER code. Such a detector necessarily carries the literal trigger
strings (see `tools/jobs_woz_triggers.json` for the canonical b64-encoded
list) as part of its detection logic or documentation. Without this
standard, every Stop-event audit re-flags the detector itself as a
violation (Mistake #43 quine FP), regenerating BLOCKED_DELIVERY.md and
tripping the kill-switch after 3 consecutive cycles.

## The contract (binding)

A detector file is exempted from the Stop-event scaffold scans (both
`scaffold-auditor.js` and `zero-issue-gate.js`) **iff both** hold:

1. **Basename allowlist** — the file's basename appears in the hardcoded
   `_JW_EXEMPT_BASENAMES` set in BOTH hooks. Adding a basename is a
   deliberate, reviewed change; never inferred from file contents.

2. **Per-file declaration** — the file contains a matching
   `JOBS-WOZ-EXEMPT sha256=<64-hex>` line AND a `JOBS-WOZ-TOKENS:
   <json-array>` line. The sha256 must equal
   `sha256(UTF-8-byte-sorted-unique(token-array).join('\n'))`.

Either condition alone is NOT exemption. This is the "double-scoped"
property of the doctrine. The "drift-evident" property comes from the
sha: if anyone adds a new trigger literal to a protected file,
re-running `tools/jobs_woz_declare.py --inplace <file>` produces a NEW
sha; the old declaration's sha stops matching; the hooks refuse the
exemption until the declaration is regenerated.

## Allowlist (as of 2026-05-20)

The canonical allowlist is the source-of-truth `_JW_EXEMPT_BASENAMES`
constant in `claude-power-pack/hooks/scaffold-auditor.js` (mirrored in
`zero-issue-gate.js`). 18 entries total: 2 original (Owner Q2a/Q3a,
2026-05-17) + 16 detector basenames added 2026-05-20.

The 16 additions are read-confirmed false-positive detectors that
carry trigger literals by design: scaffold-pattern arrays in
`scaffold-auditor.js`, `zero-issue-gate.js`, `zero-fiction-gate.js`,
`score.js`; QA/probe libraries `forensic_probes.py`,
`test_forensic_probes.py`, `oracle_cascade.py`, `visual.py`,
`baseline_ledger.py`; the KobiiDistiller pipeline `ingest.py`,
`run.py`, `validate.py`; investor-grade scoring `investment_ready.js`;
UI-pattern reference `design_index.py`; and two regex-misfire targets
`skill-heat-map-advisor.js`, `lazarus_revive_all.py`.

## Pre-commit gate (binding for future detectors)

Any new file whose name matches `*-gate.js`, `*-auditor.js`,
`*_probes.py`, `*_audit.py`, `score.js`, `verdict/*.py`, `*_ledger.py`,
or any file whose primary purpose is to scan OTHER code for
scaffold-illusion patterns, MUST satisfy ONE of:

1. **Pass scaffold-auditor on first commit** — only possible if all
   triggers are computed at runtime, not literal in source.

2. **Land its allowlist entry + declaration in the same commit.**
   Sequence:
   a. Add basename to `_JW_EXEMPT_BASENAMES` in BOTH
      `claude-power-pack/hooks/scaffold-auditor.js` and
      `claude-power-pack/hooks/zero-issue-gate.js`.
   b. Run `python tools/jobs_woz_declare.py <new-file> --inplace`.
   c. Verify `python tools/jobs_woz_declare.py <new-file> --check`
      exits 0.
   d. Commit all three changes together.

The gate is **pre-commit**, not pre-push.

## Sidecar source of truth

The canonical trigger literals live as base64-encoded substrings in
`tools/jobs_woz_triggers.json`. The trigger map is updated by editing
that JSON; `jobs_woz_declare.py` decodes b64 at runtime to scan
candidate files. The sidecar is itself bootstrap-safe (source carries
no plaintext slop strings); passes the Woz veto on first Write. This
is what made the durable fix possible within the classifier-denied
environment.

## Anti-bypass clauses

- **No basename-only bypass.** Adding a file to the allowlist without
  a matching declaration is a blanket exemption and violates the
  doctrine.

- **No regex-loosening bypass.** If a detector regex misfires on
  English commentary, the fix is EITHER (a) tighten the regex to
  require a code-identifier-start after the comment marker, OR (b) add
  the file to the allowlist + declare. Removing patterns from the
  regex set is NOT acceptable — loses detection capability.

- **No real-stub exemption.** A file with a real unimplemented body
  IS a real stub. Adding it to the allowlist is evasion. The
  2026-05-20 cycle's Step 1 spot-check verified 0/16 affected files
  were real stubs.

## Activation

Loose master copies live at `~/.claude/hooks/`. PP mirror sources live
at `claude-power-pack/hooks/`. The auto-mode classifier denies direct
Writes to `~/.claude/hooks/`; the canonical activation pattern is for
the Owner to execute:

```
Copy-Item "C:\Users\User\.claude\skills\claude-power-pack\hooks\scaffold-auditor.js" -Destination "C:\Users\User\.claude\hooks\scaffold-auditor.js" -Force
Copy-Item "C:\Users\User\.claude\skills\claude-power-pack\hooks\zero-issue-gate.js" -Destination "C:\Users\User\.claude\hooks\zero-issue-gate.js" -Force
```

The Stop event on the next session-close fires the loose master. Until
copy, the loose hooks use the OLD allowlist and will regenerate
BLOCKED_DELIVERY.md.

## Verification

After Owner copy, the empirical pass condition is:

```
echo '{"cwd":"<cwd>","session_id":"verify"}' | node ~/.claude/hooks/scaffold-auditor.js
```

emits `criticalCount = 0`. (Windows-script-encoding HIGH findings are
out of scope — they belong to MC-OVO-133 and are addressed by separate
work.) After empirical PASS, delete the existing `BLOCKED_DELIVERY.md`;
the next Stop event will not regenerate it.

## Cross-references

- `vault/knowledge_base/session_lessons.md` Addendum 16-19 — cycle's
  internal-error vaccines (skill-list injection, bash-heredoc,
  deep-find, response discipline, chunked Writes).
- `~/.claude/CLAUDE.md` § "Reality Contract" — the Analytical-Log
  Exemption clause that this standard implements at hook level.
- `vault/plans/blocked-delivery-fix-2026-05-20.md` — the plan-of-record
  for this cycle.
