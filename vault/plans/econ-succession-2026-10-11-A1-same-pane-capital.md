---
covers: [same-pane-capital, owner-decision-router, authority-changed-release, control-plane-economic-role, guard-effect-semantics, capital-self-inflation, ctx-same-pane-canary]
status: AWAITING_OWNER_APPROVAL
parent: vault/plans/econ-succession-2026-10-11.md
packet: ~/.claude/state/capital-authority/packets/same-pane-capital-2026-10-11.json
created: 2026-10-11
---

# A1 to econ-succession: same-pane capital for every goal, automatic release, control-plane isolation

Backup of the Master Plan shown inline in pane 5847a1a4. The inline copy is the approval surface.
Mode: EXECUTION amendment. HR-NOVELTY-001: about 80 % of the "Owner Authority" mega-prompt is already owned by
econ-succession (approved P80 20M at 2026-10-11 07:44, S0 sealed, S1 next) and by OCA (5a). This file adds only
the deltas. No new Economic OS.

## 1. Reality delta (measured 2026-10-11, read-only)

| fact | value | source |
|---|---|---|
| ctx-same-pane L1 cap / used | 16,000,000 / 18,072,474 (settled 17,723,797, open 348,677), programme null | `mission_spend.py goal-status`, `programme-status` |
| worker 6d8f3412 | 5.60M main, transcript idle since 2026-10-10 17:14; mission m-4d1b851262ff RUNNING + owner hold, liveness BLOCKED | `goal-autopsy`, `gsd_mission.py status` |
| coordinator d5063bac | role `pane`, 1,060,943 bound to the goal (98 calls, 18.8M pre-bind); idle since 04:04 | `goal-autopsy` |
| autopsy vs ledger | autopsy explains 6.66M of 18.07M: subagent spend missing (ctx-same-pane S1 fixes it) | `goal-autopsy` |
| S1+S4 packet | `vault/programs/ctx-same-pane/REARM-S1-S4.md` at fe66a5db, valid | git |
| same-pane approval | ALREADY LIVE for programme goals: 3 Owner-typed approvals APPLIED today (ukai-f0, econ-succession, ukai-f3), no terminal | `capsules.jsonl` |
| why I used the terminal | I took the legacy `goal-declare --owner` path for a cap-only goal instead of compiling an OCA packet | this session |
| guard false positive | `destructive_doctrine_card.js:39` `/\b(?:...|del\s|erase\s)/i` matched the Spanish word "del" inside a quoted Write-Host string | hook source + the blocked command |
| live writers | econ-succession lineage (open 1.2M) owns `econ_admission.js`, `capital_authority.py`, `succession.py`; `gsd_mission.py` dirty by another writer | goal-status, RESUMPTION_FILE |

## 2. Root-cause matrix

| id | verdict | evidence / owner |
|---|---|---|
| OWNER_AUTHORITY_CONFLATED_WITH_TERMINAL | PARTIAL: only on the legacy cap path (`goal-declare --owner`, `goal-programme --owner`); the OCA path already uses the pane | mission_spend.py:1071 |
| DUPLICATE_OWNER_CONFIRMATION / GOAL_ID_MECHANICS | CONFIRMED on the legacy path; REJECTED on OCA (packet binds goal + amount) | same |
| PREMODEL_DECISION_ROUTER_MISSING | PARTIAL: econ_admission is pre-model but has no approve verb; econ-succession S2 adds it | parent RC6 |
| AUTHORITY_CAPTURE_AND_MUTATION_COUPLED | CONFIRMED legacy; OCA separates capture (transcript) from apply (capital_authority.apply) | |
| OWNER_DONE_ACK_REQUIRED | CONFIRMED (my "reply done"); the ledger state was observable the whole time | this session |
| MANUAL_MISSION_RELEASE | CONFIRMED: no subscriber turns an APPLIED capsule into `gsd_mission release`; dgl has a capsule wake for its own chain only | e1ffe906 |
| CONTROL_PLANE_FALSE_POSITIVE_GUARD | CONFIRMED, FALSE_POSITIVE: token match anywhere in the command text, including string literals | hook:39 |
| CONTROL_PLANE_CHARGED_TO_PRODUCTIVE_GOAL | CONFIRMED: 1.06M of coordinator spend on the productive lease | autopsy |
| CAPITAL_REQUEST_SELF_INFLATION | CONFIRMED: recommendation 20,773,843 -> 22,072,474 (+1.30M) with zero productive progress; the +1.30M is coordinator spend + reservations | goal-status history |
| HARD_CAP_ADMISSION_TOO_LATE | PARTIAL: refusal at 16,044,483, then 16.24M, then 16.77M (in-flight subagent settles), then +1.06M coordinator + 0.35M open. Subagent calls never cross UserPromptSubmit admission. Exact split comes from S1 | receipts |
| SUBAGENT_SPEND_MISSING_FROM_AUTOPSY | CONFIRMED; already ctx-same-pane S1 | |

## 3. Delta workstreams (folded into econ-succession, funded by goal econ-succession-a1)

| ws | content | owner touched | mode | P50 |
|---|---|---|---|---|
| D1 | guard effect semantics: destructive shapes match at command position only, never inside quoted strings; typed control-plane effects (open Owner UI, apply receipt, release mission) are not destructive; FP telemetry row per block later proven safe | `hooks/destructive_doctrine_card.js` | EXECUTION | 0.4M |
| D2 | semantic one-word approval: a closed ES/EN lexicon (approve, yes, y, si, dale, ok, adelante, hazlo, subelo, raise it, go ahead, do it) is approval ONLY when exactly one unexpired packet was displayed in this session after the Owner's previous message; two packets = refuse as ambiguous; any negation = none | `capital_authority.parse_approval` (after econ-succession S2/S3 land; coordinated, never concurrent) | EXECUTION | 0.5M |
| D3 | AuthorityChanged -> release: an APPLIED capsule row is the event. The sweep finds missions whose hold carries typed reason CAPITAL for that goal, re-runs admission (executable >= next-call floor + reserves) and calls `gsd_mission.py release`. Untyped holds are never woken. New module, called by the sweep; `gsd_mission.py` is not edited | new `modules/provider_routing/authority_release.py` + one sweep stage | EXECUTION | 0.8M |
| D4 | cap-only goals into the programme path: apply on `programme: null` sets the programme, then `lease_open` L2 (cap = ceiling - used - reserves); the released worker binds to L2. L1 stays immutable | capital_authority.apply + ledger (existing) | EXECUTION | 0.6M |
| D5 | control-plane economic role: a pane whose binding source is cwd but which only plans, reports, applies or releases is role `control`, charged to a programme control reserve, not the productive lease. A packet's ceiling is computed from the productive baseline frozen at compile time; a re-compile for the same goal with no productive settle in between that asks for more raises CAPITAL_REQUEST_SELF_INFLATION and keeps the old figure | binding record (existing `role` field), packet compiler | EXECUTION | 0.8M |
| D6 | subagent admission: an Agent dispatch on a bound goal is admitted pre-dispatch against predicted floor (measured 25-106K per call) x bound calls; refused when it cannot fit. Exact overshoot split published first | PreToolUse goal guard (existing) | PLAN (2 calls) then EXECUTION | 0.6M |
| D7 | Autonomy CI: extend `tools/test_econ_succession.py` with the 22 adversarial cases of the prompt (each refusal paired with an admitted control) | test file | EXECUTION | 0.8M |
| D8 | vault, FIOS, UKDL (hard rules only after proof), CBR | vault | EXECUTION | 0.4M |
| canary | ctx-same-pane, below | - | EXECUTION | 0.3M |
| reserve / meta-tax | | | | 0.6M / 0.5M |

econ-succession-a1 budget: SEMANTIC LOWER BOUND 2.5M, LOWER 4M, P50 6.3M, P80 8.5M, P95 12M (low-medium confidence; S0 of
ctx-same-pane ran 13x over, so P95 is wide). HARD AUTHORITY = the approved tier.

## 4. Security model

- Authority source: an Owner entry in this session's transcript (type=user, origin.kind=human, promptSource typed|queued,
  not meta) typed AFTER an assistant entry that displayed the packet sha. Unchanged OCA rule.
- What the terminal challenge proved: a person at an interactive console confirmed the goal id. It never bound the
  amount. The OCA path binds goal, amount, scope, expiry and invalidators to a hash the Owner saw. It is stronger on
  intent, equal on anti-self-escalation (the model cannot emit a user-role prompt through the harness).
- Residual: a process that writes the transcript file directly could forge an entry. econ-succession S2 closes it with a
  hook-written receipt at UserPromptSubmit time (the model cannot fire that event); D2 relies on it.
- The legacy `--owner` TTY path stays as a cold emergency fallback, out of the normal workflow.

## 5. ctx-same-pane canary (minimum safe slice = existing OCA code)

Packet `same-pane-capital-2026-10-11.json` binds ctx-same-pane, measured settled 17,723,797 + open 348,677:
P50 22,072,474 (headroom 4.0M = S1 1.5 + S4 1.5 + reserve 1.0), P80 23,072,474, P95 24,572,474.
The +1.30M over the earlier 20,773,843 is historical coordinator spend already on the ledger; headroom is unchanged
(no self-inflation of the request). History is not rewritten: L1 stays 16M and exhausted.
After `approve`: revalidate -> apply (programme) -> lease_open L2 -> release m-4d1b851262ff -> the worker runs
REARM-S1-S4.md with no GSD plan-phase. In this first canary the runtime agent runs apply + release in the same turn;
after D3 it is model-free.

## 6. Rollback

Kill switches: CPP_ECON_APPROVE=off, CPP_AUTHORITY_RELEASE=off, CPP_DESTRUCTIVE_CARD=off (existing guard switch, if
present; otherwise added with D1). Journals are append-only: undo = compensating rows (revoke, lower programme, close
lease). One micro-commit per workstream.

## 7. Approval surface

`approve` = P50 for both goals; `approve p80`; `approve ctx-same-pane only` = canary only; `revoke <goal>` later.
Excluded: settings.json edits, raising any exhausted lease, S2/S3/S5-S7 and A1 of ctx-same-pane, new scope, anything
above the displayed tier. Invalidators: packet sha mismatch; settled+open moves > 500,000 before apply; plan scope edit;
expiry 2026-10-14T00:00:00Z; revoke.
