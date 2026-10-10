# Context Rent: from a rotation that fires late to rent control in one pane -- Master Plan (PROPOSED)

Written 2026-10-10. Status: **APPROVED** (Owner "y", 2026-10-10, HARD STOP 16M). Approval surface = chat; this file is the durable copy.
Mode: EXECUTION (owners exist; no new OS). One bounded PLAN step: S4 host probe.

## 1. Reality Delta (measured read-only, 2026-10-10, HEAD 836c1121, branch feature/knowledge-acquisition)

Ledgers: `~/.claude/state/rollover/rollover-ledger.jsonl` (3,141 rows / 14 d), `~/.claude/state/gsd-autorun-ledger.jsonl`.

| fact | value |
|---|---|
| same-pane epoch rotation (`/kclear -> gate -> /clear -> /kresume`) | **LIVE, ON by default** since 2026-09-28 (`tools/rollover.py`, `hooks/rollover_wall.js`, `context-watchdog.py::_rollover_step`) |
| automatic `/clear` dispatched, 14 d | **292** (terminal-inbox 285, orca-exact 7) |
| successor claims / certified resumes / failed | 312 / 299 / 34 |
| gate verdicts | SAFE_TO_FORGET 291, REFUSED 40, NO_CAPSULE 13 |
| top withheld reasons | background child pending (23), no capsule (33), no obligations (5), custody (7) |
| rotation wall | `ADVISORY_PCT = 45` -> ~450K resident on a 1M window |
| shadow candidates | 1,505; would_rollover False 1,309 / True 196 |
| why not earlier | "worth it / robust, **but not at a work boundary**" = **449** (boundary = tree clean or HEAD advanced) |
| resident at candidate | p50 **384K**, p90 454K |
| fresh-session floor (call #1) | p50 **125K**, p90 146K |
| automatic fallback to /compact | 6 |
| ctx-rent S2 (`Apps\pp-ctx-rent`, HEAD 0f8713fe) | **broken half-edit**: `certs` NameError in `tools/rollover_replay.py`, plus rollover.py +2/-1, uncommitted |
| status-query path | none: every "how is it going" is a model turn at full resident |
| code that prints "open a fresh pane" | **none found** in hooks/modules; the advice is model-authored, from doctrine (memory `feedback_coordinator_pane_is_the_overrun`: "hand off to a fresh pane") and RESUMPTION files |

## 2. Root cause: why the advice is still "open a new pane"

Neither "no ASER" nor "no host API" is the cause. ASER exists and runs about 20 times a day. The causal chain is:

1. **The trigger fires too late.** The only certain trigger is the 45 % wall (~450K). The economic trigger
   that could fire earlier is vetoed by the work-boundary predicate in 449 of 645 positive economic
   judgements. Panes therefore live from 150K to 450K with nothing acting, which is the band the Owner reports.
2. **The floor is high.** A fresh session starts at ~125K (p50), not 30-50K. Rotation can only
   take ~384K down to ~125K, and nothing has attributed that floor (system + CLAUDE.md + rules + skill/agent
   listings + hook injections + MEMORY.md + first prompt).
3. **Doctrine fills the gap.** Because nothing fires in that band, sessions (me included) write "open a
   fresh pane" into closers, memories and RESUMPTION files. No guard catches the phrase.
4. **Status has no zero-model path,** so every check-in pays the full resident.
5. **Contributing:** a goal bound by cwd and already spent needs `goal-declare --owner`, which requires a TTY.
   That has pushed work into new panes (ctx-rent S2, ce-lifecycle-v/v2 bricking).

## 3. Host control (evidence or marked UNPROVEN)

- Selecting which past messages reach the next call: **NO** (host owns the transcript; only `/clear`, `/compact`,
  additionalContext). In-epoch GC/paging/projection pushdown = **EXTERNAL_LIMITATION**. Eviction = epoch rotation;
  paging = capsule pointers + on-demand Read in the successor; GC = what the capsule compiler leaves out.
- Replace the payload in the same visible pane: **YES, proven 292x** (typed `/clear` + courier `/kresume`, same terminal).
- Programmatic /clear: only via the C4 transport (terminal inbox / orca-exact / tmux-exact). Refuses rather than typing into focus.
- Zero-model status: UserPromptSubmit `decision:block` + reason shown to the Owner is the candidate channel. **UNPROVEN on
  this host build. S4 probes it first.**
- Per-class cache-read attribution from the provider: **NO**. Derivable from transcript usage plus static sizing (S1).

## 4. Owner map (dispositions)

| capability | owner | disposition |
|---|---|---|
| Context Rent measure | `tools/session_autopsy.py`, `tis_observed.py`, `rollover.usage_facts` | EXTEND (attribution by source) |
| UCVM / ASER (interactive) | `tools/rollover.py` + `rollover_wall.js` + `context-watchdog.py` | EXTEND (trigger) |
| ASER (missions) | `gsd_mission.py` + `gsd_epoch.py` (capsule-v2) | ALREADY_DONE / NO_WORK |
| ContextImage | rollover capsule (`compile_capsule`, `bootstrap` <= 4,000 chars) | ALREADY_DONE; EXTEND measurement only |
| rotation economics | `rollover.decide/_economics`, `rollover_econ.py`, `rollover_replay.py` (ctx-rent S2) | CONNECT: finish S2 here |
| work-boundary predicate | `rollover.at_boundary` | EXTEND (custody-safe boundary) |
| semantic GC / paging / SSM in-epoch | host | EXTERNAL_LIMITATION (documented, tested fallback = rotation) |
| status projection | `gsd_mission.py status`, `cep_gen2`, mission_spend, rollover status | CONNECT into a UserPromptSubmit fast path (new thin hook) |
| fresh-pane advice | none (doctrine) | IMPLEMENT detector on the existing self-seal path; RETIRE the memory advice |
| hot doctrine / schema floor | CLAUDE.md, rules, skills, agents, hook injections | MEASURE in S1, then RETIRE only what is mechanically enforced |
| goal rebind TTY | goal runtime | EXTERNAL to this mission; recorded as debt |
| ce-lifecycle-v3 WU-5 (ctx-rent canary) | parked backlog | MERGE: S2 is absorbed here; ce-lifecycle stays parked |

## 5. Vertical slices (each: commit(s) + V-gate + mutation drill + receipt)

- **S0 Repair ctx-rent S2** (pp-ctx-rent): the 3-line fix, 4 suites, 4 red-path gates, replay OLD vs NEW prior,
  receipt `vault/receipts/ctx-rent-s2-replay.json`. Lands the PROTOCOL rehydration basis on live.
- **S1 Rent attribution:** `session_autopsy` gains a per-call breakdown (floor vs growth; growth split into
  tool_result / assistant / user / injected context) plus a static floor census (system-adjacent files, skill
  and agent listings, hook additionalContext by hook). Done-gate 1/13 on 5 real transcripts, including this one.
  Self-host: later slices use it.
- **S2 Trigger at the economic point:** (a) replace `at_boundary` with a custody-safe boundary: the seal
  already records dirty paths, so the boundary means "no own uncommitted writes outside the capsule repo, and
  no pending children", not "tree clean". (b) An evidence-calibrated growth gate from the S0 replay (target:
  rotate around floor + ~150K instead of 450K), with thrash guard = min calls per epoch from measured C. The
  45 % wall stays as the backstop. Replay-proven before going live.
- **S3 Pane-advice extinction:** a Stop-chain detector (closer-guard family) for "open/new/fresh pane|session"
  advice given for economics. It converts the advice into the existing `_self_sealed_step` ask (/kclear). FIOS
  `OWNER_FORCED_PANE_ROTATION`. Amend memory `feedback_coordinator_pane_is_the_overrun` to "rotate in place".
- **S4 Zero-model status:** probe UserPromptSubmit block on this host build (1 call). If it holds: a
  deterministic keyword sentinel (fail-open, kill switch) for pure status queries renders the Program State
  Projection (missions, goals/spend, rollover state, HEAD/dirty) with zero model tokens. Advisory questions pass
  through untouched. If the probe fails: EXTERNAL_LIMITATION + the cheapest fallback (a status command run in
  the pane's shell) and no claim.
- **S5 Floor reduction:** only items S1 attributes and that are mechanically enforced elsewhere. Candidates:
  hook additionalContext injections that repeat on every prompt, unused skills/agents/plugins (sleepy), and
  oversize MEMORY.md lines. Each removal is paired with a test that the behaviour is still enforced.
- **S6 Canaries + Production Reality:** (1) same-pane long-history canary: a real pane crosses >= 3 epochs and
  the successor's first call is near the floor; (2) status canary: N status prompts in a 300K+ pane, model
  tokens ~0; (3) decision canary after rotation (the exam passes; a page fault = successor Reads the pointer);
  (4) crash during rotation at 4 points + duplicate dispatch, all converging (reuses the existing fault matrix);
  (5) cross-domain: one non-PP repo pane (e.g. GEX44 tmux route). Every number comes from transcript usage, not object sizes.
- **S7 Knowledge + CBR:** Knowledge Vault entry for the root cause; FIOS classes; UKDL HR candidates (dedupe
  against existing) / PR / traps; CBR ratchet: the rotation + status path is default for every pane; liveness gate.

## 6. Self-hosting

S1 attribution runs on this mission's own panes. After S2 goes live, this coordinating pane rotates in place at the
new trigger instead of being handed to a fresh pane. After S4, status reports to the Owner go through the zero-model path.

## 7. Execution shape (lesson: the coordinator pane is the overrun)

After approval this pane does one thing: arm a Ralph mission (`gsd_mission.py arm`) with this plan as the packet.
Workers run the slices in a `Apps\pp-ctx-same-pane` worktree with their own goal declared BEFORE work; no coordinator
`Set-Location` into the goal root. Live installs go by stage merge (live tree has foreign dirt), as in L1-L5.

## 8. Token budget (subscription-quota tokens, transcript-measured; floor ~125K/call)

| item | tokens |
|---|---|
| sunk related (ctx-rent 6.03M + S2 3.11M + ce-lifecycle-v..v3 ~16M) | ~25M, not re-spent |
| semantic lower bound (S0 + S2 + S3 + S4, no surprises) | ~3.5M |
| S0 ctx-rent repair + replay | 1.2M |
| S1 attribution | 1.5M |
| S2 trigger + replay proof | 2.0M |
| S3 advice detector | 0.8M |
| S4 probe + status path | 1.5M |
| S5 floor reduction | 1.5M |
| S6 canaries: long-pane 1.5M, adversarial rotation 0.8M, cross-domain 0.7M | 3.0M |
| S7 knowledge / UKDL / CBR | 0.7M |
| integration / live installs | 0.8M |
| proof reserve | 1.0M |
| recovery reserve | 1.0M |
| **LOWER / P50 / P80 / P95** | **7M / 11M / 15M / 21M** |
| **HARD STOP** | **16M**: halt, receipt, Owner decides |

Confidence: medium on S0-S4 (owners known, measured), low on S5/S6 (floor composition unmeasured, real crossings spend quota).
Estate-wide savings opportunity (ESTIMATE, to be measured by S1/S6): if rotation moves from ~384K p50 resident to
~275K, interactive calls fall roughly 25-30 %. Every 10K cut from the 125K floor saves ~8 % of every call on every pane.
Status check-ins move from ~300K+ to ~0.

## 9. Done-gates

The prompt's 18 Master Done-Gates hold, with these declared up front as EXTERNAL_LIMITATION (detected, tested fallback,
no Owner mechanics): in-epoch selective omission (gates 3/4/5 are met at the epoch boundary, not inside an epoch);
provider-side per-class cache attribution (gate 1 is met by transcript plus static census).

## 10. Rollback

Every change sits behind an existing or new kill switch (`CPP_ROLLOVER_ACTIVE`, `CPP_ROLLOVER_ECONOMIC`, a new
`CPP_STATUS_FASTPATH`, `CPP_PANE_ADVICE_GUARD`); `git revert` per micro-commit; the 45 % wall is never removed.
