# BLOCKED_DELIVERY.md Durable Fix — Cycle Plan (2026-05-20)

> /ultra ONESHOT Phase 3 — Plan accepted by Owner after Phase-0 forensic
> diagnosis. Defects in `~/.claude/hooks/scaffold-auditor.js` (does not
> honor the declared JOBS-WOZ-EXEMPT doctrine) cause repeated false-
> positive BLOCKED_DELIVERY.md regeneration. The KARIMO/distiller stream
> is **not** the owner — these are pre-existing detectors that legitimately
> carry the literal trigger tokens by design (Mistake #43 quine FP).

## Pre-state (verified)

- `BLOCKED_DELIVERY.md` regenerated 2026-05-20T11:46:19, **failure_count 7**, kill-switch ACTIVE.
- ~70 HIGH + 1 CRITICAL findings across 16 files; **10/16 read-confirmed as detectors**, 6 pending spot-check (Step 1).
- `scaffold-auditor.js` line 113-128: blind line-by-line regex scan, no allowlist read, no JOBS-WOZ honor.
- Sibling auditors (`zero-issue-gate.js` line 39-43, `zero-fiction-gate.js` line 54-55) DO implement the doctrine — scaffold-auditor.js was simply not updated.
- 24h git log on affected files: 1 hook-canonicalization commit only; stream not actively committing.

## Decisions (Owner-Accepted, autonomous-mode defaults)

1. **Allowlist scope = tight**: only the read-verified detectors + Step 1 FP-confirmed files. Real stubs get implemented, never exempted.
2. **Owner-activation format**: emit `!`-prefix `Copy-Item` line per BL-0067 (`~/.claude/hooks/` writes are classifier-denied under auto-mode).

## Steps (clickable; check off as executed)

- [ ] **Step 1** — Per-file spot-check of 6 pending entries (read-only).
- [ ] **Step 2** — Implement JOBS-WOZ-EXEMPT honor in `claude-power-pack/hooks/scaffold-auditor.js` (PP mirror source, then Owner-copy line for the loose master at `~/.claude/hooks/`).
- [ ] **Step 3** — Per-file JOBS-WOZ-EXEMPT declarations on confirmed detectors.
- [ ] **Step 4** — Run scaffold-auditor against cwd; criticalCount target = 0.
- [ ] **Step 5** — Delete `BLOCKED_DELIVERY.md` (only after Step 4 PASS).
- [ ] **Step 6** — Seal `vault/standards/blocked-delivery-prevention.md`.
- [ ] **Step 7** — Verification: fresh Stop event, BLOCKED_DELIVERY.md does not regenerate.
- [ ] **Step 8** — Append session_lessons.md Addendum (quine-FP class).

## Reality Contract

Zero stubs get exempted. Any of the 6 pending spot-checks that resolves
to a REAL stub gets implemented in Step 3, NOT added to the allowlist.

Sealed for execution 2026-05-20.
