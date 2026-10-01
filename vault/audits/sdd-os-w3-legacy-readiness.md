# SDD-OS W3 -- legacy spec readiness (counterfactual, measured 2026-10-01)

**What this answers:** if W3 admission had been live, which real specs in this repo could
still authorize Tier 2 work, and which would be refused with `spec_not_ready`.

**Instrument:** `modules/sdd_os/readiness.assess(spec, task_tier=2)` over every spec
`spec_binding.iter_candidates()` finds that declares `covers` (an undeclared spec can only
bind by explicit path reference). Tree: `8784ad6` + W3 working copy. No spec was rewritten.

**Denominator:** 203 spec-shaped files, 44 declared. All 44 are legacy format (none uses the
readiness keys yet).

| verdict | count |
|---|---|
| LEGACY_READY (approving status + a V-gate id or runnable command) | 20 |
| NOT_READY | 24 |

## NOT_READY, by reason

The reason code is what the gate prints. Each is fixed by editing the spec, not the gate.

| reason | specs | what fixes it |
|---|---|---|
| `status:stop` | cdicf-corpus, claude-md-compaction, efaif-expansion, egcc-corpus, egcc-expansion, memory-audit, predictive-governance, uceimr-expansion, upac-corpus (all `vault/plans/`) | these are STOP-#1 plans; the status never advanced past the approval stop. Set an approving status when approved. |
| `status:not-stated` | autocompact-per-session-flags, cdio-08-mobile-app-surface, external-capability-assimilation, gsd-long-run-v2, mobile-game-wii-port | no `status:` line at all. |
| `status:spec` | gex44-mission-plane, post-edit-diagnostics, security-scan, test-gaps | `status: SPEC (nothing below is implemented unless marked LIVE)` describes the document, it does not approve it. |
| `status:planned` / `status:plan` / `status:draft` | agent-capability-virtualization, intent-verified-done, tco-meta | not approved yet -- correct refusal. |
| `proof:no-v-gate-or-command` (approved) | exact-target-continuation, interactive-context-rollover, pp-self-eval | approved, but nothing falsifiable in the body. `interactive-context-rollover` cites results (`test_rollover 48/48`) without the command that produces them. |

## Judgement

The 24 refusals are honest by the contract: none of them states both an approval and a
runnable proof. No historical spec loses meaning -- it loses the ability to *authorize new
Tier 2 work* until its owner adds the missing line. Tier 0-1 work is unaffected.

Two classes worth a second look by their owners, not by the gate:

- `status: SPEC (...)` is a document-type label used by one author for four specs
  (including today's `security-scan`). If that author means "approved", one word fixes it.
- `vault/plans/*` STOP-#1 plans bind through `covers` like specs do. A plan stuck at STOP is
  correctly not an execution permit.

## Window

`LEGACY_WINDOW_ENDS = 2026-11-01` (`readiness.py`). After it, the 20 LEGACY_READY specs also
need the readiness keys. Corpus cases R-10/R-11 and X-10/X-11 pin both sides of the date.

Reproduce (from the repo root): `python modules/sdd_os/readiness.py --audit . --today 2026-10-01`
-- last line must read `declared=44 LEGACY_READY=20 NOT_READY=24` on the tree named above.
