# Master Plan: same-pane Owner capital, self-hosted on ctx-rent-a2 (PROPOSED 2026-10-11)

Packet: `~/.claude/state/capital-authority/packets/owner-capital-ctx-rent-2026-10-11.json` (sha in the approval
message). Goals: `econ-succession-a1` (architecture delta) and `ctx-rent-a2` (original mission residual).
`econ-succession` keeps its own applied 20M programme (S1-S10) and is not part of this packet.

## 1. Reality delta (read-only, measured this session)

- ctx-rent-a2 `goal-status`: cap 14,000,000, used 12,880,278 = settled 10,117,468 + open 2,762,810, remaining 1,119,722,
  lease L1, binding since 2026-10-11T08:27:27, not exhausted. Open holds: 1 each in sessions 262be369, 47f3da08,
  b8ff709c (liveness UNKNOWN; reconciler = econ-succession S5).
- `goal-autopsy`: 3 panes, 122 calls, 20,894,119 processed (262be369 56 calls / 10.0M; 47f3da08 24 / 4.0M;
  b8ff709c 42 / 6.9M, 2 refusals). The autopsy reports bound_processed 0 while the ledger shows 10.1M settled:
  the two instruments disagree. That's an instrument defect to fix before any per-slice claim.
- econ-succession: programme 20,000,000 APPLIED (approval uuid 25a5410c, same pane, no terminal), used 3,757,467,
  remaining 16,242,533. S0 sealed; S1-S10 open.
- econ-succession-a1: plan `vault/plans/econ-succession-2026-10-11-A1-same-pane-capital.md` (D1-D8) and packet
  `same-pane-capital-2026-10-11.json` exist, NOT approved; goal has no cap and no binding. Commit 68057009 (HEAD~1)
  registered the capture leg in `hooks/econ_admission.js`.
- Owner Capital Authority (`modules/provider_routing/capital_authority.py`) already provides: provenance from
  transcript fields the model cannot author (type=user, origin.kind=human, promptSource typed|queued, string
  content); approval bound to the packet sha256 shown in an earlier assistant entry; per-(sha, goal) idempotence;
  drift revalidation (500K); expiry; P95 cap on `modify`; same-pane `revoke`; append-only capsules; detached
  apply leg spawned by the UserPromptSubmit hook (zero model calls).
- Four files (ctx-rent-a2 slice B, mtimes 11:58-12:03): writer.py (compact mirror: title + TRIGGER, list_hard_rules
  reads the archive), test_hard_rules.py, test_hard_rules_mirror.py (V-HRM-COMPACT, threshold 12/12), CLAUDE.md
  (-147 lines, mirror regenerated). The diffs match the plan; no foreign hunks seen. The tree has ~56 other dirty files
  from other writers: commits use pathspecs only.
- Backup `~/.claude/backups/rules-20261011-114632` exists (29 files).

## 2. Defects found in the scan (new)

- D9a `apply_pending` resolves the transcript from `approvals.jsonl[-1]`, the latest row from ANY pane/project. An
  approval in pane A is checked against pane B's transcript whenever B's prompt lands first. Safety holds (sha
  binding) but liveness fails: the approval is silently not applied until a later sweep. Fix: resolve per row,
  approval rows first, by the row's own session.
- D9b The pending-sweep fires a python spawn on every Owner prompt in every pane while any pair is outstanding
  (the unapproved same-pane packet keeps 2 pairs outstanding indefinitely). Bound: per-transcript once per
  packet sha, and outstanding pairs past expiry drop out.
- D10 Capital-decision freeze is absent: fd25efd1 was invalidated by 970,635 of spend while waiting; the
  econ-succession scan cost 4.9M before approval (CAPITAL_REQUEST_SELF_INFLATION, confirmed).

## 3. Workstreams (all EXECUTION unless noted; no ULTRA-PLAN: the architecture is already designed)

| ws | content | owner | goal | P50 |
|---|---|---|---|---|
| W0 | writer census on capital_authority.py / econ_admission.js / owner_capital_capture.js; bind session | - | a1 | 0.2M |
| S1 | provenance spike (interactive vs -p vs --bg), PLAN 6 calls | econ-succession | econ-succession | (its row) |
| S2+S3 | approve verb + receipt in econ_admission; receipts, expiry, INVALIDATED rows | econ-succession | econ-succession | (its rows) |
| D1-D8 | as written in the A1 plan (guard effect semantics, one-word lexicon bound to exactly one displayed packet, AuthorityChanged release, cap-only goal -> programme + L2 lease, control-plane role + self-inflation guard, pre-dispatch subagent admission, Autonomy CI, vault) | A1 plan | a1 | 6.3M |
| D9 | apply_pending per-row transcript + sweep bound (section 2) | capital_authority / capture hook | a1 | 0.4M |
| D10 | capital freeze: an outstanding packet for goal G makes econ_admission refuse non-capital model work bound to G; drift allowance stays as the backstop | econ_admission | a1 | 0.6M |
| R1 | ctx-rent-a2 self-host: after D4 + D3 pass red/green, the APPLIED capsule opens L2 for ctx-rent-a2 inside its programme and releases its hold, no Owner action | - | ctx-rent-a2 | 0.3M |
| B' | slice B closeout: verify ~/.claude edits vs backup, independent review of the 4 files (pp-code-reviewer), suites, EGCC 10/12 classification/fix, path-scoped micro-commits, plan 1.1, RESUMPTION_FILE | ctx-rent-a2 plan | ctx-rent-a2 | 2.7M |
| M | fresh epoch (/kclear -> /clear -> /kresume), `context_floor_census.py <own sid>` vs 122,093 baseline | ctx-rent-a2 plan | ctx-rent-a2 | 0.5M |
| H | econ-succession S1 canary on the reduced floor (spend charged to econ-succession; measurement here) | ctx-rent-a2 plan | ctx-rent-a2 | 0.3M |
| C-L | remaining ctx-rent-a2 slices C, D, E (mostly CONNECT: status CLIs exist), F, G, I, J/K overhead, L | ctx-rent-a2 plan | ctx-rent-a2 | 8.7M |

Order: W0 -> S1 -> S2/S3 -> D9 -> D4 -> D3 -> D10 -> D2 -> D1 -> D6 -> D7 (Autonomy CI, incl. the 27 adversarial
cases of the prompt and the model-only self-escalation canary) -> R1 -> B' -> M -> H -> C+F -> I -> D+E+G -> J/K ->
L + D8 (vault, FIOS, UKDL, CBR, retirement of terminal doctrine from the normal path). Rotate at every sealed ws.
Coordinator pane exits after launch (memory: the coordinator pane is the overrun).

## 4. Variance autopsy (ctx-rent-a2, 1.8M planned for A+B vs 12.88M ledger)

- Plan priced tokens per slice, never calls x floor. Actual: 122 calls at 163-179K/call.
- Fixed floor 122,093/call x 122 calls = ~14.9M of 20.9M processed (~71%) = Context Rent.
- History growth above the floor = ~6.0M (~29%) = Context Rent (session).
- Productive edits (4 repo files + ~6 always-loaded files) and the census tool (slice A CAPEX, 23 gates) are inside
  those calls; per-slice split UNKNOWN until the autopsy/ledger disagreement is fixed (B').
- 2.76M of the 12.88M is open holds in 3 sessions; if dead, real settled spend is 10.12M.
- Conclusion: CONTEXT_RENT_DRIVES_CAPITAL_VARIANCE CONFIRMED; the residual forecast below prices calls x floor.

## 5. Budget (processed tokens, subscription quota)

econ-succession-a1 (architecture): SLB 2.8M / LOWER 4.5M / P50 7.3M / P80 10M / P95 13.5M (low-medium confidence).
ctx-rent-a2 residual: SLB 5M / LOWER 9M / P50 13.1M / P80 17.1M / P95 23.1M (low-medium; the parent ran 7x on A+B).
Programme ceilings (absolute): ctx-rent-a2 P50 26M / P80 30M / P95 36M (from cap 14M, used 12.88M);
econ-succession-a1 P50 7.3M / P80 10M / P95 13.5M. econ-succession unchanged (20M, 16.24M left).
Lease policy: per slice, L(n+1) = slice P80 + 0.5M reserve, never above 3M; reforecast after each sealed slice.
Reserves inside each ceiling: proof 1.0M, closeout/recovery 1.0M.

## 6. Stop-losses / invalidators / exclusions

Stop: a ws exceeds 3x its P50 row; H shows <10% per-call drop vs 28a5bd61 (stop C-L scaling, return); an
anti-self-escalation test cannot be made red; a ceiling would be crossed; a live writer holds an owner file.
Invalidators: packet sha differs from the one shown; settled+open moves >500K before approval; plan scope changes;
expiry 2026-10-14T00:00Z before approval; `revoke <goal>`.
Excluded: settings.json/plugin edits, deploys, raising any exhausted lease in place, ctx-same-pane (its packet
stays for a separate Owner decision), editing tools/gsd_mission.py, deleting worktrees, econ-contain-2 beyond the
existing econ-succession canary.
