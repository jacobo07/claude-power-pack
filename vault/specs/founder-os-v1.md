---
covers: [founder-os, founder_round, business-round, repo-isolation, evidence-kernel, production-reality, constitutive-ratchet]
tier: T2
status: IN PROGRESS (F0 only; F1-F7 are written here as intent and each gets its own amendment before its first edit)
supersedes: vault/specs/founder-os-v0.md (extends, does not replace)
---

# Founder OS v1 — campaign spec

## Objective
Turn the v0 evidence journal into a repo-isolated business-intelligence capability whose every
claim of impact is observed, and whose proven lessons raise the baseline for later builds.
Two deltas are required, and neither stands in for the other: a business-capability delta and
an institutional-intelligence delta (a standard a new feature inherits by execution).

## Ownership (reuse, never duplicate)
Identity: `modules/repo_identity`. Secrets: `modules/secret_firewall` (shared; Founder adds a stricter
local guard, it does not fork the patterns). Install: `tools/install_global_core.py` discovery
(`modules.mirror_discovery`). Ratchet/promotion: UCR-CIF, `modules/done_gate/strength_ladder.py`, UKDL.
Loops: existing CPP loops; from the iteration prompt only the immutable done-gate and
false-premise-as-root-cause classification are adopted.

## F0 findings (each has a regression test in `tools/test_founder_os_f0.py`)
| ID | Defect in v0 | Evidence | Class |
|---|---|---|---|
| F0-1 | Secret Firewall passes Stripe live keys and all PII (email, IBAN, card, phone) into the journal | probe on `redact_for_log`, 5 of 9 shapes passed through | gate that asserts privacy it does not measure |
| F0-2 | `estimated_cost` / `estimated_value` accepted with no currency or sign check | `record()` allow-list, no currency rule | unit-less quantity |
| F0-3 | Same `action_ref` recordable twice in a round | `record()` has no duplicate check | non-idempotent action |
| F0-4 | A crash mid-append leaves a torn last line; every later call fails as generic integrity failure with no recovery path | `_append` writes without a torn-tail rule | crash between writes |
| F0-5 | A lock left by a dead process blocks the business forever | `_locked` O_EXCL, no owner liveness | stale lock |

## Deferred with reason (registered, not silently dropped)
- Tail truncation of a hash chain is undetectable without an external anchor; a local attacker who can
  write the journal can rewrite it. Mitigation is an anchor outside the state dir. Deferred to F5.
- `authorization_ref` is metadata and confers no authority (v0 contract 4/5). Real verification needs an
  owner-grant store; designed in F0b, built before any non-internal effect is executable.
- Installed `~/.claude/skills/claude-power-pack` currently tracks another branch, so the command's
  `tools/founder_round.py` is absent there until this work lands. Installer discovery is verified
  (`_repo_population('commands')` contains `cpp-founder-round.md`); end-to-end global activation
  is a post-landing gate, not claimed now.

## Gates
G1 foundational integrity: `python tools/test_founder_os.py` and `python tools/test_founder_os_f0.py` exit 0.
Remaining gates per the campaign prompt; each is reported with its real command and exit code.

## Rollback
Each fix is one commit on `feat/founder-os-v1-20261027`; revert the commit.
