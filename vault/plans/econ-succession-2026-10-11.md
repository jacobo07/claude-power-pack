---
covers: [econ-succession, self-completing-tombstone, owner-approval-receipt, successor-activation, econ-contain-2]
status: AWAITING_OWNER_APPROVAL
packet: ~/.claude/state/capital-authority/packets/econ-succession-2026-10-11.json
packet_sha256: 86ba1888c7bda34779eae9e21ba749ba638eb1b8dab132febf9bc59add83ca4d
created: 2026-10-11
---

# Econ succession: from a safe manual deadlock to automatic succession

Backup copy of the Master Plan shown inline in the planning pane. The inline copy is the approval
surface; this file is what a fresh session reads if that pane is lost.

## 1. Reality delta (measured 2026-10-11, read-only)

| fact | historical claim | measured now | source |
|---|---|---|---|
| goal econ-contain-2 cap / used | 23M / 22,756,864 | same | `mission_spend.py goal-status --goal econ-contain-2` |
| settled / reserved | 21,377,764 / 1,379,100 | same | same |
| tombstone | b1876f55, L1 | journal seq 54, reason budget_spent, used 22,756,864 | `goal-budget/econ-contain-2/spend.journal.jsonl` |
| lease exhausted flag | (implied) | `exhausted: false`, remaining 243,136; only the sid is tombstoned | goal-status |
| packet fd25efd1 | approved P50 34M | file sha fd25efd1...dfd84, expires 2026-10-13, **never applied** (no capsule row) | `capital-status`, `capsules.jsonl` |
| Owner approval | approved | transcript b1876f55, 2026-10-11T06:32:32.917Z, `approve`, origin.kind=human, promptSource=typed | transcript scan |
| apply attempt | blocked | 06:32:49 the model ran `capital-apply`; PreToolUse goal guard refused at 06:33:24 (budget_spent) | transcript |
| later Owner messages | - | 06:35:01 and 06:36:42 blocked by econ_admission; **no user entry written**, not in history.jsonl | transcript, history.jsonl |
| capture hook | - | `hooks/owner_capital_capture.js` exists; registered in neither settings.json nor the dispatcher; approvals.jsonl / pending.json never created | settings.json, dispatcher grep, state dir |
| HEAD | 999984d1 (WS-F) | 999984d1 is an ancestor; HEAD 928d0051 (other programmes since) | git log |
| reservations | 1,379,100 | a9647f12 `lease` 1,239,905 + b1876f55 `final` 139,195; both processes dead, transcripts final | journal, Win32_Process |

### Reservation truth (1,379,100)

| reservation | holder alive? | measured after its last settle | class |
|---|---|---|---|
| a9647f12 lease 1,239,905 | no (last entry 20:03:46Z) | 1,263,445 (4 calls) | REAL committed; under-reserved by 23,540 |
| b1876f55 final 139,195 | no | 138,594 (the final reply) | REAL 138,594; STALE 601 |
| unknown in-flight | - | 0: both holders dead, transcripts final | provable zero, not assumed |

Net after reconciliation: settled 22,779,803, reserved 0, released 601, used rises by 22,939.
Open item: a9647f12's whole transcript is 16,799,247 tokens; before its last settle it holds
15,535,802 vs a mark of 12,430,329 (gap 3,105,473). Probably history from before the goal existed
(predecessor econ-contain; same class as the J finding). Classified UNKNOWN until verified in S5.

## 2. Root-cause matrix

| id | failure | verdict | evidence |
|---|---|---|---|
| RC1 | APPROVED_AUTHORITY_NOT_EXECUTABLE_FROM_CONTROL_PLANE: the only apply path is a tool call inside the bound, spent session | CONFIRMED | 06:33:24 PreToolUse refusal |
| RC2 | OCA capture hook shipped but unregistered (silent dead gate) | CONFIRMED | grep: 0 registrations; no approvals.jsonl |
| RC3 | TOMBSTONE_BLOCK_ERASES_OWNER_PROVENANCE: a blocked prompt writes no user entry, and OCA accepts only a transcript user entry | CONFIRMED | 06:35/06:36 system rows only |
| RC4 | packet fd25efd1 went stale before approval: spend moved 970,635 > 500,000 after it was shown, because the pane kept working after compiling it | CONFIRMED | capital_authority.py:185 vs measured |
| RC5 | expiry is judged at apply time, not approval time | CONFIRMED in code (has not fired) | capital_authority.py:180 |
| RC6 | CONTROL_PLANE_CAN_REPORT_BUT_NOT_ACT: econ_admission verbs are status and detach only | CONFIRMED | econ_admission.js:29 |
| RC7 | TOMBSTONED_GOAL_REQUIRES_MANUAL_DETACH | CONFIRMED (design of WS-B) | property worth keeping: settle from transcript + fence |
| RC8 | SUCCESSOR_REQUIRES_FRESH_SESSION done by the Owner | PARTIAL | host can launch `claude --bg` (gsd_mission arm); cannot swap the process under an interactive pane |
| RC9 | RESUMPTION_FILE_AS_CONTROL_BUS: apply command, packet path, transcript path, L2 step only in prose | CONFIRMED | RESUMPTION_FILE.md |
| RC10 | RESERVATION_GHOST_AFTER_TOMBSTONE | PARTIAL: 601 ghost; 1,378,499 real; plus an under-reservation | section 1 |
| RC11 | ledger mark gap 3,105,473 for a9647f12 | UNKNOWN | section 1 |
| RC12 | OWNER_WAIT_STATE_STALE_AFTER_APPROVAL: the pane kept printing WAITING_OWNER_CAPITAL after `approve` | CONFIRMED | 06:35 block text |

## 3. Owner map

| capability | owner | action |
|---|---|---|
| pre-model interception | `hooks/econ_admission.js` (registered, critical lane) | EXTEND: approve/reject/modify verbs |
| Owner capture | `hooks/owner_capital_capture.js` | MERGE grammar into econ_admission, RETIRE the file |
| approval authority, capsule store | `modules/provider_routing/capital_authority.py` (5a) | EXTEND: receipts, approval-time expiry and drift |
| programme / lease / reserve / settle / tombstone | `modules/provider_routing/ledger.py` | ALREADY_DONE (lease_open idempotent + CAS; set_programme Owner-gated) |
| detach, binding generation, fence | `tools/econ_plane.py`, `hooks/lib/goal_binding.js` | CONNECT (called internally) |
| transactions | none | IMPLEMENT `modules/provider_routing/succession.py` (one module, both transactions) |
| successor launch, ContextImage | `tools/gsd_mission.py` arm + render_card | CONNECT |
| watchdog | `tools/gsd_long_run_sweep.ps1` pass | EXTEND with one succession stage |
| structured continuation | none canonical | IMPLEMENT `goal-budget/<goal>/continuation.json`; RESUMPTION_FILE becomes a projection |
| UWCP | gsd_mission is the working session-transfer substrate here | NO_WORK beyond CONNECT |
| same-pane process swap | host | EXTERNAL_LIMITATION; the pane becomes a view |
| settings.json | Owner | NO_WORK expected (econ_admission is already registered) |

## 4. Architecture

1. Owner types `approve` in the tombstoned pane.
2. econ_admission (pre-model) finds exactly one pending packet bound to this session's goal,
   parses the whole-message grammar, checks provenance (section 5), appends an immutable
   OWNER_APPROVED receipt (packet sha, goal, tier/ceiling, scope, exclusions, approval ts,
   invalidators, provenance class), blocks with 0 model tokens, spawns the transaction detached.
3. succession.py runs one journalled state machine, idempotent on (receipt id, goal):
   PREPARED -> OWNER_APPROVED -> REVALIDATING -> APPLYING -> APPLIED -> SUCCESSOR_PREPARING ->
   SUCCESSOR_READY -> RELEASED, or INVALIDATED / FAILED_SAFE / ROLLED_BACK.
   Steps: revalidate (sha, scope, drift at approval time, revocation); reconcile reservations of
   dead holders from their transcripts; set_programme (Owner path, gated on the receipt); close L1;
   lease_open(succession_id = receipt id, prev_lease = L1, reserves.recovery); internal detach of
   the predecessor sid (generation +1, fence); write continuation.json; render the card; launch the
   successor through gsd_mission arm bound to L2; journal SUCCESSOR_READY.
   Crash at any step: rerun replays from the journal; lease_open and arm are idempotent by key.
4. The tombstoned pane now answers `econ status` with the successor's state. The Owner does
   nothing else.
5. Self-completing tombstone: a below-model classifier maps durable state to exactly one of
   AUTO_SUCCESSOR_READY, WAITING_OWNER_CAPITAL, WAITING_OWNER_SCOPE, WAITING_EXTERNAL, RECOVERING,
   VERIFIED_DONE, CANCELLED, UNRECOVERABLE_EXTERNAL. The sweep drives any tombstone with an applied
   receipt and no successor. On lease exhaustion the packet is compiled at the boundary, from the
   ledger, so it cannot go stale while the pane keeps working (RC4).

## 5. Security model

- Two provenance classes, both required to name the packet sha the control plane displayed:
  (a) TRANSCRIPT_TYPED (unchanged OCA rule); (b) HOOK_ATTESTED_INTERACTIVE: UserPromptSubmit event
  whose ancestor claude.exe command line has no -p/--print/--bg and whose session displayed the
  packet. S1 measures which event and process fields really discriminate interactive from headless
  before (b) is trusted; if none do, (b) is not shipped and the pane lets the approval through to a
  one-call model turn instead (cost stated, not hidden).
- The model never authors a receipt: receipts are written only by the hook process and by
  capital_authority from (a). The transaction refuses anything above the receipt's ceiling or
  outside its goal and scope.
- The control-plane identity can do only: receipt, apply, reconcile, close, open, fence, card,
  launch. Product edits under it are refused (test V-SUCC-BYPASS).
- Residual risk: anything that can type into the Owner's terminal (the keystroke inbox) could
  forge (b). Mitigation in S2: the inbox refuses lines matching the approval grammar.

### 5.1 S1 provenance verdict (measured 2026-10-11, WU-OC1, 4 calls, 150 newest transcripts of this project)

Transcript user entries carry fields the model cannot author: `entrypoint` (`cli` interactive/bg, `sdk-cli` for -p/sdk), `sessionKind`
(`bg` on --bg workers, ABSENT on interactive panes), `origin.kind`, `promptSource`.
Counts of string-content human entries: interactive = 700 typed + 25 queued + 63 slash, all `sessionKind` absent, `entrypoint=cli`;
bg workers = 7 typed + 2 slash, all `sessionKind=bg`; sdk/-p = `entrypoint=sdk-cli`, `promptSource=sdk`, no origin.
FINDING: a --bg worker's launch prompt is stamped `origin.kind=human, promptSource=typed`, so the unchanged OCA rule (a) accepts
"approve" text delivered to a bg worker. VERDICT: ship (b) HOOK_ATTESTED_INTERACTIVE and tighten (a):
interactive = `entrypoint=='cli'` AND `sessionKind` absent, read from the approving session's own transcript entries (the
UserPromptSubmit event itself carries only session_id/transcript_path/prompt/cwd/permission_mode, so the discriminator is read from
the transcript, never from the event). Absent field on every entry of the session = unknown = not interactive. Gate: V-SUCC-HEADLESS-FORGERY.

### 5.2 S4 vs 3c98097b (decided WU-OC1b, 2026-10-13)
S4 EXTENDS 3c98097b: succession.py opens L2 only through GoalLedger.lease_open (shared _open_locked: one CAS, one idempotency key = receipt id, one envelope check) and never duplicates _auto_succeed; the auto path is policy-only, S4 is receipt-gated and raises the programme first.

## 6. Workstreams and mode

| ws | content | mode |
|---|---|---|
| S0 | bind to econ-succession; check for a live 5a writer; isolated worktree for hook edits | EXECUTION |
| S1 | provenance spike (interactive vs -p vs --bg) | PLAN (bounded: 6 calls) |
| S2 | approve verb + receipt in econ_admission; retire owner_capital_capture.js; inbox refusal | EXECUTION |
| S3 | receipts, approval-time expiry/drift, INVALIDATED row for fd25efd1 | EXECUTION |
| S4 | succession.py both transactions + crash replay | EXECUTION (contract fixed here) |
| S5 | dead-holder reservation reconciler; RC11 check | EXECUTION |
| S6 | tombstone classifier + sweep stage + boundary-time packet compile | EXECUTION |
| S7 | continuation.json canonical; RESUMPTION_FILE generated | EXECUTION |
| S8 | Autonomy CI `tools/test_econ_succession.py` (V-SUCC-*) | EXECUTION |
| S9 | real canary on econ-contain-2, then WS-G, J, K, L under L2 | EXECUTION |
| S10 | vault, FIOS, UKDL, CBR | EXECUTION |

## 7. Canaries (V-SUCC-*)

Full lifecycle; approval before expiry applied after expiry; unapproved expiry; stale plan;
amount tamper; goal mismatch; duplicate approval (one receipt, one L2, one successor); crash
mid-transaction; crash after L2; old writer after the generation bump; control-plane bypass;
reservation ghost; zero-burn wait (no model call, no reservation growth); pre-model routing;
headless forgery refused; RESUMPTION_FILE withheld; ContextImage size bound (8 KB card).
Each refusal paired with a control in which the fact exists and the action is admitted.
Real canary: econ-contain-2 reaches L2 and WS-G through succession.py, not by hand.

## 8. Rollback

Kill switches: CPP_ECON_ADMISSION=off (existing), CPP_ECON_APPROVE=off, CPP_SUCCESSION=off.
Journals are append-only: undo is compensating rows (lower programme, close lease), never deletion.
One micro-commit per workstream, each revertible. Hook edits are proven in a worktree with
mutation drills before the live file changes.

## 9. Token budget (processed tokens; per-call floor 100-215K measured)

| item | P50 |
|---|---|
| reality / causal scan (this pane, unbound, reported separately) | spent: about 3M |
| S0 bind + writers | 0.3M |
| S1 provenance | 0.8M |
| S2 pre-model receipt | 1.5M |
| S3 authority store / expiry | 1.0M |
| S4 transactions | 2.5M |
| S5 reconciliation | 0.8M |
| S6 tombstone + watchdog | 1.2M |
| S7 continuation + ContextImage | 0.8M |
| S8 Autonomy CI | 1.5M |
| S9 real canary | 0.6M |
| S10 vault / UKDL / CBR | 0.8M |
| recovery reserve | 1.0M |
| meta-optimization tax | 1.2M |

econ-succession: SEMANTIC LOWER BOUND 4M, LOWER 9M, P50 14M, P80 20M, P95 28M,
HARD AUTHORITY = the approved tier (P50 14M by default).
econ-contain-2 continuation (G, J, K, L): programme ceiling P50 35M (+12.2M over current spend),
P80 49M, P95 66M; L2 opened at cap 10M plus a 1M recovery reserve, the rest stays in the programme.

## 10. Approval surface

Type exactly `approve` (P50) or `approve p80` in the planning pane. It binds to packet sha
86ba1888c7bda34779eae9e21ba749ba638eb1b8dab132febf9bc59add83ca4d and authorizes, subject to
revalidation: S0-S10; programme econ-succession; programme econ-contain-2; reconciliation of L1
(settle the two dead holders from their transcripts, release 601); internal detach and rebind;
opening L2 without raising L1; launching WS-G and continuing G, J, K, L until VERIFIED_DONE or a
stop-loss. fd25efd1 is not reused; it is recorded INVALIDATED (drift). Edits to 5a-owned files
are included if no live 5a writer holds them dirty; otherwise they are coordinated first.
Excluded: settings.json, raising any exhausted lease, workstreams beyond the plan.
